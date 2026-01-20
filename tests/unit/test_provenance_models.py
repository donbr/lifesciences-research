"""Unit tests for provenance tracking models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.provenance import BatchProvenance, MCPClaim, Provenance

pytestmark = pytest.mark.unit


class TestProvenance:
    """Tests for Provenance model."""

    def test_valid_provenance(self):
        """Test creating valid provenance metadata."""
        prov = Provenance(
            source="chembl.get_compound",
            timestamp=datetime(2026, 1, 5, 14, 32, 15, tzinfo=timezone.utc),
            curie="CHEMBL:1946170",
            api_version="ChEMBL v33",
            confidence_score=1.0,
        )

        assert prov.source == "chembl.get_compound"
        assert prov.curie == "CHEMBL:1946170"
        assert prov.api_version == "ChEMBL v33"
        assert prov.confidence_score == 1.0

    def test_provenance_without_optional_fields(self):
        """Test provenance with only required fields."""
        prov = Provenance(
            source="hgnc.get_gene",
            timestamp=datetime.now(timezone.utc),
            curie="HGNC:11998",
        )

        assert prov.source == "hgnc.get_gene"
        assert prov.curie == "HGNC:11998"
        assert prov.api_version is None
        assert prov.confidence_score is None

    def test_invalid_source_format(self):
        """Test that invalid source format raises ValidationError."""
        with pytest.raises(ValidationError, match="pattern"):
            Provenance(
                source="invalid-format",  # Should be "server.tool"
                timestamp=datetime.now(timezone.utc),
                curie="CHEMBL:939",
            )

    def test_invalid_curie_format(self):
        """Test that invalid CURIE format raises ValidationError."""
        with pytest.raises(ValidationError, match="pattern"):
            Provenance(
                source="chembl.get_compound",
                timestamp=datetime.now(timezone.utc),
                curie="invalid_curie",  # Missing colon separator
            )

    def test_confidence_score_bounds(self):
        """Test confidence score validation (0.0-1.0)."""
        # Valid: 0.0
        prov1 = Provenance(
            source="hgnc.search_genes",
            timestamp=datetime.now(timezone.utc),
            curie="HGNC:11998",
            confidence_score=0.0,
        )
        assert prov1.confidence_score == 0.0

        # Valid: 1.0
        prov2 = Provenance(
            source="hgnc.search_genes",
            timestamp=datetime.now(timezone.utc),
            curie="HGNC:11998",
            confidence_score=1.0,
        )
        assert prov2.confidence_score == 1.0

        # Invalid: >1.0
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            Provenance(
                source="hgnc.search_genes",
                timestamp=datetime.now(timezone.utc),
                curie="HGNC:11998",
                confidence_score=1.5,
            )

        # Invalid: <0.0
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Provenance(
                source="hgnc.search_genes",
                timestamp=datetime.now(timezone.utc),
                curie="HGNC:11998",
                confidence_score=-0.1,
            )

    def test_to_citation_string(self):
        """Test citation string generation."""
        prov = Provenance(
            source="chembl.get_compound",
            timestamp=datetime(2026, 1, 5, 14, 32, 15, tzinfo=timezone.utc),
            curie="CHEMBL:1946170",
            api_version="ChEMBL v33",
            confidence_score=1.0,
        )

        citation = prov.to_citation_string()
        assert "source: chembl.get_compound" in citation
        assert "curie: CHEMBL:1946170" in citation
        assert "timestamp: 2026-01-05T14:32:15+00:00" in citation
        assert "api_version: ChEMBL v33" in citation
        assert "confidence: 1.00" in citation

    def test_to_citation_string_minimal(self):
        """Test citation string with only required fields."""
        prov = Provenance(
            source="hgnc.get_gene",
            timestamp=datetime(2026, 1, 5, 14, 0, 0, tzinfo=timezone.utc),
            curie="HGNC:11998",
        )

        citation = prov.to_citation_string()
        assert "source: hgnc.get_gene" in citation
        assert "curie: HGNC:11998" in citation
        assert "timestamp: 2026-01-05T14:00:00+00:00" in citation
        assert "api_version" not in citation
        assert "confidence" not in citation


class TestMCPClaim:
    """Tests for MCPClaim model."""

    def test_valid_claim(self):
        """Test creating valid MCP claim."""
        prov = Provenance(
            source="chembl.get_compound",
            timestamp=datetime.now(timezone.utc),
            curie="CHEMBL:1946170",
        )

        claim = MCPClaim(
            claim="Regorafenib is approved for hepatocellular carcinoma",
            value=4,  # max_phase
            provenance=prov,
        )

        assert claim.claim == "Regorafenib is approved for hepatocellular carcinoma"
        assert claim.value == 4
        assert claim.provenance == prov

    def test_claim_with_complex_value(self):
        """Test claim with complex value type (list)."""
        prov = Provenance(
            source="chembl.get_compound",
            timestamp=datetime.now(timezone.utc),
            curie="CHEMBL:939",
        )

        claim = MCPClaim(
            claim="Gefitinib has multiple indications",
            value=["Adenocarcinoma of Lung", "Carcinoma, Non-Small-Cell Lung"],
            provenance=prov,
        )

        assert len(claim.value) == 2
        assert claim.value[0] == "Adenocarcinoma of Lung"

    def test_empty_claim_raises_error(self):
        """Test that empty claim string raises ValidationError."""
        prov = Provenance(
            source="chembl.get_compound",
            timestamp=datetime.now(timezone.utc),
            curie="CHEMBL:939",
        )

        with pytest.raises(ValidationError, match="at least 1 character"):
            MCPClaim(
                claim="",  # Empty claim
                value=4,
                provenance=prov,
            )

    def test_to_citation_format(self):
        """Test citation-formatted string generation."""
        prov = Provenance(
            source="chembl.get_compound",
            timestamp=datetime(2026, 1, 5, 14, 32, 15, tzinfo=timezone.utc),
            curie="CHEMBL:1946170",
        )

        claim = MCPClaim(
            claim="Regorafenib is approved",
            value=4,
            provenance=prov,
        )

        citation = claim.to_citation_format()
        assert citation.startswith("Regorafenib is approved (")
        assert "source: chembl.get_compound" in citation
        assert "CHEMBL:1946170" in citation


class TestBatchProvenance:
    """Tests for BatchProvenance model."""

    def test_valid_batch_provenance(self):
        """Test creating valid batch provenance."""
        batch_prov = BatchProvenance(
            source="chembl.get_compounds_batch",
            timestamp=datetime.now(timezone.utc),
            curies=["CHEMBL:25", "CHEMBL:939", "CHEMBL:521686"],
            batch_size=3,
            api_version="ChEMBL v33",
        )

        assert batch_prov.source == "chembl.get_compounds_batch"
        assert len(batch_prov.curies) == 3
        assert batch_prov.batch_size == 3
        assert batch_prov.api_version == "ChEMBL v33"

    def test_batch_provenance_without_api_version(self):
        """Test batch provenance with only required fields."""
        batch_prov = BatchProvenance(
            source="chembl.get_compounds_batch",
            timestamp=datetime.now(timezone.utc),
            curies=["CHEMBL:25", "CHEMBL:939"],
            batch_size=2,
        )

        assert batch_prov.api_version is None

    def test_empty_curies_raises_error(self):
        """Test that empty curies list raises ValidationError."""
        with pytest.raises(ValidationError, match="at least 1 item"):
            BatchProvenance(
                source="chembl.get_compounds_batch",
                timestamp=datetime.now(timezone.utc),
                curies=[],  # Empty list
                batch_size=0,
            )

    def test_batch_size_validation(self):
        """Test batch size must be >= 1."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            BatchProvenance(
                source="chembl.get_compounds_batch",
                timestamp=datetime.now(timezone.utc),
                curies=["CHEMBL:25"],
                batch_size=0,  # Invalid: <1
            )

    def test_to_citation_string_short_batch(self):
        """Test citation string for small batch (<= 3 items)."""
        batch_prov = BatchProvenance(
            source="chembl.get_compounds_batch",
            timestamp=datetime(2026, 1, 5, 14, 0, 0, tzinfo=timezone.utc),
            curies=["CHEMBL:25", "CHEMBL:939"],
            batch_size=2,
        )

        citation = batch_prov.to_citation_string()
        assert "batch_size: 2" in citation
        assert "CHEMBL:25,CHEMBL:939" in citation
        assert "..." not in citation  # No truncation

    def test_to_citation_string_long_batch(self):
        """Test citation string for large batch (> 3 items)."""
        batch_prov = BatchProvenance(
            source="chembl.get_compounds_batch",
            timestamp=datetime(2026, 1, 5, 14, 0, 0, tzinfo=timezone.utc),
            curies=["CHEMBL:25", "CHEMBL:939", "CHEMBL:521686", "CHEMBL:1946170", "CHEMBL:2105717"],
            batch_size=5,
        )

        citation = batch_prov.to_citation_string()
        assert "batch_size: 5" in citation
        assert "CHEMBL:25,CHEMBL:939,CHEMBL:521686,... (5 total)" in citation
