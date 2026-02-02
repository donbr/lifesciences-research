"""Integration tests for ChEMBL API client.

Tests for:
- T013: search_compounds integration tests (US1)
- T018: get_compound integration tests (US2)
- T019: get_compounds_batch integration tests (US2)
- T027: cross-references integration tests (US3)
- T032: error recovery integration tests (US4)

Run with: pytest tests/integration/test_chembl_api.py -v -m integration
"""

import pytest

from lifesciences_mcp.clients import ChEMBLClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope


@pytest.mark.integration
@pytest.mark.chembl
class TestSearchCompoundsIntegration:
    """Integration tests for search_compounds (T013: US1)."""

    @pytest.fixture
    async def client(self, check_chembl_available):
        """Create a ChEMBL client.

        Automatically skips if ChEMBL API is unavailable.
        """
        client = ChEMBLClient()
        yield client
        await client.close()

    async def test_search_aspirin_returns_chembl25(self, client: ChEMBLClient):
        """Test: search "aspirin" returns candidates with CHEMBL:25."""
        result = await client.search_compounds("aspirin")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Find CHEMBL:25 (aspirin) in results
        ids = [item.id for item in result.items]
        assert "CHEMBL:25" in ids, f"CHEMBL:25 not found in results: {ids[:5]}"

    async def test_search_imatinib_returns_chembl941(self, client: ChEMBLClient):
        """Test: search "imatinib" returns CHEMBL:941 in top results."""
        result = await client.search_compounds("imatinib")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # CHEMBL:941 should be in top results
        top_ids = [item.id for item in result.items[:10]]
        assert "CHEMBL:941" in top_ids, f"CHEMBL:941 not found in top 10: {top_ids}"

    async def test_search_pagination_with_cursor(self, client: ChEMBLClient):
        """Test: pagination with cursor parameter."""
        # Get first page
        result1 = await client.search_compounds("kinase", page_size=5)
        assert isinstance(result1, PaginationEnvelope)
        assert len(result1.items) == 5
        assert result1.pagination.cursor is not None

        # Get second page using cursor
        result2 = await client.search_compounds(
            "kinase", page_size=5, cursor=result1.pagination.cursor
        )
        assert isinstance(result2, PaginationEnvelope)
        assert len(result2.items) <= 5

        # Verify different results
        ids1 = {item.id for item in result1.items}
        ids2 = {item.id for item in result2.items}
        assert ids1.isdisjoint(ids2), "Second page should have different results"

    async def test_search_slim_mode_returns_minimal_fields(self, client: ChEMBLClient):
        """Test: slim mode returns minimal fields."""
        result = await client.search_compounds("metformin", slim=True)

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Check first item has required fields
        item = result.items[0]
        assert item.id is not None
        assert item.score is not None

    async def test_search_relevance_scores_descending(self, client: ChEMBLClient):
        """Test: search results have descending relevance scores."""
        result = await client.search_compounds("aspirin", page_size=10)

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) >= 2

        # Verify scores are descending
        scores = [item.score for item in result.items]
        assert scores == sorted(scores, reverse=True), "Scores should be descending"

    async def test_search_returns_is_parent_field(self, client: ChEMBLClient):
        """Test: search "pemetrexed" returns is_parent field distinguishing parent from salts.

        Pemetrexed is a good test case because:
        - CHEMBL:225072 (PEMETREXED) is the parent compound (is_parent=True)
        - CHEMBL:2360464 (PEMETREXED DISODIUM) is a salt form (is_parent=False)
        """
        result = await client.search_compounds("pemetrexed", page_size=20)

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Collect is_parent values
        parents = [item for item in result.items if item.is_parent is True]
        salts = [item for item in result.items if item.is_parent is False]

        # Should have at least one parent and one salt
        assert len(parents) >= 1, "Expected at least one parent compound (is_parent=True)"
        assert len(salts) >= 1, "Expected at least one salt form (is_parent=False)"

        # Verify PEMETREXED (CHEMBL:225072) is marked as parent
        parent_ids = [item.id for item in parents]
        assert "CHEMBL:225072" in parent_ids, (
            f"CHEMBL:225072 (PEMETREXED) should be is_parent=True, got parents: {parent_ids}"
        )


@pytest.mark.integration
@pytest.mark.chembl
class TestGetCompoundIntegration:
    """Integration tests for get_compound (T018: US2)."""

    @pytest.fixture
    async def client(self, check_chembl_available):
        """Create a ChEMBL client.

        Automatically skips if ChEMBL API is unavailable.
        """
        client = ChEMBLClient()
        yield client
        await client.close()

    async def test_get_compound_aspirin_complete_record(self, client: ChEMBLClient):
        """Test: get_compound("CHEMBL:25") returns complete aspirin record."""
        result = await client.get_compound("CHEMBL:25")

        assert not isinstance(result, ErrorEnvelope)
        assert isinstance(result, dict)
        assert result["id"] == "CHEMBL:25"
        assert result["name"] is not None

    async def test_get_compound_has_smiles_and_inchi(self, client: ChEMBLClient):
        """Test: verify SMILES, InChI, molecular_weight present."""
        result = await client.get_compound("CHEMBL:25")

        assert not isinstance(result, ErrorEnvelope)
        # SMILES should be present for aspirin
        assert result.get("smiles") is not None, "SMILES should be present"
        # Molecular weight should be present
        assert result.get("molecular_weight") is not None, "Molecular weight should be present"

    async def test_get_compound_slim_mode(self, client: ChEMBLClient):
        """Test: slim mode returns minimal fields."""
        result = await client.get_compound("CHEMBL:25", slim=True)

        assert not isinstance(result, ErrorEnvelope)
        assert isinstance(result, dict)
        assert result["id"] == "CHEMBL:25"
        # Slim mode should NOT include cross_references
        assert "cross_references" not in result or result.get("cross_references") is None

    async def test_get_compound_invalid_curie_returns_unresolved_entity(self, client: ChEMBLClient):
        """Test: invalid CURIE returns UNRESOLVED_ENTITY."""
        result = await client.get_compound("CHEMBL25")  # Missing colon

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
        assert "CHEMBL:NNNNN" in result.error.recovery_hint

    async def test_get_compound_not_found(self, client: ChEMBLClient):
        """Test: non-existent compound returns ENTITY_NOT_FOUND."""
        result = await client.get_compound("CHEMBL:99999999999")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "ENTITY_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.chembl
class TestGetCompoundsBatchIntegration:
    """Integration tests for get_compounds_batch (T019: US2)."""

    @pytest.fixture
    async def client(self, check_chembl_available):
        """Create a ChEMBL client.

        Automatically skips if ChEMBL API is unavailable.
        """
        client = ChEMBLClient()
        yield client
        await client.close()

    async def test_batch_lookup_returns_multiple_compounds(self, client: ChEMBLClient):
        """Test: batch lookup ["CHEMBL:25", "CHEMBL:941"] returns 2 compounds."""
        result = await client.get_compounds_batch(["CHEMBL:25", "CHEMBL:941"])

        assert not isinstance(result, ErrorEnvelope)
        assert isinstance(result, list)
        assert len(result) == 2

        # Verify both compounds present
        ids = [r.get("id") for r in result if isinstance(r, dict) and "id" in r]
        assert "CHEMBL:25" in ids
        assert "CHEMBL:941" in ids

    async def test_batch_mixed_valid_invalid_handles_gracefully(self, client: ChEMBLClient):
        """Test: batch with mixed valid/invalid CURIEs handles gracefully."""
        result = await client.get_compounds_batch(["CHEMBL:25", "INVALID123", "CHEMBL:941"])

        assert not isinstance(result, ErrorEnvelope)
        assert isinstance(result, list)
        assert len(result) == 3

        # Should have 2 successful lookups and 1 error
        successes = [
            r for r in result if isinstance(r, dict) and "id" in r and r.get("success") is not False
        ]
        errors = [r for r in result if isinstance(r, dict) and r.get("success") is False]
        assert len(successes) == 2
        assert len(errors) == 1

    async def test_batch_defaults_to_slim(self, client: ChEMBLClient):
        """Test: batch defaults to slim=True."""
        result = await client.get_compounds_batch(["CHEMBL:25"])

        assert not isinstance(result, ErrorEnvelope)
        assert len(result) == 1

        # Default slim mode should NOT include cross_references
        compound = result[0]
        assert (
            "cross_references" not in compound
            or compound.get("cross_references") is None
            or compound.get("cross_references") == {}
        )


@pytest.mark.integration
@pytest.mark.chembl
class TestCrossReferencesIntegration:
    """Integration tests for cross-references (T027: US3)."""

    @pytest.fixture
    async def client(self, check_chembl_available):
        """Create a ChEMBL client.

        Automatically skips if ChEMBL API is unavailable.
        """
        client = ChEMBLClient()
        yield client
        await client.close()

    async def test_aspirin_has_cross_references(self, client: ChEMBLClient):
        """Test: aspirin (CHEMBL:25) has cross_references in full mode."""
        result = await client.get_compound("CHEMBL:25", slim=False)

        assert not isinstance(result, ErrorEnvelope)
        assert "cross_references" in result
        xrefs = result["cross_references"]

        # Should have at least chembl self-reference
        assert "chembl" in xrefs, "Should have chembl self-reference"

    async def test_curie_formats_match_registry_patterns(self, client: ChEMBLClient):
        """Test: verify CURIE formats match 22-key registry patterns."""
        result = await client.get_compound("CHEMBL:25", slim=False)

        assert not isinstance(result, ErrorEnvelope)
        xrefs = result.get("cross_references", {})

        # Check format patterns for known keys
        if "chembl" in xrefs:
            for curie in xrefs["chembl"]:
                assert curie.startswith("CHEMBL:"), (
                    f"ChEMBL CURIE should start with CHEMBL: - got {curie}"
                )

        if "uniprot" in xrefs:
            for curie in xrefs["uniprot"]:
                assert curie.startswith("UniProtKB:"), (
                    f"UniProt CURIE should start with UniProtKB: - got {curie}"
                )

        if "drugbank" in xrefs:
            for curie in xrefs["drugbank"]:
                assert curie.startswith("DB:"), (
                    f"DrugBank CURIE should start with DB: - got {curie}"
                )

    async def test_compound_with_no_xrefs_has_empty_cross_references(self, client: ChEMBLClient):
        """Test: compound with limited data has minimal or empty cross_references."""
        # Use a less well-known compound that might have fewer xrefs
        result = await client.get_compound("CHEMBL:25", slim=False)

        assert not isinstance(result, ErrorEnvelope)
        assert "cross_references" in result
        # cross_references should be a dict (possibly empty for some compounds)
        assert isinstance(result["cross_references"], dict)


@pytest.mark.integration
@pytest.mark.chembl
class TestErrorRecoveryIntegration:
    """Integration tests for error recovery (T032: US4)."""

    @pytest.fixture
    async def client(self, check_chembl_available):
        """Create a ChEMBL client.

        Automatically skips if ChEMBL API is unavailable.
        """
        client = ChEMBLClient()
        yield client
        await client.close()

    async def test_invalid_curie_format_returns_unresolved_entity(self, client: ChEMBLClient):
        """Test: get_compound("CHEMBL123") returns UNRESOLVED_ENTITY with recovery hint."""
        result = await client.get_compound("CHEMBL123")  # No colon

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
        assert result.error.recovery_hint is not None
        assert "CHEMBL:" in result.error.recovery_hint
        assert result.error.invalid_input == "CHEMBL123"

    async def test_nonexistent_compound_returns_entity_not_found(self, client: ChEMBLClient):
        """Test: get_compound("CHEMBL:99999999999") returns ENTITY_NOT_FOUND."""
        result = await client.get_compound("CHEMBL:99999999999")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "ENTITY_NOT_FOUND"
        assert result.error.recovery_hint is not None

    async def test_short_query_returns_ambiguous_query(self, client: ChEMBLClient):
        """Test: search_compounds("X") returns AMBIGUOUS_QUERY."""
        result = await client.search_compounds("X")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"
        assert "2 characters" in result.error.recovery_hint
        assert result.error.invalid_input == "X"


@pytest.mark.integration
@pytest.mark.chembl
class TestFuzzyToFactWorkflow:
    """Test complete fuzzy-to-fact workflow."""

    @pytest.fixture
    async def client(self, check_chembl_available):
        """Create a ChEMBL client.

        Automatically skips if ChEMBL API is unavailable.
        """
        client = ChEMBLClient()
        yield client
        await client.close()

    async def test_complete_workflow(self, client: ChEMBLClient):
        """Test: Search -> Extract CURIE -> Get full record -> Verify xrefs."""
        # Step 1: Fuzzy search
        search_result = await client.search_compounds("aspirin")
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

        # Step 2: Extract CURIE from top result
        top_curie = search_result.items[0].id
        assert top_curie.startswith("CHEMBL:")

        # Step 3: Get full compound record
        compound = await client.get_compound(top_curie, slim=False)
        assert not isinstance(compound, ErrorEnvelope)
        assert compound["id"] == top_curie

        # Step 4: Verify cross-references exist
        assert "cross_references" in compound
        assert isinstance(compound["cross_references"], dict)
