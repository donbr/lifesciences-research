"""Unit tests for WikiPathways Pydantic models.

Run with: pytest tests/unit/test_wikipathways_models.py -v
"""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models import (
    ComponentCounts,
    DataNode,
    Pathway,
    PathwayComponents,
    PathwayInteraction,
    PathwaySearchCandidate,
    RevisionMetadata,
)

pytestmark = [pytest.mark.unit, pytest.mark.wikipathways]


class TestRevisionMetadata:
    """Tests for RevisionMetadata model."""

    def test_revision_metadata_valid(self):
        """Test valid RevisionMetadata creation."""
        metadata = RevisionMetadata(
            version="141823",
            last_modified="2024-11-15T10:30:00Z",
            curators=["AlexanderPico", "MaintBot"],
        )
        assert metadata.version == "141823"
        assert metadata.last_modified == "2024-11-15T10:30:00Z"
        assert len(metadata.curators) == 2

    def test_revision_metadata_minimal(self):
        """Test RevisionMetadata with minimal fields."""
        metadata = RevisionMetadata(version="141823")
        assert metadata.version == "141823"
        assert metadata.last_modified is None
        assert metadata.curators == []


class TestComponentCounts:
    """Tests for ComponentCounts model."""

    def test_component_counts_default(self):
        """Test ComponentCounts with default values."""
        counts = ComponentCounts()
        assert counts.gene_count == 0
        assert counts.protein_count == 0
        assert counts.metabolite_count == 0
        assert counts.interaction_count == 0

    def test_component_counts_specified(self):
        """Test ComponentCounts with specified values."""
        counts = ComponentCounts(
            gene_count=47,
            protein_count=52,
            metabolite_count=23,
            interaction_count=89,
        )
        assert counts.gene_count == 47
        assert counts.protein_count == 52


class TestPathwaySearchCandidate:
    """Tests for PathwaySearchCandidate model."""

    def test_pathway_search_candidate_valid(self):
        """Test valid PathwaySearchCandidate creation."""
        candidate = PathwaySearchCandidate(
            id="WP:WP534",
            title="Glycolysis and gluconeogenesis",
            organism="Homo sapiens",
            description="Glycolysis is the metabolic pathway...",
            score=0.95,
        )
        assert candidate.id == "WP:WP534"
        assert candidate.score == 0.95

    def test_pathway_search_candidate_invalid_id_format(self):
        """Test PathwaySearchCandidate with invalid ID format."""
        with pytest.raises(ValidationError):
            PathwaySearchCandidate(
                id="WP534",  # Missing WP: prefix
                title="Test",
                organism="Homo sapiens",
                description="Test",
                score=0.9,
            )

    def test_pathway_search_candidate_score_bounds(self):
        """Test PathwaySearchCandidate score validation."""
        with pytest.raises(ValidationError):
            PathwaySearchCandidate(
                id="WP:WP534",
                title="Test",
                organism="Homo sapiens",
                description="Test",
                score=1.5,  # Invalid: > 1.0
            )


class TestPathway:
    """Tests for Pathway model."""

    def test_pathway_valid(self):
        """Test valid Pathway creation."""
        pathway = Pathway(
            id="WP:WP534",
            title="Glycolysis and gluconeogenesis",
            organism="Homo sapiens",
            description="Glycolysis is the metabolic pathway...",
            revision=RevisionMetadata(version="141823"),
            component_counts=ComponentCounts(gene_count=47),
            cross_references={"kegg_pathway": "hsa00010"},
            url="https://classic.wikipathways.org/index.php/Pathway:WP534",
        )
        assert pathway.id == "WP:WP534"
        assert pathway.component_counts.gene_count == 47

    def test_pathway_invalid_id(self):
        """Test Pathway with invalid ID format."""
        with pytest.raises(ValidationError):
            Pathway(
                id="534",  # Invalid format
                title="Test",
                organism="Homo sapiens",
                description="Test",
                revision=RevisionMetadata(version="1"),
                component_counts=ComponentCounts(),
                url="http://test.com",
            )

    def test_pathway_cross_references_omit_if_null(self):
        """Test that cross_references omits null values."""
        pathway = Pathway(
            id="WP:WP534",
            title="Test",
            organism="Homo sapiens",
            description="Test",
            revision=RevisionMetadata(version="1"),
            component_counts=ComponentCounts(),
            cross_references={},  # Empty cross-references
            url="http://test.com",
        )
        assert pathway.cross_references == {}


class TestDataNode:
    """Tests for DataNode model."""

    def test_datanode_gene(self):
        """Test DataNode for gene entity."""
        node = DataNode(
            id="ncbigene:672",
            label="BRCA1",
            type="Gene",
            database="Entrez Gene",
            cross_references={"entrez": "672", "hgnc": "HGNC:1100"},
        )
        assert node.type == "Gene"
        assert node.label == "BRCA1"

    def test_datanode_minimal(self):
        """Test DataNode with minimal fields."""
        node = DataNode(
            id="test:123",
            label="TestGene",
            type="Gene",
            database="Test",
        )
        assert node.cross_references == {}


class TestPathwayInteraction:
    """Tests for Interaction model."""

    def test_interaction_valid(self):
        """Test valid Interaction creation."""
        interaction = PathwayInteraction(
            source="ncbigene:5213",
            target="chebi:17234",
            type="catalysis",
        )
        assert interaction.source == "ncbigene:5213"
        assert interaction.type == "catalysis"


class TestPathwayComponents:
    """Tests for PathwayComponents model."""

    def test_pathway_components_default(self):
        """Test PathwayComponents with default values."""
        components = PathwayComponents()
        assert components.genes == []
        assert components.proteins == []
        assert components.metabolites == []
        assert components.interactions == []

    def test_pathway_components_populated(self):
        """Test PathwayComponents with populated lists."""
        components = PathwayComponents(
            genes=[
                DataNode(
                    id="ncbigene:672",
                    label="BRCA1",
                    type="Gene",
                    database="Entrez Gene",
                )
            ],
            proteins=[],
            metabolites=[],
            interactions=[],
        )
        assert len(components.genes) == 1
        assert components.genes[0].label == "BRCA1"
