"""BioGRID MCP Server for genetic and protein interaction queries.

This server exposes BioGRID API functionality via FastMCP protocol,
following ADR-001 Agentic Biolink schema and Fuzzy-to-Fact workflow.
"""

from typing import Any

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
    query: str, organism: int = 9606, slim: bool = False
) -> PaginationEnvelope[BioGridSearchCandidate] | ErrorEnvelope:
    """Search for a gene in BioGRID and confirm it exists (Fuzzy Phase 1).

    Queries BioGRID to confirm the gene exists in the database and returns
    the interaction count. Use the confirmed symbol in get_interactions for
    strict lookup.

    Args:
        query: Gene symbol to search (e.g., "TP53", "brca1")
        organism: NCBI Taxonomy ID (default: 9606 for Homo sapiens)
        slim: Token budgeting (Constitution Principle IV). No behavior change
            since search candidates are already minimal (~30 tokens).

    Returns:
        PaginationEnvelope with confirmed gene and interaction_count, or ErrorEnvelope

    Examples:
        >>> search_genes("TP53")  # Confirmed in BioGRID with interaction count
        >>> search_genes("brca1")  # Normalized to "BRCA1", confirmed via API
        >>> search_genes("ZZZZZ99")  # ENTITY_NOT_FOUND: gene not in BioGRID

    Error Codes:
        - AMBIGUOUS_QUERY: Query too short or invalid format
        - ENTITY_NOT_FOUND: Gene not found in BioGRID database
        - UPSTREAM_ERROR: BioGRID API error (invalid key, timeout, etc.)
        - RATE_LIMITED: Rate limit exceeded (2 req/sec)
    """
    client = get_client()
    return await client.search_genes(query, organism, slim=slim)


@mcp.tool()
async def get_interactions(
    gene_symbol: str,
    organism: int = 9606,
    max_results: int = 10000,
    include_interspecies: bool = False,
    slim: bool = False,
) -> InteractionResult | dict[str, Any] | ErrorEnvelope:
    """Get genetic/protein interactions for a validated gene symbol (Strict Phase 2).

    Retrieves experimentally validated interactions from BioGRID with evidence types.
    Requires a validated gene symbol from search_genes tool.

    Args:
        gene_symbol: Validated gene symbol (uppercase, e.g., "TP53")
        organism: NCBI Taxonomy ID (default: 9606 for Homo sapiens)
        max_results: Max interactions to return (default/max: 10000)
        include_interspecies: Include interspecies interactions (default: False)
        slim: Token budgeting (Constitution Principle IV). When True, returns
            minimal fields (~15 tokens/interaction): symbol_b and
            experimental_system_type only, plus counts. Default: False.

    Returns:
        InteractionResult (full), slim dict, or ErrorEnvelope on error

    Examples:
        >>> get_interactions("TP53")  # Full interaction records
        >>> get_interactions("TP53", slim=True)  # Minimal fields for token budgeting
        >>> get_interactions("MDM2", max_results=100)  # Limit results

    Error Codes:
        - AMBIGUOUS_QUERY: Invalid gene symbol format
        - ENTITY_NOT_FOUND: No interactions found for gene
        - UPSTREAM_ERROR: BioGRID API error (invalid key, timeout, etc.)
        - RATE_LIMITED: Rate limit exceeded (2 req/sec)

    Note:
        Full mode includes experimental_system (e.g., "Affinity Capture-Western"),
        experimental_system_type ("physical" or "genetic"), PubMed ID, and throughput.
        Slim mode returns only symbol_b and experimental_system_type per interaction.
    """
    client = get_client()
    return await client.get_interactions(
        gene_symbol, organism, max_results, include_interspecies, slim=slim
    )
