"""Integration tests for BioGRID API client.

These tests require:
1. Network access to BioGRID API
2. BIOGRID_API_KEY environment variable set

Get free API key at: https://webservice.thebiogrid.org/

Run with: pytest tests/integration/test_biogrid_api.py -m integration -v

Note: BioGRID API has a 2 request/second rate limit (conservative estimate).
"""

import os

import pytest

from lifesciences_mcp.clients import BioGridClient
from lifesciences_mcp.models.biogrid import (
    BioGridSearchCandidate,
    InteractionResult,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

# Skip all tests if no API key
pytestmark = [
    pytest.mark.biogrid,
    pytest.mark.skipif(
        not os.getenv("BIOGRID_API_KEY"),
        reason="BIOGRID_API_KEY not set. Get free key at https://webservice.thebiogrid.org/",
    ),
]


@pytest.mark.integration
@pytest.mark.biogrid
class TestBioGridClientIntegration:
    """Integration tests for BioGridClient with real BioGRID API."""

    @pytest.fixture
    async def client(self):
        """Create a BioGRID client."""
        client = BioGridClient()
        yield client
        await client.close()

    # ========================================================================
    # User Story 1: Gene Symbol Search (T010-T011)
    # ========================================================================

    async def test_search_genes_tp53(self, client: BioGridClient):
        """Test API-backed gene search for TP53 (T010)."""
        result = await client.search_genes("TP53")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) == 1

        candidate = result.items[0]
        assert isinstance(candidate, BioGridSearchCandidate)
        assert candidate.symbol == "TP53"
        assert candidate.organism == "Homo sapiens"
        assert candidate.taxon_id == 9606
        assert candidate.interaction_count > 0

    async def test_search_genes_validation(self, client: BioGridClient):
        """Test gene symbol format validation and API confirmation (T011)."""
        # Test valid symbols confirmed by BioGRID API
        valid_symbols = ["TP53", "brca1", "MDM2", "ATM"]
        for symbol in valid_symbols:
            result = await client.search_genes(symbol)
            assert isinstance(result, PaginationEnvelope)
            assert result.items[0].interaction_count > 0
            assert result.items[0].symbol == symbol.upper()

        # Test invalid: too short (fail-fast, no API call)
        result = await client.search_genes("a")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"

        # Test invalid: special characters (fail-fast, no API call)
        result = await client.search_genes("TP53!")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"

    async def test_search_genes_nonexistent(self, client: BioGridClient):
        """Test ENTITY_NOT_FOUND for gene not in BioGRID."""
        result = await client.search_genes("ZZZZZ99")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "ENTITY_NOT_FOUND"
        assert "not found" in result.error.message.lower()
        assert result.error.invalid_input == "ZZZZZ99"

    async def test_get_interactions_slim(self, client: BioGridClient):
        """Test slim=True returns minimal fields (T074, Constitution Principle IV)."""
        result = await client.get_interactions("TP53", organism=9606, max_results=10, slim=True)

        assert isinstance(result, dict)
        assert result["query_gene"] == "TP53"
        assert result["total_count"] == len(result["interactions"])
        assert result["physical_count"] >= 0
        assert result["genetic_count"] >= 0
        assert result["total_count"] <= 10

        # Slim interactions should only have symbol_b and experimental_system_type
        interaction = result["interactions"][0]
        assert "symbol_b" in interaction
        assert "experimental_system_type" in interaction
        assert interaction["experimental_system_type"] in ["physical", "genetic"]

        # Full fields should NOT be present in slim mode
        assert "biogrid_interaction_id" not in interaction
        assert "symbol_a" not in interaction
        assert "experimental_system" not in interaction
        assert "pubmed_id" not in interaction

        # cross_references should NOT be present at top level in slim mode
        assert "cross_references" not in result

    # ========================================================================
    # User Story 2: Genetic/Protein Interactions (T022-T026)
    # ========================================================================

    async def test_get_interactions_tp53(self, client: BioGridClient):
        """Test retrieving interactions for TP53 (T022)."""
        result = await client.get_interactions("TP53", organism=9606)

        assert isinstance(result, InteractionResult)
        assert result.query_gene == "TP53"
        assert len(result.interactions) > 0
        assert result.total_count == len(result.interactions)

        # TP53 should interact with MDM2 and ATM
        partner_symbols = {i.symbol_b for i in result.interactions}
        assert "MDM2" in partner_symbols or "ATM" in partner_symbols

    async def test_get_interactions_evidence(self, client: BioGridClient):
        """Test experimental evidence types in interactions (T023)."""
        result = await client.get_interactions("TP53", organism=9606)

        assert isinstance(result, InteractionResult)
        assert len(result.interactions) > 0

        # Check first interaction has all required fields
        interaction = result.interactions[0]
        assert interaction.biogrid_interaction_id > 0
        assert interaction.symbol_a == "TP53"
        assert len(interaction.symbol_b) > 0
        assert len(interaction.experimental_system) > 0
        assert interaction.experimental_system_type in ["physical", "genetic"]
        assert interaction.organism_a_id == 9606
        assert interaction.organism_b_id > 0

        # Optional fields may be None
        assert interaction.pubmed_id is None or interaction.pubmed_id > 0
        assert interaction.throughput in [None, "High Throughput", "Low Throughput"]

    async def test_get_interactions_counts(self, client: BioGridClient):
        """Test physical/genetic interaction counts (T024)."""
        result = await client.get_interactions("TP53", organism=9606)

        assert isinstance(result, InteractionResult)
        assert result.physical_count >= 0
        assert result.genetic_count >= 0
        assert result.total_count == result.physical_count + result.genetic_count
        assert result.total_count == len(result.interactions)

        # TP53 is well-studied, should have both physical and genetic interactions
        assert result.physical_count > 0

    async def test_get_interactions_limit(self, client: BioGridClient):
        """Test max_results parameter (T025)."""
        # Request only 10 interactions
        result = await client.get_interactions("TP53", organism=9606, max_results=10)

        assert isinstance(result, InteractionResult)
        assert len(result.interactions) <= 10
        assert result.total_count <= 10

    async def test_get_interactions_validation(self, client: BioGridClient):
        """Test gene symbol validation in get_interactions (T026)."""
        # Invalid symbol format
        result = await client.get_interactions("INVALID!")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"

        # Valid format but no interactions
        result = await client.get_interactions("ZZZZZ99")
        # Should either return empty InteractionResult or error
        assert isinstance(result, (InteractionResult, ErrorEnvelope))
        if isinstance(result, InteractionResult):
            assert len(result.interactions) == 0
        else:
            # Accept either ENTITY_NOT_FOUND or UPSTREAM_ERROR (API may reject invalid genes)
            assert result.error.code.value in ["ENTITY_NOT_FOUND", "UPSTREAM_ERROR"]

    # ========================================================================
    # User Story 3: Cross-Database Integration (T043)
    # ========================================================================

    async def test_cross_references_entrez(self, client: BioGridClient):
        """Test Entrez Gene ID cross-references (T043)."""
        result = await client.get_interactions("TP53", organism=9606)

        assert isinstance(result, InteractionResult)
        assert result.cross_references is not None

        # TP53 should have Entrez Gene ID 7157
        if result.cross_references.entrez:
            assert result.cross_references.entrez == "7157"

        # Verify omit-if-null pattern (Constitution Principle III)
        cross_refs_dict = result.cross_references.model_dump(exclude_none=True)
        # If entrez is present, it should be a string
        if "entrez" in cross_refs_dict:
            assert isinstance(cross_refs_dict["entrez"], str)
            assert cross_refs_dict["entrez"].isdigit()

    # ========================================================================
    # User Story 4: Error Recovery (T048-T050)
    # ========================================================================

    async def test_error_recovery_invalid_api_key(self):
        """Test error handling for invalid API key (T048)."""
        # Create client with invalid API key
        client = BioGridClient(api_key="invalid_key_12345")
        try:
            result = await client.get_interactions("TP53")
            assert isinstance(result, ErrorEnvelope)
            assert result.error.code.value == "UPSTREAM_ERROR"
            assert "authentication" in result.error.message.lower() or "401" in result.error.message
            assert "BIOGRID_API_KEY" in result.error.recovery_hint
        finally:
            await client.close()

    async def test_error_recovery_ambiguous_query(self, client: BioGridClient):
        """Test error recovery hints for ambiguous queries (T049)."""
        # Query too short
        result = await client.search_genes("A")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"
        assert "2 characters" in result.error.message
        assert "2 characters" in result.error.recovery_hint
        assert result.error.invalid_input == "A"

        # Invalid format
        result = await client.search_genes("TP53@#$")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"
        assert "format" in result.error.message.lower()
        assert result.error.invalid_input == "TP53@#$"

    async def test_error_recovery_entity_not_found(self, client: BioGridClient):
        """Test error handling for genes with no interactions (T050)."""
        # Use an obscure gene that may not have interactions
        result = await client.get_interactions("ZZZZZ99")

        # Should either return empty result or ENTITY_NOT_FOUND
        if isinstance(result, ErrorEnvelope):
            assert result.error.code.value in ["ENTITY_NOT_FOUND", "UPSTREAM_ERROR"]
            assert (
                "verify" in result.error.recovery_hint.lower()
                or "check" in result.error.recovery_hint.lower()
            )
            assert result.error.invalid_input == "ZZZZZ99"
        else:
            # If API returns empty result, that's also valid
            assert isinstance(result, InteractionResult)
            assert len(result.interactions) == 0
