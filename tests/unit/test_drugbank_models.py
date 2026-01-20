"""Unit tests for DrugBank Pydantic models."""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.drug import (
    DRUGBANK_CURIE_PATTERN,
    Drug,
    DrugCrossReferences,
    DrugSearchCandidate,
)

pytestmark = [pytest.mark.unit, pytest.mark.drugbank]


class TestDrugBankCuriePattern:
    """Test DrugBank CURIE validation pattern."""

    def test_valid_curie_format(self):
        """Test valid DrugBank CURIE formats."""
        valid_ids = [
            "DrugBank:DB00945",  # Aspirin
            "DrugBank:DB00001",  # First entry
            "DrugBank:DB99999",  # High number
            "DrugBank:DB12345",  # Mid-range
        ]
        for drug_id in valid_ids:
            assert DRUGBANK_CURIE_PATTERN.match(drug_id), f"{drug_id} should be valid"

    def test_invalid_curie_formats(self):
        """Test invalid DrugBank CURIE formats."""
        invalid_ids = [
            "DB00945",  # Missing prefix
            "DrugBank:00945",  # Missing DB
            "DrugBank:DB0094",  # Too short (4 digits)
            "DrugBank:DB009455",  # Too long (6 digits)
            "drugbank:DB00945",  # Wrong case
            "DrugBank:db00945",  # Wrong case in ID
            "DRUGBANK:DB00945",  # Wrong case in prefix
            "",  # Empty
            "DrugBank:",  # No ID
        ]
        for drug_id in invalid_ids:
            assert not DRUGBANK_CURIE_PATTERN.match(drug_id), f"{drug_id} should be invalid"


class TestDrugCrossReferences:
    """Test DrugCrossReferences model."""

    def test_empty_cross_references(self):
        """Test creating empty cross-references."""
        refs = DrugCrossReferences()
        dumped = refs.model_dump()
        assert dumped == {}  # All None values excluded

    def test_partial_cross_references(self):
        """Test creating partial cross-references."""
        refs = DrugCrossReferences(
            drugbank="DrugBank:DB00945",
            chembl="CHEMBL:25",
        )
        dumped = refs.model_dump()
        assert dumped == {
            "drugbank": "DrugBank:DB00945",
            "chembl": "CHEMBL:25",
        }
        assert "uniprot" not in dumped
        assert "kegg" not in dumped

    def test_full_cross_references(self):
        """Test creating full cross-references."""
        refs = DrugCrossReferences(
            drugbank="DrugBank:DB00945",
            chembl="CHEMBL:25",
            uniprot=["UniProtKB:P23219", "UniProtKB:P35354"],
            kegg="D00109",
            pubchem_compound="2244",
            pdb=["1PTH", "2PTH"],
        )
        dumped = refs.model_dump()
        assert dumped["drugbank"] == "DrugBank:DB00945"
        assert dumped["chembl"] == "CHEMBL:25"
        assert len(dumped["uniprot"]) == 2
        assert dumped["kegg"] == "D00109"
        assert dumped["pubchem_compound"] == "2244"
        assert len(dumped["pdb"]) == 2

    def test_omit_empty_values(self):
        """Test that empty strings and lists are omitted."""
        refs = DrugCrossReferences(
            drugbank="DrugBank:DB00945",
            chembl="",  # Empty string
            uniprot=[],  # Empty list
        )
        dumped = refs.model_dump()
        assert "drugbank" in dumped
        assert "chembl" not in dumped
        assert "uniprot" not in dumped


class TestDrugSearchCandidate:
    """Test DrugSearchCandidate model."""

    def test_valid_search_candidate(self):
        """Test creating a valid search candidate."""
        candidate = DrugSearchCandidate(
            id="DrugBank:DB00945",
            name="Aspirin",
            drug_type="Small molecule",
            categories=["Analgesics", "Antipyretics"],
            score=0.95,
        )
        assert candidate.id == "DrugBank:DB00945"
        assert candidate.name == "Aspirin"
        assert candidate.drug_type == "Small molecule"
        assert len(candidate.categories) == 2
        assert candidate.score == 0.95

    def test_minimal_search_candidate(self):
        """Test creating minimal search candidate."""
        candidate = DrugSearchCandidate(
            id="DrugBank:DB00945",
            name="Aspirin",
            score=1.0,
        )
        assert candidate.id == "DrugBank:DB00945"
        assert candidate.name == "Aspirin"
        assert candidate.drug_type is None
        assert candidate.categories is None
        assert candidate.score == 1.0

    def test_invalid_curie_rejected(self):
        """Test that invalid CURIE is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DrugSearchCandidate(
                id="DB00945",  # Missing prefix
                name="Aspirin",
                score=1.0,
            )
        # Pydantic pattern validation error
        assert "string_pattern_mismatch" in str(exc_info.value) or "DrugBank" in str(exc_info.value)

    def test_score_bounds(self):
        """Test score must be between 0 and 1."""
        # Valid bounds
        DrugSearchCandidate(id="DrugBank:DB00945", name="Test", score=0.0)
        DrugSearchCandidate(id="DrugBank:DB00945", name="Test", score=1.0)

        # Invalid - too high
        with pytest.raises(ValidationError):
            DrugSearchCandidate(id="DrugBank:DB00945", name="Test", score=1.5)

        # Invalid - negative
        with pytest.raises(ValidationError):
            DrugSearchCandidate(id="DrugBank:DB00945", name="Test", score=-0.1)


class TestDrug:
    """Test Drug model."""

    def test_valid_drug(self):
        """Test creating a valid drug."""
        drug = Drug(
            id="DrugBank:DB00945",
            name="Aspirin",
            drug_type="Small molecule",
            categories=["Analgesics", "Antipyretics"],
            description="The prototypical analgesic.",
            indication="For mild to moderate pain.",
            mechanism_of_action="Inhibits COX enzymes.",
            half_life="15-20 minutes",
            cross_references=DrugCrossReferences(
                drugbank="DrugBank:DB00945",
                chembl="CHEMBL:25",
            ),
        )
        assert drug.id == "DrugBank:DB00945"
        assert drug.name == "Aspirin"
        assert drug.cross_references.drugbank == "DrugBank:DB00945"

    def test_minimal_drug(self):
        """Test creating minimal drug."""
        drug = Drug(
            id="DrugBank:DB00945",
            name="Aspirin",
        )
        assert drug.id == "DrugBank:DB00945"
        assert drug.name == "Aspirin"
        assert drug.drug_type is None
        assert drug.description is None

    def test_to_search_candidate(self):
        """Test converting Drug to DrugSearchCandidate."""
        drug = Drug(
            id="DrugBank:DB00945",
            name="Aspirin",
            drug_type="Small molecule",
            categories=["Analgesics"],
        )
        candidate = drug.to_search_candidate(score=0.85)
        assert candidate.id == "DrugBank:DB00945"
        assert candidate.name == "Aspirin"
        assert candidate.drug_type == "Small molecule"
        assert candidate.score == 0.85

    def test_to_slim_dict(self):
        """Test slim mode representation."""
        drug = Drug(
            id="DrugBank:DB00945",
            name="Aspirin",
            drug_type="Small molecule",
            categories=["Analgesics", "Antipyretics"],
            description="The prototypical analgesic.",
            indication="For mild to moderate pain.",
            mechanism_of_action="Inhibits COX enzymes.",
        )
        slim = drug.to_slim_dict()
        assert slim == {
            "id": "DrugBank:DB00945",
            "name": "Aspirin",
            "drug_type": "Small molecule",
            "categories": ["Analgesics", "Antipyretics"],
        }
        # Full fields not in slim
        assert "description" not in slim
        assert "indication" not in slim
        assert "mechanism_of_action" not in slim

    def test_invalid_curie_rejected(self):
        """Test that invalid CURIE is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Drug(
                id="DB00945",  # Missing prefix
                name="Aspirin",
            )
        # Pydantic pattern validation error
        assert "string_pattern_mismatch" in str(exc_info.value) or "DrugBank" in str(exc_info.value)
