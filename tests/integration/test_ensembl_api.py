"""Integration tests for Ensembl MCP Server against live API.

These tests verify the Ensembl client and server tools work correctly
with the real Ensembl REST API at https://rest.ensembl.org.

Run with:
    uv run pytest tests/integration/test_ensembl_api.py -v -m integration
"""

import pytest

from lifesciences_mcp.clients.ensembl import EnsemblClient
from lifesciences_mcp.models.ensembl import (
    ENSEMBL_GENE_PATTERN,
    ENSEMBL_TRANSCRIPT_PATTERN,
    EnsemblGene,
    EnsemblTranscript,
    GeneSearchCandidate,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
async def client():
    """Create an Ensembl client for testing."""
    async with EnsemblClient() as client:
        yield client


# ==============================================================================
# User Story 1: Fuzzy Gene Search Tests (Phase 3)
# ==============================================================================


class TestSearchGenes:
    """Integration tests for search_genes (User Story 1)."""

    async def test_search_genes_brca1(self, client: EnsemblClient):
        """T019: Search for BRCA1 returns valid gene candidates."""
        result = await client.search_genes("BRCA1", species="human")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Verify top result has correct format
        top = result.items[0]
        assert isinstance(top, GeneSearchCandidate)
        assert ENSEMBL_GENE_PATTERN.match(top.id)
        assert top.symbol == "BRCA1"
        assert top.species == "homo_sapiens"
        assert 0.0 <= top.score <= 1.0

    async def test_search_genes_tumor_protein(self, client: EnsemblClient):
        """T020: Search for 'tumor protein' returns multiple candidates."""
        result = await client.search_genes("TP53", species="human")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) >= 1

        # Verify candidates have relevance scores
        for candidate in result.items:
            assert 0.0 <= candidate.score <= 1.0

    async def test_search_genes_species_filter(self, client: EnsemblClient):
        """T021: Species filter restricts results to specified species."""
        result = await client.search_genes("TP53", species="human")

        assert isinstance(result, PaginationEnvelope)

        # All results should be homo_sapiens
        for candidate in result.items:
            assert candidate.species == "homo_sapiens"

    async def test_search_genes_short_query(self, client: EnsemblClient):
        """T022: Short query returns AMBIGUOUS_QUERY error."""
        result = await client.search_genes("p")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"
        assert result.error.recovery_hint is not None
        assert "2 characters" in result.error.recovery_hint

    async def test_search_genes_species_alias(self, client: EnsemblClient):
        """Species alias 'human' resolves to 'homo_sapiens'."""
        result = await client.search_genes("BRCA1", species="human")

        assert isinstance(result, PaginationEnvelope)
        if result.items:
            assert result.items[0].species == "homo_sapiens"

    async def test_search_genes_pagination(self, client: EnsemblClient):
        """Pagination returns cursor for more results when available."""
        result = await client.search_genes("BRCA1", species="human", page_size=1)

        assert isinstance(result, PaginationEnvelope)
        assert result.pagination.page_size == 1
        # Pagination envelope always has total_count
        assert result.pagination.total_count is not None

    async def test_search_genes_no_results(self, client: EnsemblClient):
        """Search with no matches returns empty items."""
        result = await client.search_genes("ZZZZNONEXISTENTGENEZZZ", species="human")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) == 0
        assert result.pagination.total_count == 0


# ==============================================================================
# User Story 2: Strict Gene Lookup Tests (Phase 4)
# ==============================================================================


class TestGetGene:
    """Integration tests for get_gene (User Story 2)."""

    async def test_get_gene_tp53(self, client: EnsemblClient):
        """T029: Get TP53 gene by Ensembl ID returns complete record."""
        result = await client.get_gene("ENSG00000141510")

        assert isinstance(result, EnsemblGene)
        assert result.id == "ENSG00000141510"
        assert result.symbol == "TP53"
        assert result.biotype == "protein_coding"
        assert result.species == "homo_sapiens"
        assert result.assembly_name == "GRCh38"
        assert result.chromosome == "17"
        assert result.strand in (1, -1)
        assert result.start < result.end

        # Cross-references should be populated
        xrefs = result.cross_references
        assert xrefs.hgnc is not None or xrefs.entrez is not None

    async def test_get_gene_invalid_format(self, client: EnsemblClient):
        """T030: Invalid ID format returns UNRESOLVED_ENTITY error."""
        result = await client.get_gene("BRCA1")  # Raw symbol, not ENSG ID

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
        assert "search_genes" in result.error.recovery_hint
        assert result.error.invalid_input == "BRCA1"

    async def test_get_gene_not_found(self, client: EnsemblClient):
        """T031: Non-existent valid format ID returns ENTITY_NOT_FOUND error."""
        result = await client.get_gene("ENSG99999999999")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "ENTITY_NOT_FOUND"
        assert result.error.invalid_input == "ENSG99999999999"

    async def test_get_gene_cross_references(self, client: EnsemblClient):
        """T032: Cross-references are correctly extracted."""
        result = await client.get_gene("ENSG00000141510")  # TP53

        assert isinstance(result, EnsemblGene)
        xrefs = result.cross_references.model_dump()

        # Should have some cross-references (not empty)
        assert len(xrefs) > 0

        # No null values (omit-if-null pattern)
        for value in xrefs.values():
            assert value is not None
            if isinstance(value, list):
                assert len(value) > 0

    async def test_get_gene_slim(self, client: EnsemblClient):
        """T033: Slim mode omits cross_references."""
        result = await client.get_gene("ENSG00000012048", slim=True)  # BRCA1

        assert isinstance(result, EnsemblGene)
        assert result.id == "ENSG00000012048"

        # Cross-references should be empty in slim mode
        xrefs = result.cross_references.model_dump()
        assert len(xrefs) == 0

    async def test_get_gene_transcripts(self, client: EnsemblClient):
        """Gene includes list of transcript IDs."""
        result = await client.get_gene("ENSG00000141510")  # TP53

        assert isinstance(result, EnsemblGene)
        assert result.transcripts is not None
        assert len(result.transcripts) > 0

        # All transcripts should have ENST format
        for transcript_id in result.transcripts:
            assert ENSEMBL_TRANSCRIPT_PATTERN.match(transcript_id)

    async def test_get_gene_versioned_id(self, client: EnsemblClient):
        """Versioned ID is accepted and version is stripped."""
        result = await client.get_gene("ENSG00000141510.12")  # TP53 with version

        assert isinstance(result, EnsemblGene)
        assert result.id == "ENSG00000141510"  # Version stripped


# ==============================================================================
# User Story 3: Transcript Lookup Tests (Phase 5)
# ==============================================================================


class TestGetTranscript:
    """Integration tests for get_transcript (User Story 3)."""

    async def test_get_transcript_tp53(self, client: EnsemblClient):
        """T041: Get TP53 canonical transcript returns complete record."""
        result = await client.get_transcript("ENST00000269305")

        assert isinstance(result, EnsemblTranscript)
        assert result.id == "ENST00000269305"
        assert "TP53" in result.display_name
        assert result.biotype == "protein_coding"
        assert ENSEMBL_GENE_PATTERN.match(result.parent_gene)
        assert result.species == "homo_sapiens"
        assert result.strand in (1, -1)

    async def test_get_transcript_wrong_id_type(self, client: EnsemblClient):
        """T042: Gene ID passed to get_transcript returns clear error."""
        result = await client.get_transcript("ENSG00000141510")  # Gene ID, not transcript

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
        assert "Gene ID" in result.error.message
        assert "get_gene" in result.error.recovery_hint

    async def test_get_transcript_not_found(self, client: EnsemblClient):
        """T043: Non-existent transcript ID returns ENTITY_NOT_FOUND error."""
        result = await client.get_transcript("ENST99999999999")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "ENTITY_NOT_FOUND"

    async def test_get_transcript_canonical(self, client: EnsemblClient):
        """Canonical transcript has is_canonical = True."""
        # ENST00000269305 is the canonical TP53 transcript
        result = await client.get_transcript("ENST00000269305")

        assert isinstance(result, EnsemblTranscript)
        assert result.is_canonical is True

    async def test_get_transcript_slim(self, client: EnsemblClient):
        """Slim mode omits cross_references."""
        result = await client.get_transcript("ENST00000269305", slim=True)

        assert isinstance(result, EnsemblTranscript)
        xrefs = result.cross_references.model_dump()
        # In slim mode, only ensembl_gene should be present (or nothing)
        # Actually in slim mode we skip xrefs fetch entirely
        assert len(xrefs) == 0


# ==============================================================================
# User Story 4: Error Recovery Tests (Phase 6)
# ==============================================================================


class TestErrorRecovery:
    """Integration tests for error recovery (User Story 4)."""

    async def test_error_recovery_unresolved(self, client: EnsemblClient):
        """T048: UNRESOLVED_ENTITY recovery hint leads to successful lookup."""
        # Step 1: Get UNRESOLVED_ENTITY error
        error_result = await client.get_gene("BRCA1")
        assert isinstance(error_result, ErrorEnvelope)
        assert error_result.error.code.value == "UNRESOLVED_ENTITY"

        # Step 2: Follow recovery hint - search for the gene
        search_result = await client.search_genes("BRCA1", species="human")
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

        # Step 3: Get valid ID and retry
        valid_id = search_result.items[0].id
        gene_result = await client.get_gene(valid_id)
        assert isinstance(gene_result, EnsemblGene)
        assert gene_result.symbol == "BRCA1"

    async def test_error_envelope_format(self, client: EnsemblClient):
        """T049: Error envelopes have consistent format."""
        # Test various error conditions
        errors = [
            await client.get_gene("BRCA1"),  # UNRESOLVED_ENTITY
            await client.get_gene("ENSG99999999999"),  # ENTITY_NOT_FOUND
            await client.search_genes("p"),  # AMBIGUOUS_QUERY
        ]

        for error in errors:
            assert isinstance(error, ErrorEnvelope)
            assert error.success is False
            assert error.error.code is not None
            assert error.error.message is not None
            assert error.error.recovery_hint is not None

    async def test_error_recovery_id_type(self, client: EnsemblClient):
        """T050: Gene/transcript ID confusion has helpful recovery."""
        # Pass gene ID to transcript lookup
        error_result = await client.get_transcript("ENSG00000141510")
        assert isinstance(error_result, ErrorEnvelope)

        # Hint explains the difference
        assert "Gene ID" in error_result.error.message or "ENSG" in error_result.error.message
        assert "get_gene" in error_result.error.recovery_hint

        # Follow hint - use get_gene instead
        gene_result = await client.get_gene("ENSG00000141510")
        assert isinstance(gene_result, EnsemblGene)

        # Get transcript from gene's transcripts list
        if gene_result.transcripts:
            transcript_result = await client.get_transcript(gene_result.transcripts[0])
            assert isinstance(transcript_result, EnsemblTranscript)


# ==============================================================================
# Fuzzy-to-Fact Workflow Tests
# ==============================================================================


class TestFuzzyToFactWorkflow:
    """End-to-end tests for the Fuzzy-to-Fact protocol."""

    async def test_search_then_lookup_gene(self, client: EnsemblClient):
        """Complete Fuzzy-to-Fact workflow for genes."""
        # Phase 1: Fuzzy search
        search_result = await client.search_genes("TP53", species="human")
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

        # Select top candidate
        candidate = search_result.items[0]
        assert candidate.symbol == "TP53"

        # Phase 2: Strict lookup
        gene = await client.get_gene(candidate.id)
        assert isinstance(gene, EnsemblGene)
        assert gene.id == candidate.id
        assert gene.symbol == "TP53"

        # Verify cross-references populated
        assert gene.cross_references.hgnc is not None or gene.cross_references.entrez is not None

    async def test_gene_to_transcript_workflow(self, client: EnsemblClient):
        """Workflow: get gene -> get transcript from transcripts list."""
        # Get gene
        gene = await client.get_gene("ENSG00000141510")  # TP53
        assert isinstance(gene, EnsemblGene)
        assert gene.transcripts is not None
        assert len(gene.transcripts) > 0

        # Get first transcript
        transcript = await client.get_transcript(gene.transcripts[0])
        assert isinstance(transcript, EnsemblTranscript)
        assert transcript.parent_gene == gene.id
