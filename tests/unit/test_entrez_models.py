"""Unit tests for Entrez models.

Tests model validation, CURIE patterns, and field constraints.
Run with: pytest tests/unit/test_entrez_models.py -v
"""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.entrez import (
    EntrezCrossReferences,
    EntrezGene,
    GeneSearchCandidate,
    NCBI_GENE_CURIE_PATTERN,
)

pytestmark = [pytest.mark.unit, pytest.mark.entrez]


# =============================================================================
# T058: GeneSearchCandidate Model Tests
# =============================================================================


class TestGeneSearchCandidateModel:
    """Unit tests for GeneSearchCandidate model."""

    def test_valid_curie_pattern(self):
        """Test that valid NCBIGene CURIEs are accepted."""
        valid_curies = [
            "NCBIGene:7157",
            "NCBIGene:672",
            "NCBIGene:1017",
            "NCBIGene:1",
            "NCBIGene:999999999",
        ]

        for curie in valid_curies:
            candidate = GeneSearchCandidate(
                id=curie,
                symbol="TEST",
                name="Test Gene",
                description="Test description",
                organism="Homo sapiens",
                score=0.95,
            )
            assert candidate.id == curie

    def test_invalid_curie_pattern_missing_prefix(self):
        """Test that CURIEs without 'NCBIGene:' prefix are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            GeneSearchCandidate(
                id="7157",  # Missing NCBIGene: prefix
                symbol="TP53",
                name="tumor protein p53",
                description="Test",
                organism="Homo sapiens",
                score=1.0,
            )

        assert "Invalid NCBIGene CURIE format" in str(exc_info.value)

    def test_invalid_curie_pattern_non_numeric(self):
        """Test that CURIEs with non-numeric IDs are rejected."""
        invalid_curies = [
            "NCBIGene:ABC123",
            "NCBIGene:7157a",
            "NCBIGene:",
            "HGNC:11998",  # Wrong database
        ]

        for curie in invalid_curies:
            with pytest.raises(ValidationError):
                GeneSearchCandidate(
                    id=curie,
                    symbol="TEST",
                    name="Test Gene",
                    description="Test",
                    organism="Homo sapiens",
                    score=0.5,
                )

    def test_score_range_validation_valid(self):
        """Test that scores in 0.0-1.0 range are accepted."""
        valid_scores = [0.0, 0.5, 1.0, 0.95, 0.01, 0.99]

        for score in valid_scores:
            candidate = GeneSearchCandidate(
                id="NCBIGene:7157",
                symbol="TP53",
                name="tumor protein p53",
                description="Test",
                organism="Homo sapiens",
                score=score,
            )
            assert candidate.score == score

    def test_score_range_validation_invalid(self):
        """Test that scores outside 0.0-1.0 range are rejected."""
        invalid_scores = [-0.1, 1.1, 2.0, -1.0, 999.0]

        for score in invalid_scores:
            with pytest.raises(ValidationError):
                GeneSearchCandidate(
                    id="NCBIGene:7157",
                    symbol="TP53",
                    name="tumor protein p53",
                    description="Test",
                    organism="Homo sapiens",
                    score=score,
                )

    def test_optional_description_field(self):
        """Test that description field is optional."""
        candidate = GeneSearchCandidate(
            id="NCBIGene:672",
            symbol="BRCA1",
            name="BRCA1 DNA repair associated",
            description=None,
            organism="Homo sapiens",
            score=1.0,
        )
        assert candidate.description is None


# =============================================================================
# T059: EntrezGene Model Tests
# =============================================================================


class TestEntrezGeneModel:
    """Unit tests for EntrezGene model."""

    def test_valid_curie_pattern(self):
        """Test CURIE pattern validation."""
        gene = EntrezGene(
            id="NCBIGene:7157",
            symbol="TP53",
            name="tumor protein p53",
            description="cellular tumor antigen p53",
            summary="This gene encodes a tumor suppressor protein",
            map_location="17p13.1",
            chromosome="17",
            aliases=["P53", "TRP53"],
            organism="Homo sapiens",
            taxon_id=9606,
        )
        assert gene.id == "NCBIGene:7157"

    def test_invalid_curie_pattern(self):
        """Test that invalid CURIEs are rejected."""
        with pytest.raises(ValidationError):
            EntrezGene(
                id="7157",  # Missing prefix
                symbol="TP53",
                name="tumor protein p53",
                organism="Homo sapiens",
            )

    def test_optional_fields(self):
        """Test that optional fields can be None."""
        gene = EntrezGene(
            id="NCBIGene:7157",
            symbol="TP53",
            name="tumor protein p53",
            organism="Homo sapiens",
            # Optional fields omitted
            description=None,
            summary=None,
            map_location=None,
            chromosome=None,
            aliases=None,
            taxon_id=None,
        )

        assert gene.description is None
        assert gene.summary is None
        assert gene.map_location is None
        assert gene.chromosome is None
        assert gene.aliases is None
        assert gene.taxon_id is None

    def test_aliases_list_field(self):
        """Test that aliases accepts list of strings."""
        aliases = ["P53", "TRP53", "TP53"]
        gene = EntrezGene(
            id="NCBIGene:7157",
            symbol="TP53",
            name="tumor protein p53",
            organism="Homo sapiens",
            aliases=aliases,
        )
        assert gene.aliases == aliases

    def test_default_cross_references(self):
        """Test that cross_references has empty default."""
        gene = EntrezGene(
            id="NCBIGene:672",
            symbol="BRCA1",
            name="BRCA1 DNA repair associated",
            organism="Homo sapiens",
        )
        assert gene.cross_references is not None
        # Should be empty EntrezCrossReferences object
        xrefs_dict = gene.cross_references.model_dump(exclude_none=True)
        assert len(xrefs_dict) == 0


# =============================================================================
# T060: EntrezCrossReferences Model Tests
# =============================================================================


class TestEntrezCrossReferencesModel:
    """Unit tests for EntrezCrossReferences model."""

    def test_omit_if_null_pattern(self):
        """Test that None values are omitted from serialization."""
        xrefs = EntrezCrossReferences(
            hgnc="HGNC:11998",
            ensembl_gene="ENSG00000141510",
            uniprot=None,  # Should be omitted
            entrez=None,  # Should be omitted
        )

        xrefs_dict = xrefs.model_dump(exclude_none=True)
        assert "hgnc" in xrefs_dict
        assert "ensembl_gene" in xrefs_dict
        assert "uniprot" not in xrefs_dict
        assert "entrez" not in xrefs_dict

    def test_hgnc_prefix_formatting(self):
        """Test HGNC cross-reference formatting."""
        xrefs = EntrezCrossReferences(hgnc="HGNC:11998")
        assert xrefs.hgnc == "HGNC:11998"

    def test_uniprot_prefix_formatting(self):
        """Test UniProt cross-reference formatting (single value)."""
        xrefs = EntrezCrossReferences(uniprot="UniProtKB:P04637")
        assert xrefs.uniprot == "UniProtKB:P04637"

    def test_uniprot_list_handling(self):
        """Test that uniprot field accepts list of values."""
        uniprot_ids = ["UniProtKB:P04637", "UniProtKB:P04637-2"]
        xrefs = EntrezCrossReferences(uniprot=uniprot_ids)
        assert xrefs.uniprot == uniprot_ids
        assert isinstance(xrefs.uniprot, list)

    def test_refseq_list_handling(self):
        """Test that refseq field accepts list of values."""
        refseq_ids = ["NM_000546.6", "NP_000537.3"]
        xrefs = EntrezCrossReferences(refseq=refseq_ids)
        assert xrefs.refseq == refseq_ids
        assert isinstance(xrefs.refseq, list)

    def test_all_optional_fields(self):
        """Test that all fields are optional."""
        xrefs = EntrezCrossReferences()
        xrefs_dict = xrefs.model_dump(exclude_none=True)
        assert len(xrefs_dict) == 0  # All fields omitted

    def test_multiple_cross_references(self):
        """Test model with multiple cross-references populated."""
        xrefs = EntrezCrossReferences(
            hgnc="HGNC:11998",
            ensembl_gene="ENSG00000141510",
            ensembl_transcript="ENST00000269305",
            uniprot=["UniProtKB:P04637"],
            refseq=["NM_000546.6", "NP_000537.3"],
            omim="191170",
            kegg="hsa:7157",
            string="9606.ENSP00000269305",
            biogrid="113418",
        )

        xrefs_dict = xrefs.model_dump(exclude_none=True)
        assert len(xrefs_dict) == 9
        assert xrefs_dict["hgnc"] == "HGNC:11998"
        assert xrefs_dict["omim"] == "191170"

    def test_empty_string_values_omitted(self):
        """Test that empty strings are omitted (omit-if-null pattern)."""
        # Create with data dict to bypass validators initially
        xrefs_data = {
            "hgnc": "HGNC:11998",
            "ensembl_gene": "",  # Empty string
            "uniprot": None,
        }

        xrefs = EntrezCrossReferences.model_validate(xrefs_data)
        xrefs_dict = xrefs.model_dump(exclude_none=True)

        # Empty string should be filtered out
        assert "ensembl_gene" not in xrefs_dict
        assert "hgnc" in xrefs_dict

    def test_empty_list_values_omitted(self):
        """Test that empty lists are omitted."""
        xrefs_data = {
            "hgnc": "HGNC:11998",
            "uniprot": [],  # Empty list
            "refseq": ["NM_000546.6"],  # Non-empty list
        }

        xrefs = EntrezCrossReferences.model_validate(xrefs_data)
        xrefs_dict = xrefs.model_dump(exclude_none=True)

        assert "uniprot" not in xrefs_dict  # Empty list omitted
        assert "refseq" in xrefs_dict  # Non-empty list included


# =============================================================================
# Additional Tests
# =============================================================================


class TestNCBIGeneCURIEPattern:
    """Test the NCBI_GENE_CURIE_PATTERN regex directly."""

    def test_pattern_matches_valid_curies(self):
        """Test regex pattern matches valid CURIEs."""
        valid = [
            "NCBIGene:7157",
            "NCBIGene:1",
            "NCBIGene:999999999999",
            "NCBIGene:0",
        ]

        for curie in valid:
            assert NCBI_GENE_CURIE_PATTERN.match(curie), f"Should match: {curie}"

    def test_pattern_rejects_invalid_curies(self):
        """Test regex pattern rejects invalid CURIEs."""
        invalid = [
            "7157",
            "NCBIGene:",
            "NCBIGene:ABC",
            "HGNC:11998",
            "ncbigene:7157",  # Wrong case
            "NCBIGene:7157a",
            "NCBIGene: 7157",  # Space
        ]

        for curie in invalid:
            assert not NCBI_GENE_CURIE_PATTERN.match(curie), f"Should not match: {curie}"
