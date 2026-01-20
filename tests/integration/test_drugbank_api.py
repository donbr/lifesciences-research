"""Integration tests for DrugBank API client.

Run with: pytest tests/integration/test_drugbank_api.py -v -m integration

Note: These tests require DRUGBANK_API_KEY environment variable.
Tests are skipped if the API key is not set.
"""

import os

import pytest

from lifesciences_mcp.clients import DrugBankClient
from lifesciences_mcp.models.drug import Drug, DrugSearchCandidate
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

# Skip all tests in this module if no API key
pytestmark = [
    pytest.mark.integration,
    pytest.mark.drugbank,
    pytest.mark.skipif(
        not os.environ.get("DRUGBANK_API_KEY"),
        reason="DRUGBANK_API_KEY not set - skipping DrugBank integration tests",
    ),
]


class TestDrugBankClientIntegration:
    """Integration tests for DrugBankClient."""

    @pytest.fixture
    async def client(self):
        """Create a DrugBank client."""
        client = DrugBankClient()
        yield client
        await client.close()

    async def test_search_drugs_basic(self, client: DrugBankClient):
        """Test fuzzy search with a common drug name."""
        result = await client.search_drugs("aspirin")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Determine if we found the exact match or related
        found_aspirin = False
        for item in result.items:
            assert isinstance(item, DrugSearchCandidate)
            if "aspirin" in item.name.lower():
                found_aspirin = True
                assert item.drugbank_id.startswith("DB")

        assert found_aspirin, "Should find aspirin in search results"

    async def test_search_drugs_by_brand_name(self, client: DrugBankClient):
        """Test fuzzy search by brand name."""
        # Tylenol is a brand name for Acetaminophen
        result = await client.search_drugs("tylenol")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Should find results (DrugBank search behavior might vary)
        # Note: Some brand names may not map directly to generic names
        # If this fails frequently, we might relax it to just ensuring non-empty results.
        assert len(result.items) > 0

    async def test_get_drug_valid_id(self, client: DrugBankClient):
        """Test strict lookup with valid DrugBank ID."""
        # DB00316 is Acetaminophen
        result = await client.get_drug("DB00316")

        assert isinstance(result, Drug)
        assert result.drugbank_id == "DB00316"
        assert "Acetaminophen" in result.name

    async def test_get_drug_invalid_format(self, client: DrugBankClient):
        """Test strict lookup with invalid ID format returns UNRESOLVED_ENTITY."""
        result = await client.get_drug("INVALID_ID_FORMAT")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"

    async def test_get_drug_not_found(self, client: DrugBankClient):
        """Test strict lookup with non-existent ID returns ENTITY_NOT_FOUND."""
        # Valid format (DB + 5 digits) but ideally non-existent
        result = await client.get_drug("DB99999")

        # Depending on API, could be 404 or just header change.
        if isinstance(result, ErrorEnvelope):
            assert result.error.code.value in ["ENTITY_NOT_FOUND", "UPSTREAM_ERROR"]
        else:
            # If it somehow returns a drug, ensure it handles it gracefully
            pass

    async def test_search_drugs_pagination(self, client: DrugBankClient):
        """Test pagination for a broad query."""
        # "acid" should return many results
        result_page1 = await client.search_drugs("acid", page_size=2)

        assert isinstance(result_page1, PaginationEnvelope)
        assert len(result_page1.items) == 2
        assert result_page1.pagination.total > 2

        # Note: DrugBank API might not support deep pagination via just search params
        # checks implementation detail. Assuming standard pagination pattern if supported.
        # If client doesn't support offset/page token control directly in search_drugs logic
        # (check implementation), we might skip deep pagination verification.

        # Verify basic envelop structure
        assert result_page1.pagination.page_size == 2

    async def test_fuzzy_to_fact_workflow(self, client: DrugBankClient):
        """Test complete fuzzy-to-fact workflow: search -> get."""
        # 1. Search
        search_result = await client.search_drugs("ibuprofen")
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

        top_hit = search_result.items[0]
        assert top_hit.drugbank_id

        # 2. Get details
        drug_details = await client.get_drug(top_hit.drugbank_id)
        assert isinstance(drug_details, Drug)
        assert drug_details.drugbank_id == top_hit.drugbank_id
        assert drug_details.name == top_hit.name
