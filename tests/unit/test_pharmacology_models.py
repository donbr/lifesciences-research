"""Unit tests for pharmacology models (Ligand, Target, SearchCandidates).

Tests IUPHAR CURIE validation, cross-reference mapping, field validation,
and model serialization for both ligand and target entities.
"""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.gene import CrossReferences
from lifesciences_mcp.models.pharmacology import (
    IUPHAR_CURIE_PATTERN,
    Ligand,
    LigandSearchCandidate,
    Target,
    TargetSearchCandidate,
)

# =============================================================================
# T071-T072: IUPHAR CURIE Pattern Validation
# =============================================================================


def test_iuphar_curie_pattern_valid_formats():
    """Test IUPHAR CURIE pattern accepts valid formats."""
    valid_curies = [
        "IUPHAR:1",
        "IUPHAR:123",
        "IUPHAR:2713",
        "IUPHAR:9999999",
    ]
    for curie in valid_curies:
        assert IUPHAR_CURIE_PATTERN.match(curie), f"Should match: {curie}"


def test_iuphar_curie_pattern_invalid_formats():
    """Test IUPHAR CURIE pattern rejects invalid formats."""
    invalid_curies = [
        "IUPHAR:",  # Missing ID
        "IUPHAR",  # Missing colon and ID
        "iuphar:123",  # Lowercase prefix
        "IUPHAR:ABC",  # Non-numeric ID
        "IUPHAR:12.34",  # Decimal ID
        "CHEMBL:123",  # Wrong prefix
        "123",  # Missing prefix
        "IUPHAR: 123",  # Space before ID
        "IUPHAR:123 ",  # Trailing space
    ]
    for curie in invalid_curies:
        assert not IUPHAR_CURIE_PATTERN.match(curie), f"Should NOT match: {curie}"


# =============================================================================
# T073-T074: LigandSearchCandidate Tests
# =============================================================================


def test_ligand_search_candidate_field_validation():
    """Test LigandSearchCandidate field validation."""
    # Valid candidate
    candidate = LigandSearchCandidate(
        id="IUPHAR:2713",
        name="ibuprofen",
        type="Synthetic organic",
        approved=True,
        score=0.95,
    )
    assert candidate.id == "IUPHAR:2713"
    assert candidate.name == "ibuprofen"
    assert candidate.approved is True
    assert candidate.score == 0.95


def test_ligand_search_candidate_score_bounds():
    """Test LigandSearchCandidate score bounds (0.0-1.0)."""
    # Valid scores
    LigandSearchCandidate(id="IUPHAR:1", name="test", type="drug", score=0.0)  # Min valid
    LigandSearchCandidate(id="IUPHAR:1", name="test", type="drug", score=1.0)  # Max valid
    LigandSearchCandidate(id="IUPHAR:1", name="test", type="drug", score=0.5)  # Mid valid

    # Invalid scores
    with pytest.raises(ValidationError):
        LigandSearchCandidate(id="IUPHAR:1", name="test", type="drug", score=-0.1)  # Below min
    with pytest.raises(ValidationError):
        LigandSearchCandidate(id="IUPHAR:1", name="test", type="drug", score=1.1)  # Above max


# =============================================================================
# T075-T078: Ligand Model Tests
# =============================================================================


def test_ligand_field_validation():
    """Test Ligand field validation."""
    ligand = Ligand(
        id="IUPHAR:2713",
        ligand_id=2713,
        name="ibuprofen",
        approved_name="ibuprofen",
        type="Synthetic organic",
        abbreviation="IBU",
        approved=True,
        approval_source="FDA (1974)",
        who_essential=True,
        withdrawn=False,
        synonyms=["Advil", "Motrin"],
        cross_references=CrossReferences(chembl="521", drugbank="DB01050"),
    )
    assert ligand.id == "IUPHAR:2713"
    assert ligand.ligand_id == 2713
    assert ligand.name == "ibuprofen"
    assert ligand.approved is True
    assert len(ligand.synonyms or []) == 2


def test_ligand_cross_references_mapping():
    """Test Ligand cross_references field mapping."""
    ligand = Ligand(
        id="IUPHAR:2713",
        ligand_id=2713,
        name="ibuprofen",
        type="Synthetic organic",
        cross_references=CrossReferences(chembl="521", drugbank="DB01050", pubchem_compound="3672"),
    )
    assert ligand.cross_references.chembl == "521"
    assert ligand.cross_references.drugbank == "DB01050"
    assert ligand.cross_references.pubchem_compound == "3672"


def test_ligand_to_search_candidate_conversion():
    """Test Ligand.to_search_candidate() method."""
    ligand = Ligand(
        id="IUPHAR:2713",
        ligand_id=2713,
        name="ibuprofen",
        type="Synthetic organic",
        approved=True,
    )
    candidate = ligand.to_search_candidate(score=0.85)

    assert isinstance(candidate, LigandSearchCandidate)
    assert candidate.id == ligand.id
    assert candidate.name == ligand.name
    assert candidate.type == ligand.type
    assert candidate.approved == ligand.approved
    assert candidate.score == 0.85


def test_ligand_model_dump_exclude_none():
    """Test Ligand.model_dump() excludes None values."""
    ligand = Ligand(
        id="IUPHAR:2713",
        ligand_id=2713,
        name="ibuprofen",
        type="Synthetic organic",
        # Optional fields left as None
        approved_name=None,
        abbreviation=None,
        approval_source=None,
        who_essential=None,
        withdrawn=None,
        synonyms=None,
    )
    dumped = ligand.model_dump()

    # Required fields present
    assert "id" in dumped
    assert "name" in dumped
    assert "type" in dumped

    # None fields excluded (omit-if-null pattern)
    assert "approved_name" not in dumped
    assert "abbreviation" not in dumped
    assert "approval_source" not in dumped
    assert "who_essential" not in dumped
    assert "withdrawn" not in dumped
    assert "synonyms" not in dumped


# =============================================================================
# T079-T080: TargetSearchCandidate Tests
# =============================================================================


def test_target_search_candidate_field_validation():
    """Test TargetSearchCandidate field validation."""
    candidate = TargetSearchCandidate(
        id="IUPHAR:215",
        name="D2 receptor",
        family="Dopamine receptors",
        type="GPCR",
        score=0.90,
    )
    assert candidate.id == "IUPHAR:215"
    assert candidate.name == "D2 receptor"
    assert candidate.family == "Dopamine receptors"
    assert candidate.score == 0.90


def test_target_search_candidate_score_bounds():
    """Test TargetSearchCandidate score bounds (0.0-1.0)."""
    # Valid scores
    TargetSearchCandidate(id="IUPHAR:1", name="test", family="test", type="GPCR", score=0.0)
    TargetSearchCandidate(id="IUPHAR:1", name="test", family="test", type="GPCR", score=1.0)

    # Invalid scores
    with pytest.raises(ValidationError):
        TargetSearchCandidate(id="IUPHAR:1", name="test", family="test", type="GPCR", score=-0.1)
    with pytest.raises(ValidationError):
        TargetSearchCandidate(id="IUPHAR:1", name="test", family="test", type="GPCR", score=1.5)


# =============================================================================
# T081-T085: Target Model Tests
# =============================================================================


def test_target_field_validation():
    """Test Target field validation."""
    target = Target(
        id="IUPHAR:215",
        target_id=215,
        name="D2 receptor",
        target_family="Dopamine receptors",
        family_ids=[78],
        species="Homo sapiens",
        gene_symbol="DRD2",
        cross_references=CrossReferences(
            uniprot=["P14416"], ensembl_gene="ENSG00000149295", entrez="1813"
        ),
    )
    assert target.id == "IUPHAR:215"
    assert target.target_id == 215
    assert target.gene_symbol == "DRD2"
    assert target.species == "Homo sapiens"


def test_target_html_stripping():
    """Test Target HTML stripping in name field."""
    # GtoPdb returns names like "D<sub>2</sub> receptor"
    target = Target(
        id="IUPHAR:215",
        target_id=215,
        name="D<sub>2</sub> receptor",
        target_family="Dopamine receptors",
    )
    # HTML tags should be stripped automatically by validator
    assert target.name == "D2 receptor"
    assert "<sub>" not in target.name
    assert "</sub>" not in target.name


def test_target_cross_references_mapping():
    """Test Target cross_references field mapping."""
    target = Target(
        id="IUPHAR:215",
        target_id=215,
        name="D2 receptor",
        target_family="Dopamine receptors",
        cross_references=CrossReferences(
            uniprot=["P14416"],
            ensembl_gene="ENSG00000149295",
            entrez="1813",
            hgnc="HGNC:3023",
            omim="126450",
        ),
    )
    assert target.cross_references.uniprot == ["P14416"]
    assert target.cross_references.ensembl_gene == "ENSG00000149295"
    assert target.cross_references.entrez == "1813"
    assert target.cross_references.hgnc == "HGNC:3023"


def test_target_to_search_candidate_conversion():
    """Test Target.to_search_candidate() method."""
    target = Target(
        id="IUPHAR:215",
        target_id=215,
        name="D2 receptor",
        target_family="Dopamine receptors",
    )
    candidate = target.to_search_candidate(score=0.75)

    assert isinstance(candidate, TargetSearchCandidate)
    assert candidate.id == target.id
    assert candidate.name == target.name
    assert candidate.family == target.target_family
    assert candidate.type == target.target_family
    assert candidate.score == 0.75


def test_target_model_dump_exclude_none():
    """Test Target.model_dump() excludes None values."""
    target = Target(
        id="IUPHAR:215",
        target_id=215,
        name="D2 receptor",
        target_family="Dopamine receptors",
        # Optional fields left as None
        family_ids=None,
        gene_symbol=None,
    )
    dumped = target.model_dump()

    # Required fields present
    assert "id" in dumped
    assert "name" in dumped
    assert "target_family" in dumped
    assert "species" in dumped  # Has default value

    # None fields excluded (omit-if-null pattern)
    assert "family_ids" not in dumped
    assert "gene_symbol" not in dumped
