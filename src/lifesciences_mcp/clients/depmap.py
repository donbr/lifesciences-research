"""DepMap client: cancer cell-line dependencies and genotype-selective contrasts.

Two data planes (ADR-681 design):
1. **Provenance-matched genotype contrast** — pure, offline computation over Broad DepMap
   24Q2 gene-effect matrices (checksum-pinned upstream, never fetched here). This is the
   key new capability: does loss of a tumor suppressor make cells selectively dependent on
   a target? It is the ``demeter_validation.py`` logic from sprime-lung-repro promoted to a
   reusable, tested tool. numpy-only (no scipy dependency).
2. **Live cross-validation** — the Sanger Cell Model Passports REST API
   (https://api.cellmodelpassports.sanger.ac.uk, JSONAPI v1.0). Different dataset
   (Sanger Project Score, not Broad 24Q2) — always provenance-labeled. Third-party app use
   requires prior permission (depmap@sanger.ac.uk); non-commercial only.

Follows ADR-001 (async httpx, Fuzzy-to-Fact), ADR-004 (no shutdown hooks), ADR-006 (clients/).
"""

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.depmap import (
    DataSource,
    DepMapModelCandidate,
    GenotypeContrast,
)
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    Pagination,
    PaginationEnvelope,
)

# Genotype encoding (matches the S′ pipeline / DepMap damaging-mutation matrix):
WT_CALL = 0
MUT_CALL = 2  # 1 (and anything else) = excluded

# Sanger Cell Model Passports mutation-cohort types (endpoint /models/by_<type>/<gene>).
# NOTE: "mutation" = ANY variant in the gene (very broad — e.g. by_mutation/RB1 returns
# ~2185/2266 models). It is NOT the paper's damaging/homozygous call. Use a specific
# damaging type (frameshift/deletion/splice_variant) or reconcile against the mutations
# dataset to approximate the S′ genotype definition.
MutationType = Literal[
    "mutation", "frameshift", "snp", "insertion", "deletion", "splice_variant"
]


# ---------------------------------------------------------------------------
# Pure statistics (numpy-free core so it is trivially testable and dependency-light)
# ---------------------------------------------------------------------------
def _rankdata(values: Sequence[float]) -> list[float]:
    """Average ranks (1-based), ties share the mean rank. Pure Python."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    n = len(values)
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # mean of 1-based ranks i+1..j+1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def mannwhitney_u_p(a: Sequence[float], b: Sequence[float]) -> float:
    """Two-sided Mann-Whitney U p-value via normal approximation with tie correction.

    Adequate for the cohort sizes used here (n >= 5 per side, enforced upstream).
    Returns NaN if either sample is empty.
    """
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return float("nan")
    ranks = _rankdata(list(a) + list(b))
    r1 = sum(ranks[:n1])
    u1 = r1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    n = n1 + n2
    # tie correction
    counts: dict[float, int] = {}
    for v in list(a) + list(b):
        counts[v] = counts.get(v, 0) + 1
    tie_term = sum(t**3 - t for t in counts.values())
    sigma_sq = (n1 * n2 / 12.0) * ((n + 1) - tie_term / (n * (n - 1))) if n > 1 else 0.0
    if sigma_sq <= 0:
        return 1.0
    z = (u1 - mu) / math.sqrt(sigma_sq)
    # two-sided p from standard normal survival, with 0.5 continuity correction
    z = max(0.0, abs(z) - 0.5 / math.sqrt(sigma_sq)) if sigma_sq else abs(z)
    p = math.erfc(abs(z) / math.sqrt(2.0))  # 2 * (1 - Phi(|z|))
    return min(1.0, p)


def bh_fdr(pvals: Sequence[float]) -> list[float]:
    """Benjamini-Hochberg FDR. NaNs pass through as NaN."""
    idx = [i for i, p in enumerate(pvals) if p == p]  # not NaN
    m = len(idx)
    q = [float("nan")] * len(pvals)
    order = sorted(idx, key=lambda i: pvals[i])
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        prev = min(prev, pvals[i] * m / (rank + 1))
        q[i] = prev
    return q


def compute_genotype_contrast(
    target_gene: str,
    genotype_gene: str,
    gene_effect_by_model: Mapping[str, float],
    genotype_by_model: Mapping[str, int],
    *,
    min_lines: int = 5,
    data_source: DataSource = "broad_24q2",
) -> GenotypeContrast:
    """WT-vs-mutant dependency contrast for one target under one genotype.

    Args:
        target_gene: gene whose dependency is contrasted.
        genotype_gene: tumor suppressor defining WT (call 0) vs mutant (call 2) cohorts.
        gene_effect_by_model: {model_id: Chronos/gene-effect value} for ``target_gene``
            (negative = dependent). NaN values are ignored.
        genotype_by_model: {model_id: 0|1|2} damaging-mutation call for ``genotype_gene``.
        min_lines: minimum per-cohort n; below this the contrast is not tested.
        data_source: provenance label.

    Returns:
        GenotypeContrast (delta_dep < 0 => mutant-selective).
    """
    wt, mu = [], []
    for model, eff in gene_effect_by_model.items():
        if eff is None or (isinstance(eff, float) and eff != eff):  # skip None/NaN
            continue
        call = genotype_by_model.get(model)
        dep = -float(eff)  # dependency: higher = more dependent
        if call == WT_CALL:
            wt.append(dep)
        elif call == MUT_CALL:
            mu.append(dep)

    n_wt, n_mut = len(wt), len(mu)
    if n_wt < min_lines or n_mut < min_lines:
        return GenotypeContrast(
            target_gene=target_gene,
            genotype_gene=genotype_gene,
            n_wt=n_wt,
            n_mut=n_mut,
            direction="none",
            min_lines=min_lines,
            tested=False,
            data_source=data_source,
            note=f"cohort too small to test (need n>={min_lines} per side; got WT={n_wt}, MUT={n_mut})",
        )

    mean_wt = sum(wt) / n_wt
    mean_mut = sum(mu) / n_mut
    delta = mean_wt - mean_mut
    p = mannwhitney_u_p(wt, mu)
    direction = "mutant-selective" if delta < 0 else "WT-selective"
    return GenotypeContrast(
        target_gene=target_gene,
        genotype_gene=genotype_gene,
        n_wt=n_wt,
        n_mut=n_mut,
        mean_dep_wt=round(mean_wt, 4),
        mean_dep_mut=round(mean_mut, 4),
        delta_dep=round(delta, 4),
        direction=direction,
        mw_p=p,
        min_lines=min_lines,
        tested=True,
        data_source=data_source,
    )


class DepMapClient(LifeSciencesClient):
    """Async client for DepMap: Sanger Cell Model Passports REST + local contrast core."""

    BASE_URL = "https://api.cellmodelpassports.sanger.ac.uk"

    def __init__(self) -> None:
        super().__init__(base_url=self.BASE_URL)

    # ---- Data plane 1: provenance-matched genotype contrast (offline, tested) ----
    def genotype_contrast(
        self,
        target_gene: str,
        genotype_gene: str,
        gene_effect_by_model: Mapping[str, float],
        genotype_by_model: Mapping[str, int],
        *,
        min_lines: int = 5,
        data_source: DataSource = "broad_24q2",
    ) -> GenotypeContrast:
        """Compute a WT-vs-mutant dependency contrast (see module-level function)."""
        return compute_genotype_contrast(
            target_gene,
            genotype_gene,
            gene_effect_by_model,
            genotype_by_model,
            min_lines=min_lines,
            data_source=data_source,
        )

    # ---- Data plane 2: Sanger Cell Model Passports REST (model resolution + cohorts) ----
    # Confirmed endpoints (JSONAPI v1.0 — https://depmap.sanger.ac.uk/documentation/api/endpoints/):
    #   /models                          list of all models (meta.count = total, ~2266)
    #   /models/<SIDM#####>              single model
    #   /models/<source>/<source_id>     resolve by external id (CCLE_ID, cosmic_id, model_name, ...)
    #   /models/by_<mut_type>/<gene>     models with a <mut_type> mutation in <gene>  (genotype cohort)
    #   /models/<id>/datasets/<name>     per-model datasets: mutations | cancer_drivers | genecnv | growth_rate
    # NOT served as a queryable endpoint: CRISPR gene-effect values. `crispr_ko_available` is only a
    #   boolean flag; the dependency matrix is a Project Score / Data Miner file download (probes to
    #   /datasets/crispr and /datasets/crispr_ko return empty). Genotype CONTRASTS therefore use the
    #   offline matrix core above for BOTH providers; this REST API supplies model + genotype resolution.
    # Policy: non-commercial; third-party application use requires Sanger permission (depmap@sanger.ac.uk).

    @staticmethod
    def _candidate(rec: dict[str, Any]) -> DepMapModelCandidate:
        names = (rec.get("attributes") or {}).get("names") or []
        return DepMapModelCandidate(
            model_id=str(rec.get("id")),
            model_name=names[0] if names else None,
            lineage=None,  # tissue/lineage is on the linked sample, not model attributes
            data_source="sanger_project_score",
        )

    @staticmethod
    def _unexpected(e: Exception, inp: str) -> ErrorEnvelope:
        return ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"Unexpected error: {e!r}",
                recovery_hint="Check network and the Sanger API (see /documentation/api/endpoints).",
                invalid_input=inp,
            )
        )

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._get(
            path, params=params or {}, headers={"Accept": "application/vnd.api+json"}
        )
        resp.raise_for_status()
        return resp.json()

    async def get_model(self, model_id: str) -> DepMapModelCandidate | ErrorEnvelope:
        """Strict: fetch one model by Sanger id (SIDM#####)."""
        mid = model_id.strip()
        try:
            body = await self._get_json(f"/models/{mid}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.ENTITY_NOT_FOUND,
                        message=f"No model '{mid}' in Cell Model Passports",
                        recovery_hint="Resolve via /models/<source>/<source_id> (e.g. CCLE_ID, model_name).",
                        invalid_input=mid,
                    )
                )
            return ErrorEnvelope.upstream_error(e.response.status_code)
        except Exception as e:
            return self._unexpected(e, mid)
        data = body.get("data")
        if not data:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"No model '{mid}'",
                    recovery_hint="Check the SIDM id or resolve by source id.",
                    invalid_input=mid,
                )
            )
        return self._candidate(data if isinstance(data, dict) else data[0])

    async def resolve_model(
        self, source: str, source_id: str
    ) -> DepMapModelCandidate | ErrorEnvelope:
        """Strict: resolve a model by external identifier.

        Source is case-insensitive, id is case-sensitive. Examples:
        resolve_model("CCLE_ID", "769P_KIDNEY"), resolve_model("model_name", "NCI-H1581").
        """
        key = f"{source}/{source_id}"
        try:
            body = await self._get_json(f"/models/{source}/{source_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.ENTITY_NOT_FOUND,
                        message=f"No model for {key}",
                        recovery_hint="Check the identifier source and value (id is case-sensitive).",
                        invalid_input=key,
                    )
                )
            return ErrorEnvelope.upstream_error(e.response.status_code)
        except Exception as e:
            return self._unexpected(e, key)
        data = body.get("data")
        if not data:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"No model for {key}",
                    recovery_hint="Verify the identifier.",
                    invalid_input=key,
                )
            )
        return self._candidate(data if isinstance(data, dict) else data[0])

    async def search_models(
        self, query: str, *, limit: int = 10
    ) -> PaginationEnvelope[DepMapModelCandidate] | ErrorEnvelope:
        """Fuzzy Phase 1: best-effort model search by name.

        Cell Model Passports is filter/resolve-based, not full-text. This tries a JSONAPI name
        filter; if you already know an identifier prefer resolve_model() (exact) or get_model()
        (SIDM). The exact array-column filter operator should be confirmed against /swagger — on
        failure this returns UPSTREAM_ERROR with that hint.
        """
        if len(query) < 2:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message="Query must be at least 2 characters",
                    recovery_hint="Provide at least 2 characters",
                    invalid_input=query,
                )
            )
        flt = json.dumps([{"name": "names", "op": "any", "val": query}])
        try:
            body = await self._get_json("/models", params={"filter": flt, "page[size]": limit})
        except httpx.HTTPStatusError as e:
            return ErrorEnvelope.upstream_error(
                e.response.status_code,
                detail="Confirm the /models names-filter operator against /swagger.",
            )
        except Exception as e:
            return self._unexpected(e, query)
        recs = body.get("data") or []
        items = [self._candidate(r) for r in recs[:limit]]
        if not items:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"No models matched '{query}'",
                    recovery_hint="Try resolve_model('model_name', <exact name>) or an external id.",
                    invalid_input=query,
                )
            )
        return PaginationEnvelope(
            items=items,
            pagination=Pagination(
                cursor=None,
                total_count=body.get("meta", {}).get("count", len(items)),
                page_size=limit,
            ),
        )

    async def models_with_mutation(
        self, gene: str, mut_type: MutationType = "mutation", *, max_models: int = 500
    ) -> PaginationEnvelope[DepMapModelCandidate] | ErrorEnvelope:
        """Genotype resolution: the cohort of models carrying a <mut_type> mutation in <gene>.

        Uses /models/by_<mut_type>/<gene>, following JSONAPI links.next up to max_models.
        WARNING: mut_type="mutation" matches ANY variant (very broad — e.g. RB1 returns ~2185/2266
        models), which is NOT the paper's damaging/homozygous call. Prefer a specific damaging type
        (frameshift/deletion/splice_variant) or reconcile against the mutations dataset before using
        these cohorts in a contrast. total_count is meta.count.
        """
        sym = gene.strip().upper()
        items: list[DepMapModelCandidate] = []
        total: int | None = None
        path: str | None = f"/models/by_{mut_type}/{sym}"
        params: dict[str, Any] | None = {"page[size]": min(max_models, 100)}
        try:
            while path and len(items) < max_models:
                body = await self._get_json(path, params)
                params = None  # links.next already carries the query string
                if total is None:
                    total = (body.get("meta") or {}).get("count")
                for r in body.get("data") or []:
                    items.append(self._candidate(r))
                    if len(items) >= max_models:
                        break
                nxt = (body.get("links") or {}).get("next")
                # next is an absolute URL; keep only the path+query so base_url (https) is used
                path = nxt[nxt.find("/models"):] if nxt and "/models" in nxt else None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.ENTITY_NOT_FOUND,
                        message=f"No '{mut_type}' cohort for gene '{sym}'",
                        recovery_hint="Check the gene symbol and mut_type "
                        "(mutation|frameshift|snp|insertion|deletion|splice_variant).",
                        invalid_input=sym,
                    )
                )
            return ErrorEnvelope.upstream_error(e.response.status_code)
        except Exception as e:
            return self._unexpected(e, sym)
        return PaginationEnvelope(
            items=items,
            pagination=Pagination(cursor=None, total_count=total, page_size=len(items)),
        )
