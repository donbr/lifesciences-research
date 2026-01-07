"""Integration tests for PubChem MCP Server.

These tests query the live PubChem REST API.

Run with: pytest tests/integration/test_pubchem_api.py -v -m integration
"""

import pytest

from lifesciences_mcp.clients.pubchem import PubChemClient
from lifesciences_mcp.models.envelopes import ErrorCode, ErrorEnvelope

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestSearchCompoundsIntegration:
    """Integration tests for search_compounds against live API (T061-T066)."""

    @pytest.mark.asyncio
    async def test_search_aspirin(self) -> None:
        """Test searching for aspirin returns results (T061)."""
        client = PubChemClient()

        result = await client.search_compounds("aspirin", page_size=10)

        # Should return PaginationEnvelope, not ErrorEnvelope
        assert not isinstance(result, ErrorEnvelope)

        # Should have results
        assert len(result.items) > 0

        # First result should be aspirin CID2244
        first = result.items[0]
        assert first.id == "PubChem:CID2244"
        assert first.name == "Aspirin"
        assert first.molecular_formula == "C9H8O4"
        assert first.score == 1.0

        # Verify pagination metadata
        assert result.pagination.page_size == 10
        assert result.pagination.total_count > 0

        await client.close()

    @pytest.mark.asyncio
    async def test_search_acetylsalicylic_acid(self) -> None:
        """Test searching for aspirin by synonym (T062)."""
        client = PubChemClient()

        result = await client.search_compounds("acetylsalicylic acid", page_size=10)

        assert not isinstance(result, ErrorEnvelope)
        assert len(result.items) > 0

        # Should find aspirin
        first = result.items[0]
        assert first.id == "PubChem:CID2244"

        await client.close()

    @pytest.mark.asyncio
    async def test_search_ibuprofen(self) -> None:
        """Test searching for ibuprofen returns related compounds (T063)."""
        client = PubChemClient()

        result = await client.search_compounds("ibuprofen", page_size=10)

        assert not isinstance(result, ErrorEnvelope)
        assert len(result.items) > 0

        # Should find ibuprofen (CID3672)
        first = result.items[0]
        assert first.id == "PubChem:CID3672"
        assert "ibuprofen" in first.name.lower()

        # Verify scores are descending
        scores = [item.score for item in result.items]
        assert scores == sorted(scores, reverse=True)

        await client.close()

    @pytest.mark.asyncio
    async def test_search_nonexistent_compound(self) -> None:
        """Test searching for nonexistent compound returns empty results (T064)."""
        client = PubChemClient()

        result = await client.search_compounds("xyznonexistent999", page_size=10)

        # Should return empty results, not error
        assert not isinstance(result, ErrorEnvelope)
        assert result.items == []
        assert result.pagination.total_count == 0
        assert result.pagination.cursor is None

        await client.close()

    @pytest.mark.asyncio
    async def test_search_pagination(self) -> None:
        """Test pagination with cursor (T065)."""
        client = PubChemClient()

        # Get first page
        page1 = await client.search_compounds("aspirin", page_size=5)

        assert not isinstance(page1, ErrorEnvelope)
        # Note: We might get fewer than 5 if there are only 1-2 results for aspirin
        assert len(page1.items) > 0

        # If we have results and a cursor, test pagination
        if page1.pagination.cursor:
            # Get second page using cursor
            cursor = page1.pagination.cursor
            page2 = await client.search_compounds("aspirin", page_size=5, cursor=cursor)

            assert not isinstance(page2, ErrorEnvelope)
            assert len(page2.items) > 0

            # Pages should have different items
            page1_ids = [item.id for item in page1.items]
            page2_ids = [item.id for item in page2.items]
            assert page1_ids != page2_ids

        await client.close()

    @pytest.mark.asyncio
    async def test_search_query_too_short(self) -> None:
        """Test query too short returns AMBIGUOUS_QUERY error (T066)."""
        client = PubChemClient()

        result = await client.search_compounds("a", page_size=10)

        # Should return ErrorEnvelope
        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == ErrorCode.AMBIGUOUS_QUERY
        assert "too short" in result.error.message.lower()
        assert "2 characters" in result.error.recovery_hint
        assert result.error.invalid_input == "a"

        await client.close()

    @pytest.mark.asyncio
    async def test_search_url_encoding(self) -> None:
        """Test that compound names with special characters work."""
        client = PubChemClient()

        # Test with compound name containing spaces
        result = await client.search_compounds("vitamin c", page_size=10)

        assert not isinstance(result, ErrorEnvelope)
        assert len(result.items) > 0

        await client.close()

    @pytest.mark.asyncio
    async def test_search_caffeine(self) -> None:
        """Test searching for caffeine."""
        client = PubChemClient()

        result = await client.search_compounds("caffeine", page_size=10)

        assert not isinstance(result, ErrorEnvelope)
        assert len(result.items) > 0

        # Should find caffeine (CID2519)
        first = result.items[0]
        assert first.id == "PubChem:CID2519"
        assert "caffeine" in first.name.lower()

        await client.close()

    @pytest.mark.asyncio
    async def test_search_score_range(self) -> None:
        """Test that all scores are in valid range [0.1, 1.0]."""
        client = PubChemClient()

        result = await client.search_compounds("aspirin", page_size=50)

        assert not isinstance(result, ErrorEnvelope)

        # All scores should be in [0.1, 1.0]
        for item in result.items:
            assert 0.1 <= item.score <= 1.0

        await client.close()


class TestGetCompoundIntegration:
    """Integration tests for get_compound against live API (T123-T132)."""

    @pytest.mark.asyncio
    async def test_get_compound_aspirin_full(self) -> None:
        """Test getting full aspirin compound data (T123)."""
        client = PubChemClient()

        result = await client.get_compound("PubChem:CID2244", slim=False)

        # Should return PubChemCompound, not ErrorEnvelope
        assert not isinstance(result, ErrorEnvelope)

        # Verify all fields
        assert result.id == "PubChem:CID2244"
        assert result.name == "Aspirin"
        assert result.iupac_name is not None
        assert result.molecular_formula == "C9H8O4"
        assert result.molecular_weight is not None
        # SMILES should be present (canonical or isomeric)
        assert result.canonical_smiles is not None or result.isomeric_smiles is not None
        assert result.inchi is not None
        assert result.inchikey is not None
        assert len(result.synonyms) > 0

        # Verify cross-references (at minimum should have self-reference)
        assert "pubchem_compound" in result.cross_references
        assert result.cross_references["pubchem_compound"] == ["2244"]

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_aspirin_slim(self) -> None:
        """Test getting slim aspirin compound data (T124)."""
        client = PubChemClient()

        result = await client.get_compound("PubChem:CID2244", slim=True)

        assert not isinstance(result, ErrorEnvelope)

        # Slim mode should only have 3 fields
        result_dict = result.model_dump()
        assert result_dict["id"] == "PubChem:CID2244"
        assert result_dict["name"] == "Aspirin"
        assert result_dict["molecular_formula"] == "C9H8O4"

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_cross_references_chembl(self) -> None:
        """Test ChEMBL cross-reference extraction (T125).

        Note: ChEMBL IDs might not always be in the first 20 synonyms,
        so we test the extraction logic works when they ARE present.
        """
        client = PubChemClient()

        result = await client.get_compound("PubChem:CID2244")

        assert not isinstance(result, ErrorEnvelope)

        # If ChEMBL IDs are present in synonyms, they should be extracted
        # (They might not be in first 20 synonyms from live API)
        chembl_in_synonyms = any("CHEMBL" in syn for syn in result.synonyms)
        if chembl_in_synonyms:
            assert "chembl" in result.cross_references

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_cross_references_drugbank(self) -> None:
        """Test DrugBank cross-reference extraction (T126).

        Note: DrugBank IDs might not always be in the first 20 synonyms,
        so we test the extraction logic works when they ARE present.
        """
        client = PubChemClient()

        result = await client.get_compound("PubChem:CID2244")

        assert not isinstance(result, ErrorEnvelope)

        # If DrugBank IDs are present in synonyms, they should be extracted
        # (They might not be in first 20 synonyms from live API)
        drugbank_in_synonyms = any(
            syn.startswith("DB") and len(syn) == 7 for syn in result.synonyms
        )
        if drugbank_in_synonyms:
            assert "drugbank" in result.cross_references

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_invalid_curie(self) -> None:
        """Test invalid CURIE format returns error (T127)."""
        client = PubChemClient()

        result = await client.get_compound("CID2244")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert "Invalid PubChem CURIE format" in result.error.message
        assert "PubChem:CID{number}" in result.error.recovery_hint
        assert result.error.invalid_input == "CID2244"

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_not_found(self) -> None:
        """Test compound not found returns error (T128)."""
        client = PubChemClient()

        # Use a CID that doesn't exist but is valid format
        # Very large CIDs return 400 (UNRESOLVED_ENTITY), which is also acceptable
        result = await client.get_compound("PubChem:CID999999999999")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        # Could be ENTITY_NOT_FOUND or UNRESOLVED_ENTITY depending on how PubChem responds
        assert result.error.code in (ErrorCode.ENTITY_NOT_FOUND, ErrorCode.UNRESOLVED_ENTITY)
        assert result.error.invalid_input == "PubChem:CID999999999999"

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_ibuprofen(self) -> None:
        """Test getting ibuprofen compound data (T129)."""
        client = PubChemClient()

        result = await client.get_compound("PubChem:CID3672")

        assert not isinstance(result, ErrorEnvelope)
        assert result.id == "PubChem:CID3672"
        assert "ibuprofen" in result.name.lower()
        assert result.molecular_formula == "C13H18O2"

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_fuzzy_to_fact_workflow(self) -> None:
        """Test complete Fuzzy-to-Fact workflow (T130)."""
        client = PubChemClient()

        # Phase 1: Fuzzy search
        search_result = await client.search_compounds("aspirin", page_size=10)
        assert not isinstance(search_result, ErrorEnvelope)
        assert len(search_result.items) > 0

        # Get top candidate CURIE
        top_candidate = search_result.items[0]
        assert top_candidate.id == "PubChem:CID2244"

        # Phase 2: Strict lookup
        compound = await client.get_compound(top_candidate.id)
        assert not isinstance(compound, ErrorEnvelope)
        assert compound.id == "PubChem:CID2244"
        assert compound.name == "Aspirin"

        # Should have complete data
        assert compound.molecular_formula is not None
        # At least one SMILES should be present
        assert compound.canonical_smiles is not None or compound.isomeric_smiles is not None
        assert len(compound.cross_references) > 0

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_synonyms_limit(self) -> None:
        """Test synonyms limited to 20 (T131)."""
        client = PubChemClient()

        result = await client.get_compound("PubChem:CID2244")

        assert not isinstance(result, ErrorEnvelope)

        # Synonyms should be limited to 20
        assert len(result.synonyms) <= 20

        await client.close()

    @pytest.mark.asyncio
    async def test_get_compound_caffeine(self) -> None:
        """Test getting caffeine compound data (T132)."""
        client = PubChemClient()

        result = await client.get_compound("PubChem:CID2519")

        assert not isinstance(result, ErrorEnvelope)
        assert result.id == "PubChem:CID2519"
        assert "caffeine" in result.name.lower()
        assert result.molecular_formula == "C8H10N4O2"

        # Should have cross-references
        assert "pubchem_compound" in result.cross_references

        await client.close()
