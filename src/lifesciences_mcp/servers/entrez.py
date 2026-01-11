"""NCBI Entrez MCP Server - Gene resolution using the Fuzzy-to-Fact protocol.

This server provides three tools for gene discovery and literature links:
- search_genes: Fuzzy search returning ranked candidates with NCBIGene CURIEs
- get_gene: Strict lookup by NCBIGene CURIE with cross-references
- get_pubmed_links: Get PubMed IDs associated with a gene

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/entrez.py

Reference: specs/009-entrez-mcp-server/
"""

from typing import Any

from fastmcp import FastMCP

from lifesciences_mcp.clients.entrez import EntrezClient
from lifesciences_mcp.models.entrez import (
    EntrezGene,
    GeneSearchCandidate,
)
from lifesciences_mcp.models.envelopes import (
    ErrorEnvelope,
    PaginationEnvelope,
)

# Initialize the MCP server
mcp = FastMCP("NCBI Entrez Gene Server")

# Shared client instance (connection pooling) per ADR-004
_client: EntrezClient | None = None


async def get_client() -> EntrezClient:
    """Get or create the shared Entrez client."""
    global _client
    if _client is None:
        _client = EntrezClient()
    return _client


@mcp.tool
async def search_genes(
    query: str,
    organism: str | None = "human",
    page_size: int = 50,
    cursor: str | None = None,
) -> PaginationEnvelope[GeneSearchCandidate] | ErrorEnvelope:
    """Fuzzy search for genes in NCBI Gene database by symbol, name, or description.

    Returns ranked candidates with NCBIGene CURIEs for Phase 2 strict lookup.
    Uses NCBI E-utilities esearch + esummary two-step pattern.

    Args:
        query: Search term (gene symbol, name, description, or natural language).
               Minimum 2 characters required.
        organism: Organism filter (e.g., "human", "Homo sapiens", "mouse").
                  Default: "human" (Homo sapiens). Pass None for all organisms.
        page_size: Number of results per page (1-100, default 50).
        cursor: Opaque cursor for pagination (from previous response).

    Returns:
        PaginationEnvelope with GeneSearchCandidate items containing:
        - id: NCBIGene CURIE (e.g., "NCBIGene:7157")
        - symbol: Gene symbol (e.g., "TP53")
        - name: Gene name/description
        - organism: Scientific name
        - score: Relevance score (0.0-1.0)

        Or ErrorEnvelope with recovery hints on failure.

    Examples:
        Search for TP53: query="TP53", organism="human"
        Search for BRCA genes: query="BRCA"
        Paginate results: cursor=<cursor from previous response>
    """
    client = await get_client()
    return await client.search_genes(
        query=query,
        organism=organism,
        page_size=page_size,
        cursor=cursor,
    )


@mcp.tool
async def get_gene(
    entrez_id: str,
    slim: bool = False,
) -> EntrezGene | dict[str, Any] | ErrorEnvelope:
    """Get complete gene record from NCBI Gene database by NCBIGene CURIE.

    Returns full Agentic Biolink entity with cross-references to HGNC, Ensembl,
    UniProt, RefSeq, and OMIM. Requires resolved CURIE from search_genes.

    Args:
        entrez_id: NCBIGene CURIE in format 'NCBIGene:NNNNN'
                   (e.g., 'NCBIGene:7157' for TP53, 'NCBIGene:672' for BRCA1).
        slim: If True, return minimal fields (id, symbol, name, organism)
              for token efficiency (~25 vs ~115-300 tokens).

    Returns:
        EntrezGene record with:
        - id, symbol, name, organism (always present)
        - summary, description, map_location, chromosome, aliases (full mode)
        - cross_references: HGNC, Ensembl, UniProt, RefSeq, OMIM links

        Or ErrorEnvelope with recovery hints on failure.

    Examples:
        Get TP53: entrez_id="NCBIGene:7157"
        Get BRCA1 slim: entrez_id="NCBIGene:672", slim=True
    """
    client = await get_client()
    return await client.get_gene(entrez_id=entrez_id, slim=slim)


@mcp.tool
async def get_pubmed_links(
    entrez_id: str,
    limit: int = 10,
) -> list[str] | ErrorEnvelope:
    """Get PubMed IDs associated with a gene for evidence gathering.

    Returns list of PubMed IDs linked to the gene. Use these IDs with a
    PubMed MCP server for full article metadata.

    Args:
        entrez_id: NCBIGene CURIE in format 'NCBIGene:NNNNN'
                   (e.g., 'NCBIGene:7157' for TP53).
        limit: Maximum number of PubMed IDs to return (1-100, default 10).

    Returns:
        List of PubMed ID strings (e.g., ["39804234", "39804163"]).
        Empty list if gene has no associated literature (not an error).

        Or ErrorEnvelope with recovery hints on failure.

    Examples:
        Get TP53 citations: entrez_id="NCBIGene:7157", limit=10
        Get top 5 BRCA1 papers: entrez_id="NCBIGene:672", limit=5
    """
    client = await get_client()
    return await client.get_pubmed_links(entrez_id=entrez_id, limit=limit)


if __name__ == "__main__":
    mcp.run()
