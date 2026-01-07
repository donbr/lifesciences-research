# Test Failures - Follow Up Required

**Test Run Date:** 2026-01-07
**Total Tests:** 291 (28 skipped)
**Passed:** 255
**Failed:** 8
**Run Time:** 9 minutes 30 seconds

## Summary

8 tests failed across 3 test files:
- 4 failures in ClinicalTrials error recovery tests
- 2 failures in Entrez performance tests
- 2 failures in WikiPathways integration tests

## Failed Tests

### 1. ClinicalTrials Error Recovery (4 failures)

**File:** `tests/integration/test_error_recovery.py`

1. `test_unresolved_entity_recovery_workflow`
2. `test_entity_not_found_recovery_hint`
3. `test_complete_error_hint_recovery_success_cycle`
4. `test_multiple_error_recovery_cycles_clinicaltrials`

**Notes:**
- These are error recovery workflow tests
- May be related to the Cloudflare blocking issue documented in CLAUDE.md
- ClinicalTrials.gov blocks Python httpx clients (403 Forbidden)
- Consider skipping these tests or marking as expected failures

### 2. Entrez Performance (2 failures)

**File:** `tests/integration/test_entrez_performance.py`

1. `test_get_gene_performance`
2. `test_rate_limiting_performance`

**Notes:**
- Performance tests may be timing-sensitive
- Could fail due to network latency or NCBI rate limiting
- Review SC-001 performance criteria (<2s for 95% of queries)

### 3. WikiPathways Integration (2 failures)

**File:** `tests/integration/test_wikipathways_api.py`

1. `test_get_pathway_not_found`
2. `test_search_pathways_empty_results`

**Notes:**
- Error handling tests for not-found scenarios
- May need to update expected error codes or recovery hints

## Action Items

- [ ] Investigate ClinicalTrials error recovery failures
- [ ] Review Entrez performance thresholds
- [ ] Fix WikiPathways error handling for not-found cases
- [ ] Consider marking ClinicalTrials tests as xfail due to Cloudflare blocking
- [ ] Run individual test files to get detailed error messages

## Commands to Debug

```bash
# Run individual test files with verbose output
uv run pytest tests/integration/test_error_recovery.py::TestClinicalTrialsErrorRecovery -v
uv run pytest tests/integration/test_entrez_performance.py -v
uv run pytest tests/integration/test_wikipathways_api.py -v

# Run with full traceback
uv run pytest tests/integration/test_error_recovery.py -vv --tb=long
```
