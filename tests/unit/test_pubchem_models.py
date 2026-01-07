"""Unit tests for PubChem Pydantic models."""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.pubchem_compound import (
    PubChemCompound,
    PubChemSearchCandidate,
)


class TestPubChemSearchCandidate:
    """Tests for PubChemSearchCandidate model (T055-T057)."""

    def test_search_candidate_model_valid(self) -> None:
        """Test valid PubChemSearchCandidate creation (T055)."""
        candidate = PubChemSearchCandidate(
            id="PubChem:CID2244",
            name="Aspirin",
            molecular_formula="C9H8O4",
            score=1.0,
        )

        assert candidate.id == "PubChem:CID2244"
        assert candidate.name == "Aspirin"
        assert candidate.molecular_formula == "C9H8O4"
        assert candidate.score == 1.0

    def test_search_candidate_curie_validation_valid(self) -> None:
        """Test CURIE validation accepts valid formats (T056)."""
        # Valid formats
        valid_curies = [
            "PubChem:CID2244",
            "PubChem:CID1",
            "PubChem:CID123456789",
        ]

        for curie in valid_curies:
            candidate = PubChemSearchCandidate(
                id=curie,
                score=1.0,
            )
            assert candidate.id == curie

    def test_search_candidate_curie_validation_invalid(self) -> None:
        """Test CURIE validation rejects invalid formats (T056)."""
        # Invalid formats
        invalid_curies = [
            "CID2244",  # Missing prefix
            "2244",  # Bare number
            "PubChem:2244",  # Missing CID
            "pubchem:cid2244",  # Wrong case
            "PubChem:CIDABC",  # Non-numeric CID
        ]

        for curie in invalid_curies:
            with pytest.raises(ValidationError) as exc_info:
                PubChemSearchCandidate(
                    id=curie,
                    score=1.0,
                )
            assert "Invalid PubChem CURIE format" in str(exc_info.value)

    def test_search_candidate_score_bounds_valid(self) -> None:
        """Test score validation accepts valid range (T057)."""
        # Valid scores
        valid_scores = [0.0, 0.1, 0.5, 1.0]

        for score in valid_scores:
            candidate = PubChemSearchCandidate(
                id="PubChem:CID2244",
                score=score,
            )
            assert candidate.score == score

    def test_search_candidate_score_bounds_invalid(self) -> None:
        """Test score validation rejects out-of-bounds values (T057)."""
        # Invalid scores
        invalid_scores = [-0.1, 1.1, 2.0]

        for score in invalid_scores:
            with pytest.raises(ValidationError) as exc_info:
                PubChemSearchCandidate(
                    id="PubChem:CID2244",
                    score=score,
                )
            # Pydantic should complain about ge=0.0 or le=1.0
            assert "greater than or equal to" in str(
                exc_info.value
            ) or "less than or equal to" in str(exc_info.value)

    def test_search_candidate_optional_fields(self) -> None:
        """Test that name and molecular_formula are optional."""
        candidate = PubChemSearchCandidate(
            id="PubChem:CID2244",
            score=0.95,
        )

        assert candidate.id == "PubChem:CID2244"
        assert candidate.name is None
        assert candidate.molecular_formula is None
        assert candidate.score == 0.95

    def test_search_candidate_json_schema_examples(self) -> None:
        """Test that model_config includes examples."""
        schema = PubChemSearchCandidate.model_config
        assert "json_schema_extra" in schema
        assert "examples" in schema["json_schema_extra"]
        examples = schema["json_schema_extra"]["examples"]
        assert len(examples) == 2
        assert examples[0]["id"] == "PubChem:CID2244"
        assert examples[1]["id"] == "PubChem:CID3672"


class TestPubChemCompound:
    """Tests for PubChemCompound model (T067-T076)."""

    def test_compound_model_valid_full(self) -> None:
        """Test valid PubChemCompound creation with all fields (T067)."""
        compound = PubChemCompound(
            id="PubChem:CID2244",
            name="Aspirin",
            iupac_name="2-acetoxybenzoic acid",
            molecular_formula="C9H8O4",
            molecular_weight=180.16,
            canonical_smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
            isomeric_smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
            inchi="InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
            inchikey="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
            synonyms=["acetylsalicylic acid", "ASA", "Ecotrin"],
            cross_references={
                "pubchem_compound": ["2244"],
                "chembl": ["CHEMBL:25"],
                "drugbank": ["DB00945"],
            },
        )

        assert compound.id == "PubChem:CID2244"
        assert compound.name == "Aspirin"
        assert compound.iupac_name == "2-acetoxybenzoic acid"
        assert compound.molecular_formula == "C9H8O4"
        assert compound.molecular_weight == 180.16
        assert compound.canonical_smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
        assert compound.isomeric_smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
        assert compound.inchi.startswith("InChI=1S/C9H8O4")
        assert compound.inchikey == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        assert len(compound.synonyms) == 3
        assert "chembl" in compound.cross_references

    def test_compound_model_minimal(self) -> None:
        """Test PubChemCompound with minimal required fields (T068)."""
        compound = PubChemCompound(
            id="PubChem:CID2244",
        )

        assert compound.id == "PubChem:CID2244"
        assert compound.name is None
        assert compound.iupac_name is None
        assert compound.molecular_formula is None
        assert compound.molecular_weight is None
        assert compound.synonyms == []
        assert compound.cross_references == {}

    def test_compound_curie_validation_valid(self) -> None:
        """Test CURIE validation accepts valid formats (T069)."""
        valid_curies = [
            "PubChem:CID2244",
            "PubChem:CID1",
            "PubChem:CID123456789",
        ]

        for curie in valid_curies:
            compound = PubChemCompound(id=curie)
            assert compound.id == curie

    def test_compound_curie_validation_invalid(self) -> None:
        """Test CURIE validation rejects invalid formats (T070)."""
        invalid_curies = [
            "CID2244",
            "2244",
            "PubChem:2244",
            "pubchem:cid2244",
            "PubChem:CIDABC",
        ]

        for curie in invalid_curies:
            with pytest.raises(ValidationError) as exc_info:
                PubChemCompound(id=curie)
            assert "Invalid PubChem CURIE format" in str(exc_info.value)

    def test_compound_to_slim(self) -> None:
        """Test to_slim() method returns minimal fields (T071)."""
        compound = PubChemCompound(
            id="PubChem:CID2244",
            name="Aspirin",
            iupac_name="2-acetoxybenzoic acid",
            molecular_formula="C9H8O4",
            molecular_weight=180.16,
            canonical_smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
            synonyms=["acetylsalicylic acid"],
            cross_references={"chembl": ["CHEMBL:25"]},
        )

        slim = compound.to_slim()

        # Should only have 3 keys
        assert len(slim) == 3
        assert slim["id"] == "PubChem:CID2244"
        assert slim["name"] == "Aspirin"
        assert slim["molecular_formula"] == "C9H8O4"

        # Should not include other fields
        assert "iupac_name" not in slim
        assert "molecular_weight" not in slim
        assert "canonical_smiles" not in slim
        assert "synonyms" not in slim
        assert "cross_references" not in slim

    def test_compound_cross_references_omit_if_null(self) -> None:
        """Test that cross_references can be empty (omit-if-null) (T072)."""
        compound = PubChemCompound(
            id="PubChem:CID2244",
            name="Aspirin",
        )

        # Empty cross_references should be valid
        assert compound.cross_references == {}

        # Can serialize to dict without cross_references key having null values
        as_dict = compound.model_dump(exclude_none=True)
        assert "cross_references" in as_dict
        assert as_dict["cross_references"] == {}

    def test_compound_synonyms_list(self) -> None:
        """Test that synonyms is a list (T073)."""
        compound = PubChemCompound(
            id="PubChem:CID2244",
            synonyms=["aspirin", "acetylsalicylic acid", "ASA"],
        )

        assert isinstance(compound.synonyms, list)
        assert len(compound.synonyms) == 3
        assert "aspirin" in compound.synonyms

    def test_compound_molecular_weight_type(self) -> None:
        """Test that molecular_weight is a float (T074)."""
        compound = PubChemCompound(
            id="PubChem:CID2244",
            molecular_weight=180.16,
        )

        assert isinstance(compound.molecular_weight, float)
        assert compound.molecular_weight == 180.16

    def test_compound_json_schema_examples(self) -> None:
        """Test that model_config includes examples (T075)."""
        schema = PubChemCompound.model_config
        assert "json_schema_extra" in schema
        assert "examples" in schema["json_schema_extra"]
        examples = schema["json_schema_extra"]["examples"]
        assert len(examples) == 1
        assert examples[0]["id"] == "PubChem:CID2244"
        assert examples[0]["name"] == "Aspirin"
        assert "cross_references" in examples[0]

    def test_compound_optional_fields_none(self) -> None:
        """Test that optional fields can be None (T076)."""
        compound = PubChemCompound(
            id="PubChem:CID2244",
            name=None,
            iupac_name=None,
            molecular_formula=None,
            molecular_weight=None,
            canonical_smiles=None,
            isomeric_smiles=None,
            inchi=None,
            inchikey=None,
        )

        assert compound.name is None
        assert compound.iupac_name is None
        assert compound.molecular_formula is None
        assert compound.molecular_weight is None
        assert compound.canonical_smiles is None
        assert compound.isomeric_smiles is None
        assert compound.inchi is None
        assert compound.inchikey is None
