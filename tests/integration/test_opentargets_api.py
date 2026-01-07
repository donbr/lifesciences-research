"""Integration tests for Open Targets API client.

Run with: pytest tests/integration/test_opentargets_api.py -v -m integration
"""

import pytest

from lifesciences_mcp.clients import OpenTargetsClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope
from lifesciences_mcp.models.target import Target


@pytest.mark.integration
class TestOpenTargetsClientIntegration:
    """Integration tests for OpenTargetsClient."""

    @pytest.fixture
    async def client(self):
        """Create an Open Targets client."""
        client = OpenTargetsClient()
        yield client
        await client.close()

    async def test_search_targets_brca1(self, client: OpenTargetsClient):
        """Test fuzzy target search for BRCA1.

        Example: Search for "BRCA1" should return breast cancer associated gene.
        """
        result = await client.search_targets("BRCA1", page_size=5)

        assert isinstance(result, PaginationEnvelope)
        assert result.pagination.total_count > 0
        assert len(result.items) > 0

        # BRCA1 should be in the top results
        ids = [item.id for item in result.items]
        assert any("ENSG00000012048" in id for id in ids), (
            "BRCA1 (ENSG00000012048) should be in results"
        )

    async def test_search_targets_tp53(self, client: OpenTargetsClient):
        """Test fuzzy target search for TP53."""
        result = await client.search_targets("TP53", page_size=5)

        assert isinstance(result, PaginationEnvelope)
        assert result.pagination.total_count > 0

        # Find TP53 in results
        tp53_found = False
        for item in result.items:
            if item.approved_symbol == "TP53" or item.id == "ENSG00000141510":
                tp53_found = True
                assert item.score is not None
                assert item.score > 0
                break

        assert tp53_found, "TP53 should be in search results"

    async def test_search_targets_short_query(self, client: OpenTargetsClient):
        """Test that short queries return error."""
        result = await client.search_targets("A")

        assert isinstance(result, ErrorEnvelope)
        assert "too short" in result.error.message.lower()

    async def test_get_target_tp53(self, client: OpenTargetsClient):
        """Test strict target lookup by Ensembl ID.

        Example: ENSG00000141510 should return TP53 gene.
        """
        result = await client.get_target("ENSG00000141510")

        assert isinstance(result, Target)
        assert result.id == "ENSG00000141510"
        assert result.approved_symbol == "TP53"
        assert result.approved_name is not None
        assert (
            "tumor protein" in result.approved_name.lower() or "p53" in result.approved_name.lower()
        )
        assert result.biotype == "protein_coding"

    async def test_get_target_invalid_id(self, client: OpenTargetsClient):
        """Test that invalid ID format returns error."""
        result = await client.get_target("INVALID_ID")

        assert isinstance(result, ErrorEnvelope)
        assert "invalid" in result.error.message.lower()

    async def test_get_target_not_found(self, client: OpenTargetsClient):
        """Test that non-existent valid ID returns not found."""
        result = await client.get_target("ENSG99999999999")

        assert isinstance(result, ErrorEnvelope)
        assert "not found" in result.error.message.lower()

    async def test_get_associations_tp53(self, client: OpenTargetsClient):
        """Test target-disease association retrieval.

        Example: TP53 should have associations with multiple cancer types.
        """
        result = await client.get_associations("ENSG00000141510", page_size=10)

        assert isinstance(result, PaginationEnvelope)
        assert result.pagination.total_count > 0
        assert len(result.items) > 0

        # Check first association structure
        assoc = result.items[0]
        assert assoc.target_id == "ENSG00000141510"
        assert assoc.disease_id is not None
        assert assoc.disease_name is not None
        assert 0 <= assoc.score <= 1.0

    async def test_get_associations_invalid_target(self, client: OpenTargetsClient):
        """Test that invalid target ID returns error."""
        result = await client.get_associations("INVALID")

        assert isinstance(result, ErrorEnvelope)


@pytest.mark.integration
class TestFuzzyToFactWorkflow:
    """Test the complete Fuzzy-to-Fact workflow."""

    @pytest.fixture
    async def client(self):
        """Create an Open Targets client."""
        client = OpenTargetsClient()
        yield client
        await client.close()

    async def test_complete_workflow_kinase(self, client: OpenTargetsClient):
        """Test complete workflow: search -> resolve -> associations.

        Validates the Fuzzy-to-Fact protocol end-to-end.
        """
        # Step 1: Fuzzy search for kinase
        search_result = await client.search_targets("EGFR", page_size=5)
        assert isinstance(search_result, PaginationEnvelope)
        assert search_result.pagination.total_count > 0

        # Get first candidate ID
        candidate = search_result.items[0]
        assert candidate.id.startswith("ENSG")

        # Step 2: Strict resolution
        target = await client.get_target(candidate.id)
        assert isinstance(target, Target)
        assert target.id == candidate.id

        # Step 3: Get associations
        associations = await client.get_associations(target.id, page_size=5)
        assert isinstance(associations, PaginationEnvelope)
        # EGFR should have disease associations
        assert associations.pagination.total_count > 0
