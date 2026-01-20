"""Unit tests for Ensembl Pydantic models.

These tests verify model validation and serialization without API calls.

Run with:
    uv run pytest tests/unit/test_ensembl_models.py -v
"""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.ensembl import (
    ENSEMBL_GENE_PATTERN,
    ENSEMBL_TRANSCRIPT_PATTERN,
    EnsemblCrossReferences,
    EnsemblGene,
    EnsemblTranscript,
    GeneSearchCandidate,
)

pytestmark = [pytest.mark.unit, pytest.mark.ensembl]

# ==============================================================================
# GeneSearchCandidate Tests (T057)
# ==============================================================================


class TestGeneSearchCandidate:
    """Unit tests for GeneSearchCandidate model."""

    def test_valid_candidate(self):
        """Valid candidate with all required fields."""
        candidate = GeneSearchCandidate(
            id="ENSG00000141510",
            symbol="TP53",
            name="tumor protein p53",
            biotype="protein_coding",
            species="homo_sapiens",
            score=0.95,
        )
        assert candidate.id == "ENSG00000141510"
        assert candidate.symbol == "TP53"
        assert candidate.score == 0.95

    def test_valid_id_pattern(self):
        """Valid Ensembl Gene ID patterns are accepted."""
        valid_ids = [
            "ENSG00000141510",
            "ENSG00000012048",
            "ENSG00000157764",
            "ENSG00000000001",
            "ENSG99999999999",
        ]
        for gene_id in valid_ids:
            candidate = GeneSearchCandidate(
                id=gene_id,
                symbol="TEST",
                name="Test gene",
                biotype="protein_coding",
                species="homo_sapiens",
                score=1.0,
            )
            assert candidate.id == gene_id

    def test_invalid_id_pattern_rejected(self):
        """Invalid Ensembl Gene ID patterns are rejected."""
        invalid_ids = [
            "BRCA1",  # Raw symbol
            "ENS00000141510",  # Missing 'G'
            "ENSG0000014151",  # Too few digits (10)
            "ENSG000001415100",  # Too many digits (12)
            "ENST00000269305",  # Transcript ID, not gene
            "ensg00000141510",  # Lowercase
            "",  # Empty
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError):
                GeneSearchCandidate(
                    id=invalid_id,
                    symbol="TEST",
                    name="Test",
                    biotype="protein_coding",
                    species="homo_sapiens",
                    score=1.0,
                )

    def test_score_range_valid(self):
        """Valid scores between 0.0 and 1.0 are accepted."""
        for score in [0.0, 0.5, 1.0, 0.95, 0.01]:
            candidate = GeneSearchCandidate(
                id="ENSG00000141510",
                symbol="TEST",
                name="Test",
                biotype="protein_coding",
                species="homo_sapiens",
                score=score,
            )
            assert 0.0 <= candidate.score <= 1.0

    def test_score_range_invalid(self):
        """Scores outside 0.0-1.0 are rejected."""
        for invalid_score in [-0.1, 1.1, 2.0, -1.0]:
            with pytest.raises(ValidationError):
                GeneSearchCandidate(
                    id="ENSG00000141510",
                    symbol="TEST",
                    name="Test",
                    biotype="protein_coding",
                    species="homo_sapiens",
                    score=invalid_score,
                )

    def test_score_rounded(self):
        """Scores are rounded to 2 decimal places."""
        candidate = GeneSearchCandidate(
            id="ENSG00000141510",
            symbol="TEST",
            name="Test",
            biotype="protein_coding",
            species="homo_sapiens",
            score=0.12345,
        )
        assert candidate.score == 0.12


# ==============================================================================
# EnsemblGene Tests (T058)
# ==============================================================================


class TestEnsemblGene:
    """Unit tests for EnsemblGene model."""

    def test_valid_gene(self):
        """Valid gene with all required fields."""
        gene = EnsemblGene(
            id="ENSG00000141510",
            symbol="TP53",
            name="tumor protein p53",
            biotype="protein_coding",
            species="homo_sapiens",
            assembly_name="GRCh38",
            chromosome="17",
            start=7661779,
            end=7687538,
            strand=-1,
        )
        assert gene.id == "ENSG00000141510"
        assert gene.strand == -1
        assert gene.start < gene.end

    def test_strand_validation_positive(self):
        """Strand +1 is valid."""
        gene = EnsemblGene(
            id="ENSG00000141510",
            symbol="TEST",
            name="Test",
            biotype="protein_coding",
            species="homo_sapiens",
            assembly_name="GRCh38",
            chromosome="1",
            start=1000,
            end=2000,
            strand=1,
        )
        assert gene.strand == 1

    def test_strand_validation_negative(self):
        """Strand -1 is valid."""
        gene = EnsemblGene(
            id="ENSG00000141510",
            symbol="TEST",
            name="Test",
            biotype="protein_coding",
            species="homo_sapiens",
            assembly_name="GRCh38",
            chromosome="1",
            start=1000,
            end=2000,
            strand=-1,
        )
        assert gene.strand == -1

    def test_strand_validation_invalid(self):
        """Invalid strand values are rejected."""
        for invalid_strand in [0, 2, -2, 10]:
            with pytest.raises(ValidationError):
                EnsemblGene(
                    id="ENSG00000141510",
                    symbol="TEST",
                    name="Test",
                    biotype="protein_coding",
                    species="homo_sapiens",
                    assembly_name="GRCh38",
                    chromosome="1",
                    start=1000,
                    end=2000,
                    strand=invalid_strand,
                )

    def test_start_less_than_end(self):
        """Start must be less than end."""
        with pytest.raises(ValidationError):
            EnsemblGene(
                id="ENSG00000141510",
                symbol="TEST",
                name="Test",
                biotype="protein_coding",
                species="homo_sapiens",
                assembly_name="GRCh38",
                chromosome="1",
                start=2000,  # Greater than end
                end=1000,
                strand=1,
            )

    def test_start_equal_to_end_invalid(self):
        """Start cannot equal end."""
        with pytest.raises(ValidationError):
            EnsemblGene(
                id="ENSG00000141510",
                symbol="TEST",
                name="Test",
                biotype="protein_coding",
                species="homo_sapiens",
                assembly_name="GRCh38",
                chromosome="1",
                start=1000,
                end=1000,  # Equal to start
                strand=1,
            )

    def test_optional_transcripts(self):
        """Transcripts field is optional."""
        gene = EnsemblGene(
            id="ENSG00000141510",
            symbol="TEST",
            name="Test",
            biotype="protein_coding",
            species="homo_sapiens",
            assembly_name="GRCh38",
            chromosome="1",
            start=1000,
            end=2000,
            strand=1,
        )
        assert gene.transcripts is None

    def test_transcripts_list(self):
        """Transcripts can be a list of IDs."""
        gene = EnsemblGene(
            id="ENSG00000141510",
            symbol="TEST",
            name="Test",
            biotype="protein_coding",
            species="homo_sapiens",
            assembly_name="GRCh38",
            chromosome="1",
            start=1000,
            end=2000,
            strand=1,
            transcripts=["ENST00000269305", "ENST00000445888"],
        )
        assert len(gene.transcripts) == 2

    def test_to_search_candidate(self):
        """Gene can be converted to search candidate."""
        gene = EnsemblGene(
            id="ENSG00000141510",
            symbol="TP53",
            name="tumor protein p53",
            biotype="protein_coding",
            species="homo_sapiens",
            assembly_name="GRCh38",
            chromosome="17",
            start=1000,
            end=2000,
            strand=1,
        )
        candidate = gene.to_search_candidate(score=0.9)
        assert isinstance(candidate, GeneSearchCandidate)
        assert candidate.id == gene.id
        assert candidate.symbol == gene.symbol
        assert candidate.score == 0.9


# ==============================================================================
# EnsemblTranscript Tests (T059)
# ==============================================================================


class TestEnsemblTranscript:
    """Unit tests for EnsemblTranscript model."""

    def test_valid_transcript(self):
        """Valid transcript with all required fields."""
        transcript = EnsemblTranscript(
            id="ENST00000269305",
            display_name="TP53-201",
            biotype="protein_coding",
            parent_gene="ENSG00000141510",
            is_canonical=True,
            species="homo_sapiens",
            assembly_name="GRCh38",
            chromosome="17",
            start=7669609,
            end=7687538,
            strand=-1,
        )
        assert transcript.id == "ENST00000269305"
        assert transcript.parent_gene == "ENSG00000141510"
        assert transcript.is_canonical is True

    def test_transcript_id_pattern(self):
        """Valid transcript ID patterns are accepted."""
        valid_ids = [
            "ENST00000269305",
            "ENST00000445888",
            "ENST00000000001",
            "ENST99999999999",
        ]
        for transcript_id in valid_ids:
            transcript = EnsemblTranscript(
                id=transcript_id,
                display_name="TEST",
                biotype="protein_coding",
                parent_gene="ENSG00000141510",
                species="homo_sapiens",
                assembly_name="GRCh38",
                chromosome="1",
                start=1000,
                end=2000,
                strand=1,
            )
            assert transcript.id == transcript_id

    def test_invalid_transcript_id(self):
        """Invalid transcript IDs are rejected."""
        invalid_ids = [
            "ENSG00000141510",  # Gene ID, not transcript
            "ENST0000026930",  # Too few digits
            "ENT00000269305",  # Missing 'S'
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError):
                EnsemblTranscript(
                    id=invalid_id,
                    display_name="TEST",
                    biotype="protein_coding",
                    parent_gene="ENSG00000141510",
                    species="homo_sapiens",
                    assembly_name="GRCh38",
                    chromosome="1",
                    start=1000,
                    end=2000,
                    strand=1,
                )

    def test_parent_gene_pattern(self):
        """Parent gene must be valid ENSG ID."""
        with pytest.raises(ValidationError):
            EnsemblTranscript(
                id="ENST00000269305",
                display_name="TEST",
                biotype="protein_coding",
                parent_gene="TP53",  # Invalid - should be ENSG ID
                species="homo_sapiens",
                assembly_name="GRCh38",
                chromosome="1",
                start=1000,
                end=2000,
                strand=1,
            )

    def test_is_canonical_default(self):
        """is_canonical defaults to False."""
        transcript = EnsemblTranscript(
            id="ENST00000269305",
            display_name="TEST",
            biotype="protein_coding",
            parent_gene="ENSG00000141510",
            species="homo_sapiens",
            assembly_name="GRCh38",
            chromosome="1",
            start=1000,
            end=2000,
            strand=1,
        )
        assert transcript.is_canonical is False


# ==============================================================================
# CrossReferences Tests (T060)
# ==============================================================================


class TestEnsemblCrossReferences:
    """Unit tests for EnsemblCrossReferences model."""

    def test_empty_cross_references(self):
        """Empty cross-references are valid."""
        xrefs = EnsemblCrossReferences()
        dump = xrefs.model_dump()
        assert dump == {}

    def test_omit_none_values(self):
        """None values are omitted from dump."""
        xrefs = EnsemblCrossReferences(
            hgnc="HGNC:11998",
            uniprot=None,
            entrez=None,
        )
        dump = xrefs.model_dump()
        assert "hgnc" in dump
        assert "uniprot" not in dump
        assert "entrez" not in dump

    def test_omit_empty_lists(self):
        """Empty lists are converted to None and omitted."""
        xrefs = EnsemblCrossReferences(
            hgnc="HGNC:11998",
            uniprot=[],  # Empty list
            refseq=[],
        )
        dump = xrefs.model_dump()
        assert "hgnc" in dump
        assert "uniprot" not in dump
        assert "refseq" not in dump

    def test_omit_empty_strings(self):
        """Empty strings are converted to None and omitted."""
        xrefs = EnsemblCrossReferences(
            hgnc="",  # Empty string
            entrez="7157",
        )
        dump = xrefs.model_dump()
        assert "hgnc" not in dump
        assert "entrez" in dump

    def test_list_fields(self):
        """List fields support multiple values."""
        xrefs = EnsemblCrossReferences(
            uniprot=["P04637", "Q53GA5"],
            refseq=["NM_000546", "NP_000537"],
            pdb=["1TUP", "2OCJ", "3KMD"],
        )
        dump = xrefs.model_dump()
        assert len(dump["uniprot"]) == 2
        assert len(dump["refseq"]) == 2
        assert len(dump["pdb"]) == 3

    def test_all_fields(self):
        """All cross-reference fields can be populated."""
        xrefs = EnsemblCrossReferences(
            hgnc="HGNC:11998",
            ensembl_gene="ENSG00000141510",
            ensembl_transcript=["ENST00000269305"],
            uniprot=["P04637"],
            entrez="7157",
            refseq=["NM_000546"],
            omim="191170",
            pdb=["1TUP"],
            kegg="hsa:7157",
            chembl="CHEMBL3927",
            string="9606.ENSP00000269305",
            biogrid="123456",
        )
        dump = xrefs.model_dump()
        assert len(dump) == 12  # All 12 fields


# ==============================================================================
# Pattern Tests
# ==============================================================================


class TestPatterns:
    """Tests for ID validation patterns."""

    def test_ensembl_gene_pattern(self):
        """ENSEMBL_GENE_PATTERN matches valid gene IDs."""
        assert ENSEMBL_GENE_PATTERN.match("ENSG00000141510")
        assert ENSEMBL_GENE_PATTERN.match("ENSG00000000001")
        assert ENSEMBL_GENE_PATTERN.match("ENSG99999999999")
        assert not ENSEMBL_GENE_PATTERN.match("ENST00000269305")
        assert not ENSEMBL_GENE_PATTERN.match("ensg00000141510")
        assert not ENSEMBL_GENE_PATTERN.match("BRCA1")

    def test_ensembl_transcript_pattern(self):
        """ENSEMBL_TRANSCRIPT_PATTERN matches valid transcript IDs."""
        assert ENSEMBL_TRANSCRIPT_PATTERN.match("ENST00000269305")
        assert ENSEMBL_TRANSCRIPT_PATTERN.match("ENST00000000001")
        assert ENSEMBL_TRANSCRIPT_PATTERN.match("ENST99999999999")
        assert not ENSEMBL_TRANSCRIPT_PATTERN.match("ENSG00000141510")
        assert not ENSEMBL_TRANSCRIPT_PATTERN.match("enst00000269305")
        assert not ENSEMBL_TRANSCRIPT_PATTERN.match("TP53-201")
