# Pytest Best Practices for Life Sciences MCP

This document captures testing patterns that mirror the error handling behavior built into our MCP clients.

## Test Layer Architecture

| Layer | Purpose | Network | Markers |
|-------|---------|---------|---------|
| **Unit** | Validate logic without external calls | No | `@pytest.mark.unit` |
| **Integration** | Validate against live APIs | Yes | `@pytest.mark.integration` |
| **E2E** | Validate complete workflows | Yes | `@pytest.mark.e2e` |

**Recommended execution order:** unit → integration → e2e

## Error Handling in Tests

Our MCP clients handle errors with:
- **Rate limiting (429):** Exponential backoff with retry
- **Service unavailable (503):** Exponential backoff with retry
- **Internal errors (500):** Return ErrorEnvelope, no retry
- **Timeouts:** Return ErrorEnvelope with recovery hint

### Tests Should Mirror Client Behavior

Integration tests should:

1. **Assert ErrorEnvelopes on failure** - Don't fail when API returns expected errors
2. **Use test-level timeouts** - Prevent indefinite hangs
3. **Handle flaky APIs gracefully** - External services are unpredictable

```python
@pytest.mark.integration
@pytest.mark.timeout(60)
async def test_get_gene_handles_server_error(client):
    """Test that 500 errors return proper ErrorEnvelope."""
    result = await client.get_gene("ENSG00000141510")

    # Accept both success and proper error handling
    if isinstance(result, ErrorEnvelope):
        assert result.error.code in (ErrorCode.UPSTREAM_ERROR, ErrorCode.RATE_LIMITED)
        assert result.error.recovery_hint is not None
    else:
        assert isinstance(result, EnsemblGene)
```

## Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
markers = [
    "unit: marks tests as unit tests (no network required)",
    "integration: marks tests as integration tests (require network)",
    "e2e: marks tests as end-to-end tests (require live server)",
    "flaky: marks tests as flaky (retry on failure)",
]
timeout = 60  # Global timeout prevents hanging tests
timeout_method = "thread"
# Retry configuration for transient failures
reruns = 2
reruns_delay = 5
```

## Running Tests

```bash
# Run by layer (recommended order)
uv run pytest -m unit -v              # Fast, no network
uv run pytest -m integration -v       # Network required
uv run pytest -m e2e -v               # Full system

# Run by folder (alternative)
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest tests/e2e/ -v

# Stop on first failure (useful when API is having issues)
uv run pytest -m integration -v -x

# Skip specific flaky tests
uv run pytest -m integration -v -k "not ensembl"

# Run with retry for flaky tests
uv run pytest -m integration -v --reruns=2 --reruns-delay=5
```

## Handling Flaky External APIs

When external APIs are unreliable:

1. **Isolate the problem** - Run failing tests individually
2. **Check API status** - Some APIs have status pages
3. **Use skip conditions** - Mark tests to skip when service is unavailable
4. **Add retry logic** - Use pytest-rerunfailures for automatic retries

### Health Check Fixtures

We provide health check fixtures in `tests/integration/conftest.py` that skip tests when external services are unavailable:

```python
import httpx
import pytest

@pytest.fixture(scope="function")
async def check_ensembl_available():
    """Check if Ensembl REST API is reachable before running tests.

    Uses the dedicated /info/ping endpoint for health checks.
    Skips tests if the service is down to prevent cascading failures.
    """
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get("https://rest.ensembl.org/info/ping")
            if response.status_code == 200:
                data = response.json()
                if data.get("ping") == 1:
                    return True
            pytest.skip(f"Ensembl API unhealthy: status={response.status_code}")
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"Ensembl API unavailable: {e}")
    except Exception as e:
        pytest.skip(f"Ensembl health check failed: {e}")
    return False

@pytest.fixture(scope="function")
async def check_entrez_available():
    """Check if NCBI Entrez service is reachable before running tests."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi",
                params={"retmode": "json"},
            )
            if response.status_code == 200:
                return True
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"NCBI Entrez service unavailable: {e}")
    except Exception as e:
        pytest.skip(f"Entrez health check failed: {e}")
    return False
```

**Usage in test files:**
```python
class TestGetGene:
    async def test_get_gene_tp53(self, client: EnsemblClient, check_ensembl_available):
        """Test requires Ensembl API to be available."""
        result = await client.get_gene("ENSG00000141510")
        assert isinstance(result, EnsemblGene)
```

### pytest-rerunfailures for Automatic Retries

For tests that may fail due to transient issues, use the `flaky` marker:

```python
@pytest.mark.flaky(reruns=3, reruns_delay=2)
@pytest.mark.integration
async def test_external_api():
    """Test with automatic retry on failure."""
    pass

# Only retry on specific exceptions
@pytest.mark.flaky(reruns=3, only_rerun=["httpx.TimeoutException", "AssertionError"])
async def test_slow_api():
    pass
```

## Current Client Retry Behavior

| Client | Rate Limit (429) | Server Error (500) | Timeout |
|--------|------------------|--------------------|---------|
| Ensembl | 3 retries + backoff | No retry | No retry |
| ChEMBL | 3 retries + backoff | 3 retries + backoff | No retry |
| UniProt | Rate limited | No retry | No retry |
| Others | Varies | Return ErrorEnvelope | Return ErrorEnvelope |

## API Reliability by Service

Based on test observations:

| API | Reliability | Common Failure Mode | Mitigation |
|-----|-------------|---------------------|------------|
| HGNC | HIGH | Rare | None needed |
| UniProt | HIGH | Rare | None needed |
| ChEMBL | HIGH | Rare | None needed |
| Open Targets | HIGH | Rare | None needed |
| STRING | HIGH | Rare | Health check fixture |
| BioGRID | HIGH | Rare | None needed |
| **Ensembl** | **MEDIUM** | HTTP 500 server errors | Health check fixture |
| **Entrez** | **MEDIUM** | Timeouts on high-volume | Health check fixture |
| PubChem | HIGH | Rare | None needed |
| IUPHAR | HIGH | Rare | Health check fixture |
| WikiPathways | HIGH | Rare | Health check fixture |
| ClinicalTrials.gov | N/A | Cloudflare blocking | Manual curl testing |

## Unit Testing with RESPX (Mocking httpx)

For deterministic unit tests that don't require network access, use RESPX:

```python
import respx
import httpx
import pytest
from lifesciences_mcp.clients.ensembl import EnsemblClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope

@respx.mock
@pytest.mark.asyncio
async def test_get_gene_returns_gene_on_success():
    """Unit test: verify client parses valid API response correctly."""
    respx.get("https://rest.ensembl.org/lookup/id/ENSG00000141510").mock(
        return_value=httpx.Response(200, json={
            "id": "ENSG00000141510",
            "display_name": "TP53",
            "biotype": "protein_coding",
            "species": "homo_sapiens",
        })
    )

    async with EnsemblClient() as client:
        result = await client.get_gene("ENSG00000141510")

    assert result.id == "ENSG00000141510"
    assert result.symbol == "TP53"

@respx.mock
@pytest.mark.asyncio
async def test_get_gene_returns_error_envelope_on_500():
    """Unit test: verify client returns ErrorEnvelope on server error."""
    respx.get("https://rest.ensembl.org/lookup/id/ENSG00000141510").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )

    async with EnsemblClient() as client:
        result = await client.get_gene("ENSG00000141510")

    assert isinstance(result, ErrorEnvelope)
    assert result.error.code.value == "UPSTREAM_ERROR"
```

## Implementation Checklist

### Completed
- [x] Test markers (unit, integration, e2e)
- [x] Global timeout configuration (60s)
- [x] Health check fixtures for IUPHAR, WikiPathways, STRING, ChEMBL
- [x] Async client fixtures with proper cleanup
- [x] ErrorEnvelope pattern in tests
- [x] Granular client timeouts (connect=5s, read=30s, write=10s, pool=5s)
- [x] Rate limit handling with exponential backoff

### High Priority (Implement Next)
- [ ] Add Ensembl health check fixture
- [ ] Add Entrez health check fixture
- [ ] Add `pytest-rerunfailures>=14.0` to dev dependencies
- [ ] Configure global retry settings in pyproject.toml

### Medium Priority (Near-Term)
- [ ] Add `respx>=0.21.0` to dev dependencies
- [ ] Create unit tests for each client using RESPX mocks
- [ ] Consider adding 500 error retry to client base class

### Future Improvements
- [ ] Evaluate VCR/pytest-recording for cassette-based testing
- [ ] Add timing assertions to catch performance regressions
- [ ] Consider CI/CD separation: unit tests on PRs, integration tests nightly

## Research Sources

- [pytest External API Testing Guide](https://pytest-with-eric.com/api-testing/pytest-external-api-testing/)
- [Python Integration Testing Guide](https://www.lambdatest.com/learning-hub/python-integration-testing)
- [pytest-rerunfailures Documentation](https://pytest-rerunfailures.readthedocs.io/latest/mark.html)
- [RESPX User Guide](https://lundberg.github.io/respx/guide/)
- [pytest Skip Documentation](https://docs.pytest.org/en/stable/how-to/skipping.html)
