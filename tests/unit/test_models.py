"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorEnvelope,
    PaginationEnvelope,
)
from lifesciences_mcp.models.cross_references import CrossReferences
from lifesciences_mcp.models.gene import Gene, SearchCandidate


class TestSearchCandidate:
    """Tests for SearchCandidate model."""

    def test_valid_candidate(self):
        """Test creating a valid search candidate."""
        candidate = SearchCandidate(
            id="HGNC:1100",
            symbol="BRCA1",
            name="BRCA1 DNA repair associated",
            score=1.0,
        )
        assert candidate.id == "HGNC:1100"
        assert candidate.symbol == "BRCA1"
        assert candidate.score == 1.0

    def test_invalid_curie_format(self):
        """Test that invalid CURIE format is rejected."""
        with pytest.raises(ValidationError):
            SearchCandidate(
                id="BRCA1",  # Missing HGNC: prefix
                symbol="BRCA1",
                name="BRCA1 DNA repair associated",
                score=1.0,
            )

    def test_score_bounds(self):
        """Test that score must be between 0 and 1."""
        with pytest.raises(ValidationError):
            SearchCandidate(
                id="HGNC:1100",
                symbol="BRCA1",
                name="BRCA1 DNA repair associated",
                score=1.5,  # Out of bounds
            )


class TestGene:
    """Tests for Gene model."""

    def test_valid_gene(self, sample_gene: Gene):
        """Test creating a valid gene."""
        assert sample_gene.id == "HGNC:1100"
        assert sample_gene.symbol == "BRCA1"
        assert sample_gene.status == "Approved"
        assert sample_gene.cross_references.ensembl_gene == "ENSG00000012048"

    def test_invalid_status(self):
        """Test that invalid status is rejected."""
        with pytest.raises(ValidationError):
            Gene(
                id="HGNC:1100",
                symbol="BRCA1",
                name="BRCA1 DNA repair associated",
                status="Invalid",  # Not a valid status
            )

    def test_to_search_candidate(self, sample_gene: Gene):
        """Test converting Gene to SearchCandidate."""
        candidate = sample_gene.to_search_candidate(score=0.95)
        assert candidate.id == sample_gene.id
        assert candidate.symbol == sample_gene.symbol
        assert candidate.score == 0.95


class TestCrossReferences:
    """Tests for CrossReferences model."""

    def test_omit_empty_values(self):
        """Test that empty values are omitted."""
        refs = CrossReferences(
            ensembl_gene="ENSG00000012048",
            uniprot=[],  # Should be omitted
            entrez="",  # Should be omitted
        )
        data = refs.model_dump()
        assert "ensembl_gene" in data
        assert "uniprot" not in data
        assert "entrez" not in data

    def test_valid_cross_references(self):
        """Test creating valid cross references."""
        refs = CrossReferences(
            ensembl_gene="ENSG00000012048",
            uniprot=["P38398"],
            entrez="672",
        )
        assert refs.ensembl_gene == "ENSG00000012048"
        assert refs.uniprot == ["P38398"]


class TestErrorEnvelope:
    """Tests for ErrorEnvelope model."""

    def test_unresolved_entity(self):
        """Test UNRESOLVED_ENTITY error creation."""
        error = ErrorEnvelope.unresolved_entity("BRCA1")
        assert error.success is False
        assert error.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert "BRCA1" in error.error.message
        assert "search_genes" in error.error.recovery_hint

    def test_entity_not_found(self):
        """Test ENTITY_NOT_FOUND error creation."""
        error = ErrorEnvelope.entity_not_found("HGNC:99999")
        assert error.error.code == ErrorCode.ENTITY_NOT_FOUND
        assert "HGNC:99999" in error.error.message

    def test_rate_limited(self):
        """Test RATE_LIMITED error creation."""
        error = ErrorEnvelope.rate_limited(retry_after=30)
        assert error.error.code == ErrorCode.RATE_LIMITED
        assert "30" in error.error.recovery_hint

    def test_upstream_error(self):
        """Test UPSTREAM_ERROR creation."""
        error = ErrorEnvelope.upstream_error(502, "Bad Gateway")
        assert error.error.code == ErrorCode.UPSTREAM_ERROR
        assert "502" in error.error.message


class TestPaginationEnvelope:
    """Tests for PaginationEnvelope model."""

    def test_create_envelope(self):
        """Test creating a pagination envelope."""
        items = [
            SearchCandidate(
                id="HGNC:1100",
                symbol="BRCA1",
                name="BRCA1 DNA repair associated",
                score=1.0,
            )
        ]
        envelope = PaginationEnvelope.create(
            items=items,
            cursor="abc123",
            total_count=100,
            page_size=50,
        )
        assert len(envelope.items) == 1
        assert envelope.pagination.cursor == "abc123"
        assert envelope.pagination.total_count == 100
        assert envelope.pagination.page_size == 50

    def test_empty_envelope(self):
        """Test creating an empty pagination envelope."""
        envelope = PaginationEnvelope.create(
            items=[],
            total_count=0,
            page_size=50,
        )
        assert len(envelope.items) == 0
        assert envelope.pagination.cursor is None
