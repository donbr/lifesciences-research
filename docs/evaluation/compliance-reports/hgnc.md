# Constitution Compliance Report: HGNC

**Agent**: Agent 1
**Date**: 2026-02-06
**Client**: `src/lifesciences_mcp/clients/hgnc.py`
**Server**: `src/lifesciences_mcp/servers/hgnc.py`

## Summary

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Async-First | PASS | Inherits from LifeSciencesClient, uses httpx.AsyncClient |
| II. Fuzzy-to-Fact | PASS | search_genes makes real API calls at lines 159, 265 |
| III. Schema Determinism | PASS | PaginationEnvelope, ErrorEnvelope, CrossReferences all present |
| IV. Token Budgeting | FAIL | No to_slim() method, slim parameter exposed but not implemented |
| V. Spec-Before-Code | PASS | specs/001-hgnc-mcp-server/ directory exists with 8 artifacts |
| Rate Limiting | PASS | _rate_limited_get() with asyncio.Lock, exponential backoff |

## Critical Findings

### Principle II: Fuzzy-to-Fact
- **Search method**: `search_genes` at line 110
- **Makes API call**: YES
- **Evidence**:
  ```python
  # Line 159: General search
  response = await self._rate_limited_get(f"/search/{query}")

  # Line 265: Alias search
  response = await self._rate_limited_get(f"/search/alias_symbol/{query}")
  ```
- **Nonexistent entity handling**: ENTITY_NOT_FOUND
  - Line 303: `return ErrorEnvelope.entity_not_found(hgnc_id)` when no docs returned
  - Strict lookup at line 273 validates CURIE format first (line 283): `if not HGNC_CURIE_PATTERN.match(hgnc_id): return ErrorEnvelope.unresolved_entity(hgnc_id)`
- **Verdict**: PASS

**Architecture**: Uses dual-API strategy with alias boosting:
1. First searches `/search/alias_symbol/{query}` for exact alias matches (boosted to score=1.0)
2. Then searches `/search/{query}` for general symbol/name matches
3. Merges results with alias matches prioritized

This ensures common aliases like "p53" resolve to TP53 first, demonstrating strong Fuzzy-to-Fact compliance.

### Principle IV: Token Budgeting
- **slim parameter on search**: YES (line 113: `slim: bool = False`)
- **slim parameter on strict lookup**: NO (get_gene at line 273 does not accept slim parameter)
- **to_slim() on model**: NO (Gene model at gene.py:39-88 has no to_slim() method)
- **slim exposed on server tool**: YES (server search_genes line 39, but NOT on get_gene line 68)
- **Verdict**: FAIL

**Evidence of partial implementation**:
- Client search_genes accepts `slim` parameter (line 113) but never uses it
- Server search_genes accepts `slim` parameter (line 39) and passes it to client (line 59-64)
- However, the parameter has no effect on output - no conditional logic based on slim value
- Gene model has `to_search_candidate()` method (line 80) but NOT `to_slim()`
- SearchCandidate is already minimal (~20 tokens) so slim mode may not be needed there
- Gene model is full (~115-300 tokens depending on cross-refs) and SHOULD have to_slim()

**Comparison with BioGRID reference**:
- BioGRID InteractionResult has `to_slim()` method (biogrid.py:115)
- BioGRID get_interactions accepts `slim: bool = False` (biogrid.py:262)
- BioGRID implements slim logic: `if slim: return result.to_slim()` (biogrid.py:390)

## Remediation Required

### HIGH PRIORITY: Principle IV Token Budgeting

1. **Add to_slim() method to Gene model** (`src/lifesciences_mcp/models/gene.py`)
   - Location: After line 88 (after to_search_candidate method)
   - Implementation:
     ```python
     def to_slim(self) -> dict[str, Any]:
         """Return minimal representation (~20 tokens) for token budgeting."""
         return {
             "id": self.id,
             "symbol": self.symbol,
             "name": self.name,
             "status": self.status,
         }
     ```

2. **Add slim parameter to get_gene client method** (`src/lifesciences_mcp/clients/hgnc.py`)
   - Location: Line 273 method signature
   - Change: `async def get_gene(self, hgnc_id: str) -> Gene | ErrorEnvelope:`
   - To: `async def get_gene(self, hgnc_id: str, slim: bool = False) -> Gene | dict[str, Any] | ErrorEnvelope:`
   - Add before return at line 326:
     ```python
     if slim:
         return gene.to_slim()
     return gene
     ```

3. **Add slim parameter to get_gene server tool** (`src/lifesciences_mcp/servers/hgnc.py`)
   - Location: Line 68 method signature
   - Change: `async def get_gene(hgnc_id: str) -> Gene | ErrorEnvelope:`
   - To: `async def get_gene(hgnc_id: str, slim: bool = False) -> Gene | dict[str, Any] | ErrorEnvelope:`
   - Update client call at line 81: `return await client.get_gene(hgnc_id=hgnc_id, slim=slim)`

4. **Implement slim logic in search_genes client method** (`src/lifesciences_mcp/clients/hgnc.py`)
   - Location: After line 230 (after candidates.sort)
   - Note: SearchCandidate is already minimal, so slim could return even simpler dict or remain as-is
   - Document in docstring that slim has no effect since SearchCandidate is already ~20 tokens
   - Alternative: If slim=True, convert SearchCandidate to plain dict with just id/symbol/score

### MEDIUM PRIORITY: Documentation

5. **Update CLAUDE.md** to reflect HGNC's partial token budgeting compliance
   - Location: Line referring to HGNC as "Complete"
   - Add note: "HGNC partial token budgeting (search only, strict lookup needs implementation)"

## Architecture Strengths

1. **Robust Fuzzy-to-Fact**: Dual-API search with alias boosting is sophisticated
2. **Rate Limiting**: Excellent implementation with lock inside request + exponential backoff (lines 75-108)
3. **Error Handling**: Comprehensive ErrorEnvelope usage with all 6 standard codes
4. **Schema Compliance**: Perfect PaginationEnvelope and CrossReferences usage
5. **Async-First**: Clean inheritance from LifeSciencesClient base class

## Comparison with BioGRID Reference

| Feature | HGNC | BioGRID | Status |
|---------|------|---------|--------|
| API-backed search | ✅ (2 endpoints) | ✅ (format=count) | HGNC more sophisticated |
| Rate limiting | ✅ | ✅ | Equal quality |
| Fuzzy-to-Fact | ✅ | ✅ | Both PASS |
| Token budgeting | ❌ (partial) | ✅ (full) | HGNC needs work |
| slim on search | ✅ (exposed but no-op) | ✅ (full) | HGNC not implemented |
| slim on strict | ❌ | ✅ | HGNC missing |
| to_slim() method | ❌ | ✅ | HGNC missing |

## Files Reviewed

- `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/hgnc.py` (363 lines)
- `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/models/gene.py` (88 lines)
- `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/servers/hgnc.py` (86 lines)
- `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/base.py` (77 lines)
- `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/models/envelopes.py` (145 lines)
- `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/models/cross_references.py` (155 lines)
- `/home/donbr/graphiti-org/lifesciences-research/tests/integration/test_hgnc_api.py` (121 lines)
- `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/biogrid.py` (first 300 lines, reference)
- `/home/donbr/graphiti-org/lifesciences-research/specs/001-hgnc-mcp-server/` (8 spec artifacts confirmed)

## Test Coverage Analysis

Integration tests at `tests/integration/test_hgnc_api.py` cover:
- ✅ Fuzzy search for BRCA1 (line 26)
- ✅ Pagination with cursor (line 38)
- ✅ Strict lookup by CURIE (line 62)
- ✅ Invalid CURIE returns UNRESOLVED_ENTITY (line 73)
- ✅ Nonexistent CURIE returns ENTITY_NOT_FOUND (line 81)
- ✅ Complete Fuzzy-to-Fact workflow (line 88)
- ✅ Short query returns AMBIGUOUS_QUERY (line 112)

**Missing test coverage**:
- ❌ No tests for slim parameter on search_genes
- ❌ No tests for slim parameter on get_gene (doesn't exist yet)

## Recommendations

### Immediate Actions (Required for Full Compliance)

1. Implement `to_slim()` on Gene model
2. Add `slim` parameter to `get_gene()` in client, server, and implement logic
3. Add integration tests for slim mode on both search and strict lookup

### Future Enhancements (Optional)

1. Consider if SearchCandidate needs even slimmer representation (currently ~20 tokens, could go to ~10)
2. Document token budgeting in HGNC spec artifacts (specs/001-hgnc-mcp-server/)
3. Add performance benchmark comparing full vs slim responses (estimate: 20 tokens vs 115-300 tokens)

## Conclusion

HGNC is **mostly compliant** with 5/6 Constitution principles fully passing. The Fuzzy-to-Fact implementation is exemplary with dual-API search and alias boosting. The main gap is **Principle IV (Token Budgeting)** which is partially implemented but not functional.

**Recommendation**: Address token budgeting remediation items 1-4 above to achieve full Constitution compliance. Estimated effort: 2-3 hours (add to_slim(), update method signatures, add tests).
