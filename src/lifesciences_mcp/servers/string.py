"""STRING MCP Server - Protein-protein interactions using the Fuzzy-to-Fact protocol.

This server provides three tools for protein interaction analysis:
- search_proteins: Fuzzy search returning ranked candidates
- get_interactions: Strict lookup by STRING CURIE
- get_network_image_url: Generate network visualization URL

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/string.py
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients.string import STRINGClient
from lifesciences_mcp.models import (
    ErrorEnvelope,
    PaginationEnvelope,
)
from lifesciences_mcp.models.interaction import (
    InteractionNetwork,
    InteractionSearchCandidate,
)

# Initialize the MCP server
mcp = FastMCP("STRING Protein Interactions Server")

# Shared client instance (connection pooling)
_client: STRINGClient | None = None


async def get_client() -> STRINGClient:
    """Get or create the shared STRING client."""
    global _client
    if _client is None:
        _client = STRINGClient()
    return _client


@mcp.tool
async def search_proteins(
    query: str,
    species: int = 9606,
    limit: int = 10,
    cursor: str | None = None,
) -> PaginationEnvelope[InteractionSearchCandidate] | ErrorEnvelope:
    """Fuzzy search for proteins by name, gene symbol, or identifier.

    Returns ranked candidates for resolution. Use this before calling get_interactions.

    Args:
        query: Search term (gene symbol, protein name, or identifier).
               Minimum 2 characters required.
        species: NCBI Taxonomy ID (default 9606 for Homo sapiens).
                 Common species: 9606 (human), 10090 (mouse), 10116 (rat).
        limit: Number of results per page (1-100, default 10).
        cursor: Opaque cursor for pagination. Pass from previous response for next page.

    Returns:
        PaginationEnvelope with InteractionSearchCandidate items, or ErrorEnvelope on failure.

    Example:
        # Search for TP53 in human
        result = await search_proteins("TP53", species=9606)
        # Top candidate: STRING:9606.ENSP00000269305
    """
    client = await get_client()
    return await client.search_proteins(
        query=query,
        species=species,
        limit=limit,
        cursor=cursor,
    )


@mcp.tool
async def get_interactions(
    string_id: str,
    required_score: int = 400,
    limit: int = 10,
) -> InteractionNetwork | ErrorEnvelope:
    """Get protein-protein interactions by STRING CURIE.

    Returns the interaction network with evidence scores for each edge.
    Requires resolved CURIE from search_proteins.

    Args:
        string_id: STRING CURIE in format 'STRING:<taxid>.ENSP<id>'
                   (e.g., 'STRING:9606.ENSP00000269305' for TP53).
        required_score: Minimum combined confidence score (0-1000).
                        400 = medium confidence (default).
                        700 = high confidence.
                        900 = highest confidence.
        limit: Maximum number of interactions to return.

    Returns:
        InteractionNetwork with interactions and evidence scores, or ErrorEnvelope on failure.

    Example:
        # Get high-confidence interactions for TP53
        result = await get_interactions(
            "STRING:9606.ENSP00000269305",
            required_score=700,
            limit=10
        )
        # Returns MDM2, ATM, BRCA1 interactions with evidence breakdown
    """
    client = await get_client()
    return await client.get_interactions(
        string_id=string_id,
        required_score=required_score,
        limit=limit,
    )


@mcp.tool
def get_network_image_url(
    identifiers: str,
    species: int = 9606,
    add_nodes: int = 10,
    network_flavor: str = "confidence",
) -> str:
    """Generate a STRING network visualization URL.

    Returns a URL that can be used to display the protein interaction network.
    The URL points to a high-resolution PNG image.

    Args:
        identifiers: Gene symbol(s) or STRING ID(s), separated by newlines.
                     Example: "TP53" or "TP53\\nMDM2\\nBRCA1"
        species: NCBI Taxonomy ID (default 9606 for Homo sapiens).
        add_nodes: Number of additional interaction partners to include (default 10).
        network_flavor: Visual style for edges:
                        - 'confidence': Edge thickness shows confidence score (default)
                        - 'evidence': Edge color shows evidence type
                        - 'actions': Edge color shows effect type

    Returns:
        URL string for the network visualization image.

    Example:
        url = get_network_image_url("TP53", species=9606, add_nodes=10)
        # Returns: https://string-db.org/api/highres_image/network?identifiers=TP53&species=9606&add_nodes=10
    """
    # Use synchronous URL construction (no client needed)
    base_url = "https://string-db.org/api"

    # Handle multiple identifiers
    if "\\n" in identifiers:
        identifiers = identifiers.replace("\\n", "%0d")

    return (
        f"{base_url}/highres_image/network"
        f"?identifiers={identifiers}"
        f"&species={species}"
        f"&add_nodes={add_nodes}"
        f"&network_flavor={network_flavor}"
    )


if __name__ == "__main__":
    mcp.run()
