"""Unit tests for DrugBank client with mocked HTTP responses."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from lifesciences_mcp.clients.drugbank import DrugBankClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope


class TestDrugBankClientValidation:
    """Test input validation without API calls."""

    @pytest.fixture
    def client(self):
        """Create DrugBank client."""
        return DrugBankClient()

    async def test_search_drugs_query_too_short(self, client):
        """Test that short queries return AMBIGUOUS_QUERY error."""
        result = await client.search_drugs("A")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code == "AMBIGUOUS_QUERY"
        assert "too short" in result.error.message.lower()

    async def test_get_drug_invalid_curie_format(self, client):
        """Test that invalid CURIE returns UNRESOLVED_ENTITY error."""
        result = await client.get_drug("DB00945")  # Missing prefix

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code == "UNRESOLVED_ENTITY"
        assert "Invalid DrugBank CURIE format" in result.error.message

    async def test_get_drug_invalid_curie_short(self, client):
        """Test that short ID returns UNRESOLVED_ENTITY error."""
        result = await client.get_drug("DrugBank:DB0094")  # Too short

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code == "UNRESOLVED_ENTITY"


class TestDrugBankClientMocked:
    """Test client methods with mocked HTTP responses."""

    @pytest.fixture
    def client(self):
        """Create DrugBank client."""
        return DrugBankClient()

    @pytest.fixture
    def mock_response_success(self):
        """Create a successful mock response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.headers = {"content-type": "application/json"}
        return response

    @pytest.fixture
    def mock_response_404(self):
        """Create a 404 mock response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 404
        response.headers = {}
        return response

    @pytest.fixture
    def mock_response_429(self):
        """Create a 429 rate limit mock response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 429
        response.headers = {"Retry-After": "60"}
        return response

    @pytest.fixture
    def mock_response_401(self):
        """Create a 401 unauthorized mock response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        response.headers = {}
        return response

    async def test_search_drugs_success(self, client, mock_response_success):
        """Test successful drug search."""
        mock_response_success.json.return_value = [
            {
                "drugbank_id": "DB00945",
                "name": "Aspirin",
                "type": "Small molecule",
                "groups": ["approved"],
            },
            {
                "drugbank_id": "DB00055",
                "name": "Aspirin Complex",
                "type": "Small molecule",
                "groups": ["approved"],
            },
        ]

        with patch.object(client, "_rate_limited_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_success
            result = await client.search_drugs("aspirin", page_size=10)

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) == 2
        # Check CURIE normalization
        assert result.items[0]["id"] == "DrugBank:DB00945"
        assert result.items[0]["name"] == "Aspirin"

    async def test_search_drugs_empty_results(self, client, mock_response_success):
        """Test search with no results."""
        mock_response_success.json.return_value = []

        with patch.object(client, "_rate_limited_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_success
            result = await client.search_drugs("xyznonexistent", page_size=10)

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) == 0

    async def test_get_drug_success(self, client, mock_response_success):
        """Test successful drug lookup."""
        mock_response_success.json.return_value = {
            "drugbank_id": "DB00945",
            "name": "Aspirin",
            "type": "Small molecule",
            "groups": ["approved"],
            "description": "The prototypical analgesic.",
            "indication": "For mild to moderate pain.",
            "mechanism_of_action": "Inhibits COX enzymes.",
            "half_life": "15-20 minutes",
            "external_identifiers": [
                {"resource": "ChEMBL", "identifier": "CHEMBL25"},
                {"resource": "KEGG Drug", "identifier": "D00109"},
                {"resource": "PubChem Compound", "identifier": "2244"},
            ],
            "targets": [
                {
                    "polypeptides": [
                        {"source": "Swiss-Prot", "id": "P23219"},
                        {"source": "Swiss-Prot", "id": "P35354"},
                    ]
                }
            ],
        }

        with patch.object(client, "_rate_limited_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_success
            result = await client.get_drug("DrugBank:DB00945")

        assert isinstance(result, dict)
        assert result["id"] == "DrugBank:DB00945"
        assert result["name"] == "Aspirin"
        assert "cross_references" in result
        assert result["cross_references"]["chembl"] == "CHEMBL:25"
        assert result["cross_references"]["kegg"] == "D00109"
        assert len(result["cross_references"]["uniprot"]) == 2

    async def test_get_drug_not_found(self, client, mock_response_404):
        """Test drug lookup with 404 response."""
        with patch.object(client, "_rate_limited_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_404
            result = await client.get_drug("DrugBank:DB99999")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code == "ENTITY_NOT_FOUND"
        assert "not found" in result.error.message.lower()

    async def test_get_drug_rate_limited(self, client, mock_response_429):
        """Test rate limit handling."""
        with patch.object(client, "_rate_limited_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_429
            result = await client.get_drug("DrugBank:DB00945")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code == "RATE_LIMITED"
        assert "60" in result.error.recovery_hint

    async def test_get_drug_unauthorized(self, client, mock_response_401):
        """Test unauthorized response handling."""
        with patch.object(client, "_rate_limited_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_401
            result = await client.get_drug("DrugBank:DB00945")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code == "UPSTREAM_ERROR"
        assert "commercial" in result.error.recovery_hint.lower()

    async def test_get_drug_slim_mode(self, client, mock_response_success):
        """Test slim mode returns minimal fields."""
        mock_response_success.json.return_value = {
            "drugbank_id": "DB00945",
            "name": "Aspirin",
            "type": "Small molecule",
            "groups": ["approved"],
            "description": "The prototypical analgesic.",
            "indication": "For mild to moderate pain.",
        }

        with patch.object(client, "_rate_limited_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_success
            result = await client.get_drug("DrugBank:DB00945", slim=True)

        assert isinstance(result, dict)
        assert "id" in result
        assert "name" in result
        # Slim mode excludes verbose fields
        assert "description" not in result
        assert "indication" not in result


class TestDrugBankClientCursor:
    """Test pagination cursor encoding/decoding."""

    @pytest.fixture
    def client(self):
        """Create DrugBank client."""
        return DrugBankClient()

    def test_encode_cursor(self, client):
        """Test cursor encoding."""
        cursor = client._encode_cursor(page=2, per_page=50)
        assert isinstance(cursor, str)
        assert len(cursor) > 0

    def test_decode_cursor(self, client):
        """Test cursor decoding."""
        cursor = client._encode_cursor(page=3, per_page=25)
        page, per_page = client._decode_cursor(cursor)
        assert page == 3
        assert per_page == 25

    def test_decode_cursor_none(self, client):
        """Test decoding None cursor returns defaults."""
        page, per_page = client._decode_cursor(None)
        assert page == 1
        assert per_page == 50

    def test_decode_cursor_invalid(self, client):
        """Test decoding invalid cursor returns defaults."""
        page, per_page = client._decode_cursor("invalid-base64!")
        assert page == 1
        assert per_page == 50


class TestDrugBankClientApiKey:
    """Test API key handling."""

    def test_no_api_key_uses_public_url(self):
        """Test client without API key uses public URL."""
        with patch.dict("os.environ", {}, clear=True):
            client = DrugBankClient()
            assert client._api_key is None
            assert client._select_base_url() == "https://go.drugbank.com"

    def test_api_key_uses_commercial_url(self):
        """Test client with API key uses commercial URL."""
        with patch.dict("os.environ", {"DRUGBANK_API_KEY": "test-key-123"}):
            client = DrugBankClient()
            assert client._api_key == "test-key-123"
            assert client._select_base_url() == "https://api.drugbank.com/v1"

    def test_headers_include_auth_when_key_set(self):
        """Test headers include Authorization when API key is set."""
        with patch.dict("os.environ", {"DRUGBANK_API_KEY": "test-key-123"}):
            client = DrugBankClient()
            headers = client._get_headers()
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer test-key-123"

    def test_headers_no_auth_when_no_key(self):
        """Test headers exclude Authorization when no API key."""
        with patch.dict("os.environ", {}, clear=True):
            client = DrugBankClient()
            headers = client._get_headers()
            assert "Authorization" not in headers
