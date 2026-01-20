"""Unit tests for WikiPathways client (non-network tests).

Run with: pytest tests/unit/test_wikipathways_client.py -v
"""

import pytest

from lifesciences_mcp.clients.wikipathways import WikiPathwaysClient

pytestmark = [pytest.mark.unit, pytest.mark.wikipathways]


class TestWikiPathwaysClient:
    """Tests for WikiPathwaysClient helper methods."""

    @pytest.fixture
    def client(self):
        """Create a WikiPathways client."""
        return WikiPathwaysClient()

    def test_validate_pathway_id_valid(self, client):
        """Test pathway ID validation with valid IDs."""
        assert client._validate_pathway_id("WP:WP534") is True
        assert client._validate_pathway_id("WP:WP1") is True
        assert client._validate_pathway_id("WP:WP99999") is True

    def test_validate_pathway_id_invalid(self, client):
        """Test pathway ID validation with invalid IDs."""
        assert client._validate_pathway_id("WP534") is False  # Missing WP: prefix
        assert client._validate_pathway_id("534") is False
        assert client._validate_pathway_id("WP:534") is False  # Missing WP prefix
        assert client._validate_pathway_id("WP:WPabc") is False  # Non-numeric
        assert client._validate_pathway_id("") is False

    def test_normalize_gene_symbol(self, client):
        """Test gene symbol normalization."""
        assert client._normalize_gene_symbol("brca1") == "BRCA1"
        assert client._normalize_gene_symbol("tp53") == "TP53"
        assert client._normalize_gene_symbol("BRCA1") == "BRCA1"
        assert client._normalize_gene_symbol("Tp53") == "TP53"

    def test_encode_decode_cursor(self, client):
        """Test cursor encoding and decoding."""
        # Test offset 0
        cursor = client._encode_cursor(0)
        assert client._decode_cursor(cursor) == 0

        # Test offset 50
        cursor = client._encode_cursor(50)
        assert client._decode_cursor(cursor) == 50

        # Test offset 100
        cursor = client._encode_cursor(100)
        assert client._decode_cursor(cursor) == 100

    def test_decode_cursor_invalid(self, client):
        """Test cursor decoding with invalid input."""
        with pytest.raises(ValueError):
            client._decode_cursor("invalid_base64!!!")

        with pytest.raises(ValueError):
            client._decode_cursor("YWJj")  # Valid base64 but not a number

    def test_map_cross_references_ncbigene(self, client):
        """Test cross-reference mapping for ncbigene."""
        pathway_data = {
            "id": "WP534",
            "ncbigene": "ncbigene:672, ncbigene:675, ncbigene:5213",
        }
        xrefs = client._map_cross_references("WP534", pathway_data)
        assert "entrez" in xrefs
        assert xrefs["entrez"] == ["672", "675", "5213"]

    def test_map_cross_references_ensembl(self, client):
        """Test cross-reference mapping for ensembl."""
        pathway_data = {
            "id": "WP534",
            "ensembl": "ensembl:ENSG00000012048, ensembl:ENSG00000013374",
        }
        xrefs = client._map_cross_references("WP534", pathway_data)
        assert "ensembl_gene" in xrefs
        assert xrefs["ensembl_gene"] == ["ENSG00000012048", "ENSG00000013374"]

    def test_map_cross_references_hgnc(self, client):
        """Test cross-reference mapping for HGNC symbols."""
        pathway_data = {
            "id": "WP534",
            "hgnc": "hgnc.symbol:BRCA1, hgnc.symbol:TP53",
        }
        xrefs = client._map_cross_references("WP534", pathway_data)
        assert "hgnc" in xrefs
        assert xrefs["hgnc"] == ["BRCA1", "TP53"]

    def test_map_cross_references_uniprot_isoforms(self, client):
        """Test cross-reference mapping for UniProt with isoforms."""
        pathway_data = {
            "id": "WP534",
            "uniprot": "uniprot:P38398;P51587, uniprot:Q01813",
        }
        xrefs = client._map_cross_references("WP534", pathway_data)
        assert "uniprot" in xrefs
        # Should take first isoform only
        assert xrefs["uniprot"] == ["P38398", "Q01813"]

    def test_map_cross_references_empty(self, client):
        """Test cross-reference mapping with no references."""
        pathway_data = {"id": "WP534"}
        xrefs = client._map_cross_references("WP534", pathway_data)
        assert xrefs == {}

    def test_map_cross_references_omit_empty(self, client):
        """Test that empty cross-references are omitted."""
        pathway_data = {
            "id": "WP534",
            "ncbigene": "",  # Empty value
            "ensembl": "ensembl:ENSG00000012048",
        }
        xrefs = client._map_cross_references("WP534", pathway_data)
        # Should omit empty ncbigene
        assert "entrez" not in xrefs
        assert "ensembl_gene" in xrefs
