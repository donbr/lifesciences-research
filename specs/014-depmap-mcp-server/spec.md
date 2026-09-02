# 014 — DepMap MCP Server

**Linear:** AGE-681 (child of AGE-680, the open-biosciences plugin roadmap)
**Status:** kickoff / TDD scaffold
**Origin:** the S′ lung synthetic-lethality paper needed genotype-selective dependency
contrasts (does loss of tumor-suppressor X make cells depend on target Y?). BioGRID ORCS
gives per-screen essentiality only; the registry has no DepMap dependency connector. This
server fills that gap.

## Decision: API vs files
- **Broad DepMap 24Q2** (the paper's data) has **no stable public query API** — figshare
  matrices + `depmap`/`taigapy` packages. The reproducible pipeline (`sprime-lung-repro`)
  keeps its checksum-pinned file approach; a live API would break byte-reproducibility.
- **Sanger Cell Model Passports** has a documented JSONAPI v1.0 REST API
  (`https://api.cellmodelpassports.sanger.ac.uk`, `/swagger`). Different dataset (Project
  Score, not Broad 24Q2) — always provenance-labeled. Third-party app use needs prior
  permission (depmap@sanger.ac.uk); non-commercial only.

## Two data planes
1. **Genotype contrast (offline, provenance-matched)** — pure computation over Broad 24Q2
   gene-effect matrices supplied by the caller: WT-vs-mutant Δdependency + Mann-Whitney +
   (optional) BH FDR + small-cohort exclusion. This is `demeter_validation.py` promoted to a
   reusable, tested tool. **numpy-free core** (no scipy dependency).
2. **Sanger REST (model + genotype resolution)** — see confirmed endpoints below.

## Sanger Cell Model Passports endpoints (confirmed live 2026-09-02)
Base `https://api.cellmodelpassports.sanger.ac.uk`, JSONAPI v1.0, filter syntax
`?filter=[{"name","op","val"}]`, pagination `page[size]`/`page[number]` with `meta.count`.
- `/models` — all models (`meta.count` ≈ 2266); record: `id` = `SIDM#####`, `attributes.names`,
  `*_available` flags (incl. `crispr_ko_available`), `model_type`; tissue/lineage is on the linked `sample`.
- `/models/<SIDM#####>` — single model → `get_model`.
- `/models/<source>/<source_id>` — resolve by external id (CCLE_ID, cosmic_id, model_name) → `resolve_model`.
- `/models/by_<mut_type>/<gene>` — genotype cohort → `models_with_mutation`.
- `/models/<id>/datasets/<name>` — `mutations` | `cancer_drivers` | `genecnv` | `growth_rate`.

**Two findings that shaped the design:**
- **`by_mutation` is broad:** `/models/by_mutation/RB1` returns ~2185/2266 models (ANY variant),
  **not** the paper's damaging/homozygous call. Cohorts must use a specific damaging `mut_type`
  (frameshift/deletion/splice_variant) or be reconciled against the mutations dataset.
- **CRISPR gene-effect is NOT a queryable endpoint.** `crispr_ko_available` is only a flag; probes
  to `/datasets/crispr` and `/datasets/crispr_ko` return empty — the dependency matrix is a Project
  Score / Data Miner file. **Therefore genotype contrasts consume an offline matrix for both Broad
  and Sanger; the REST API supplies model + genotype resolution, not dependency values.**

*Unconfirmed / follow-up:* the exact `/models` names-filter operator for free-text `search_models`
(confirm vs `/swagger`); `search_models` currently best-effort, with `resolve_model`/`get_model` as the
reliable resolution paths.

## Tools (Fuzzy-to-Fact, ADR-001 §3)
- `search_models(query, limit)` — Fuzzy: cell-line candidates (Sanger, provenance-labeled).
- `genotype_contrast(target_gene, genotype_gene, gene_effect_by_model, genotype_by_model, min_lines, data_source)` — Strict: the key capability.
- *(follow-up)* `get_dependency(gene, model_id?)`, and a matrix-backed `genotype_contrast_by_gene(target, genotype)` that loads the checksum-pinned Broad matrix so callers need not pass raw arrays.

## Architecture (ADR compliance)
- `DepMapClient(LifeSciencesClient)` — async httpx, module-level singleton (ADR-004),
  `src/lifesciences_mcp/clients/depmap.py` (ADR-006).
- Models: `DepMapModelCandidate`, `DependencyRecord`, `GenotypeContrast` — Agentic Biolink,
  `exclude_none`, always carry `data_source ∈ {broad_24q2, sanger_project_score}`.
- Canonical Pagination/Error envelopes (ADR-001 §8).

## Tests (TDD — written first)
- `tests/unit/test_depmap_client.py` — Mann-Whitney (separated/identical/empty), BH FDR
  (monotone/NaN), and the contrast: mutant-selective, WT-selective flip, small-cohort
  not-tested, NaN skipped, provenance preserved. **All pass** (verified numpy-only).
- `tests/unit/test_depmap_models.py` — validation, uppercasing, enum rejection, exclude_none.
- *(follow-up, integration-marked)* live Sanger REST calls confirmed against `/swagger`.

## Acceptance criteria
- `genotype_contrast("AURKB","RB1", …)` on Broad 24Q2 reproduces the RB1-mutant-selective
  AURKB / RB–E2F result from `sprime-lung-repro` (add a frozen fixture from the real matrix).
- Cohorts with n < `min_lines` (e.g. PTEN) return `tested=False` with a note — never silently.
- Every record labels Broad-vs-Sanger provenance; the Sanger path documents the permission caveat.
- Pipeline code stays file-based; the MCP is interactive-research only (no network in pipeline).

## Next steps (SpecKit)
`/speckit.plan` → `/speckit.tasks` → `/speckit.implement`; confirm Sanger endpoints via
`/swagger`; add the matrix-backed contrast + the Broad-24Q2 regression fixture; wire into
`servers/gateway.py`.
