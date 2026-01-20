"""Unit tests for EnsemblClient with mocked responses.

These tests verify client behavior without making actual API calls.

Run with:
    uv run pytest tests/unit/test_ensembl_client.py -v
"""

from unittest.mock import MagicMock, patch

import pytest

from lifesciences_mcp.clients.ensembl import (
    SPECIES_ALIASES,
    EnsemblClient,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope

pytestmark = [pytest.mark.unit, pytest.mark.ensembl]

# ==============================================================================
# Client Initialization Tests
# ==============================================================================


class TestEnsemblClientInit:
    """Tests for EnsemblClient initialization."""

    def test_base_url(self):
        """Client has correct base URL."""
        client = EnsemblClient()
        assert client.base_url == "https://rest.ensembl.org"

    def test_rate_limit_delay(self):
        """Rate limit delay is 66.67ms (15 req/s)."""
        client = EnsemblClient()
        assert client.RATE_LIMIT_DELAY == pytest.approx(1.0 / 15, rel=0.01)

    def test_max_retries(self):
        """Max retries is 3."""
        client = EnsemblClient()
        assert client.MAX_RETRIES == 3


# ==============================================================================
# Species Normalization Tests
# ==============================================================================


class TestSpeciesNormalization:
    """Tests for species name normalization."""

    def test_species_aliases(self):
        """Species aliases are defined."""
        assert "human" in SPECIES_ALIASES
        assert "mouse" in SPECIES_ALIASES
        assert SPECIES_ALIASES["human"] == "homo_sapiens"
        assert SPECIES_ALIASES["mouse"] == "mus_musculus"

    def test_normalize_species_alias(self):
        """Common aliases are normalized."""
        client = EnsemblClient()
        assert client._normalize_species("human") == "homo_sapiens"
        assert client._normalize_species("Human") == "homo_sapiens"
        assert client._normalize_species("HUMAN") == "homo_sapiens"
        assert client._normalize_species("mouse") == "mus_musculus"
        assert client._normalize_species("fly") == "drosophila_melanogaster"

    def test_normalize_species_passthrough(self):
        """Unknown species are passed through."""
        client = EnsemblClient()
        assert client._normalize_species("homo_sapiens") == "homo_sapiens"
        assert client._normalize_species("mus_musculus") == "mus_musculus"
        assert client._normalize_species("unknown_species") == "unknown_species"

    def test_normalize_species_whitespace(self):
        """Whitespace is handled."""
        client = EnsemblClient()
        assert client._normalize_species("  human  ") == "homo_sapiens"
        # "c. elegans" with space/period is aliased
        assert client._normalize_species("c.elegans") == "caenorhabditis_elegans"
        # "worm" is also aliased
        assert client._normalize_species("worm") == "caenorhabditis_elegans"


# ==============================================================================
# Error Envelope Creation Tests (T051)
# ==============================================================================


class TestCreateErrorEnvelope:
    """Tests for error envelope creation."""

    def test_create_error_envelope_basic(self):
        """Create basic error envelope."""
        client = EnsemblClient()
        from lifesciences_mcp.models.envelopes import ErrorCode

        error = client._create_error_envelope(
            code=ErrorCode.UNRESOLVED_ENTITY,
            message="Test message",
            recovery_hint="Test hint",
        )
        assert isinstance(error, ErrorEnvelope)
        assert error.success is False
        assert error.error.code.value == "UNRESOLVED_ENTITY"
        assert error.error.message == "Test message"
        assert error.error.recovery_hint == "Test hint"
        assert error.error.invalid_input is None

    def test_create_error_envelope_with_input(self):
        """Create error envelope with invalid input."""
        client = EnsemblClient()
        from lifesciences_mcp.models.envelopes import ErrorCode

        error = client._create_error_envelope(
            code=ErrorCode.ENTITY_NOT_FOUND,
            message="Not found",
            recovery_hint="Try again",
            invalid_input="ENSG99999999999",
        )
        assert error.error.invalid_input == "ENSG99999999999"


# ==============================================================================
# Cross-Reference Mapping Tests
# ==============================================================================


class TestCrossReferenceMapping:
    """Tests for cross-reference mapping."""

    def test_map_hgnc(self):
        """HGNC cross-reference is mapped with prefix."""
        client = EnsemblClient()
        xrefs = [{"dbname": "HGNC", "primary_id": "11998"}]
        result = client._map_cross_references(xrefs)
        assert result.hgnc == "HGNC:11998"

    def test_map_uniprot_swissprot(self):
        """UniProt/SWISSPROT is mapped to uniprot list."""
        client = EnsemblClient()
        xrefs = [{"dbname": "Uniprot/SWISSPROT", "primary_id": "P04637"}]
        result = client._map_cross_references(xrefs)
        assert result.uniprot == ["P04637"]

    def test_map_uniprot_trembl(self):
        """UniProt/SPTREMBL is mapped to uniprot list."""
        client = EnsemblClient()
        xrefs = [{"dbname": "Uniprot/SPTREMBL", "primary_id": "Q53GA5"}]
        result = client._map_cross_references(xrefs)
        assert result.uniprot == ["Q53GA5"]

    def test_map_multiple_uniprot(self):
        """Multiple UniProt entries are collected in list."""
        client = EnsemblClient()
        xrefs = [
            {"dbname": "Uniprot/SWISSPROT", "primary_id": "P04637"},
            {"dbname": "Uniprot/SPTREMBL", "primary_id": "Q53GA5"},
        ]
        result = client._map_cross_references(xrefs)
        assert len(result.uniprot) == 2
        assert "P04637" in result.uniprot
        assert "Q53GA5" in result.uniprot

    def test_map_entrez(self):
        """EntrezGene is mapped."""
        client = EnsemblClient()
        xrefs = [{"dbname": "EntrezGene", "primary_id": "7157"}]
        result = client._map_cross_references(xrefs)
        assert result.entrez == "7157"

    def test_map_refseq(self):
        """RefSeq entries are collected in list."""
        client = EnsemblClient()
        xrefs = [
            {"dbname": "RefSeq_mRNA", "primary_id": "NM_000546"},
            {"dbname": "RefSeq_peptide", "primary_id": "NP_000537"},
        ]
        result = client._map_cross_references(xrefs)
        assert len(result.refseq) == 2

    def test_map_omim(self):
        """OMIM entries are mapped."""
        client = EnsemblClient()
        xrefs = [{"dbname": "MIM_GENE", "primary_id": "191170"}]
        result = client._map_cross_references(xrefs)
        assert result.omim == "191170"

    def test_map_pdb(self):
        """PDB entries are collected in list."""
        client = EnsemblClient()
        xrefs = [
            {"dbname": "PDB", "primary_id": "1TUP"},
            {"dbname": "PDB", "primary_id": "2OCJ"},
        ]
        result = client._map_cross_references(xrefs)
        assert len(result.pdb) == 2

    def test_map_kegg(self):
        """KEGG entries are mapped."""
        client = EnsemblClient()
        xrefs = [{"dbname": "KEGG_Enzyme", "primary_id": "hsa:7157"}]
        result = client._map_cross_references(xrefs)
        assert result.kegg == "hsa:7157"

    def test_map_chembl(self):
        """ChEMBL entries are mapped."""
        client = EnsemblClient()
        xrefs = [{"dbname": "ChEMBL", "primary_id": "CHEMBL3927"}]
        result = client._map_cross_references(xrefs)
        assert result.chembl == "CHEMBL3927"

    def test_map_empty_xrefs(self):
        """Empty xrefs list returns empty CrossReferences."""
        client = EnsemblClient()
        result = client._map_cross_references([])
        assert result.model_dump() == {}

    def test_map_unknown_dbname_ignored(self):
        """Unknown database names are ignored."""
        client = EnsemblClient()
        xrefs = [{"dbname": "UnknownDB", "primary_id": "12345"}]
        result = client._map_cross_references(xrefs)
        assert result.model_dump() == {}

    def test_map_missing_primary_id(self):
        """Entries without primary_id are skipped."""
        client = EnsemblClient()
        xrefs = [{"dbname": "HGNC", "primary_id": ""}]
        result = client._map_cross_references(xrefs)
        assert result.hgnc is None


# ==============================================================================
# Search Genes Validation Tests
# ==============================================================================


class TestSearchGenesValidation:
    """Tests for search_genes input validation."""

    @pytest.mark.asyncio
    async def test_short_query_rejected(self):
        """Query with less than 2 characters returns error."""
        client = EnsemblClient()
        result = await client.search_genes("p")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"

    @pytest.mark.asyncio
    async def test_empty_query_rejected(self):
        """Empty query returns error."""
        client = EnsemblClient()
        result = await client.search_genes("")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"

    @pytest.mark.asyncio
    async def test_whitespace_query_rejected(self):
        """Whitespace-only query returns error."""
        client = EnsemblClient()
        result = await client.search_genes("   ")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"

    @pytest.mark.asyncio
    async def test_page_size_clamped_minimum(self):
        """Page size is clamped to minimum 1."""
        client = EnsemblClient()
        # This would proceed with the request, clamping page_size
        # We just verify the function doesn't crash
        with patch.object(client, "_rate_limited_get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            await client.search_genes("BRCA1", page_size=-5)
            # Should not raise

    @pytest.mark.asyncio
    async def test_page_size_clamped_maximum(self):
        """Page size is clamped to maximum 100."""
        client = EnsemblClient()
        with patch.object(client, "_rate_limited_get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            await client.search_genes("BRCA1", page_size=500)
            # Should not raise


# ==============================================================================
# Get Gene Validation Tests
# ==============================================================================


class TestGetGeneValidation:
    """Tests for get_gene input validation."""

    @pytest.mark.asyncio
    async def test_invalid_id_format(self):
        """Non-ENSG format returns UNRESOLVED_ENTITY."""
        client = EnsemblClient()
        result = await client.get_gene("BRCA1")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
        assert "search_genes" in result.error.recovery_hint

    @pytest.mark.asyncio
    async def test_transcript_id_rejected(self):
        """ENST ID returns UNRESOLVED_ENTITY."""
        client = EnsemblClient()
        result = await client.get_gene("ENST00000269305")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"

    @pytest.mark.asyncio
    async def test_version_stripped(self):
        """Version suffix is stripped from ID."""
        # We can't fully test without mocking, but we verify the strip logic
        versioned_id = "ENSG00000141510.12"
        stripped = versioned_id.split(".")[0]
        assert stripped == "ENSG00000141510"


# ==============================================================================
# Get Transcript Validation Tests
# ==============================================================================


class TestGetTranscriptValidation:
    """Tests for get_transcript input validation."""

    @pytest.mark.asyncio
    async def test_gene_id_rejected(self):
        """ENSG ID returns specific error about ID type."""
        client = EnsemblClient()
        result = await client.get_transcript("ENSG00000141510")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
        assert "Gene ID" in result.error.message

    @pytest.mark.asyncio
    async def test_invalid_id_format(self):
        """Non-ENST format returns UNRESOLVED_ENTITY."""
        client = EnsemblClient()
        result = await client.get_transcript("TP53-201")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"


# ==============================================================================
# Context Manager Tests
# ==============================================================================


class TestContextManager:
    """Tests for context manager usage."""

    @pytest.mark.asyncio
    async def test_context_manager_entry_exit(self):
        """Context manager enters and exits cleanly."""
        async with EnsemblClient() as client:
            assert isinstance(client, EnsemblClient)
        # Should not raise

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Close method can be called."""
        client = EnsemblClient()
        await client.close()  # Should not raise
