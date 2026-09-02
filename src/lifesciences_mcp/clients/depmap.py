"""DepMap client: cancer cell-line dependencies and genotype-selective contrasts.

Two data planes:

1. **Provenance-matched genotype contrast** - pure, offline computation over a cached
   gene-effect matrix. This is the key capability: does loss of a tumour suppressor make
   cells selectively dependent on a target? It is the ``demeter_validation.py`` logic from
   sprime-lung-repro promoted to a reusable, tested function. The statistics are hand-rolled
   so the package gains no numpy or scipy dependency.

2. **Sanger Cell Model Passports REST** (https://api.cellmodelpassports.sanger.ac.uk,
   JSON:API v1.0) for model resolution and genotype cohorts. Different dataset from Broad
   (Project Score), so every record is provenance-labelled. Non-commercial; third-party
   application use requires prior permission (depmap@sanger.ac.uk).

**Gene effect is never fetched live.** ``crispr_ko_available`` is a boolean flag only, and
probes to ``/datasets/crispr`` and ``/datasets/crispr_ko`` return empty: the dependency
matrix is a Project Score / Data Miner file. Contrasts are therefore matrix-based for both
providers, and this API supplies model and genotype resolution only.

**Fuzzy search is local, by necessity.** The upstream ``names`` filter accepts only the
``any`` operator (every other operator returns HTTP 500) and matches exactly and
case-sensitively. Measured 2026-09-02: ``a549``, ``MCF-7`` and ``hela`` return nothing,
while ``HeLa`` returns a hit and ``HELA`` does not, so no single server-side transformation
works. The whole catalogue is instead fetched once with a sparse fieldset (2266 rows,
250 KB, ~1.7 s) and matched against a normalised in-process index.

Follows ADR-001 (async httpx, Fuzzy-to-Fact), ADR-004 (no shutdown hooks), ADR-006 (clients/).
"""

import asyncio
import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.depmap import (
    MUTATION_TYPES,
    SIDM_BARE_PATTERN,
    SIDM_CURIE_PATTERN,
    CellModel,
    DataSource,
    DependencyRecord,
    DepMapCrossReferences,
    GenotypeContrast,
    MutationType,
)
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    Pagination,
    PaginationEnvelope,
)

# Genotype encoding (matches the S-prime pipeline / DepMap damaging-mutation matrix):
WT_CALL = 0
MUT_CALL = 2  # 1 (and anything else) = excluded

# Access terms, surfaced to agents rather than buried in a docstring.
ACCESS_TERMS = (
    "Cell Model Passports data is non-commercial; third-party application use requires "
    "prior permission from depmap@sanger.ac.uk."
)

_PUNCTUATION = re.compile(r"[^a-z0-9]+")


def normalize_alias(value: str) -> str:
    """Fold a cell-line name to a comparable key.

    Case-fold, then strip every non-alphanumeric character, so ``A549``, ``a549``,
    ``MCF-7``, ``MCF7`` and ``HeLa`` all reduce to a form that can be compared. The upstream
    filter does none of this, which is why it fails on the names researchers actually type.
    """
    return _PUNCTUATION.sub("", value.casefold())


# ---------------------------------------------------------------------------
# Pure statistics (no numpy or scipy, so the core is trivially testable)
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
    sigma = math.sqrt(sigma_sq)
    # two-sided p from the standard normal survival, with a 0.5 continuity correction
    z = max(0.0, abs((u1 - mu) / sigma) - 0.5 / sigma)
    p = math.erfc(z / math.sqrt(2.0))  # 2 * (1 - Phi(|z|))
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
    mutation_type: MutationType | None = None,
) -> GenotypeContrast:
    """WT-vs-mutant dependency contrast for one target under one genotype.

    This is an internal function rather than a tool. Exposed as a tool it would require an
    agent to serialise the full per-model vectors (roughly 2000 entries) on every call, so
    it could not be used at all; ``genotype_contrast_by_gene`` loads the vectors from the
    cached release and calls this.

    Args:
        target_gene: gene whose dependency is contrasted.
        genotype_gene: tumour suppressor defining WT (call 0) vs mutant (call 2) cohorts.
        gene_effect_by_model: {model_id: gene-effect value} for ``target_gene``
            (negative = dependent). None and NaN values are dropped from both cohorts.
        genotype_by_model: {model_id: 0|1|2} damaging-mutation call for ``genotype_gene``.
        min_lines: minimum per-cohort n; below this the contrast is not tested.
        data_source: provenance label.
        mutation_type: the variant class the mutant cohort was built from, recorded on the
            result so a reader can see how the cohort was defined.

    Returns:
        GenotypeContrast. delta_dep < 0 means the mutant cohort is more dependent.
    """
    wt, mut = [], []
    for model, eff in gene_effect_by_model.items():
        if eff is None or (isinstance(eff, float) and eff != eff):  # skip None/NaN
            continue
        call = genotype_by_model.get(model)
        dep = -float(eff)  # dependency: higher = more dependent
        if call == WT_CALL:
            wt.append(dep)
        elif call == MUT_CALL:
            mut.append(dep)

    n_wt, n_mut = len(wt), len(mut)
    if n_wt < min_lines or n_mut < min_lines:
        return GenotypeContrast(
            target_gene=target_gene,
            genotype_gene=genotype_gene,
            n_wt=n_wt,
            n_mut=n_mut,
            direction="none",
            min_lines=min_lines,
            tested=False,
            mutation_type=mutation_type,
            data_source=data_source,
            note=(
                f"cohort too small to test (need n>={min_lines} per side; "
                f"got WT={n_wt}, MUT={n_mut})"
            ),
        )

    mean_wt = sum(wt) / n_wt
    mean_mut = sum(mut) / n_mut
    delta = mean_wt - mean_mut
    p = mannwhitney_u_p(wt, mut)
    # An exact tie is neither cohort's result. Defaulting it to WT-selective would report a
    # direction the data does not support.
    if delta < 0:
        direction = "mutant-selective"
    elif delta > 0:
        direction = "WT-selective"
    else:
        direction = "none"
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
        mutation_type=mutation_type,
        data_source=data_source,
    )


class DepMapClient(LifeSciencesClient):
    """Async client for DepMap: Sanger Cell Model Passports REST plus the contrast core.

    Rate limiting: 1 request/second with exponential backoff. The upstream publishes no
    documented limit and third-party use is permission-gated, so this matches the
    conservative rate the repository uses for other unspecified APIs. Cohort pagination is
    the real exposure: an RB1 deletion cohort is 501 models across several sequential pages.
    """

    BASE_URL = "https://api.cellmodelpassports.sanger.ac.uk"

    # Confirmed endpoints (JSON:API v1.0, https://api.cellmodelpassports.sanger.ac.uk/swagger):
    #   /models                       all models; meta.count = 2266
    #   /models/<SIDM#####>           single model
    #   /models/<source>/<source_id>  resolve by external id. CCLE_ID and cosmic_id confirmed;
    #                                 model_name is NOT a valid source (404)
    #   /models/by_<mut_type>/<gene>  genotype cohort
    #   /models/<id>/datasets/<name>  mutations | cancer_drivers | genecnv | growth_rate

    _MIN_INTERVAL = 1.0
    _MAX_RETRIES = 3

    def __init__(self) -> None:
        super().__init__(base_url=self.BASE_URL)
        self._last_request_time: float = 0.0
        self._request_lock = asyncio.Lock()
        self._alias_index: list[tuple[str, CellModel]] | None = None
        self._index_lock = asyncio.Lock()

    # ---- Identifier handling (Fuzzy-to-Fact Phase 2) ------------------------
    @staticmethod
    def validate_id(model_id: str) -> bool:
        """True if ``model_id`` is a well-formed SIDM CURIE."""
        return bool(SIDM_CURIE_PATTERN.match(model_id))

    @staticmethod
    def normalize_id(model_id: str) -> str | None:
        """Return the CURIE form, accepting the bare upstream form; None if unrecognisable."""
        candidate = model_id.strip()
        if SIDM_CURIE_PATTERN.match(candidate):
            return candidate
        if SIDM_BARE_PATTERN.match(candidate):
            return f"SIDM:{candidate[4:]}"
        return None

    @staticmethod
    def _unresolved(model_id: str) -> ErrorEnvelope:
        return ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=f"The input '{model_id}' is not a valid Cell Model Passports CURIE.",
                recovery_hint=(
                    "Call search_models to resolve the name first, then pass the returned "
                    "CURIE (format SIDM:NNNNN)."
                ),
                invalid_input=model_id,
            )
        )

    # ---- Error mapping (attributed to THIS data source) ---------------------
    @staticmethod
    def _upstream_error(status_code: int, invalid_input: str, detail: str = "") -> ErrorEnvelope:
        """Map an upstream failure, naming Cell Model Passports rather than another API."""
        code = ErrorCode.RATE_LIMITED if status_code == 429 else ErrorCode.UPSTREAM_ERROR
        message = f"Cell Model Passports API returned error {status_code}."
        if detail:
            message = f"{message} {detail}"
        hint = (
            "Retry after a few seconds."
            if status_code == 429
            else "Cell Model Passports may be temporarily unavailable. Retry later."
        )
        return ErrorEnvelope(
            error=ErrorDetail(
                code=code, message=message, recovery_hint=hint, invalid_input=invalid_input
            )
        )

    @staticmethod
    def _unexpected(e: Exception, inp: str) -> ErrorEnvelope:
        return ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"Cell Model Passports request failed: {e!r}",
                recovery_hint="Check network connectivity and retry.",
                invalid_input=inp,
            )
        )

    # ---- Transport ----------------------------------------------------------
    async def _rate_limited_get(self, path: str, params: dict[str, Any] | None) -> httpx.Response:
        """GET with 1 req/sec pacing and exponential backoff on 429."""
        async with self._request_lock:
            loop = asyncio.get_event_loop()
            elapsed = loop.time() - self._last_request_time
            if elapsed < self._MIN_INTERVAL:
                await asyncio.sleep(self._MIN_INTERVAL - elapsed)

            client = await self._get_client()
            response = None
            for attempt in range(self._MAX_RETRIES):
                response = await client.get(
                    path,
                    params=params or {},
                    headers={"Accept": "application/vnd.api+json"},
                )
                self._last_request_time = loop.time()
                if response.status_code != 429:
                    return response
                if attempt < self._MAX_RETRIES - 1:
                    await asyncio.sleep(2**attempt)  # 1s, 2s
            assert response is not None
            return response

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._rate_limited_get(path, params)
        resp.raise_for_status()
        return resp.json()

    # ---- Record mapping -----------------------------------------------------
    @staticmethod
    def _cell_model(rec: dict[str, Any]) -> CellModel | None:
        """Map one JSON:API record to a CellModel, or None if the id is unusable."""
        model_id = DepMapClient.normalize_id(str(rec.get("id", "")))
        if model_id is None:
            return None
        attrs = rec.get("attributes") or {}
        names = [str(n) for n in (attrs.get("names") or [])]
        available = sorted(
            key[: -len("_available")]
            for key, value in attrs.items()
            if key.endswith("_available") and value
        )
        xrefs = DepMapCrossReferences(
            ccle=attrs.get("ccle_id") or None,
            cosmic=str(attrs["cosmic_id"]) if attrs.get("cosmic_id") else None,
        )
        return CellModel(
            id=model_id,
            name=names[0] if names else model_id,
            aliases=names,
            # Tissue and lineage live on the linked sample, not on model attributes, so they
            # are omitted here rather than guessed at.
            lineage=attrs.get("tissue") or None,
            model_type=attrs.get("model_type") or None,
            data_available=available,
            data_source="sanger_project_score",
            cross_references=xrefs if (xrefs.ccle or xrefs.cosmic) else None,
        )

    @staticmethod
    def _envelope(
        models: list[CellModel],
        *,
        slim: bool,
        cursor: str | None,
        total_count: int | None,
        page_size: int,
    ) -> PaginationEnvelope[Any]:
        items: list[Any] = [m.slim() for m in models] if slim else list(models)
        return PaginationEnvelope(
            items=items,
            pagination=Pagination(cursor=cursor, total_count=total_count, page_size=page_size),
        )

    # ---- Alias index (Fuzzy Phase 1) ---------------------------------------
    async def _get_alias_index(self) -> list[tuple[str, CellModel]]:
        """Build (or reuse) the normalised alias index.

        One request with a sparse fieldset covers the whole catalogue. This exists because
        the upstream filter cannot serve a fuzzy phase: it matches exactly and
        case-sensitively, and ``any`` is its only accepted operator.
        """
        if self._alias_index is not None:
            return self._alias_index
        async with self._index_lock:
            if self._alias_index is not None:  # another task built it while we waited
                return self._alias_index
            body = await self._get_json("/models", {"fields[model]": "names", "page[size]": 2500})
            index: list[tuple[str, CellModel]] = []
            for rec in body.get("data") or []:
                model = self._cell_model(rec)
                if model is None:
                    continue
                for alias in model.aliases or [model.name]:
                    index.append((normalize_alias(alias), model))
            self._alias_index = index
            return index

    async def search_models(
        self,
        query: str,
        *,
        slim: bool = False,
        page_size: int = 50,
    ) -> PaginationEnvelope[Any] | ErrorEnvelope:
        """Fuzzy Phase 1: resolve a cell-line name to CURIEs.

        Matching is local and case- and punctuation-insensitive. A query that matches
        nothing returns an empty envelope: no match is an answer, not a failure.
        """
        if len(query.strip()) < 2:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message="Query must be at least 2 characters.",
                    recovery_hint="Provide at least 2 characters of the cell-line name.",
                    invalid_input=query,
                )
            )
        try:
            index = await self._get_alias_index()
        except httpx.HTTPStatusError as e:
            return self._upstream_error(e.response.status_code, query)
        except Exception as e:
            return self._unexpected(e, query)

        needle = normalize_alias(query)
        exact: list[CellModel] = []
        prefix: list[CellModel] = []
        seen: set[str] = set()
        for key, model in index:
            if model.id in seen:
                continue
            if key == needle:
                exact.append(model)
                seen.add(model.id)
            elif needle and key.startswith(needle):
                prefix.append(model)
                seen.add(model.id)
        ranked = exact + prefix
        return self._envelope(
            ranked[:page_size],
            slim=slim,
            cursor=None,
            total_count=len(ranked),
            page_size=page_size,
        )

    # ---- Strict lookups (Fuzzy-to-Fact Phase 2) -----------------------------
    async def get_model(self, model_id: str) -> CellModel | ErrorEnvelope:
        """Strict: fetch one model by CURIE. Free text is refused before any request."""
        curie = self.normalize_id(model_id)
        if curie is None:
            return self._unresolved(model_id)
        bare = f"SIDM{curie.split(':', 1)[1]}"
        try:
            body = await self._get_json(f"/models/{bare}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return self._not_found(curie)
            return self._upstream_error(e.response.status_code, curie)
        except Exception as e:
            return self._unexpected(e, curie)
        data = body.get("data")
        if not data:
            return self._not_found(curie)
        model = self._cell_model(data if isinstance(data, dict) else data[0])
        return model if model is not None else self._not_found(curie)

    @staticmethod
    def _not_found(curie: str) -> ErrorEnvelope:
        return ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message=f"No model '{curie}' in Cell Model Passports.",
                recovery_hint="Verify the CURIE, or call search_models to resolve a name.",
                invalid_input=curie,
            )
        )

    async def resolve_model(self, source: str, source_id: str) -> CellModel | ErrorEnvelope:
        """Strict: resolve a model by external identifier.

        The source name is case-insensitive; the identifier is case-sensitive. ``CCLE_ID``
        and ``cosmic_id`` are confirmed working. ``model_name`` is NOT a valid source and
        returns 404: plain names go through ``search_models``.
        """
        key = f"{source}/{source_id}"
        try:
            body = await self._get_json(f"/models/{source}/{source_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.ENTITY_NOT_FOUND,
                        message=f"No model for {key} in Cell Model Passports.",
                        recovery_hint=(
                            "Confirmed sources are CCLE_ID and cosmic_id; identifiers are "
                            "case-sensitive. For a plain cell-line name use search_models."
                        ),
                        invalid_input=key,
                    )
                )
            return self._upstream_error(e.response.status_code, key)
        except Exception as e:
            return self._unexpected(e, key)
        data = body.get("data")
        if not data:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"No model for {key} in Cell Model Passports.",
                    recovery_hint="Verify the identifier.",
                    invalid_input=key,
                )
            )
        model = self._cell_model(data if isinstance(data, dict) else data[0])
        if model is None:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"Model for {key} has no usable identifier.",
                    recovery_hint="Report this upstream record; try another identifier.",
                    invalid_input=key,
                )
            )
        return model

    async def models_with_mutation(
        self,
        gene: str,
        mutation_type: MutationType,
        *,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope[Any] | ErrorEnvelope:
        """Assemble the genotype cohort: models carrying ``mutation_type`` in ``gene``.

        ``mutation_type`` is required and validated. It has no default because the upstream's
        own default, ``mutation``, means any variant: for RB1 it returns 2185 of 2266 models,
        which would put almost the whole catalogue in the mutant arm and destroy any contrast
        built from it.

        Pagination follows the upstream ``next`` link and reports it as an opaque cursor, so
        a large cohort is fully reachable rather than silently truncated.
        """
        if mutation_type not in MUTATION_TYPES:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message=f"'{mutation_type}' is not a Cell Model Passports mutation type.",
                    recovery_hint=f"Use one of: {', '.join(MUTATION_TYPES)}.",
                    invalid_input=str(mutation_type),
                )
            )
        sym = gene.strip().upper()
        path = cursor or f"/models/by_{mutation_type}/{sym}"
        params: dict[str, Any] | None = None if cursor else {"page[size]": page_size}
        try:
            body = await self._get_json(path, params)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.ENTITY_NOT_FOUND,
                        message=f"No '{mutation_type}' cohort for gene '{sym}'.",
                        recovery_hint=(
                            f"Check the gene symbol. Accepted mutation types: "
                            f"{', '.join(MUTATION_TYPES)}."
                        ),
                        invalid_input=sym,
                    )
                )
            return self._upstream_error(e.response.status_code, sym)
        except Exception as e:
            return self._unexpected(e, sym)

        models = [m for m in (self._cell_model(r) for r in body.get("data") or []) if m]
        return self._envelope(
            models,
            slim=slim,
            cursor=self._next_cursor(body),
            total_count=(body.get("meta") or {}).get("count"),
            page_size=page_size,
        )

    @staticmethod
    def _next_cursor(body: dict[str, Any]) -> str | None:
        """Extract the next-page path from a JSON:API links block.

        Parsed with urlsplit rather than by searching for a substring: a naive
        ``find("/models")`` breaks whenever the host or a query parameter contains that text.
        """
        nxt = (body.get("links") or {}).get("next")
        if not nxt:
            return None
        parts = httpx.URL(str(nxt))
        path = parts.raw_path.decode()
        return path or None

    async def get_dependency(
        self,
        gene: str,
        model_id: str,
        *,
        gene_effect: float | None = None,
        data_source: DataSource = "broad_24q2",
    ) -> DependencyRecord | ErrorEnvelope:
        """Strict: how essential ``gene`` is in ``model_id``, from a cached release.

        Gene effect is not served by any query API (see the module docstring), so a value is
        either supplied by a caller that already holds the release or this returns
        UPSTREAM_ERROR naming what is missing. It never returns a zero that would read as a
        measurement.
        """
        curie = self.normalize_id(model_id)
        if curie is None:
            return self._unresolved(model_id)
        if gene_effect is None:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=(
                        f"No cached '{data_source}' gene-effect release is available for "
                        f"{gene.upper()} in {curie}."
                    ),
                    recovery_hint=(
                        "Gene effect is a released matrix file, not an API endpoint. Obtain "
                        "the checksum-pinned release and configure its path."
                    ),
                    invalid_input=f"{gene}/{curie}",
                )
            )
        return DependencyRecord(
            gene=gene,
            model_id=curie,
            gene_effect=gene_effect,
            dependency=-gene_effect,
            dependent=gene_effect < 0,
            data_source=data_source,
        )

    async def genotype_contrast_by_gene(
        self,
        target_gene: str,
        genotype_gene: str,
        gene_effect_by_model: Mapping[str, float] | None = None,
        genotype_by_model: Mapping[str, int] | None = None,
        *,
        mutation_type: MutationType = "deletion",
        min_lines: int = 5,
        data_source: DataSource = "broad_24q2",
    ) -> GenotypeContrast | ErrorEnvelope:
        """Contrast a target's dependency between WT and mutant cohorts.

        Vectors come from a cached, checksum-pinned gene-effect release. They may be supplied
        directly by a caller that already holds them; when they are not, and no release is
        configured, this returns UPSTREAM_ERROR naming what is missing rather than fabricating
        a value. No provider serves gene effect over a query API.
        """
        if gene_effect_by_model is None or genotype_by_model is None:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=(
                        f"No cached '{data_source}' gene-effect release is available, so the "
                        f"contrast cannot be computed."
                    ),
                    recovery_hint=(
                        "Gene effect is not served by any API; it is a released matrix file. "
                        "Obtain the checksum-pinned release and pass gene_effect_by_model and "
                        "genotype_by_model, or configure the release path."
                    ),
                    invalid_input=f"{target_gene}/{genotype_gene}",
                )
            )
        return compute_genotype_contrast(
            target_gene,
            genotype_gene,
            gene_effect_by_model,
            genotype_by_model,
            min_lines=min_lines,
            data_source=data_source,
            mutation_type=mutation_type,
        )


# Kept so a caller can build the upstream filter, and so its shape is documented in one
# place. `any` is the only operator the upstream accepts; every other operator returns 500.
def names_filter(query: str) -> str:
    """Build the JSON:API names filter. Exact and case-sensitive upstream."""
    return json.dumps([{"name": "names", "op": "any", "val": query}])
