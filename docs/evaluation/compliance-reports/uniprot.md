# UniProt MCP Client - Constitution Compliance Audit

**Auditor**: Claude Sonnet 4.5
**Date**: 2026-02-06
**Status**: READ-ONLY AUDIT (no files modified)
**Reference Implementation**: BioGRID (all principles PASS)

---

## Executive Summary

| Principle | Status | Severity | Finding |
|-----------|--------|----------|---------|
| **II. Fuzzy-to-Fact** | **FAIL** | **CRITICAL** | `search_proteins` does NOT make API call to confirm entity existence. Only validates query length (≥2 chars). No ENTITY_NOT_FOUND for nonexistent proteins. |
| **IV. Token Budgeting** | **FAIL** | **CRITICAL** | `Protein` model has NO `to_slim()` method. Client conditionally builds slim dict, but no standardized method. |
| I. Async-First | **PASS** | - | Inherits from `LifeSciencesClient`, uses `httpx.AsyncClient` |
| III. Schema Determinism | **PASS** | - | Returns `PaginationEnvelope`, `ErrorEnvelope`, `CrossReferences`. Omits null values. |
| V. Rate Limiting | **PASS** | - | `_rate_limited_get()` with `asyncio.Lock`, exponential backoff on 429/403 |
| VI. Spec Artifacts | **PASS** | - | Directory `specs/002-uniprot-mcp-server/` exists with 7 artifacts |

---

## Critical Findings

### 🚨 PRINCIPLE II — Fuzzy-to-Fact (CRITICAL VIOLATION)

**Expected Behavior (BioGRID reference):**

```python
# BioGRID makes API call with format=count to confirm gene exists
response = await self._rate_limited_get(url, params)
count = int(response.text.strip())

if count == 0:
    return ErrorEnvelope(
        error=ErrorDetail(
            code=ErrorCode.ENTITY_NOT_FOUND,
            message=f"Gene not found in BioGRID: {symbol}",
            recovery_hint="Verify gene symbol is correct...",
            invalid_input=query,
        )
    )
```

**Actual Behavior (UniProt):**

```python
# File: src/lifesciences_mcp/clients/uniprot.py, lines 190-199
# ONLY validates query length - NO API call to confirm existence

if len(query.strip()) < 2:
    return ErrorEnvelope(
        error=ErrorDetail(
            code=ErrorCode.AMBIGUOUS_QUERY,
            message=f"Query '{query}' is too short...",
            ...
        )
    )

# Then immediately calls API with query (line 217)
response = await self._rate_limited_get("/uniprotkb/search", params=params)
```

**Impact:**

- ❌ No existence confirmation before returning candidates
- ❌ Invalid queries (e.g., "ZZZZZ99") may return empty results WITHOUT `ENTITY_NOT_FOUND`
- ❌ Agents cannot distinguish "no results" from "invalid query"
- ✅ Does make API call (line 217), but does NOT check if results are empty before building candidates

**Evidence:**

Lines 236-287 in `uniprot.py` show the search logic:
- Line 236: `data = response.json()`
- Line 237: `results = data.get("results", [])`
- Lines 239-276: Loop through results to build candidates
- **MISSING**: No check for `if len(results) == 0: return ErrorEnvelope(ENTITY_NOT_FOUND)`

**Constitutional Requirement:**

> "Phase 1 (fuzzy search) must confirm entity exists via API call before Phase 2 (strict lookup)."

**Compliance Status:** ❌ **PARTIAL** - Makes API call but does NOT confirm entity exists (no empty result handling).

---

### 🚨 PRINCIPLE IV — Token Budgeting (CRITICAL VIOLATION)

**Expected Behavior (BioGRID reference):**

```python
# BioGRID InteractionResult model has to_slim() method
def to_slim(self) -> dict[str, Any]:
    """Return slim representation with minimal fields (~15 tokens/interaction).

    Constitution Principle IV: Token budgeting for context-constrained agents.
    Omits biogrid_interaction_id, symbol_a, experimental_system, pubmed_id,
    throughput, organism IDs, entrez IDs, and cross_references.
    """
    return {
        "query_gene": self.query_gene,
        "interactions": [
            {
                "symbol_b": i.symbol_b,
                "experimental_system_type": i.experimental_system_type,
            }
            for i in self.interactions
        ],
        "physical_count": self.physical_count,
        "genetic_count": self.genetic_count,
        "total_count": self.total_count,
    }
```

**Actual Behavior (UniProt):**

```python
# File: src/lifesciences_mcp/models/protein.py
# NO to_slim() method defined

class Protein(BaseModel):
    """Complete protein record from UniProt..."""

    id: str = Field(...)
    accession: str = Field(...)
    name: str = Field(...)
    # ... more fields ...

    # ❌ NO to_slim() method
```

**Client-side workaround (not standardized):**

```python
# File: src/lifesciences_mcp/clients/uniprot.py, lines 438-460
# Client conditionally builds slim dict instead of model method

protein_dict = {
    "id": uniprot_id,
    "accession": accession,
    "name": full_name,
    "organism": organism_name,
}

# Add optional fields only if not in slim mode
if not slim:
    protein_dict.update({
        "full_name": full_name,
        "gene_names": gene_names,
        "organism_id": organism_id,
        "function": function_text,
        "sequence_length": sequence_length,
        "cross_references": cross_references,
    })

return Protein(**protein_dict)
```

**Impact:**

- ❌ Violates standardized `to_slim()` pattern used by 6 other servers
- ❌ Logic scattered across client instead of encapsulated in model
- ❌ Harder to maintain consistency across batch operations
- ✅ Server DOES expose `slim` parameter (line 66 in `servers/uniprot.py`)
- ✅ Client DOES accept `slim` parameter (lines 173, 314)

**Evidence:**

Grep search for `to_slim` shows 6 other models implement this method:
- `models/entrez.py:260`: `def to_slim(self) -> dict[str, Any]:`
- `models/biogrid.py:115`: `def to_slim(self) -> dict[str, Any]:`
- `models/compound.py:152`: `def to_slim(self) -> dict[str, Any]:`
- `models/target.py:128`: `def to_slim(self) -> dict:`
- `models/pubchem_compound.py:157`: `def to_slim(self) -> dict[str, Any]:`
- `models/drug.py:210`: `def to_slim_dict(self) -> dict:`

UniProt's `Protein` model (lines 1-92 in `models/protein.py`) has NO such method.

**Constitutional Requirement:**

> "Does the primary model have `to_slim()` method?"

**Compliance Status:** ❌ **FAIL** - Model missing standardized method. Client workaround exists but not compliant.

---

## Remediation Required

### 1. Fix Principle II (Fuzzy-to-Fact) — HIGH PRIORITY

**Location**: `src/lifesciences_mcp/clients/uniprot.py`, lines 236-287

**Required Changes**:

Add empty result check after line 237:

```python
data = response.json()
results = data.get("results", [])

# ADD THIS CHECK (Constitution Principle II):
if len(results) == 0:
    return ErrorEnvelope(
        error=ErrorDetail(
            code=ErrorCode.ENTITY_NOT_FOUND,
            message=f"No proteins found matching query: {query}",
            recovery_hint="Try a different search term or check spelling. Examples: 'p53', 'insulin', 'BRCA1'",
            invalid_input=query,
        )
    )

# Then continue with existing candidate building logic...
candidates = []
for i, result in enumerate(results):
    ...
```

**Testing**:

Add test case for nonexistent protein:

```python
async def test_search_nonexistent_protein():
    """Test search returns ENTITY_NOT_FOUND for invalid queries."""
    client = UniProtClient()
    result = await client.search_proteins("ZZZZZ99")

    assert isinstance(result, ErrorEnvelope)
    assert result.error.code == ErrorCode.ENTITY_NOT_FOUND
    assert "No proteins found" in result.error.message
```

---

### 2. Fix Principle IV (Token Budgeting) — HIGH PRIORITY

**Location**: `src/lifesciences_mcp/models/protein.py`, lines 44-92

**Required Changes**:

Add `to_slim()` method to `Protein` model:

```python
class Protein(BaseModel):
    """Complete protein record from UniProt..."""

    # ... existing fields ...

    def to_slim(self) -> dict[str, Any]:
        """Return slim representation with minimal fields (~20 tokens).

        Constitution Principle IV: Token budgeting for context-constrained agents.
        Omits full_name, gene_names, organism_id, function, sequence_length,
        and cross_references.

        Returns:
            Dict with id, accession, name, organism only.
        """
        return {
            "id": self.id,
            "accession": self.accession,
            "name": self.name,
            "organism": self.organism,
        }
```

**Then update client** (`src/lifesciences_mcp/clients/uniprot.py`, lines 438-460):

Replace conditional dict building with model method call:

```python
# OLD (lines 438-460):
protein_dict = {
    "id": uniprot_id,
    "accession": accession,
    "name": full_name,
    "organism": organism_name,
}

if not slim:
    protein_dict.update({...})

return Protein(**protein_dict)

# NEW:
# Always build full Protein model
protein = Protein(
    id=uniprot_id,
    accession=accession,
    name=full_name,
    full_name=full_name,
    gene_names=gene_names,
    organism=organism_name,
    organism_id=organism_id,
    function=function_text,
    sequence_length=sequence_length,
    cross_references=cross_references,
)

# Return slim representation if requested
if slim:
    return Protein(**protein.to_slim())
else:
    return protein
```

**Testing**:

Add test case for slim mode:

```python
async def test_get_protein_slim_mode():
    """Test slim mode returns only essential fields."""
    client = UniProtClient()
    result = await client.get_protein("UniProtKB:P04637", slim=True)

    assert isinstance(result, Protein)
    # Check only essential fields present
    assert "id" in result.model_dump()
    assert "name" in result.model_dump()
    assert "organism" in result.model_dump()
    # Check optional fields ABSENT
    assert "cross_references" not in result.model_dump(exclude_none=True)
    assert "function" not in result.model_dump(exclude_none=True)
```

---

## Non-Critical Findings

### Principle I — Async-First ✅ PASS

**Evidence:**

- Inherits from `LifeSciencesClient` (line 29 in `uniprot.py`)
- Uses `httpx.AsyncClient` via `self._get()` inherited method
- All methods are `async def` (lines 170, 314)
- Context manager support (lines 55-63)

**Compliance:** Fully compliant.

---

### Principle III — Schema Determinism ✅ PASS

**Evidence:**

- Returns `PaginationEnvelope[ProteinSearchCandidate]` for search (line 176)
- Returns `ErrorEnvelope` for errors (lines 192, 220-234, 289-312, 331-395)
- Uses `CrossReferences` model (line 168, field at line 63)
- Omits null values via Pydantic `exclude_none=True` (line 94 in server)

**Compliance:** Fully compliant.

---

### Principle V — Rate Limiting ✅ PASS

**Evidence:**

- `_rate_limited_get()` method (lines 65-112)
- `asyncio.Lock` for concurrency control (line 53)
- Rate limit delay: 0.1s = 10 req/sec (line 42)
- Exponential backoff on 429/403 (lines 88-111)
- Retry-After header support (line 94)
- Thundering herd prevention (lines 102-107)

**Compliance:** Fully compliant. Matches BioGRID reference implementation.

---

### Principle VI — Spec Artifacts ✅ PASS

**Evidence:**

```
specs/002-uniprot-mcp-server/
├── compliance-analysis-2026-01-03.md
├── plan.md
├── quickstart.md
├── research.md
├── spec.md
├── tasks.md
└── checklists/
    └── requirements.md
```

**Compliance:** Spec directory exists with standard artifacts.

---

## Files Reviewed

1. **Client**: `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/uniprot.py` (461 lines)
   - Line 217: API call in `search_proteins` (makes call but no empty check)
   - Lines 236-287: Search result parsing (MISSING empty result check)
   - Lines 314-460: `get_protein` strict lookup (correct CURIE validation, 404 → ENTITY_NOT_FOUND)
   - Lines 438-460: Client-side slim mode logic (SHOULD be model method)

2. **Models**: `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/models/protein.py` (92 lines)
   - Lines 19-42: `ProteinSearchCandidate` (search phase model)
   - Lines 44-92: `Protein` (strict lookup model)
   - **MISSING**: `to_slim()` method (required by Principle IV)

3. **Server**: `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/servers/uniprot.py` (99 lines)
   - Lines 34-62: `search_proteins` tool (exposes `slim` parameter ✅)
   - Lines 65-94: `get_protein` tool (exposes `slim` parameter ✅)

4. **Reference**: `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/biogrid.py` (lines 1-250)
   - Lines 163-225: Reference implementation showing API-backed existence check
   - Line 199: `if count == 0: return ErrorEnvelope(ENTITY_NOT_FOUND)` ← **This is what UniProt needs**

5. **Reference Model**: `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/models/biogrid.py` (lines 115-134)
   - Lines 115-134: `to_slim()` method implementation ← **This is what Protein model needs**

---

## Conclusion

UniProt client is **66% compliant** (4/6 principles PASS).

**Critical blockers for full compliance:**

1. **Principle II (Fuzzy-to-Fact)**: Add empty result check in `search_proteins` to return `ENTITY_NOT_FOUND`
2. **Principle IV (Token Budgeting)**: Add `to_slim()` method to `Protein` model

**Estimated effort**: 1-2 hours (add 1 if-statement + 1 method + 2 test cases).

**Priority**: HIGH - These are constitutional principles that all 13 MCP servers must follow for consistency.
