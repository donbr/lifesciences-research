"""WikiPathways MCP Server - Biological pathway database resolution using the Fuzzy-to-Fact protocol.

This server provides tools for querying WikiPathways, a community-curated pathway database:
- search_pathways: Fuzzy search returning ranked pathway candidates
- get_pathway: Strict lookup by WikiPathways CURIE
- get_pathways_for_gene: Reverse lookup finding all pathways containing a specific gene
- get_pathway_components: Extract genes, proteins, metabolites from pathway

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/wikipathways.py
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients import WikiPathwaysClient
from lifesciences_mcp.models import (
    ErrorEnvelope,
    PaginationEnvelope,
)

# Initialize the MCP server
mcp = FastMCP("WikiPathways Server")

# Shared client instance (connection pooling)
_client: WikiPathwaysClient | None = None


async def get_client() -> WikiPathwaysClient:
    """Get or create the shared WikiPathways client."""
    global _client
    if _client is None:
        _client = WikiPathwaysClient()
    return _client


@mcp.tool
async def search_pathways(
    query: str,
    organism: str | None = "Homo sapiens",
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
    """Fuzzy search for pathways by name, description, or gene.

    Returns ranked candidates for resolution. Use this before calling get_pathway.

    Args:
        query: Search term (pathway name, description, gene, or natural language query).
               Minimum 2 characters required.
        organism: Organism filter (exact scientific name, e.g., "Homo sapiens", "Mus musculus").
                  Default: "Homo sapiens". Pass None for all organisms.
        slim: If true, return only id/name/organism/score (~20 tokens per entity).
              Default false returns full candidates.
        cursor: Opaque cursor for pagination. Pass from previous response for next page.
        page_size: Number of results per page (1-100, default 50).

    Returns:
        PaginationEnvelope with PathwaySearchCandidate items, or ErrorEnvelope on failure.
    """
    client = await get_client()

    # Call client method
    result = await client.search_pathways(
        query=query,
        organism=organism,
        cursor=cursor,
        page_size=page_size,
    )

    # Return result (PaginationEnvelope or ErrorEnvelope)
    return result


@mcp.tool
async def get_pathway(pathway_id: str) -> dict | ErrorEnvelope:
    """Get complete pathway record by WikiPathways CURIE.

    Returns full pathway details with cross-references.
    Requires resolved CURIE from search_pathways.

    Args:
        pathway_id: WikiPathways CURIE in format 'WP:WPNNNNN' (e.g., 'WP:WP4868' for ACE2 pathway).

    Returns:
        Pathway record with cross_references, or ErrorEnvelope on failure.
    """
    client = await get_client()

    # Call client method
    result = await client.get_pathway(pathway_id=pathway_id)

    # Convert Pathway model to dict if successful
    if isinstance(result, ErrorEnvelope):
        return result
    else:
        return result.model_dump()


@mcp.tool
async def get_pathways_for_gene(
    gene_id: str,
    organism: str | None = "Homo sapiens",
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
    """Find all pathways containing a specific gene.

    Returns ranked pathway candidates containing the specified gene.
    Useful for reverse lookup: gene → pathways.

    Args:
        gene_id: Gene identifier (symbol like "BRCA1", Entrez ID like "672",
                 or Ensembl ID like "ENSG00000012048").
                 Case-insensitive for gene symbols (converted to uppercase).
        organism: Organism filter (exact scientific name, e.g., "Homo sapiens").
                  Default: "Homo sapiens". Pass None for all organisms.
        cursor: Opaque cursor for pagination. Pass from previous response for next page.
        page_size: Number of results per page (1-100, default 50).

    Returns:
        PaginationEnvelope with PathwaySearchCandidate items, or ErrorEnvelope on failure.
    """
    client = await get_client()

    # Call client method
    result = await client.get_pathways_for_gene(
        gene_id=gene_id,
        organism=organism,
        cursor=cursor,
        page_size=page_size,
    )

    # Return result (PaginationEnvelope or ErrorEnvelope)
    return result


@mcp.tool
async def get_pathway_components(pathway_id: str) -> dict | ErrorEnvelope:
    """Extract all biological entities from a pathway.

    Returns genes, proteins, metabolites, and interactions from the pathway.
    Requires resolved CURIE from search_pathways or get_pathways_for_gene.

    Args:
        pathway_id: WikiPathways CURIE in format 'WP:WPNNNNN' (e.g., 'WP:WP534' for Glycolysis).

    Returns:
        PathwayComponents with genes, proteins, metabolites, interactions or ErrorEnvelope on failure.
        Note: Empty component lists are omitted from response (ADR-001 §4 omit-if-null pattern).
    """
    client = await get_client()

    # Call client method
    result = await client.get_pathway_components(pathway_id=pathway_id)

    # Convert PathwayComponents model to dict if successful
    if isinstance(result, ErrorEnvelope):
        return result
    else:
        return result.model_dump(exclude_none=True)


if __name__ == "__main__":
    mcp.run()
