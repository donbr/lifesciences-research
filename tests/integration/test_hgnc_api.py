"""Integration tests for HGNC API client.

These tests require network access and hit the real HGNC API.
Run with: pytest tests/integration/ -m integration -v
"""

import pytest

from lifesciences_mcp.clients import HGNCClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope
from lifesciences_mcp.models.gene import Gene


@pytest.mark.integration
class TestHGNCClientIntegration:
    """Integration tests for HGNCClient with real HGNC API."""

    @pytest.fixture
    async def client(self):
        """Create an HGNC client."""
        client = HGNCClient()
        yield client
        await client.close()

    async def test_search_genes_brca1(self, client: HGNCClient):
        """Test fuzzy search for BRCA1."""
        result = await client.search_genes("BRCA1")

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # BRCA1 should be in results
        brca1 = next((c for c in result.items if c.symbol == "BRCA1"), None)
        assert brca1 is not None
        assert brca1.id == "HGNC:1100"

    async def test_search_genes_pagination(self, client: HGNCClient):
        """Test pagination with a broad search."""
        # First page
        result1 = await client.search_genes("kinase", page_size=5)

        assert isinstance(result1, PaginationEnvelope)
        assert len(result1.items) == 5
        assert result1.pagination.cursor is not None

        # Second page
        result2 = await client.search_genes(
            "kinase",
            page_size=5,
            cursor=result1.pagination.cursor,
        )

        assert isinstance(result2, PaginationEnvelope)
        assert len(result2.items) == 5

        # Items should be different
        ids1 = {c.id for c in result1.items}
        ids2 = {c.id for c in result2.items}
        assert ids1.isdisjoint(ids2)

    async def test_get_gene_brca1(self, client: HGNCClient):
        """Test strict lookup for BRCA1 by CURIE."""
        result = await client.get_gene("HGNC:1100")

        assert isinstance(result, Gene)
        assert result.id == "HGNC:1100"
        assert result.symbol == "BRCA1"
        assert result.status == "Approved"
        assert result.cross_references.ensembl_gene is not None
        assert result.cross_references.entrez is not None

    async def test_get_gene_invalid_curie(self, client: HGNCClient):
        """Test that raw string returns UNRESOLVED_ENTITY error."""
        result = await client.get_gene("BRCA1")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
        assert "search_genes" in result.error.recovery_hint

    async def test_get_gene_not_found(self, client: HGNCClient):
        """Test that non-existent CURIE returns ENTITY_NOT_FOUND."""
        result = await client.get_gene("HGNC:9999999")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "ENTITY_NOT_FOUND"

    async def test_fuzzy_to_fact_workflow(self, client: HGNCClient):
        """Test complete Fuzzy-to-Fact protocol workflow."""
        # Step 1: Fuzzy search
        search_result = await client.search_genes("tumor protein p53")

        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

        # Find TP53 in results
        tp53_candidate = next(
            (c for c in search_result.items if "TP53" in c.symbol or "p53" in c.name.lower()),
            None,
        )
        assert tp53_candidate is not None

        # Step 2: Strict lookup
        gene = await client.get_gene(tp53_candidate.id)

        assert isinstance(gene, Gene)
        assert gene.cross_references is not None


@pytest.mark.integration
async def test_search_short_query():
    """Test that short queries return AMBIGUOUS_QUERY error."""
    client = HGNCClient()
    try:
        result = await client.search_genes("a")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "AMBIGUOUS_QUERY"
    finally:
        await client.close()
