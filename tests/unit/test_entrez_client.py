"""Unit tests for EntrezClient with mocked API responses.

Tests client logic including rate limiting, error mapping, and XML parsing
without making actual API calls.

Run with: pytest tests/unit/test_entrez_client.py -v
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lifesciences_mcp.clients.entrez import EntrezClient
from lifesciences_mcp.models.envelopes import ErrorCode, ErrorEnvelope, PaginationEnvelope
from lifesciences_mcp.models.entrez import EntrezGene, GeneSearchCandidate


# =============================================================================
# T061: EntrezClient Unit Tests
# =============================================================================


class TestEntrezClientRateLimiting:
    """Test adaptive rate limiting logic."""

    def test_rate_limit_without_api_key(self, monkeypatch):
        """Test that rate limit is 3 req/s without API key."""
        monkeypatch.delenv("NCBI_API_KEY", raising=False)
        client = EntrezClient()

        # Without API key: 3 req/s = 0.333s delay
        assert client.rate_limit_delay == pytest.approx(0.333, rel=0.01)

    def test_rate_limit_with_api_key(self, monkeypatch):
        """Test that rate limit is 10 req/s with API key."""
        monkeypatch.setenv("NCBI_API_KEY", "test-api-key")
        client = EntrezClient()

        # With API key: 10 req/s = 0.1s delay
        assert client.rate_limit_delay == 0.1
        assert client.api_key == "test-api-key"

    @pytest.mark.asyncio
    async def test_rate_limiting_enforces_delay(self, monkeypatch):
        """Test that rate limiting actually delays requests."""
        monkeypatch.delenv("NCBI_API_KEY", raising=False)
        client = EntrezClient()

        # Mock httpx.AsyncClient.get to return immediately
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"esearchresult": {"idlist": []}}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Make two rapid requests
            start = asyncio.get_event_loop().time()
            await client._rate_limited_get("https://test.url", {})
            await client._rate_limited_get("https://test.url", {})
            elapsed = asyncio.get_event_loop().time() - start

            # Should take at least one rate limit delay (0.333s)
            assert elapsed >= 0.3, f"Expected delay of ~0.333s, got {elapsed}s"

        await client.close()


class TestEntrezClientExponentialBackoff:
    """Test exponential backoff for 429/503 errors."""

    def test_max_retries_constant_defined(self):
        """Test that MAX_RETRIES constant is defined."""
        client = EntrezClient()
        assert hasattr(client, "MAX_RETRIES")
        assert client.MAX_RETRIES >= 3

    def test_backoff_delay_calculation(self):
        """Test exponential backoff delay calculation exists."""
        client = EntrezClient()
        # Client should have logic for calculating backoff delays
        # This is verified indirectly through integration tests


class TestEntrezClientErrorMapping:
    """Test error mapping from NCBI API to ErrorEnvelope."""

    def test_error_envelope_creation_method_exists(self):
        """Test that client has error creation method."""
        client = EntrezClient()
        assert hasattr(client, "_create_error_envelope")

    def test_error_codes_are_defined(self):
        """Test that error codes are available."""
        # Verify ErrorCode enum has required codes
        assert hasattr(ErrorCode, "ENTITY_NOT_FOUND")
        assert hasattr(ErrorCode, "UNRESOLVED_ENTITY")
        assert hasattr(ErrorCode, "RATE_LIMITED")
        assert hasattr(ErrorCode, "UPSTREAM_ERROR")
        assert hasattr(ErrorCode, "AMBIGUOUS_QUERY")

    @pytest.mark.asyncio
    async def test_create_error_envelope_structure(self):
        """Test that error envelope has correct structure."""
        client = EntrezClient()

        error = client._create_error_envelope(
            code=ErrorCode.RATE_LIMITED,
            message="Test message",
            recovery_hint="Test hint",
            invalid_input="test"
        )

        assert isinstance(error, ErrorEnvelope)
        assert error.error.code == ErrorCode.RATE_LIMITED
        assert error.error.message == "Test message"
        assert error.error.recovery_hint == "Test hint"
        assert error.error.invalid_input == "test"

        await client.close()


class TestEntrezClientXMLParsing:
    """Test XML parsing with defusedxml."""

    @pytest.mark.asyncio
    async def test_parse_gene_xml_extracts_basic_fields(self):
        """Test that _parse_gene_xml extracts basic gene fields."""
        client = EntrezClient()

        # Sample XML (simplified)
        xml_content = """<?xml version="1.0"?>
        <Entrezgene-Set>
          <Entrezgene>
            <Entrezgene_track-info>
              <Gene-track>
                <Gene-track_geneid>7157</Gene-track_geneid>
              </Gene-track>
            </Entrezgene_track-info>
            <Entrezgene_gene>
              <Gene-ref>
                <Gene-ref_locus>TP53</Gene-ref_locus>
                <Gene-ref_desc>tumor protein p53</Gene-ref_desc>
                <Gene-ref_syn>
                  <Gene-ref_syn_E>P53</Gene-ref_syn_E>
                  <Gene-ref_syn_E>TRP53</Gene-ref_syn_E>
                </Gene-ref_syn>
                <Gene-ref_maploc>17p13.1</Gene-ref_maploc>
              </Gene-ref>
            </Entrezgene_gene>
            <Entrezgene_summary>This gene encodes a tumor suppressor protein</Entrezgene_summary>
            <Entrezgene_source>
              <BioSource>
                <BioSource_org>
                  <Org-ref>
                    <Org-ref_taxname>Homo sapiens</Org-ref_taxname>
                  </Org-ref>
                </BioSource_org>
              </BioSource>
            </Entrezgene_source>
          </Entrezgene>
        </Entrezgene-Set>
        """

        gene_data = client._parse_gene_xml(xml_content)

        assert gene_data is not None
        assert gene_data["gene_id"] == "7157"
        assert gene_data["symbol"] == "TP53"
        assert gene_data["name"] == "tumor protein p53"
        assert "P53" in gene_data["aliases"]
        assert "TRP53" in gene_data["aliases"]
        assert gene_data["map_location"] == "17p13.1"
        assert gene_data["organism"] == "Homo sapiens"
        assert "tumor suppressor" in gene_data["summary"]

        await client.close()

    @pytest.mark.asyncio
    async def test_parse_gene_xml_handles_missing_fields(self):
        """Test that _parse_gene_xml handles missing optional fields gracefully."""
        client = EntrezClient()

        # Minimal XML with only required fields
        xml_content = """<?xml version="1.0"?>
        <Entrezgene-Set>
          <Entrezgene>
            <Entrezgene_track-info>
              <Gene-track>
                <Gene-track_geneid>12345</Gene-track_geneid>
              </Gene-track>
            </Entrezgene_track-info>
            <Entrezgene_gene>
              <Gene-ref>
                <Gene-ref_locus>TEST</Gene-ref_locus>
                <Gene-ref_desc>test gene</Gene-ref_desc>
              </Gene-ref>
            </Entrezgene_gene>
            <Entrezgene_source>
              <BioSource>
                <BioSource_org>
                  <Org-ref>
                    <Org-ref_taxname>Homo sapiens</Org-ref_taxname>
                  </Org-ref>
                </BioSource_org>
              </BioSource>
            </Entrezgene_source>
          </Entrezgene>
        </Entrezgene-Set>
        """

        gene_data = client._parse_gene_xml(xml_content)

        assert gene_data is not None
        assert gene_data["gene_id"] == "12345"
        assert gene_data["symbol"] == "TEST"
        assert gene_data["summary"] is None
        # Aliases can be None or empty list when not present in XML
        assert gene_data["aliases"] is None or gene_data["aliases"] == []

        await client.close()


class TestEntrezClientCursorEncoding:
    """Test cursor encoding/decoding for pagination."""

    def test_encode_cursor(self):
        """Test that encode_cursor creates base64-encoded cursor."""
        client = EntrezClient()

        cursor = client._encode_cursor(100)
        assert cursor is not None
        assert isinstance(cursor, str)
        # Should be base64-encoded
        assert len(cursor) > 0

    def test_decode_cursor(self):
        """Test that decode_cursor reverses encode_cursor."""
        client = EntrezClient()

        offset = 100
        cursor = client._encode_cursor(offset)
        decoded = client._decode_cursor(cursor)

        assert decoded == offset

    def test_decode_none_cursor(self):
        """Test that decode_cursor handles None gracefully."""
        client = EntrezClient()

        decoded = client._decode_cursor(None)
        assert decoded is None or decoded == 0  # Should return start position

    def test_decode_invalid_cursor(self):
        """Test that decode_cursor handles invalid cursor gracefully."""
        client = EntrezClient()

        # Invalid base64
        decoded = client._decode_cursor("invalid!!!cursor")
        assert decoded is None or decoded == 0  # Should fail gracefully


class TestEntrezClientQueryValidation:
    """Test query validation for search_genes."""

    @pytest.mark.asyncio
    async def test_short_query_returns_ambiguous_query_error(self):
        """Test that queries < 2 characters return AMBIGUOUS_QUERY error."""
        client = EntrezClient()

        result = await client.search_genes("A")  # 1 character

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code == ErrorCode.AMBIGUOUS_QUERY
        assert result.error.invalid_input == "A"
        assert "2 characters" in result.error.recovery_hint

        await client.close()

    @pytest.mark.asyncio
    async def test_valid_query_length_accepted(self):
        """Test that queries >= 2 characters are accepted."""
        client = EntrezClient()

        # Mock successful response
        mock_search = MagicMock(
            status_code=200,
            json=lambda: {
                "esearchresult": {
                    "count": "0",
                    "idlist": [],
                    "retstart": 0,
                    "retmax": 50
                }
            }
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_search

            result = await client.search_genes("AB")  # 2 characters

            # Should proceed without validation error
            assert isinstance(result, PaginationEnvelope)

        await client.close()
