# Tasks: DepMap Genotype-Selective Dependency MCP Server

**Input**: Design documents from `/specs/014-depmap-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Tests**: Included. The spec's acceptance scenarios are the test list, and the Constitution
requires contract tests for `slim` support and envelope conformance.

**Format**: `[ID] [P?] [Story] Description` — `[P]` marks tasks that touch different files and can
run in parallel.

**Starting point**: unlike a greenfield feature, a scaffold already exists on this branch (commits
`d1ea300`, `5a1f65a`). Many tasks below are corrections to committed code rather than new files.
Each one names the defect and the in-repo pattern to copy, so none is a judgement call at
implementation time.

---

## Phase 1: Foundational (blocking prerequisites)

**Purpose**: schema and client-infrastructure defects that every user story depends on. No story
work can begin until these are done.

- [x] **T001** Fix omit-if-null across `src/lifesciences_mcp/models/depmap.py`. Remove
  `model_config = ConfigDict(exclude_none=True)`, which is not a valid Pydantic v2 key and is
  silently ignored, and add the `model_dump` override used by `models/drug.py`, `models/ensembl.py`
  and `models/pharmacology.py`. Apply it to **every** model including `GenotypeContrast`, which has
  no configuration today and emits six nulls. Confirms: the currently failing
  `test_depmap_models.py::TestModelCandidate::test_omits_none` turns green.
- [x] **T002** Rename `DepMapModelCandidate` to `CellModel`, the name used throughout spec.md and
  data-model.md, so the schema and its specification agree. Add the `SIDM:#####` CURIE to the model schema and a `validate_id` static method plus
  a `normalize_id` that accepts the bare upstream `SIDM00903` form, mirroring
  `ClinicalTrialsClient.NCT_ID_PATTERN` and `validate_nct_id`.
- [x] **T003** [P] Add `_rate_limited_call` to `DepMapClient`: one request per second behind an
  `asyncio.Lock`, with exponential backoff on 429 and 5xx. Copy the structure from
  `clients/clinicaltrials.py`. Route every request through it, including cohort pagination.
  (FR-015; Constitution Required Patterns.)
- [x] **T004** [P] Stop using `ErrorEnvelope.upstream_error()`, which hardcodes another API's name,
  so Sanger failures currently surface to agents as HGNC failures. Build `ErrorDetail` explicitly at
  all four call sites, naming this data source. (FR-014.)
- [x] **T005** [P] Export `DepMapClient` from `clients/__init__.py` and the DepMap models from
  `models/__init__.py`, then import from the packages rather than the submodules in
  `servers/depmap.py`. Every other client and model in the tree is exported this way.
- [x] **T006** [P] Fix import ordering in `servers/depmap.py`, which places `from fastmcp import
  FastMCP` after the local imports. Ruff will flag it.

**Checkpoint**: schema, identifiers, rate limiting and error attribution are correct. Story work can
begin.

---

## Phase 2: User Story 1 — Test a genotype-selective dependency claim (P1) 🎯 MVP

**Goal**: return a wild-type-versus-mutant dependency contrast with cohort sizes, significance,
direction and provenance.

**Independent Test**: request a contrast for a known pair and confirm direction, effect size,
significance and cohort sizes against a frozen reference, with no other tool involved.

### Tests

- [x] **T007** [P] [US1] Extend `tests/unit/test_depmap_client.py`: an exact zero delta returns
  direction `none` (FR-004). This case currently reports WT-selective.
- [x] **T008** [P] [US1] Unit test: a cohort below `min_lines` returns `tested` false with a note and
  **no** statistics keys present in the dump (FR-003 plus omit-if-null).
- [x] **T009** [P] [US1] Unit test: cells with missing values are dropped and the reported cohort
  sizes reflect the drop (FR-002); an all-missing cohort reports size zero.

### Implementation

- [x] **T010** [US1] Fix the direction tie in `compute_genotype_contrast`:
  `"mutant-selective" if delta < 0 else "WT-selective"` must yield `none` when the delta is exactly
  zero.
- [x] **T011** [US1] Add `mutation_type` and `min_lines` to `GenotypeContrast` so a result records
  the cohort definition it came from (FR-005, FR-009).
- [x] **T012** [US1] (FR-001) Demote the vector-argument `genotype_contrast` tool to the internal
  `compute_genotype_contrast` function, and add the `genotype_contrast_by_gene` tool per
  `contracts/genotype_contrast_by_gene.md`. Rationale in plan.md Complexity Tracking: as a tool it required
  an agent to serialise ~2000 entries per call, so it was unusable and its acceptance criterion
  could never be exercised.
- [x] **T013** [US1] Add the cached-release loader behind `genotype_contrast_by_gene` and
  `get_dependency`. When the configured release is absent, return `UPSTREAM_ERROR` naming the
  missing release; never return zero or null as if it were a measurement.
- [x] **T014** [US1] Make `genotype_contrast_by_gene` an `async def` tool, matching every other tool
  in `servers/`.
- [x] **T015** [US1] Add the `get_dependency` tool per `contracts/get_dependency.md`. The
  `DependencyRecord` model already exists but is produced by nothing today.

**Checkpoint**: the capability the feature exists for is callable and independently testable.

---

## Phase 3: User Story 2 — Resolve a cell model from the name a researcher types (P2)

**Goal**: fuzzy search that works for the names people actually write.

**Independent Test**: search a set of names in mixed case and punctuation, confirm each resolves to
the expected identifier, then confirm a strict lookup with that identifier returns the full record.

### Tests

- [x] **T016** [P] [US2] Unit test alias normalisation over a fixture index: `A549`, `a549`,
  `MCF-7`, `MCF7`, `HeLa`, `hela` all resolve; ranking puts an exact alias match first.
- [x] **T017** [P] [US2] Unit test: an unmatched query returns an empty `PaginationEnvelope`, not
  `ENTITY_NOT_FOUND` (FR-007).
- [x] **T018** [P] [US2] Unit test: `get_model("A549")` returns `UNRESOLVED_ENTITY` whose recovery
  hint names `search_models`, and makes no request (FR-008).
- [x] **T019** [P] [US2] Contract test: both list tools accept `slim` and the slim payload carries
  only `id`, `name` and `data_source` (FR-012, Constitution Principle IV).

### Implementation

- [x] **T020** [US2] Build the local alias index in `DepMapClient`: one request to
  `/models?fields[model]=names&page[size]=2500` (measured 2266 rows, 250 KB, ~1.7 s), normalised by
  case-fold plus punctuation and whitespace removal, cached for the process lifetime and rebuilt
  lazily. Delegating to the upstream filter cannot satisfy FR-006: `any` is the only accepted
  operator and it matches exactly and case-sensitively (research.md R4).
- [x] **T021** [US2] Rewrite `search_models` to rank against that index, and return an empty
  envelope rather than an error on no match.
- [x] **T022** [US2] Add the `UNRESOLVED_ENTITY` guard to `get_model` and every other strict tool,
  before any network call.
- [x] **T023** [P] [US2] Add `slim` to `search_models` and `models_with_mutation`, and change the
  default page size from 10 and 500 to 50.
- [x] **T024** [P] [US2] Add `cross_references` to the cell-model schema, populated with the CCLE
  and COSMIC identifiers confirmed resolvable in research.md R5, omitting either key when absent
  (FR-013).

**Checkpoint**: the Fuzzy-to-Fact entry point works for realistic queries.

---

## Phase 4: User Story 3 — Assemble a genotype cohort (P3)

**Goal**: build the mutant cohort from a deliberate, recorded variant class.

**Independent Test**: request cohorts for one gene under different variant classes, confirm the
sizes differ as expected and the chosen class is reported back.

### Tests

- [x] **T025** [P] [US3] Unit test: an unaccepted mutation type returns `INVALID_INPUT` listing the
  six accepted values, before any request.
- [x] **T026** [P] [US3] (FR-010, FR-011) Unit test: `page_size` in the envelope is the requested size, and a cursor
  is present whenever more results remain.

### Implementation

- [x] **T027** [US3] Make `mutation_type` required with no default on `models_with_mutation`, and
  validate it against the closed set the upstream states in its own 404 body: `frameshift`, `snp`,
  `insertion`, `deletion`, `splice_variant`, `mutation`. A default of `mutation` would silently
  return 2185 of 2266 models for RB1 and destroy the contrast (research.md R2).
- [x] **T028** [US3] Fix pagination: return the requested `page_size`, propagate the upstream `next`
  link as a cursor instead of dropping it at a `max_models` cap, and stop parsing that link with
  `nxt.find("/models")`, which breaks if the host or any query parameter contains that string.
- [x] **T029** [US3] Echo `mutation_type` on the cohort and on any contrast derived from it.

---

## Phase 5: Integration and polish

- [x] **T030** Add `tests/integration/test_depmap_api.py`, marked `integration` and `depmap`, with a
  health-check skip like the other integration suites. Cover: `A549` resolves to `SIDM:00903`;
  `HeLa` and `hela` resolve to the same model; `models_with_mutation("RB1", "deletion")` returns
  roughly 501 models; an unaccepted mutation type is rejected. Every other API in this repo has an
  integration suite; this one has none.
- [x] **T031** Wire the server into `src/lifesciences_mcp/servers/gateway.py` with prefix `depmap`
  and explicit `tool_names`, copying the ClinicalTrials mount block, inserted alphabetically before
  `ensembl`. Update the module docstring, which still says "12 of 13".
- [x] **T032** [P] Surface the access terms in the tool descriptions, not only in docstrings: Cell
  Model Passports is non-commercial and third-party application use requires prior permission from
  depmap@sanger.ac.uk (FR-016).
- [x] **T033** [P] Remove the unreachable branch in `mannwhitney_u_p` (the `if sigma_sq else`
  fallback after an early return already covers non-positive variance).
- [x] **T034** [P] Update `CLAUDE.md`: add DepMap to the status list, the structure tree and the
  implemented-tools table, and note that gene-effect requires a cached release.
- [x] **T036** [P] (FR-013, FR-014) Unit tests for the two requirements that currently have an
  implementation task but no verification: a returned entity carries `cross_references` with the
  CCLE and COSMIC keys populated and absent keys omitted, and an upstream failure produces an error
  whose message names this data source rather than another API.
- [x] **T037** [P] (FR-015) Unit test that consecutive client calls are spaced by the configured
  interval and that a 429 triggers backoff rather than an immediate retry, using a fake clock.
- [x] **T038** (FR-017) Add a guard that the analysis pipeline gains no dependency on this server:
  assert no module under `src/lifesciences_mcp/` is imported by the companion pipeline, and state
  the invariant in the server docstring. This requirement had no coverage at all, so nothing
  prevented a future change from violating it silently.
- [x] **T039** (SC-002) Make the alias resolution test sample-based rather than a fixed list of six
  names: draw a sample of aliases from the built index, query each in lower case, upper case and
  with punctuation stripped, and assert the resolution rate meets the criterion. As written, T016
  cannot substantiate the 95% figure SC-002 claims.
- [x] **T035** Run `uv run pytest -m depmap -v`, `uv run pytest -m unit -v`,
  `uv run ruff check --fix . && uv run ruff format .`, and `uv run pyright`. All must be clean.

---

## Deferred (tracked in Linear AGE-681, not in this PR)

- [ ] **D001** Broad 24Q2 regression fixture reproducing the AURKB-against-RB1 mutant-selective
  result (SC-003). **Blocked**: needs a slice of the gated gene-effect and damaging-mutation
  matrices, which are not in this repository. SC-003 stays in the spec, unmet and visible, rather
  than being dropped to make the checklist look complete.
- [ ] **D002** Reconcile the Sanger by-mutation cohorts against the mutations dataset, so a damaging
  call can be derived rather than approximated by variant class.
- [ ] **D003** Fix the same latent `ConfigDict(exclude_none=True)` no-op in `models/biogrid.py`.
  Pre-existing, unrelated to this feature, and deserves its own change.

---

## Dependencies

- Phase 1 blocks everything. T001 in particular: every schema assertion in later tests depends on
  omit-if-null actually working.
- T010 to T015 (US1) depend only on Phase 1 and deliver the MVP on their own.
- T020 to T024 (US2) depend on Phase 1; T022 depends on T002 for the identifier pattern.
- T027 to T029 (US3) depend on Phase 1; T029 touches the model T011 changes, so it follows T011.
- T031 (gateway) must come after all tools have their final names and signatures.

---

## Status

All 39 tasks complete. 3 deferred items remain open, each with its blocker stated;
they are tracked in Linear AGE-681 and are deliberately not in this change.
