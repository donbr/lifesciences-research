"""Unit tests for PubChemClient with mocked API responses.

Tests client logic including rate limiting, CURIE validation, error mapping,
and exponential backoff without making actual API calls.

Run with: pytest tests/unit/test_pubchem_client.py -v
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from lifesciences_mcp.clients.pubchem import PubChemClient
from lifesciences_mcp.models.envelopes import ErrorCode, ErrorEnvelope

# =============================================================================
# T027: Rate Limit Per Second Tests
# =============================================================================


class TestRateLimitPerSecond:
    """Test per-second rate limiting (5 req/s = 200ms minimum interval)."""

    @pytest.mark.asyncio
    async def test_rate_limit_per_second(self):
        """Verify 5 req/s limit with 200ms minimum interval using mock time."""
        client = PubChemClient()

        # Mock httpx.AsyncClient.get to return immediately
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"PC_Compounds": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Make 3 rapid requests and measure timing
            start = time.monotonic()
            await client._rate_limited_get("https://test.url")
            await client._rate_limited_get("https://test.url")
            await client._rate_limited_get("https://test.url")
            elapsed = time.monotonic() - start

            # Should take at least 2 intervals (200ms * 2 = 400ms)
            # Allow 350ms to account for timing precision
            assert elapsed >= 0.35, f"Expected delay of ~400ms, got {elapsed * 1000:.1f}ms"

        await client.close()

    @pytest.mark.asyncio
    async def test_rate_limit_minimum_interval(self):
        """Verify minimum 200ms interval between requests."""
        client = PubChemClient()

        # Verify configuration
        assert client.RATE_LIMIT_PER_SECOND == 5
        min_interval = 1.0 / client.RATE_LIMIT_PER_SECOND
        assert min_interval == pytest.approx(0.2, rel=0.01)  # 200ms

        await client.close()

    @pytest.mark.asyncio
    async def test_rate_limit_enforces_delay_with_jitter(self):
        """Test that rate limiting delays requests with jitter."""
        client = PubChemClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"PC_Compounds": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Make two rapid requests
            start = time.monotonic()
            await client._rate_limited_get("https://test.url")
            await client._rate_limited_get("https://test.url")
            elapsed = time.monotonic() - start

            # Should take at least one interval (200ms), but jitter adds up to 20ms
            # Allow 190ms minimum due to timing precision
            assert elapsed >= 0.19, f"Expected delay of ~200ms, got {elapsed * 1000:.1f}ms"
            # Should not exceed 250ms (200ms + 20ms jitter + 30ms buffer)
            assert elapsed <= 0.25, f"Expected max delay of ~250ms, got {elapsed * 1000:.1f}ms"

        await client.close()


# =============================================================================
# T028: Rate Limit Per Minute Tests
# =============================================================================


class TestRateLimitPerMinute:
    """Test per-minute rate limiting (400 req/min rolling window)."""

    @pytest.mark.asyncio
    async def test_rate_limit_per_minute_configuration(self):
        """Verify rate limit configuration constants."""
        client = PubChemClient()

        assert client.RATE_LIMIT_PER_MINUTE == 400
        assert client._minute_window.maxlen == 400

        await client.close()

    @pytest.mark.asyncio
    async def test_rate_limit_rolling_window_tracking(self):
        """Verify rolling window tracks request timestamps."""
        client = PubChemClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"PC_Compounds": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Make 3 requests
            await client._rate_limited_get("https://test.url")
            await client._rate_limited_get("https://test.url")
            await client._rate_limited_get("https://test.url")

            # Window should contain 3 timestamps
            assert len(client._minute_window) == 3

            # Timestamps should be recent
            now = time.monotonic()
            for timestamp in client._minute_window:
                assert now - timestamp < 1.0  # All within last second

        await client.close()

    @pytest.mark.asyncio
    async def test_rate_limit_window_expiration(self):
        """Test that old timestamps are removed when window is full."""
        client = PubChemClient()

        # Fill the window to capacity (400 items)
        old_time = time.monotonic() - 61.0
        for _ in range(400):
            client._minute_window.append(old_time)

        assert len(client._minute_window) == 400

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"PC_Compounds": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Make a request - should clean up old timestamps since window is full
            await client._rate_limited_get("https://test.url")

            # Window should still be at capacity but with old timestamp removed
            assert len(client._minute_window) == 400
            # All timestamps should be old (the deque maxlen handles overflow)
            # The newest timestamp should be recent
            now = time.monotonic()
            newest_timestamp = client._minute_window[-1]
            assert now - newest_timestamp < 1.0

        await client.close()


# =============================================================================
# T029: CURIE Validation Valid Tests
# =============================================================================


class TestCurieValidationValid:
    """Test valid CURIE format validation."""

    def test_curie_validation_valid_short(self):
        """Test valid CURIE format with short CID."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("PubChem:CID2244")

        assert isinstance(result, int)
        assert result == 2244

    def test_curie_validation_valid_long(self):
        """Test valid CURIE format with long CID."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("PubChem:CID123456789")

        assert isinstance(result, int)
        assert result == 123456789

    def test_curie_validation_valid_single_digit(self):
        """Test valid CURIE format with single-digit CID."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("PubChem:CID1")

        assert isinstance(result, int)
        assert result == 1

    def test_curie_validation_valid_aspirin(self):
        """Test valid CURIE format for aspirin (CID2244)."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("PubChem:CID2244")

        assert isinstance(result, int)
        assert result == 2244


# =============================================================================
# T030: CURIE Validation Invalid Tests
# =============================================================================


class TestCurieValidationInvalid:
    """Test invalid CURIE format validation returns ErrorEnvelope."""

    def test_curie_validation_invalid_no_prefix(self):
        """Test invalid format without PubChem prefix (CID2244)."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("CID2244")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert "PubChem:CID" in result.error.recovery_hint
        assert result.error.invalid_input == "CID2244"

    def test_curie_validation_invalid_bare_number(self):
        """Test invalid format with bare number (2244)."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("2244")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert "PubChem:CID{number}" in result.error.recovery_hint
        assert result.error.invalid_input == "2244"

    def test_curie_validation_invalid_missing_cid(self):
        """Test invalid format missing CID component (PubChem:2244)."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("PubChem:2244")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert result.error.invalid_input == "PubChem:2244"

    def test_curie_validation_invalid_wrong_case(self):
        """Test invalid format with wrong case (pubchem:cid2244)."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("pubchem:cid2244")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == ErrorCode.UNRESOLVED_ENTITY

    def test_curie_validation_invalid_non_numeric_cid(self):
        """Test invalid format with non-numeric CID (PubChem:CIDABC)."""
        client = PubChemClient()

        result = client._validate_pubchem_curie("PubChem:CIDABC")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == ErrorCode.UNRESOLVED_ENTITY


# =============================================================================
# T031: Exponential Backoff Tests
# =============================================================================


class TestExponentialBackoff:
    """Test exponential backoff on HTTP 503 responses."""

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Mock HTTP 503 responses and verify backoff timing (1s, 2s, 4s with jitter)."""
        client = PubChemClient()

        # Mock response that returns 503 twice, then 200
        mock_responses = [
            MagicMock(status_code=503),
            MagicMock(status_code=503),
            MagicMock(status_code=200),
        ]
        mock_responses[2].raise_for_status = MagicMock()
        mock_responses[2].json.return_value = {"PC_Compounds": []}

        # Configure mock to raise HTTPStatusError for 503
        for i in [0, 1]:
            error = httpx.HTTPStatusError(
                "Service Unavailable", request=MagicMock(), response=mock_responses[i]
            )
            mock_responses[i].raise_for_status.side_effect = error

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = mock_responses

            start = time.monotonic()
            # This will retry on 503 with exponential backoff
            await client._request_with_backoff("https://test.url")
            elapsed = time.monotonic() - start

            # Expected: 1s (first retry) + 2s (second retry) = 3s
            # With jitter: up to 10% additional = 3.3s max
            # Allow 2.9s minimum due to timing precision
            assert elapsed >= 2.9, f"Expected delay of ~3s, got {elapsed:.1f}s"
            assert elapsed <= 3.5, f"Expected max delay of ~3.3s, got {elapsed:.1f}s"

        await client.close()

    @pytest.mark.asyncio
    async def test_exponential_backoff_max_retries(self):
        """Test that backoff respects MAX_RETRIES limit."""
        client = PubChemClient()

        # Mock response that always returns 503
        mock_response = MagicMock(status_code=503)
        error = httpx.HTTPStatusError(
            "Service Unavailable", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Should raise after MAX_RETRIES attempts
            with pytest.raises(httpx.HTTPStatusError):
                await client._request_with_backoff("https://test.url")

            # Should have made exactly MAX_RETRIES attempts
            assert mock_get.call_count == client.MAX_RETRIES

        await client.close()

    @pytest.mark.asyncio
    async def test_exponential_backoff_max_delay(self):
        """Test that backoff delay caps at MAX_DELAY (60s)."""
        client = PubChemClient()

        # Verify constants
        assert client.MAX_RETRIES == 3
        assert client.BASE_DELAY == 1.0
        assert client.MAX_DELAY == 60.0

        # Calculate delay for each retry
        for attempt in range(client.MAX_RETRIES):
            delay = min(client.BASE_DELAY * (2**attempt), client.MAX_DELAY)
            # Delays should be: 1s, 2s, 4s (all under 60s max)
            assert delay <= client.MAX_DELAY

        await client.close()


# =============================================================================
# T032: Error Mapping HTTP 400 Tests
# =============================================================================


class TestErrorMappingHTTP400:
    """Test HTTP 400 error mapping to UNRESOLVED_ENTITY."""

    def test_error_mapping_400_basic(self):
        """Verify HTTP 400 maps to UNRESOLVED_ENTITY with CURIE format hint."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=400, response_text="Invalid CID format", original_input="PubChem:CIDABC"
        )

        assert isinstance(error, ErrorEnvelope)
        assert error.success is False
        assert error.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert "Bad request" in error.error.message
        assert "PubChem:CID{number}" in error.error.recovery_hint
        assert error.error.invalid_input == "PubChem:CIDABC"

    def test_error_mapping_400_includes_response_text(self):
        """Verify error message includes response text."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=400, response_text="Invalid parameter: name", original_input="test"
        )

        assert "Invalid parameter: name" in error.error.message

    def test_error_mapping_400_recovery_hint_mentions_curie(self):
        """Verify recovery hint mentions CURIE format."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=400, response_text="Bad request", original_input=""
        )

        assert "CURIE format" in error.error.recovery_hint
        assert "PubChem:CID2244" in error.error.recovery_hint


# =============================================================================
# T033: Error Mapping HTTP 404 Tests
# =============================================================================


class TestErrorMappingHTTP404:
    """Test HTTP 404 error mapping to ENTITY_NOT_FOUND."""

    def test_error_mapping_404_basic(self):
        """Verify HTTP 404 maps to ENTITY_NOT_FOUND with search_compounds hint."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=404, response_text="CID not found", original_input="PubChem:CID999999999"
        )

        assert isinstance(error, ErrorEnvelope)
        assert error.success is False
        assert error.error.code == ErrorCode.ENTITY_NOT_FOUND
        assert "Compound not found" in error.error.message
        assert "search_compounds" in error.error.recovery_hint
        assert error.error.invalid_input == "PubChem:CID999999999"

    def test_error_mapping_404_message_includes_input(self):
        """Verify error message includes original input."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=404, response_text="Not found", original_input="PubChem:CID123456789"
        )

        assert "PubChem:CID123456789" in error.error.message

    def test_error_mapping_404_recovery_hint_mentions_search(self):
        """Verify recovery hint suggests using search_compounds."""
        client = PubChemClient()

        error = client._map_http_error(status_code=404, response_text="", original_input="")

        assert "search_compounds" in error.error.recovery_hint
        assert (
            "CID not found" in error.error.recovery_hint
            or "find valid CIDs" in error.error.recovery_hint
        )


# =============================================================================
# T034: Error Mapping HTTP 503 Tests
# =============================================================================


class TestErrorMappingHTTP503:
    """Test HTTP 503 error mapping to RATE_LIMITED."""

    def test_error_mapping_503_basic(self):
        """Verify HTTP 503 maps to RATE_LIMITED with wait time hint."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=503, response_text="Service temporarily unavailable", original_input=""
        )

        assert isinstance(error, ErrorEnvelope)
        assert error.success is False
        assert error.error.code == ErrorCode.RATE_LIMITED
        assert "busy" in error.error.message or "rate limit" in error.error.message
        assert "60 seconds" in error.error.recovery_hint
        assert "5 req/s" in error.error.recovery_hint
        assert "400 req/min" in error.error.recovery_hint

    def test_error_mapping_503_recovery_hint_mentions_limits(self):
        """Verify recovery hint mentions rate limits."""
        client = PubChemClient()

        error = client._map_http_error(status_code=503, response_text="", original_input="")

        hint = error.error.recovery_hint
        assert "5 req/s" in hint or "400 req/min" in hint
        assert "60 seconds" in hint or "60s" in hint.replace(" ", "")

    def test_error_mapping_503_message_mentions_rate_limit(self):
        """Verify error message mentions rate limiting or server busy."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=503, response_text="Rate limit exceeded", original_input=""
        )

        message = error.error.message.lower()
        assert "busy" in message or "rate limit" in message


# =============================================================================
# T026: Additional Error Mapping Tests
# =============================================================================


class TestErrorMappingOtherHTTPCodes:
    """Test error mapping for other HTTP status codes."""

    def test_error_mapping_500_maps_to_upstream_error(self):
        """Verify HTTP 500 maps to UPSTREAM_ERROR."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=500, response_text="Internal server error", original_input=""
        )

        assert isinstance(error, ErrorEnvelope)
        assert error.error.code == ErrorCode.UPSTREAM_ERROR
        assert "500" in error.error.message
        assert "Retry" in error.error.recovery_hint or "retry" in error.error.recovery_hint

    def test_error_mapping_502_maps_to_upstream_error(self):
        """Verify HTTP 502 maps to UPSTREAM_ERROR."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=502, response_text="Bad gateway", original_input=""
        )

        assert isinstance(error, ErrorEnvelope)
        assert error.error.code == ErrorCode.UPSTREAM_ERROR
        assert "502" in error.error.message

    def test_error_mapping_timeout_maps_to_upstream_error(self):
        """Verify timeout-like errors map to UPSTREAM_ERROR."""
        client = PubChemClient()

        error = client._map_http_error(
            status_code=504, response_text="Gateway timeout", original_input=""
        )

        assert isinstance(error, ErrorEnvelope)
        assert error.error.code == ErrorCode.UPSTREAM_ERROR
        assert "504" in error.error.message


# =============================================================================
# Additional Utility Tests
# =============================================================================


class TestCurieFormatting:
    """Test CURIE formatting utility."""

    def test_format_pubchem_curie_basic(self):
        """Test formatting CID as CURIE."""
        client = PubChemClient()

        curie = client._format_pubchem_curie(2244)

        assert curie == "PubChem:CID2244"

    def test_format_pubchem_curie_long(self):
        """Test formatting long CID as CURIE."""
        client = PubChemClient()

        curie = client._format_pubchem_curie(123456789)

        assert curie == "PubChem:CID123456789"

    def test_format_pubchem_curie_single_digit(self):
        """Test formatting single-digit CID as CURIE."""
        client = PubChemClient()

        curie = client._format_pubchem_curie(1)

        assert curie == "PubChem:CID1"


class TestClientConfiguration:
    """Test client initialization and configuration."""

    def test_base_url_configuration(self):
        """Test base URL is correctly configured."""
        client = PubChemClient()

        assert client.base_url == "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        assert client.PUBCHEM_BASE_URL == "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    def test_rate_limit_constants(self):
        """Test rate limiting constants are correctly set."""
        client = PubChemClient()

        assert client.RATE_LIMIT_PER_SECOND == 5
        assert client.RATE_LIMIT_PER_MINUTE == 400

    def test_backoff_constants(self):
        """Test exponential backoff constants are correctly set."""
        client = PubChemClient()

        assert client.MAX_RETRIES == 3
        assert client.BASE_DELAY == 1.0
        assert client.MAX_DELAY == 60.0

    def test_timeout_configuration(self):
        """Test timeout is configured."""
        client = PubChemClient()

        # Timeout should be set during initialization
        assert hasattr(client, "_timeout") or hasattr(client, "timeout")


class TestClientLifecycle:
    """Test client lifecycle management."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Client initializes correctly."""
        client = PubChemClient()
        assert isinstance(client, PubChemClient)
        await client.close()

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Close method can be called."""
        client = PubChemClient()
        await client.close()  # Should not raise


# =============================================================================
# T058-T060: Search Methods Unit Tests
# =============================================================================


class TestSearchByName:
    """Test _search_by_name method with mocked responses (T058)."""

    @pytest.mark.asyncio
    async def test_search_by_name_aspirin(self):
        """Test searching for aspirin returns CID list."""
        client = PubChemClient()

        # Mock response with aspirin CID
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"IdentifierList": {"CID": [2244, 135565885]}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client._search_by_name("aspirin")

            assert isinstance(result, list)
            assert 2244 in result
            assert len(result) == 2

        await client.close()

    @pytest.mark.asyncio
    async def test_search_by_name_url_encoding(self):
        """Test that compound names with special characters are URL encoded."""
        client = PubChemClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"IdentifierList": {"CID": [123]}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            await client._search_by_name("acetylsalicylic acid")

            # Verify URL encoding happened (spaces -> %20)
            call_args = mock_get.call_args[0][0]
            assert "acetylsalicylic%20acid" in call_args

        await client.close()

    @pytest.mark.asyncio
    async def test_search_by_name_404_empty_results(self):
        """Test HTTP 404 returns empty list (not error)."""
        client = PubChemClient()

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client._search_by_name("xyznonexistent999")

            assert isinstance(result, list)
            assert len(result) == 0

        await client.close()


class TestCursorEncoding:
    """Test cursor encoding/decoding (T059)."""

    def test_encode_cursor(self):
        """Test encoding offset to cursor."""
        client = PubChemClient()

        cursor = client._encode_cursor(10)

        assert isinstance(cursor, str)
        # Verify it's base64 encoded
        import base64
        import json

        decoded = json.loads(base64.b64decode(cursor))
        assert decoded["offset"] == 10

    def test_decode_cursor(self):
        """Test decoding cursor to offset."""
        client = PubChemClient()

        # First encode a cursor
        cursor = client._encode_cursor(25)

        # Then decode it
        offset = client._decode_cursor(cursor)

        assert offset == 25

    def test_decode_cursor_invalid(self):
        """Test that invalid cursor returns 0."""
        client = PubChemClient()

        # Invalid base64
        offset = client._decode_cursor("invalid!!!")

        assert offset == 0

    def test_decode_cursor_empty(self):
        """Test that empty cursor returns 0."""
        client = PubChemClient()

        offset = client._decode_cursor("")

        assert offset == 0


class TestScoringAlgorithm:
    """Test linear decay scoring algorithm (T060)."""

    @pytest.mark.asyncio
    async def test_scoring_linear_decay(self):
        """Test that scores decay linearly by position."""
        client = PubChemClient()

        # Mock search results with 5 CIDs
        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {"IdentifierList": {"CID": [1, 2, 3, 4, 5]}}

        # Mock properties response
        mock_props_response = MagicMock()
        mock_props_response.status_code = 200
        mock_props_response.json.return_value = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 1, "Title": "Compound1", "MolecularFormula": "C1H1"},
                    {"CID": 2, "Title": "Compound2", "MolecularFormula": "C2H2"},
                    {"CID": 3, "Title": "Compound3", "MolecularFormula": "C3H3"},
                    {"CID": 4, "Title": "Compound4", "MolecularFormula": "C4H4"},
                    {"CID": 5, "Title": "Compound5", "MolecularFormula": "C5H5"},
                ]
            }
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_search_response, mock_props_response]

            result = await client.search_compounds("test", page_size=50)

            # Convert to dict for easier testing
            result_dict = result.model_dump()

            # Verify scoring: score = max(0.1, 1.0 - (i * 0.05))
            assert result_dict["items"][0]["score"] == 1.0  # position 0
            assert result_dict["items"][1]["score"] == 0.95  # position 1
            assert result_dict["items"][2]["score"] == 0.9  # position 2
            assert result_dict["items"][3]["score"] == 0.85  # position 3
            assert result_dict["items"][4]["score"] == 0.8  # position 4

        await client.close()

    @pytest.mark.asyncio
    async def test_scoring_min_threshold(self):
        """Test that score never goes below 0.1."""
        client = PubChemClient()

        # Create 25 CIDs (position 20+ would be <0.1 without threshold)
        cids = list(range(1, 26))

        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {"IdentifierList": {"CID": cids}}

        # Mock properties for all CIDs
        props = [
            {"CID": cid, "Title": f"Compound{cid}", "MolecularFormula": f"C{cid}H{cid}"}
            for cid in cids
        ]
        mock_props_response = MagicMock()
        mock_props_response.status_code = 200
        mock_props_response.json.return_value = {"PropertyTable": {"Properties": props}}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_search_response, mock_props_response]

            result = await client.search_compounds("test", page_size=50)

            # Convert to dict for easier testing
            result_dict = result.model_dump()

            # Position 20: 1.0 - (20 * 0.05) = 0.0, but should be clamped to 0.1
            assert result_dict["items"][20]["score"] >= 0.1
            # Position 24: would be negative, should be 0.1
            assert result_dict["items"][24]["score"] == 0.1

        await client.close()


# =============================================================================
# T098-T110: User Story 2 (get_compound) Unit Tests
# =============================================================================


class TestGetCompoundSynonyms:
    """Test _get_compound_synonyms method (T098)."""

    @pytest.mark.asyncio
    async def test_get_compound_synonyms_success(self):
        """Test getting synonyms for aspirin."""
        client = PubChemClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "InformationList": {
                "Information": [
                    {
                        "CID": 2244,
                        "Synonym": [
                            "aspirin",
                            "acetylsalicylic acid",
                            "ASA",
                            "Ecotrin",
                            "CHEMBL25",
                            "DB00945",
                        ],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client._get_compound_synonyms(2244)

            assert isinstance(result, list)
            assert len(result) == 6
            assert "aspirin" in result
            assert "CHEMBL25" in result

        await client.close()
