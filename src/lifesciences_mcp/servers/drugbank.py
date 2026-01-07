"""DrugBank MCP Server - Drug resolution using the Fuzzy-to-Fact protocol.

This server provides tools for drug resolution and information:
- search_drugs: Fuzzy search returning ranked drug candidates
- get_drug: Strict lookup by DrugBank CURIE

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/drugbank.py
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients import DrugBankClient
from lifesciences_mcp.models import (
    ErrorEnvelope,
    PaginationEnvelope,
)

# Initialize the MCP server
mcp = FastMCP("DrugBank Server")

# Shared client instance (connection pooling)
_client: DrugBankClient | None = None


async def get_client() -> DrugBankClient:
    """Get or create the shared DrugBank client."""
    global _client
    if _client is None:
        _client = DrugBankClient()
    return _client


@mcp.tool
async def search_drugs(
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
    """Fuzzy search for drugs by name, brand name, or indication.

    Returns ranked candidates for resolution. Use this before calling get_drug.

    Args:
        query: Search term (drug name, brand name, or indication).
               Minimum 2 characters required.
        slim: If true, return only id/name/type/score (~20 tokens per entity).
              Default false returns full candidates.
        cursor: Opaque cursor for pagination. Pass from previous response for next page.
        page_size: Number of results per page (1-100, default 50).

    Returns:
        PaginationEnvelope with DrugSearchCandidate items, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.search_drugs(
        query=query,
        slim=slim,
        cursor=cursor,
        page_size=page_size,
    )


@mcp.tool
async def get_drug(drugbank_id: str, slim: bool = False) -> dict | ErrorEnvelope:
    """Get complete drug record by DrugBank CURIE.

    Args:
        drugbank_id: DrugBank CURIE in format 'DrugBank:DBXXXXX' (e.g., 'DrugBank:DB00945').
        slim: If true, return minimal fields for token efficiency.

    Returns:
        Drug record with cross_references, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.get_drug(drugbank_id=drugbank_id, slim=slim)


if __name__ == "__main__":
    mcp.run()
