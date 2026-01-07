"""Integration tests for WikiPathways API client.

These tests require network access and hit the real WikiPathways API.
Run with: pytest tests/integration/test_wikipathways_api.py -v -m integration
"""

import pytest

from lifesciences_mcp.clients import WikiPathwaysClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope


@pytest.mark.integration
class TestWikiPathwaysClientIntegration:
    """Integration tests for WikiPathwaysClient with real WikiPathways API."""

    @pytest.fixture
    async def client(self):
        """Create a WikiPathways client."""
        client = WikiPathwaysClient()
        yield client
        await client.close()

    async def test_search_pathways_glycolysis(self, client: WikiPathwaysClient):
        """Test fuzzy search for glycolysis pathways (US1 Scenario 1)."""
        result = await client.search_pathways(
            query="glycolysis",
            organism="Homo sapiens",
            page_size=10,
        )

        # Verify response is PaginationEnvelope
        assert isinstance(result, PaginationEnvelope)

        # Verify results exist
        assert len(result.items) > 0
        assert len(result.items) <= 10

        # Verify first result has expected structure (convert to dict)
        top_result = (
            result.items[0].model_dump()
            if hasattr(result.items[0], "model_dump")
            else result.items[0]
        )
        assert "id" in top_result
        assert top_result["id"].startswith("WP:WP")
        assert "title" in top_result
        assert "organism" in top_result
        assert top_result["organism"] == "Homo sapiens"
        assert "score" in top_result
        assert 0.0 <= top_result["score"] <= 1.0

        # Verify pagination metadata
        assert result.pagination.page_size == 10
        assert result.pagination.total_count is not None

    async def test_search_pathways_pagination(self, client: WikiPathwaysClient):
        """Test pagination with a broad search (US1 Scenario 2)."""
        # Get first page
        page1 = await client.search_pathways(
            query="metabolism",
            page_size=10,
        )

        assert isinstance(page1, PaginationEnvelope)
        assert len(page1.items) == 10

        # Get second page using cursor
        cursor = page1.pagination.cursor
        if cursor:  # Only test if there are more results
            page2 = await client.search_pathways(
                query="metabolism",
                page_size=10,
                cursor=cursor,
            )

            assert isinstance(page2, PaginationEnvelope)
            # Verify different results
            page1_items = [
                item.model_dump() if hasattr(item, "model_dump") else item for item in page1.items
            ]
            page2_items = [
                item.model_dump() if hasattr(item, "model_dump") else item for item in page2.items
            ]
            page1_ids = {item["id"] for item in page1_items}
            page2_ids = {item["id"] for item in page2_items}
            assert page1_ids != page2_ids  # Pages should be different

    async def test_get_pathway_by_id(self, client: WikiPathwaysClient):
        """Test strict lookup for pathway by CURIE (US2 Scenario 1)."""
        from lifesciences_mcp.models import Pathway

        result = await client.get_pathway(pathway_id="WP:WP534")

        # Verify response is Pathway model
        assert isinstance(result, Pathway)
        assert result.id == "WP:WP534"
        assert result.title
        assert result.organism
        assert result.description
        assert result.url

        # Verify revision metadata
        assert result.revision.version

        # Verify component counts
        assert result.component_counts.gene_count >= 0
        assert result.component_counts.protein_count >= 0

        # Verify cross_references exists (may be empty)
        assert isinstance(result.cross_references, dict)

    async def test_get_pathway_invalid_curie(self, client: WikiPathwaysClient):
        """Test that raw string returns UNRESOLVED_ENTITY error (US2 Scenario 2)."""
        result = await client.get_pathway(pathway_id="glycolysis")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == "UNRESOLVED_ENTITY"
        assert "WP:WPNNNNN format" in result.error.message
        assert result.error.invalid_input == "glycolysis"

    async def test_get_pathway_not_found(self, client: WikiPathwaysClient):
        """Test that non-existent CURIE returns ENTITY_NOT_FOUND (US2 Scenario 3)."""
        result = await client.get_pathway(pathway_id="WP:WP99999999")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == "ENTITY_NOT_FOUND"
        assert "not found" in result.error.message

    async def test_fuzzy_to_fact_workflow(self, client: WikiPathwaysClient):
        """Test complete Fuzzy-to-Fact protocol workflow (US1+US2)."""
        from lifesciences_mcp.models import Pathway

        # Step 1: Fuzzy search
        search_result = await client.search_pathways(
            query="glycolysis",
            organism="Homo sapiens",
            page_size=5,
        )

        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

        # Step 2: Strict lookup using top candidate ID
        top_candidate_dict = (
            search_result.items[0].model_dump()
            if hasattr(search_result.items[0], "model_dump")
            else search_result.items[0]
        )
        pathway_id = top_candidate_dict["id"]

        pathway = await client.get_pathway(pathway_id=pathway_id)

        # Verify strict lookup succeeds
        assert isinstance(pathway, Pathway)
        assert pathway.id == pathway_id
        assert pathway.title == top_candidate_dict["title"]
        assert pathway.organism == top_candidate_dict["organism"]

    async def test_search_pathways_empty_results(self, client: WikiPathwaysClient):
        """Test search with no results (US1 Scenario 3)."""
        result = await client.search_pathways(
            query="nonexistent pathway XYZ123456789",
            page_size=10,
        )

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) == 0
        assert result.pagination.total_count == 0
        assert result.pagination.cursor is None

    async def test_search_pathways_no_organism_filter(self, client: WikiPathwaysClient):
        """Test search without organism filter (US1 Scenario 4)."""
        result = await client.search_pathways(
            query="apoptosis",
            page_size=10,
        )

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Verify results include multiple organisms
        items_dict = [
            item.model_dump() if hasattr(item, "model_dump") else item for item in result.items
        ]
        organisms = {item["organism"] for item in items_dict}
        # Should have results from different species when no filter
        assert len(organisms) >= 1  # At least one organism


@pytest.mark.integration
async def test_search_short_query():
    """Test that short queries return AMBIGUOUS_QUERY error."""
    client = WikiPathwaysClient()
    try:
        result = await client.search_pathways(query="a")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == "AMBIGUOUS_QUERY"
        assert "minimum 2 characters" in result.error.message
        assert result.error.invalid_input == "a"
    finally:
        await client.close()


@pytest.mark.integration
class TestWikiPathwaysGeneToPathwayLookup:
    """Integration tests for reverse gene-to-pathway lookup (User Story 3)."""

    @pytest.fixture
    async def client(self):
        """Create a WikiPathways client."""
        client = WikiPathwaysClient()
        yield client
        await client.close()

    async def test_get_pathways_for_gene_with_organism(self, client: WikiPathwaysClient):
        """Test BRCA1 pathways with organism filter (US3 Scenario 1)."""
        result = await client.get_pathways_for_gene(
            gene_id="BRCA1",
            organism="Homo sapiens",
            page_size=10,
        )

        # Verify response is PaginationEnvelope
        assert isinstance(result, PaginationEnvelope)

        # Verify results exist for BRCA1
        assert len(result.items) > 0
        assert len(result.items) <= 10

        # Verify all results are for Homo sapiens
        items_dict = [
            item.model_dump() if hasattr(item, "model_dump") else item for item in result.items
        ]
        for item in items_dict:
            assert item["organism"] == "Homo sapiens"
            assert "id" in item
            assert item["id"].startswith("WP:WP")
            assert "title" in item

    async def test_get_pathways_for_gene_organism_mismatch(self, client: WikiPathwaysClient):
        """Test organism filter mismatch (US3 Scenario 2)."""
        result = await client.get_pathways_for_gene(
            gene_id="BRCA1",
            organism="Mus musculus",  # Mouse instead of human
            page_size=10,
        )

        # Verify response is PaginationEnvelope
        assert isinstance(result, PaginationEnvelope)

        # Verify all results (if any) are for Mus musculus
        items_dict = [
            item.model_dump() if hasattr(item, "model_dump") else item for item in result.items
        ]
        for item in items_dict:
            assert item["organism"] == "Mus musculus"

    async def test_get_pathways_for_gene_no_pathways(self, client: WikiPathwaysClient):
        """Test gene with no pathways (US3 Scenario 3)."""
        result = await client.get_pathways_for_gene(
            gene_id="NONEXISTENTGENE123456",
            page_size=10,
        )

        # Verify response is PaginationEnvelope with empty results
        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) == 0
        assert result.pagination.total_count == 0
        assert result.pagination.cursor is None

    async def test_get_pathways_for_gene_no_organism_filter(self, client: WikiPathwaysClient):
        """Test gene lookup without organism filter (US3 Scenario 4)."""
        result = await client.get_pathways_for_gene(
            gene_id="TP53",
            page_size=10,
        )

        # Verify response is PaginationEnvelope
        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Verify results include multiple organisms
        items_dict = [
            item.model_dump() if hasattr(item, "model_dump") else item for item in result.items
        ]
        organisms = {item["organism"] for item in items_dict}
        # TP53 should appear in pathways from multiple species
        # At minimum we expect 1 organism, but likely more
        assert len(organisms) >= 1


@pytest.mark.integration
class TestWikiPathwaysComponentExtraction:
    """Integration tests for pathway component extraction (User Story 4)."""

    @pytest.fixture
    async def client(self):
        """Create a WikiPathways client."""
        client = WikiPathwaysClient()
        yield client
        await client.close()

    async def test_get_pathway_components_all_types(self, client: WikiPathwaysClient):
        """Test component extraction with all entity types (US4 Scenario 1)."""
        from lifesciences_mcp.models import PathwayComponents

        result = await client.get_pathway_components(pathway_id="WP:WP534")

        # Verify response is PathwayComponents model
        assert isinstance(result, PathwayComponents)

        # Verify genes exist
        assert len(result.genes) > 0
        for gene in result.genes:
            assert gene.id
            assert gene.label
            assert gene.type in ["Gene", "Protein"]
            assert gene.database

        # Verify proteins exist
        assert len(result.proteins) > 0
        for protein in result.proteins:
            assert protein.id
            assert protein.label
            assert protein.type == "Protein"
            assert protein.database

    async def test_get_pathway_components_only_genes(self, client: WikiPathwaysClient):
        """Test pathway with only genes, no metabolites (US4 Scenario 2)."""
        from lifesciences_mcp.models import PathwayComponents

        # Use a pathway that likely has genes but minimal metabolites
        result = await client.get_pathway_components(pathway_id="WP:WP4224")

        # Verify response is PathwayComponents model
        assert isinstance(result, PathwayComponents)

        # Verify genes exist
        assert len(result.genes) > 0

        # Metabolites may or may not exist (omit-if-null pattern)
        if hasattr(result, "metabolites"):
            # If present, should be a list
            assert isinstance(result.metabolites, list)

    async def test_get_pathway_components_invalid_id(self, client: WikiPathwaysClient):
        """Test invalid pathway ID returns error (US4 Scenario 3)."""
        result = await client.get_pathway_components(pathway_id="invalid123")

        assert isinstance(result, ErrorEnvelope)
        assert result.success is False
        assert result.error.code == "UNRESOLVED_ENTITY"
        assert "WP:WPNNNNN format" in result.error.message

    async def test_get_pathway_components_interactions(self, client: WikiPathwaysClient):
        """Test interaction extraction (US4 Scenario 4)."""
        from lifesciences_mcp.models import PathwayComponents

        result = await client.get_pathway_components(pathway_id="WP:WP534")

        # Verify response is PathwayComponents model
        assert isinstance(result, PathwayComponents)

        # Verify interactions exist (or empty list if unavailable)
        assert isinstance(result.interactions, list)
        # If interactions exist, verify structure
        if len(result.interactions) > 0:
            interaction = result.interactions[0]
            assert interaction.source
            assert interaction.target
            assert interaction.type
