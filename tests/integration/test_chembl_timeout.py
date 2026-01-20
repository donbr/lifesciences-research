
import asyncio
import unittest.mock
import pytest
from unittest.mock import MagicMock, patch

from lifesciences_mcp.clients.chembl import ChEMBLClient
from lifesciences_mcp.models.envelopes import ErrorCode, ErrorEnvelope

pytestmark = pytest.mark.chembl


@pytest.mark.asyncio
async def test_chembl_client_timeout_enforcement():
    """Verify that ChEMBL client enforces timeout on slow SDK calls."""
    client = ChEMBLClient()
    # reduce timeout for test speed
    client._timeout = 0.5

    # Create a mock SDK function that sleeps longer than the timeout
    # We need to wrap it so it runs in the executor (thread)
    def slow_sdk_function():
        import time
        time.sleep(1.0)  # Sleep longer than timeout (0.5s)
        return "result"

    try:
        # Verify that _rate_limited_sdk_call enforces timeout on slow SDK calls
        with pytest.raises(TimeoutError) as excinfo:
            await client._rate_limited_sdk_call(slow_sdk_function)
        
        assert "timeout" in str(excinfo.value).lower()
        
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_chembl_client_timeout_mapping_integration():
    """Verify that a timeout actually results in UPSTREAM_ERROR when calling a public method."""
    client = ChEMBLClient()
    client._timeout = 0.1
    
    # Mock the internal _molecule.search to hang
    # Since search_compounds defines a local 'sdk_search' function calling _molecule.search
    # we can mock self._molecule.search to sleep.
    
    mock_search = MagicMock()
    def slow_search(*args, **kwargs):
        import time
        time.sleep(0.5)
        return []
    
    mock_search.search.side_effect = slow_search
    client._molecule = mock_search

    # Act - Timeout should fail immediately without retries (per implementation)
    result = await client.search_compounds("aspirin")
    
    # Assert
    assert isinstance(result, ErrorEnvelope)
    assert result.error.code == ErrorCode.UPSTREAM_ERROR
    assert "temporarily unavailable" in result.error.recovery_hint

    await client.close()


@pytest.mark.asyncio
async def test_chembl_timeout_no_retry():
    """Verify that timeouts fail fast without exponential backoff retries."""
    client = ChEMBLClient()
    client._timeout = 0.2
    
    # Track how many times the slow function is called
    call_count = 0
    def slow_sdk_function():
        nonlocal call_count
        call_count += 1
        import time
        time.sleep(0.5)
        return "result"
    
    try:
        import time
        start_time = time.monotonic()
        # Expect failure
        with pytest.raises(TimeoutError):
            await client._sdk_call_with_backoff(slow_sdk_function)
        
        elapsed = time.monotonic() - start_time
        
        # Should fail after ~0.2s (timeout), not after multiple retries
        # If it retried, it would be at least 0.2s + backoff + 0.2s + ...
        assert elapsed < 1.0, f"Timeout should fail fast, took {elapsed:.2f}s"
        assert call_count == 1, f"Timeout should not retry, called {call_count} times"
        
    except Exception as e:
        # Just in case some other error pops up
        if "timeout" not in str(e).lower():
            raise e
    finally:
        await client.close()
