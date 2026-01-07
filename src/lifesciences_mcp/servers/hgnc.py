"""HGNC MCP Server - Gene resolution using the Fuzzy-to-Fact protocol.

This server provides two tools for gene resolution:
- search_genes: Fuzzy search returning ranked candidates
- get_gene: Strict lookup by HGNC CURIE

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients import HGNCClient
from lifesciences_mcp.models import (
    ErrorEnvelope,
    Gene,
    PaginationEnvelope,
    SearchCandidate,
)

# Initialize the MCP server
mcp = FastMCP("HGNC Gene Server")

# Shared client instance (connection pooling)
_client: HGNCClient | None = None


async def get_client() -> HGNCClient:
    """Get or create the shared HGNC client."""
    global _client
    if _client is None:
        _client = HGNCClient()
    return _client


@mcp.tool
async def search_genes(
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope[SearchCandidate] | ErrorEnvelope:
    """Fuzzy search for genes by name, symbol, synonym, or description.

    Returns ranked candidates for resolution. Use this before calling get_gene.

    Args:
        query: Search term (gene symbol, name, synonym, or natural language query).
               Minimum 2 characters required.
        slim: If true, return only id/symbol/name/score (~20 tokens per entity).
              Default false returns full candidates.
        cursor: Opaque cursor for pagination. Pass from previous response for next page.
        page_size: Number of results per page (1-100, default 50).

    Returns:
        PaginationEnvelope with SearchCandidate items, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.search_genes(
        query=query,
        slim=slim,
        cursor=cursor,
        page_size=page_size,
    )


@mcp.tool
async def get_gene(hgnc_id: str) -> Gene | ErrorEnvelope:
    """Get complete gene record by HGNC CURIE.

    Returns full Agentic Biolink entity with cross-references.
    Requires resolved CURIE from search_genes.

    Args:
        hgnc_id: HGNC CURIE in format 'HGNC:NNNNN' (e.g., 'HGNC:1100' for BRCA1).

    Returns:
        Gene record with cross_references, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.get_gene(hgnc_id=hgnc_id)


if __name__ == "__main__":
    mcp.run()
