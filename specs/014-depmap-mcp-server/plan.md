# Implementation Plan: DepMap Genotype-Selective Dependency MCP Server

**Branch**: `implement/014-depmap-mcp-server` (feature `014-depmap-mcp-server`) | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-depmap-mcp-server/spec.md`

## Summary

Provide the wild-type-versus-mutant dependency contrast that no existing connector offers: given a
target gene and a genotype gene, report how much more (or less) essential the target is in cells
that have lost the genotype gene, with a significance value, cohort sizes and explicit provenance.

Technical approach, grounded in the live-API findings in [research.md](./research.md): the Sanger
Cell Model Passports REST API supplies model resolution and genotype cohorts; dependency values come
from a cached, checksum-pinned gene-effect matrix because no provider serves them over an API. Fuzzy
model search is built locally over a one-request alias index, because the upstream filter is exact
and case-sensitive and no server-side transformation resolves all common names.

**Status note**: a hand-written scaffold for this feature was committed before this plan existed
(commits `d1ea300` and `5a1f65a`). This plan is the governance gate that scaffold skipped. The
Constitution Check below evaluates the committed code as it stands, not an imagined greenfield, and
every FAIL becomes a task.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastMCP >=2.14.1,<3.0; httpx >=0.27 (async); pydantic >=2.0. No new
third-party dependency is added by this feature (see research.md R6).
**Storage**: None. Stateless live queries plus an in-process alias cache for the process lifetime.
A cached gene-effect matrix is read from disk when supplied; it is not written by this server.
**Testing**: pytest with pytest-asyncio; markers `unit`, `integration`, `depmap`.
**Target Platform**: Local MCP server (stdio) and the mounted gateway for cloud deployment.
**Project Type**: Single project, existing `src/lifesciences_mcp` package.
**Performance Goals**: 1 request/second against the upstream catalogue; alias index built in one
request (2266 rows, 250 KB, ~1.7 s measured) and reused thereafter.
**Constraints**: Upstream requires prior permission for third-party application use and is
non-commercial only; provenance must be visible on every record; the companion analysis pipeline
must stay file-based and gain no dependency on this server.
**Scale/Scope**: 2266 cell models; genotype cohorts up to ~500 models; 5 tools.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.1.0, and against the code already committed
on this branch.

### Principle I: Async-First Architecture — PASS

- The client extends `LifeSciencesClient` and uses the inherited async httpx transport.
- No synchronous SDK is involved; the upstream returns JSON.
- No `@mcp.on_event` hook is used; the client is a module-level singleton (ADR-004).
- One deviation to fix: `genotype_contrast` is currently a synchronous `def` tool, the only one in
  `servers/`. It is pure computation so it does not block on I/O, but it breaks the uniform tool
  signature. Task T014.

### Principle II: Fuzzy-to-Fact Resolution Protocol — FAIL as committed, fixed by this plan

- Phase 1 exists (`search_models`) but does not work as a fuzzy phase: the upstream filter is exact
  and case-sensitive, so `a549`, `MCF-7` and `hela` all return nothing (research.md R4). Tasks T020,
  T021.
- Phase 2 accepts a bare identifier with no validation. There is no CURIE and no `UNRESOLVED_ENTITY`
  path, so `get_model("A549")` performs a network call and returns `ENTITY_NOT_FOUND` where the
  Constitution requires a refusal naming the resolve tool. Tasks T002, T018, T022.

### Principle III: Schema Determinism — FAIL as committed, fixed by this plan

- Canonical `PaginationEnvelope` and `ErrorEnvelope` are used, with `ErrorCode` values and recovery
  hints. That part is compliant.
- `model_config = ConfigDict(exclude_none=True)` is **not a valid Pydantic v2 key**. It is silently
  ignored, so every optional field serialises as `null`. `GenotypeContrast` has no config at all and
  emits six nulls. Emitting `null` instead of omitting the key is a named Forbidden Pattern. The
  repository's working pattern is a `model_dump` override; `models/drug.py`, `models/ensembl.py` and
  `models/pharmacology.py` all use it. Task T001.
- No entity carries a `cross_references` object, which Principle III requires of every entity.
  Research R5 confirms CCLE and COSMIC identifiers are both resolvable, so there is real content for
  it. Tasks T024, T036.

### Principle IV: Token Budgeting — FAIL as committed, fixed by this plan

- No `slim` parameter on either list tool, where all eleven other servers support it.
- `models_with_mutation` defaults to 500 results against a mandated default of 50, and a genotype
  cohort can legitimately be that large, so the unslimmed default is a context-window hazard.
- Tasks T019, T023.

### Principle V: Specification-Before-Code — VIOLATED, and this plan is the remedy

The scaffold was written and committed with only a free-form `spec.md`, no `plan.md`, no `tasks.md`
and no approval gate. The Constitution's exception covers changes under three lines; this was about
700 lines across five files, so it does not apply.

Remedy, not excuse: the spec has been rewritten to the template with testable requirements, this
plan and its Phase 1 artefacts now exist, tasks follow, and every deviation found in the committed
code is listed above with a task rather than being merged unexamined. The work is not merged until
that is done. Recorded here because the Governance section requires violations to be justified in
this document rather than discovered at review.

### Principle VI: Platform Skill Delegation — VIOLATED, mitigated

`scaffold-fastmcp-v2` exists and was not used; the server was hand-written outside this environment,
where the skill was unavailable. The drift the principle predicts is exactly what the Check above
found: missing `slim`, missing `cross_references`, missing rate limiting, missing package exports.

Mitigation: rather than regenerate and lose the genuinely valuable live-API findings in the existing
code, the tasks below bring the hand-written files up to the pattern the skill would have produced,
using the named reference implementations in `clients/clinicaltrials.py` and `models/trial.py`.

### Forbidden Patterns Check

| Pattern | Status |
|---|---|
| Synchronous blocking in async | Not present |
| Hardcoded credentials | Not present; the upstream needs no key |
| Raw strings to strict tools | **Present.** Fixed by T002, T018, T022 |
| Null cross-references | **Present**, and worse: all optional fields emit null. Fixed by T001 |
| Skip specification | **Occurred.** Remedied by this plan; see Principle V |
| Bypass Platform Skills | **Occurred.** Mitigated; see Principle VI |
| Deep JSON nesting | Not present; records are flat |
| Unbounded concurrency | Not present, but pagination is unthrottled. Fixed by T003 |

### Required Patterns Check

| Pattern | Status |
|---|---|
| Canonical Pagination Envelope | Present |
| Canonical Error Envelope | Present, but with another data source's wording. Fixed by T004, T036 |
| Cross-reference validation | Absent. Fixed by T024, T036 |
| Async httpx clients | Present |
| `slim=True` support | Absent. Fixed by T019, T023 |
| Client-side rate limiting | Absent. Fixed by T003, T037 |

**Gate result**: The design in this plan passes. The committed code does not, and may not merge
until the tasks above are complete. No violation is being carried forward unjustified; the two that
are historical (Principles V and VI) are recorded above and cannot be undone, only remedied.

## Project Structure

### Documentation (this feature)

```text
specs/014-depmap-mcp-server/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: live-API findings
├── data-model.md        # Phase 1: entities and validation rules
├── quickstart.md        # Phase 1: how to run and try it
├── contracts/           # Phase 1: one contract per tool
│   ├── search_models.md
│   ├── get_model.md
│   ├── models_with_mutation.md
│   ├── get_dependency.md
│   └── genotype_contrast_by_gene.md
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/lifesciences_mcp/
├── clients/
│   ├── __init__.py       # add DepMapClient export
│   └── depmap.py         # DepMapClient: Sanger REST + alias index + contrast core
├── models/
│   ├── __init__.py       # add DepMap model exports
│   └── depmap.py         # CellModel, DependencyRecord, GenotypeCohort, GenotypeContrast
└── servers/
    ├── depmap.py         # FastMCP tools
    └── gateway.py        # mount depmap, prefix "depmap"

tests/
├── unit/
│   ├── test_depmap_client.py   # contrast maths, alias normalisation, CURIE validation
│   └── test_depmap_models.py   # validation, omit-if-null, cross_references
└── integration/
    └── test_depmap_api.py      # live Sanger calls, marked integration + depmap
```

**Structure Decision**: Single project, extending the existing `src/lifesciences_mcp` package. The
client lives in `clients/` per ADR-006 so the module stays a single-writer file, matching the
twelve servers already in the tree.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| A local alias index instead of upstream search | The upstream `names` filter is exact and case-sensitive; `any` is the only accepted operator and every alternative returns HTTP 500. No single server-side transformation resolves `a549`, `MCF-7` and `HeLa` together (research.md R4) | Upper-casing the query breaks `HeLa`; trying several transformations costs several round trips per search and still fails punctuation variants; server-side substring matching is not offered |
| Contrast computed from a supplied or cached matrix rather than a live call | Neither provider serves gene-effect over an API; it is a distributed file (research.md R3) | There is no live endpoint to call, so no simpler alternative exists |
| `genotype_contrast` demoted from a tool to an internal function, replaced by `genotype_contrast_by_gene` | As a tool it takes the full per-model dependency and genotype vectors as arguments, so an agent would serialise ~2000 entries per call. That is not usable, and it is why the scaffold's own acceptance criterion could not be exercised | Keeping the vector-argument tool means shipping a headline tool no agent can call; keeping both doubles the surface for no gain. The maths stays unit-tested as a function, which is where its tests already point |
