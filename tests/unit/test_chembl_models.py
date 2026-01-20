"""Unit tests for ChEMBL compound models.

Tests for:
- T012: CompoundSearchCandidate validation
- T017: Compound model validation
- T026: Cross-reference mapping
"""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.compound import (
    CHEMBL_CURIE_PATTERN,
    Compound,
    CompoundSearchCandidate,
)

pytestmark = [pytest.mark.unit, pytest.mark.chembl]


class TestCompoundSearchCandidate:
    """Tests for CompoundSearchCandidate model (T012: US1)."""

    def test_valid_curie_format(self) -> None:
        """Test valid CURIE format is accepted."""
        candidate = CompoundSearchCandidate(
            id="CHEMBL:25",
            name="Aspirin",
            molecular_formula="C9H8O4",
            score=1.0,
        )
        assert candidate.id == "CHEMBL:25"
        assert candidate.name == "Aspirin"
        assert candidate.molecular_formula == "C9H8O4"
        assert candidate.score == 1.0

    def test_valid_curie_with_large_id(self) -> None:
        """Test valid CURIE with large numeric ID."""
        candidate = CompoundSearchCandidate(
            id="CHEMBL:1201583",
            name="Acetylsalicylic acid lysinate",
            score=0.85,
        )
        assert candidate.id == "CHEMBL:1201583"

    def test_invalid_curie_missing_prefix(self) -> None:
        """Test that CURIE without prefix is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompoundSearchCandidate(
                id="25",
                name="Aspirin",
                score=1.0,
            )
        assert "Invalid ChEMBL CURIE format" in str(exc_info.value)

    def test_invalid_curie_missing_colon(self) -> None:
        """Test that CURIE without colon is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompoundSearchCandidate(
                id="CHEMBL25",
                name="Aspirin",
                score=1.0,
            )
        assert "Invalid ChEMBL CURIE format" in str(exc_info.value)

    def test_invalid_curie_lowercase_prefix(self) -> None:
        """Test that lowercase prefix is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompoundSearchCandidate(
                id="chembl:25",
                name="Aspirin",
                score=1.0,
            )
        assert "Invalid ChEMBL CURIE format" in str(exc_info.value)

    def test_invalid_curie_non_numeric_id(self) -> None:
        """Test that non-numeric ID is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompoundSearchCandidate(
                id="CHEMBL:ABC",
                name="Unknown",
                score=1.0,
            )
        assert "Invalid ChEMBL CURIE format" in str(exc_info.value)

    def test_score_bounds_valid(self) -> None:
        """Test valid score values are accepted."""
        # Minimum valid score
        candidate_min = CompoundSearchCandidate(
            id="CHEMBL:25",
            name="Aspirin",
            score=0.0,
        )
        assert candidate_min.score == 0.0

        # Maximum valid score
        candidate_max = CompoundSearchCandidate(
            id="CHEMBL:25",
            name="Aspirin",
            score=1.0,
        )
        assert candidate_max.score == 1.0

    def test_score_bounds_invalid_above(self) -> None:
        """Test that score > 1.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompoundSearchCandidate(
                id="CHEMBL:25",
                name="Aspirin",
                score=1.5,
            )
        assert "less than or equal to 1" in str(exc_info.value)

    def test_score_bounds_invalid_below(self) -> None:
        """Test that score < 0.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompoundSearchCandidate(
                id="CHEMBL:25",
                name="Aspirin",
                score=-0.1,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_optional_fields(self) -> None:
        """Test that optional fields can be None."""
        candidate = CompoundSearchCandidate(
            id="CHEMBL:25",
            name=None,
            molecular_formula=None,
            score=1.0,
        )
        assert candidate.name is None
        assert candidate.molecular_formula is None


class TestCompound:
    """Tests for Compound model (T017: US2)."""

    def test_full_mode_includes_all_fields(self) -> None:
        """Test full mode includes all fields."""
        compound = Compound(
            id="CHEMBL:25",
            name="Aspirin",
            molecular_formula="C9H8O4",
            molecular_weight=180.16,
            smiles="CC(=O)Oc1ccccc1C(=O)O",
            inchi="InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
            canonical_name="2-acetoxybenzoic acid",
            synonyms=["Acetylsalicylic acid", "ASA"],
            cross_references={
                "uniprot": ["UniProtKB:P23219"],
                "pdb": ["1PTY"],
            },
        )
        dump = compound.model_dump()
        assert dump["id"] == "CHEMBL:25"
        assert dump["name"] == "Aspirin"
        assert dump["molecular_formula"] == "C9H8O4"
        assert dump["molecular_weight"] == 180.16
        assert dump["smiles"] == "CC(=O)Oc1ccccc1C(=O)O"
        assert dump["inchi"] is not None
        assert dump["canonical_name"] == "2-acetoxybenzoic acid"
        assert dump["synonyms"] == ["Acetylsalicylic acid", "ASA"]
        assert dump["cross_references"]["uniprot"] == ["UniProtKB:P23219"]

    def test_slim_mode_excludes_verbose_fields(self) -> None:
        """Test slim mode excludes cross_references and synonyms."""
        compound = Compound(
            id="CHEMBL:25",
            name="Aspirin",
            molecular_formula="C9H8O4",
            molecular_weight=180.16,
            smiles="CC(=O)Oc1ccccc1C(=O)O",
            synonyms=["Acetylsalicylic acid", "ASA"],
            cross_references={
                "uniprot": ["UniProtKB:P23219"],
                "pdb": ["1PTY"],
            },
        )
        slim = compound.to_slim()
        assert slim["id"] == "CHEMBL:25"
        assert slim["name"] == "Aspirin"
        assert slim["molecular_formula"] == "C9H8O4"
        assert "molecular_weight" not in slim
        assert "smiles" not in slim
        assert "synonyms" not in slim
        assert "cross_references" not in slim

    def test_cross_references_omit_if_null_pattern(self) -> None:
        """Test that missing cross_references use empty dict (not null keys)."""
        compound = Compound(
            id="CHEMBL:25",
            name="Aspirin",
        )
        dump = compound.model_dump()
        # cross_references should be empty dict, not have null values
        assert dump["cross_references"] == {}
        # No null values should exist in cross_references
        for key, value in dump["cross_references"].items():
            assert value is not None, f"Key {key} should not be null"

    def test_curie_validation_in_compound(self) -> None:
        """Test CURIE validation applies to Compound model too."""
        with pytest.raises(ValidationError):
            Compound(id="CHEMBL25", name="Invalid")  # Missing colon

    def test_default_empty_lists(self) -> None:
        """Test that synonyms and cross_references default to empty."""
        compound = Compound(id="CHEMBL:25")
        assert compound.synonyms == []
        assert compound.cross_references == {}


class TestCrossReferenceMapping:
    """Tests for cross-reference transformation (T026: US3)."""

    def test_uniprot_xref_transformation(self) -> None:
        """Test UniProt cross-reference adds UniProtKB prefix."""
        # The transformation is done in ChEMBLClient._normalize_xref_id
        # Here we just verify the expected output format
        compound = Compound(
            id="CHEMBL:25",
            cross_references={
                "uniprot": ["UniProtKB:P23219"],
            },
        )
        assert compound.cross_references["uniprot"][0].startswith("UniProtKB:")

    def test_drugbank_xref_transformation(self) -> None:
        """Test DrugBank cross-reference adds DB: prefix."""
        compound = Compound(
            id="CHEMBL:25",
            cross_references={
                "drugbank": ["DB:00945"],
            },
        )
        assert compound.cross_references["drugbank"][0].startswith("DB:")

    def test_omit_if_null_pattern_enforcement(self) -> None:
        """Test that missing xrefs are omitted entirely (not null)."""
        # Compound with only UniProt xref - no pdb, drugbank, etc.
        compound = Compound(
            id="CHEMBL:25",
            cross_references={
                "uniprot": ["UniProtKB:P23219"],
            },
        )
        xrefs = compound.cross_references
        # Only uniprot key should exist
        assert "uniprot" in xrefs
        # Other keys should not exist (not null)
        assert "pdb" not in xrefs
        assert "drugbank" not in xrefs
        assert "pubchem_compound" not in xrefs


class TestCuriePattern:
    """Tests for CURIE regex pattern."""

    def test_valid_curie_patterns(self) -> None:
        """Test valid CURIE patterns match."""
        valid_curies = [
            "CHEMBL:25",
            "CHEMBL:941",
            "CHEMBL:1201583",
            "CHEMBL:1",
            "CHEMBL:99999999",
        ]
        for curie in valid_curies:
            assert CHEMBL_CURIE_PATTERN.match(curie), f"{curie} should be valid"

    def test_invalid_curie_patterns(self) -> None:
        """Test invalid CURIE patterns don't match."""
        invalid_curies = [
            "25",  # No prefix
            "CHEMBL25",  # No colon
            "chembl:25",  # Lowercase
            "CHEMBL:",  # No ID
            "CHEMBL:ABC",  # Non-numeric
            "CHEMBL: 25",  # Space
            "CHEMBL:25 ",  # Trailing space
            " CHEMBL:25",  # Leading space
        ]
        for curie in invalid_curies:
            assert not CHEMBL_CURIE_PATTERN.match(curie), f"{curie} should be invalid"
