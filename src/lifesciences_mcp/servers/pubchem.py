"""PubChem MCP Server.

FastMCP server providing access to PubChem chemical compound data
through fuzzy search and strict lookup operations.
"""

from typing import Any

from fastmcp import FastMCP

from lifesciences_mcp.clients.pubchem import PubChemClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope

# Initialize FastMCP server
mcp = FastMCP("PubChem MCP Server")

# Module-level singleton (ADR-004)
_client: PubChemClient | None = None


def get_client() -> PubChemClient:
    """Get or create the singleton PubChemClient instance (T051).

    Following ADR-004, we use module-level singleton pattern instead of
    @mcp.on_event shutdown hooks (not supported in FastMCP).
    """
    global _client
    if _client is None:
        _client = PubChemClient()
    return _client


@mcp.tool()
async def search_compounds(
    query: str,
    slim: bool = True,
    cursor: str | None = None,
    page_size: int = 50,
) -> dict[str, Any]:
    """Fuzzy search for compounds by name, synonym, or identifier (T052).

    This is Phase 1 of the Fuzzy-to-Fact protocol. Returns ranked candidates
    for resolution. Use this before calling get_compound for strict lookups.

    Args:
        query: Search term (compound name, synonym, or natural language query).
               Minimum 2 characters required.
        slim: If true, return minimal fields (~20 tokens per entity).
              Default true for token efficiency.
        cursor: Opaque cursor for pagination. Pass from previous response for next page.
        page_size: Number of results per page (1-100, default 50).

    Returns:
        PaginationEnvelope with PubChemSearchCandidate items on success, or ErrorEnvelope on error.

    Error Codes:
        AMBIGUOUS_QUERY: Query too short (<2 characters)
        RATE_LIMITED: Rate limit exceeded (>5 req/s or >400 req/min)
        UPSTREAM_ERROR: PubChem API unavailable or returned error

    Examples:
        # Search for aspirin
        >>> result = await search_compounds(query="aspirin", page_size=10)
        >>> result["items"][0]["id"]
        "PubChem:CID2244"

        # Search for ibuprofen
        >>> result = await search_compounds(query="ibuprofen")
        >>> len(result["items"])
        50  # page_size default

        # Pagination
        >>> page1 = await search_compounds(query="acetylsalicylic acid", page_size=10)
        >>> page2 = await search_compounds(
        ...     query="acetylsalicylic acid",
        ...     page_size=10,
        ...     cursor=page1["pagination"]["cursor"]
        ... )

        # Empty results (no error)
        >>> result = await search_compounds(query="xyznonexistent999")
        >>> result["items"]
        []
        >>> result["pagination"]["total_count"]
        0

        # Error: query too short
        >>> result = await search_compounds(query="a")
        >>> result["success"]
        False
        >>> result["error"]["code"]
        "AMBIGUOUS_QUERY"
    """
    client = get_client()
    result = await client.search_compounds(
        query=query,
        page_size=page_size,
        cursor=cursor,
        slim=slim,
    )

    if isinstance(result, ErrorEnvelope):
        return result.model_dump()

    # Convert PaginationEnvelope to dict
    return result.model_dump()


@mcp.tool()
async def get_compound(pubchem_id: str, slim: bool = False) -> dict[str, Any]:
    """Get complete compound record by PubChem CURIE (T093-T097).

    Returns full Agentic Biolink entity with SMILES, InChI, InChIKey, and
    cross-references. Requires resolved CURIE from search_compounds.

    This is Phase 2 of the Fuzzy-to-Fact protocol. Use after identifying the
    correct compound with search_compounds.

    Args:
        pubchem_id: PubChem CURIE in format 'PubChem:CID{number}' (e.g., 'PubChem:CID2244').
                    Must be a valid CURIE obtained from search_compounds.
        slim: If true, return minimal fields (id, name, molecular_formula only) for
              token efficiency. Default false.

    Returns:
        PubChemCompound with complete data including cross_references on success,
        or ErrorEnvelope on error.

    Error Codes:
        UNRESOLVED_ENTITY: Invalid CURIE format (missing 'PubChem:CID' prefix or non-numeric ID)
        ENTITY_NOT_FOUND: Valid CURIE but compound doesn't exist in PubChem
        RATE_LIMITED: Rate limit exceeded (>5 req/s or >400 req/min)
        UPSTREAM_ERROR: PubChem API unavailable or returned error

    Examples:
        # Get full compound data for aspirin
        >>> compound = await get_compound(pubchem_id="PubChem:CID2244")
        >>> compound["name"]
        "Aspirin"
        >>> compound["molecular_formula"]
        "C9H8O4"
        >>> compound["cross_references"]["chembl"]
        ["CHEMBL:25"]
        >>> compound["cross_references"]["drugbank"]
        ["DB00945"]

        # Get slim compound data (minimal tokens)
        >>> compound = await get_compound(pubchem_id="PubChem:CID2244", slim=True)
        >>> compound.keys()
        dict_keys(['id', 'name', 'molecular_formula'])

        # Fuzzy-to-Fact workflow
        >>> search_result = await search_compounds(query="aspirin", page_size=10)
        >>> top_candidate = search_result["items"][0]
        >>> compound = await get_compound(pubchem_id=top_candidate["id"])
        >>> compound["name"]
        "Aspirin"

        # Error: Invalid CURIE format
        >>> result = await get_compound(pubchem_id="CID2244")
        >>> result["success"]
        False
        >>> result["error"]["code"]
        "UNRESOLVED_ENTITY"
        >>> result["error"]["recovery_hint"]
        "Use format 'PubChem:CID{number}' (e.g., 'PubChem:CID2244'). Call search_compounds to find valid CIDs."

        # Error: Compound not found
        >>> result = await get_compound(pubchem_id="PubChem:CID999999999999")
        >>> result["success"]
        False
        >>> result["error"]["code"]
        "ENTITY_NOT_FOUND"
        >>> result["error"]["recovery_hint"]
        "CID not found in PubChem. Verify CURIE from search_compounds results."
    """
    client = get_client()
    result = await client.get_compound(pubchem_id=pubchem_id, slim=slim)

    if isinstance(result, ErrorEnvelope):
        return result.model_dump()

    # Convert PubChemCompound to dict
    return result.model_dump()
