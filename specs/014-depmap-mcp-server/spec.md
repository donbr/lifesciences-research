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
2. **Sanger REST (live cross-validation)** — `search_models` now; `get_dependency` to follow
   once endpoint paths are confirmed against `/swagger`.

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
