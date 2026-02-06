# Constitution Compliance Audit Playbook

**Purpose**: Instructions for a multi-agent team to validate all 13 MCP clients against the Life Sciences MCP Constitution (v1.1.0).
**Date**: 2026-02-06
**Scope**: All clients in `src/lifesciences_mcp/clients/` and their corresponding servers, models, and tests.
**Parallelism**: Each client is an independent unit of work. Assign one agent per client for maximum parallelism.

---

## Background

The BioGRID client was recently brought into full Constitution compliance through the SpecKit pipeline (PR #22). This audit extends that validation to all 13 clients to identify gaps and prioritize remediation.

### Constitution Principles Being Audited

| # | Principle | Key MUST Requirements |
|---|-----------|----------------------|
| I | Async-First | `httpx` async (or `run_in_executor` for ChEMBL only). No synchronous blocking. |
| II | Fuzzy-to-Fact | Phase 1 (fuzzy search) MUST make an **API call** to confirm entity exists before Phase 2 (strict lookup). Client-side-only validation is a violation. |
| III | Schema Determinism | `PaginationEnvelope` for all list tools. `ErrorEnvelope` for all errors. `cross_references` using 22-key registry. Omit-if-null (never `null` or `""`). |
| IV | Token Budgeting | `slim=True` parameter on all batch/list tools. `to_slim()` on models. |
| V | Spec-Before-Code | Spec artifacts exist in `specs/` directory. |
| VI | Platform Skills | Uses established scaffold patterns. |
| Rate Limiting | Client-side rate limiting with backoff. `asyncio.Lock` or equivalent. |

---

## Agent Assignment Matrix

Each agent audits ONE client independently. All agents can run in parallel.

| Agent | Client | Spec Dir | Server | Priority |
|-------|--------|----------|--------|----------|
| Agent 1 | `hgnc.py` | `specs/001-hgnc-mcp-server/` | `servers/hgnc.py` | Tier 1 |
| Agent 2 | `uniprot.py` | `specs/002-uniprot-mcp-server/` | `servers/uniprot.py` | Tier 1 |
| Agent 3 | `chembl.py` | `specs/003-chembl-mcp-server/` | `servers/chembl.py` | Tier 0 |
| Agent 4 | `opentargets.py` | `specs/004-opentargets-mcp-server/` | `servers/opentargets.py` | Tier 0 |
| Agent 5 | `drugbank.py` | `specs/005-drugbank-mcp-server/` | `servers/drugbank.py` | Tier 0 |
| Agent 6 | `string.py` | `specs/006-string-mcp-server/` | `servers/string.py` | Tier 1 |
| Agent 7 | `biogrid.py` | `specs/007-biogrid-mcp-server/` | `servers/biogrid.py` | Tier 1 (reference) |
| Agent 8 | `ensembl.py` | `specs/008-ensembl-mcp-server/` | `servers/ensembl.py` | Tier 4 |
| Agent 9 | `entrez.py` | `specs/009-entrez-mcp-server/` | `servers/entrez.py` | Tier 4 |
| Agent 10 | `pubchem.py` | `specs/010-pubchem-mcp-server/` | `servers/pubchem.py` | Tier 2 |
| Agent 11 | `iuphar.py` | `specs/011-iuphar-mcp-server/` | `servers/iuphar.py` | Tier 2 |
| Agent 12 | `wikipathways.py` | `specs/012-wikipathways-mcp-server/` | `servers/wikipathways.py` | Tier 3 |
| Agent 13 | `clinicaltrials.py` | `specs/013-clinicaltrials-mcp-server/` | `servers/clinicaltrials.py` | Tier 3 |

**Note**: Agent 7 (BioGRID) serves as the **reference implementation**. All other agents should compare their client's patterns against BioGRID for consistency.

---

## Per-Agent Instructions

### Files to Read

For your assigned client `{name}`:

1. **Client**: `src/lifesciences_mcp/clients/{name}.py`
2. **Models**: `src/lifesciences_mcp/models/{model_file}.py` (check `__init__.py` for imports)
3. **Server**: `src/lifesciences_mcp/servers/{name}.py`
4. **Tests**: `tests/integration/test_{name}_api.py` and `tests/unit/test_{name}_*.py`
5. **Spec**: `specs/{NNN}-{name}-mcp-server/spec.md`
6. **Constitution**: `.specify/memory/constitution.md`

Also read the **BioGRID reference** for comparison:
- `src/lifesciences_mcp/clients/biogrid.py` — reference for API-backed search + slim
- `src/lifesciences_mcp/models/biogrid.py` — reference for `to_slim()` pattern

### Audit Checklist

For each principle, determine: **PASS**, **PARTIAL**, or **FAIL**.

#### CHECK 1: Principle II — Fuzzy-to-Fact (CRITICAL)

This is the highest-priority check. The search/fuzzy tool MUST make a real API call to confirm the entity exists.

**What to look for in the client's search method** (e.g., `search_genes`, `search_proteins`, `search_compounds`):

- [ ] **Does Phase 1 (fuzzy search) make an HTTP API call?**
  - PASS: Method calls `self._get_client()`, `httpx.get()`, `self._rate_limited_get()`, or equivalent
  - FAIL: Method only does regex/string validation without any API call
  - FAIL: Method returns hardcoded/cached results without server confirmation

- [ ] **Does Phase 2 (strict lookup) require a resolved identifier?**
  - PASS: `get_gene(hgnc_id)`, `get_compound(chembl_id)`, etc. require CURIE/ID parameter
  - FAIL: Strict tool accepts raw strings without requiring prior search

- [ ] **Does the search tool return enough information for the agent to proceed?**
  - PASS: Returns candidate with ID, name, and score/count metadata
  - PARTIAL: Returns candidate but missing useful metadata

- [ ] **Does a nonexistent entity return ENTITY_NOT_FOUND error?**
  - PASS: Search for gibberish (e.g., "ZZZZZ99") returns `ErrorEnvelope` with `ENTITY_NOT_FOUND`
  - FAIL: Returns empty results without error, or silently succeeds

**Evidence to capture**: Quote the specific lines where the API call is made in the search method. If there is no API call, quote the lines showing client-side-only validation.

#### CHECK 2: Principle IV — Token Budgeting

- [ ] **Does the search tool accept a `slim` parameter?**
  - PASS: `slim: bool = False` in method signature
  - FAIL: No `slim` parameter

- [ ] **Does the strict lookup tool accept a `slim` parameter?**
  - PASS: `slim: bool = False` in method signature
  - FAIL: No `slim` parameter

- [ ] **Do batch tools default to `slim=True`?**
  - PASS: Batch methods (e.g., `get_compounds_batch`) have `slim: bool = True`
  - N/A: No batch tools for this client

- [ ] **Does the primary model have a `to_slim()` method?**
  - PASS: Model class has `def to_slim(self) -> dict[str, Any]`
  - FAIL: No `to_slim()` method

- [ ] **Does the server tool expose the `slim` parameter?**
  - PASS: Server `@mcp.tool()` function includes `slim: bool = False`
  - FAIL: Server doesn't expose `slim`

#### CHECK 3: Principle I — Async-First

- [ ] **Does the client use `httpx.AsyncClient`?**
  - PASS: Inherits from `LifeSciencesClient` or uses `httpx.AsyncClient`
  - EXCEPTION: ChEMBL may use `run_in_executor` for SDK calls
  - FAIL: Uses `requests`, synchronous `httpx`, or blocking I/O

- [ ] **Does the client implement `async` context manager?**
  - PASS: Has `close()` method or `__aenter__`/`__aexit__`

#### CHECK 4: Principle III — Schema Determinism

- [ ] **Fuzzy search returns `PaginationEnvelope`?**
- [ ] **Errors return `ErrorEnvelope` with code, message, recovery_hint, invalid_input?**
- [ ] **Entity models include `cross_references` using 22-key registry?**
- [ ] **Null values omitted (never `null` or empty string in cross_references)?**

#### CHECK 5: Rate Limiting (Constitution v1.1.0)

- [ ] **Client implements rate limiting?**
  - PASS: Has `asyncio.Lock`, delay between requests, or inherits from `LifeSciencesClient`
  - FAIL: No rate limiting

- [ ] **Exponential backoff on 429/503?**
  - PASS: Retry logic with increasing delays
  - PARTIAL: Fixed delay retry
  - FAIL: No retry logic

#### CHECK 6: Spec Artifacts

- [ ] **Spec directory exists** at `specs/{NNN}-{name}-mcp-server/`?
- [ ] **spec.md exists** with user stories and acceptance scenarios?
- [ ] **plan.md exists** with Constitution Check section?
- [ ] **Plan Principle II shows FULL** (not PARTIAL or ADAPTED)?
- [ ] **Plan Principle IV shows FULL** (not justified deviation)?

---

### Output Format

Each agent MUST produce a report in this exact format:

```markdown
# Constitution Compliance Report: {Client Name}

**Agent**: {agent_id}
**Date**: {date}
**Client**: `src/lifesciences_mcp/clients/{name}.py`
**Server**: `src/lifesciences_mcp/servers/{name}.py`

## Summary

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Async-First | PASS/PARTIAL/FAIL | {brief note} |
| II. Fuzzy-to-Fact | PASS/PARTIAL/FAIL | {brief note} |
| III. Schema Determinism | PASS/PARTIAL/FAIL | {brief note} |
| IV. Token Budgeting | PASS/PARTIAL/FAIL | {brief note} |
| V. Spec-Before-Code | PASS/PARTIAL/FAIL | {brief note} |
| Rate Limiting | PASS/PARTIAL/FAIL | {brief note} |

## Critical Findings

### Principle II: Fuzzy-to-Fact
- **Search method**: `{method_name}` at line {N}
- **Makes API call**: YES/NO
- **Evidence**: `{quote the relevant code lines}`
- **Nonexistent entity handling**: ENTITY_NOT_FOUND / empty result / no check
- **Verdict**: PASS/FAIL

### Principle IV: Token Budgeting
- **slim parameter on search**: YES/NO
- **slim parameter on strict lookup**: YES/NO
- **to_slim() on model**: YES/NO
- **slim exposed on server tool**: YES/NO
- **Verdict**: PASS/FAIL

## Remediation Required

1. {specific action needed, with file path and line numbers}
2. {specific action needed}
...

## Files Reviewed

- {list all files read during audit}
```

---

## Aggregation

After all 13 agents complete, an aggregator agent should:

1. Collect all 13 reports
2. Build a cross-client compliance matrix
3. Identify systemic gaps (e.g., "8 of 13 clients missing slim=True")
4. Prioritize remediation by tier (Tier 0 first, then 1, 2, 3, 4)
5. Estimate scope per client (number of files/methods to change)

### Expected Compliance Matrix Output

```markdown
| Client | Pr.I | Pr.II | Pr.III | Pr.IV | Rate Lim. | Overall |
|--------|------|-------|--------|-------|-----------|---------|
| hgnc | PASS | ? | ? | ? | ? | ? |
| uniprot | PASS | ? | ? | ? | ? | ? |
| chembl | PASS | ? | ? | ? | ? | ? |
| ... | | | | | | |
| biogrid | PASS | PASS | PASS | PASS | PASS | PASS |
```

---

## Reference Implementation

BioGRID (PR #22) is the gold standard for full compliance:

- **Principle II**: `search_genes` calls `/interactions?format=count` to confirm gene exists via API before any strict lookup. Returns `ENTITY_NOT_FOUND` when `count == 0`.
- **Principle IV**: `slim=True` on `get_interactions` returns `to_slim()` dict with only `symbol_b` + `experimental_system_type` per interaction (~15 tokens vs ~100 full).
- **Key files**: `clients/biogrid.py:120-250`, `models/biogrid.py:115-134`, `servers/biogrid.py:65-105`

---

## Execution Notes

- **DO NOT modify any files** — this is audit-only. Produce reports.
- **DO NOT run tests** — just read code and spec artifacts.
- Each agent should complete in 3-5 minutes of read-only analysis.
- Focus on Principle II (Fuzzy-to-Fact) and Principle IV (Token Budgeting) first — these are the most likely gaps based on the BioGRID experience.
- If a spec directory doesn't exist for a client, note it as a Principle V violation.
