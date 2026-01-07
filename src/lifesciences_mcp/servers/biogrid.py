"""BioGRID MCP Server for genetic and protein interaction queries.

This server exposes BioGRID API functionality via FastMCP protocol,
following ADR-001 Agentic Biolink schema and Fuzzy-to-Fact workflow.
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients.biogrid import BioGridClient
from lifesciences_mcp.models.biogrid import (
    BioGridSearchCandidate,
    InteractionResult,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

# Initialize FastMCP server
mcp = FastMCP("biogrid")

# Module-level singleton client (per ADR-004)
_client: BioGridClient | None = None


def get_client() -> BioGridClient:
    """Get or create singleton BioGridClient instance."""
    global _client
    if _client is None:
        _client = BioGridClient()
    return _client


@mcp.tool()
async def search_genes(
    query: str, organism: int = 9606
) -> PaginationEnvelope[BioGridSearchCandidate] | ErrorEnvelope:
    """Validate gene symbol for BioGRID interaction queries (Fuzzy Phase 1).

    This tool validates gene symbol format and normalizes to uppercase.
    Use the validated symbol in get_interactions tool for strict lookup.

    Args:
        query: Gene symbol to validate (e.g., "TP53", "brca1")
        organism: NCBI Taxonomy ID (default: 9606 for Homo sapiens)

    Returns:
        PaginationEnvelope with validated gene symbol or ErrorEnvelope on error

    Examples:
        >>> search_genes("TP53")  # Valid gene
        >>> search_genes("brca1")  # Will be normalized to "BRCA1"
        >>> search_genes("X")  # Error: too short

    Error Codes:
        - AMBIGUOUS_QUERY: Query too short or invalid format
    """
    client = get_client()
    return await client.search_genes(query, organism)


@mcp.tool()
async def get_interactions(
    gene_symbol: str,
    organism: int = 9606,
    max_results: int = 10000,
    include_interspecies: bool = False,
) -> InteractionResult | ErrorEnvelope:
    """Get genetic/protein interactions for a validated gene symbol (Strict Phase 2).

    Retrieves experimentally validated interactions from BioGRID with evidence types.
    Requires a validated gene symbol from search_genes tool.

    Args:
        gene_symbol: Validated gene symbol (uppercase, e.g., "TP53")
        organism: NCBI Taxonomy ID (default: 9606 for Homo sapiens)
        max_results: Max interactions to return (default/max: 10000)
        include_interspecies: Include interspecies interactions (default: False)

    Returns:
        InteractionResult with interaction network or ErrorEnvelope on error

    Examples:
        >>> get_interactions("TP53")  # Get TP53 interactions
        >>> get_interactions("MDM2", max_results=100)  # Limit results
        >>> get_interactions("TP53", include_interspecies=True)  # Include cross-species

    Error Codes:
        - AMBIGUOUS_QUERY: Invalid gene symbol format
        - ENTITY_NOT_FOUND: No interactions found for gene
        - UPSTREAM_ERROR: BioGRID API error (invalid key, timeout, etc.)
        - RATE_LIMITED: Rate limit exceeded (2 req/sec)

    Note:
        Interactions include experimental_system (e.g., "Affinity Capture-Western"),
        experimental_system_type ("physical" or "genetic"), PubMed ID, and throughput.
    """
    client = get_client()
    return await client.get_interactions(gene_symbol, organism, max_results, include_interspecies)
