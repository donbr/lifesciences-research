"""ChEMBL MCP Server - Compound and bioactivity data using the Fuzzy-to-Fact protocol.

This server provides tools for compound discovery and bioactivity search:
- search_compounds: Fuzzy search returning ranked compound candidates
- get_compound: Strict lookup by ChEMBL CURIE
- get_compounds_batch: Batch lookup for multiple ChEMBL IDs

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/chembl.py

Per ADR-004: No shutdown hooks (@mcp.on_event not supported in FastMCP).
Lifecycle management handled by module-level singleton pattern.
"""

from typing import Any

from fastmcp import FastMCP

from lifesciences_mcp.clients import ChEMBLClient
from lifesciences_mcp.models import (
    ErrorEnvelope,
    PaginationEnvelope,
)

# Initialize the MCP server
mcp = FastMCP("ChEMBL Compound Server")

# Module-level singleton (ADR-004: FastMCP Lifecycle Management)
_client: ChEMBLClient | None = None


async def get_client() -> ChEMBLClient:
    """Get or create the shared ChEMBL client.

    Uses lazy initialization with module-level singleton pattern.
    FastMCP manages lifecycle internally - no cleanup hooks needed (ADR-004).
    """
    global _client
    if _client is None:
        _client = ChEMBLClient()
    return _client


@mcp.tool
async def search_compounds(
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
    """Fuzzy search for compounds by name, synonym, or identifier.

    Returns ranked candidates for resolution. Use this before calling get_compound.

    Args:
        query: Search term (compound name, synonym, or natural language query).
               Minimum 2 characters required.
        slim: If true, return minimal fields (~20 tokens per entity).
              Default false returns full candidates.
        cursor: Opaque cursor for pagination. Pass from previous response for next page.
        page_size: Number of results per page (1-100, default 50).

    Returns:
        PaginationEnvelope with CompoundSearchCandidate items, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.search_compounds(
        query=query,
        slim=slim,
        cursor=cursor,
        page_size=page_size,
    )


@mcp.tool
async def get_compound(chembl_id: str, slim: bool = False) -> dict[str, Any] | ErrorEnvelope:
    """Get complete compound record by ChEMBL CURIE.

    Returns full Agentic Biolink entity with cross-references.
    Requires resolved CURIE from search_compounds.

    Args:
        chembl_id: ChEMBL CURIE in format 'CHEMBL:NNNNN' (e.g., 'CHEMBL:25', 'CHEMBL:1201583').
        slim: If true, return minimal fields for token efficiency.

    Returns:
        Compound record with cross_references, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.get_compound(chembl_id=chembl_id, slim=slim)


@mcp.tool
async def get_compounds_batch(
    chembl_ids: list[str], slim: bool = True
) -> list[dict[str, Any]] | ErrorEnvelope:
    """Batch lookup for multiple compounds to prevent thread pool exhaustion.

    Use this for bulk operations instead of calling get_compound repeatedly.

    Args:
        chembl_ids: List of ChEMBL CURIEs (e.g., ['CHEMBL:25', 'CHEMBL:941']).
        slim: If true (default), return minimal fields to reduce tokens.

    Returns:
        List of Compound records, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.get_compounds_batch(chembl_ids=chembl_ids, slim=slim)


if __name__ == "__main__":
    mcp.run()
