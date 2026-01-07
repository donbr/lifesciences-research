"""UniProt MCP Server - Protein sequence and annotation data.

This server provides tools for protein data retrieval:
- search_proteins: Fuzzy search returning ranked candidates
- get_protein: Strict lookup by UniProt CURIE

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/uniprot.py
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients import UniProtClient
from lifesciences_mcp.models import (
    ErrorEnvelope,
    PaginationEnvelope,
)

# Initialize the MCP server
mcp = FastMCP("UniProt Protein Server")

# Shared client instance (connection pooling)
_client: UniProtClient | None = None


async def get_client() -> UniProtClient:
    """Get or create the shared UniProt client."""
    global _client
    if _client is None:
        _client = UniProtClient()
    return _client


@mcp.tool
async def search_proteins(
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
    """Fuzzy search for proteins by name, accession, gene, or organism.

    Returns ranked candidates for resolution. Use this before calling get_protein.

    Args:
        query: Search term (protein name, accession, gene symbol, or organism).
               Minimum 2 characters required.
        slim: If true, return only id/name/organism/score (~20 tokens per entity).
              Default false returns full candidates.
        cursor: Opaque cursor for pagination. Pass from previous response for next page.
        page_size: Number of results per page (1-500, default 50).

    Returns:
        PaginationEnvelope with protein candidates, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.search_proteins(
        query=query,
        slim=slim,
        cursor=cursor,
        page_size=page_size,
    )


@mcp.tool
async def get_protein(uniprot_id: str, slim: bool = False) -> dict | ErrorEnvelope:
    """Get complete protein record by UniProt CURIE.

    Returns full Agentic Biolink entity with cross-references.
    Requires resolved CURIE from search_proteins.

    Implements User Story 2: Strict Protein Lookup (T041-T043).

    Args:
        uniprot_id: UniProt CURIE in format 'UniProtKB:XXXXXX' (e.g., 'UniProtKB:P38398' for BRCA1).
        slim: If true, return only id/name/organism (~20 tokens vs ~115-300 full record).

    Returns:
        Protein record with cross_references, or ErrorEnvelope on failure.
    """
    client = await get_client()
    result = await client.get_protein(uniprot_id, slim=slim)

    # T042-T043: Error handling is done in UniProtClient.get_protein()
    # Returns ErrorEnvelope for:
    # - UNRESOLVED_ENTITY: Invalid CURIE format (FR-004, FR-009)
    # - ENTITY_NOT_FOUND: Valid CURIE but protein doesn't exist (FR-009)
    # - UPSTREAM_ERROR: API errors, network issues

    # Convert Protein model to dict for MCP response
    if isinstance(result, ErrorEnvelope):
        return result
    else:
        return result.model_dump(exclude_none=True)


if __name__ == "__main__":
    mcp.run()
