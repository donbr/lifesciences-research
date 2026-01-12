
import asyncio
import unittest.mock
import pytest
from unittest.mock import MagicMock, patch

from lifesciences_mcp.clients.chembl import ChEMBLClient
from lifesciences_mcp.models.envelopes import ErrorCode, ErrorEnvelope


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

    # We mock _get_executor to return a real ThreadPoolExecutor 
    # (or just use the real one, but we want to be sure it's working)
    
    try:
        # We need to mock the _rate_limited_sdk_call ONLY for the actual execution part?
        # No, we want to test _rate_limited_sdk_call logic itself.
        # But _rate_limited_sdk_call calls loop.run_in_executor(self._get_executor(), sdk_func)
        # So we can pass our slow function directly to _rate_limited_sdk_call?
        # No, _rate_limited_sdk_call is "internal" but widely used.
        # Let's call a public method like search_compounds but mock the SDK object inside it.
        
        # Actually, verifying _rate_limited_sdk_call directly is effective integration testing.
        with pytest.raises(TimeoutError) as excinfo:
            await client._rate_limited_sdk_call(slow_sdk_function)
        
        assert "timeout" in str(excinfo.value)
        
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

    # Act
    # We expect an internal retry loop, so it might take 0.1s * (retries)
    # But wait, we said "timeouts not retried" in the code comment!
    # Let's verify that expectation too.
    
    result = await client.search_compounds("aspirin")
    
    # Assert
    assert isinstance(result, ErrorEnvelope)
    assert result.error.code == ErrorCode.UPSTREAM_ERROR
    assert "temporarily unavailable" in result.error.recovery_hint

    await client.close()
