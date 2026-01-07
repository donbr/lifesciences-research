"""Ensembl MCP Server - Gene and transcript resolution using the Fuzzy-to-Fact protocol.

This server provides three tools for genomic data access:
- search_genes: Fuzzy search returning ranked gene candidates
- get_gene: Strict lookup by Ensembl Gene ID (ENSG*)
- get_transcript: Strict lookup by Ensembl Transcript ID (ENST*)

Implements the Fuzzy-to-Fact protocol per ADR-001 Section 3:
1. Fuzzy Phase: Agents discover entities via search_genes
2. Strict Phase: Agents retrieve complete records via get_gene/get_transcript

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/ensembl.py
    uv run fastmcp dev src/lifesciences_mcp/servers/ensembl.py

See specs/008-ensembl-mcp-server/ for full documentation.
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients.ensembl import EnsemblClient
from lifesciences_mcp.models.ensembl import (
    EnsemblGene,
    EnsemblTranscript,
    GeneSearchCandidate,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

# Initialize the MCP server
mcp = FastMCP("Ensembl Genomics Server")

# Module-level singleton client (per ADR-004)
_client: EnsemblClient | None = None


async def get_client() -> EnsemblClient:
    """Get or create the shared Ensembl client."""
    global _client
    if _client is None:
        _client = EnsemblClient()
    return _client


@mcp.tool
async def search_genes(
    query: str,
    species: str = "homo_sapiens",
    page_size: int = 50,
    cursor: str | None = None,
    slim: bool = False,
) -> PaginationEnvelope[GeneSearchCandidate] | ErrorEnvelope:
    """Fuzzy search for genes by symbol, name, or description.

    Returns ranked candidates with Ensembl Gene IDs for Phase 2 strict lookup.
    This is Phase 1 of the Fuzzy-to-Fact protocol - use before calling get_gene.

    Args:
        query: Search term (gene symbol, name, or description).
               Minimum 2 characters required.
               Examples: "BRCA1", "TP53", "tumor protein"
        species: Species name or alias. Default is "homo_sapiens" (human).
                 Supported aliases: human, mouse, rat, zebrafish, drosophila, fly,
                 c.elegans, worm, yeast, chicken, pig, dog, cow.
        page_size: Number of results per page (1-100, default 50).
        cursor: Opaque cursor for pagination. Pass from previous response for next page.
        slim: If true, return minimal fields (~25 tokens per entity).
              Default false returns full candidates.

    Returns:
        PaginationEnvelope with GeneSearchCandidate items (id, symbol, name, biotype, species, score).
        On error: ErrorEnvelope with code, message, recovery_hint.

    Example:
        >>> result = await search_genes("BRCA1", species="human")
        >>> top_gene_id = result.items[0].id  # "ENSG00000012048"
        >>> gene = await get_gene(top_gene_id)  # Phase 2: strict lookup
    """
    client = await get_client()
    return await client.search_genes(
        query=query,
        species=species,
        page_size=page_size,
        cursor=cursor,
        slim=slim,
    )


@mcp.tool
async def get_gene(
    ensembl_id: str,
    slim: bool = False,
) -> EnsemblGene | ErrorEnvelope:
    """Get complete gene record by Ensembl Gene ID.

    Returns full Agentic Biolink entity with cross-references.
    Requires resolved ENSG* ID from search_genes (Phase 2 of Fuzzy-to-Fact).

    Args:
        ensembl_id: Ensembl Gene ID in format 'ENSG' + 11 digits.
                    Example: "ENSG00000141510" (TP53), "ENSG00000012048" (BRCA1).
                    Versioned IDs are accepted (e.g., "ENSG00000141510.12").
        slim: If true, omit cross_references to reduce token count.
              Full mode: ~150-350 tokens, Slim mode: ~50 tokens.

    Returns:
        EnsemblGene with:
        - id, symbol, name, biotype, species
        - assembly_name, chromosome, start, end, strand
        - transcripts: list of ENST* IDs for this gene
        - cross_references: HGNC, UniProt, Entrez, RefSeq, OMIM, PDB, KEGG, ChEMBL

        On error: ErrorEnvelope with code, message, recovery_hint.
        - UNRESOLVED_ENTITY: Invalid ID format (use search_genes first)
        - ENTITY_NOT_FOUND: Valid format but gene doesn't exist
        - RATE_LIMITED: Too many requests (retry after delay)
        - UPSTREAM_ERROR: Ensembl API unavailable (retry later)

    Example:
        >>> gene = await get_gene("ENSG00000141510")
        >>> print(gene.symbol)  # "TP53"
        >>> print(gene.cross_references.hgnc)  # "HGNC:11998"
    """
    client = await get_client()
    return await client.get_gene(ensembl_id=ensembl_id, slim=slim)


@mcp.tool
async def get_transcript(
    transcript_id: str,
    slim: bool = False,
) -> EnsemblTranscript | ErrorEnvelope:
    """Get transcript record by Ensembl Transcript ID.

    Returns full transcript details with parent gene reference.
    Typically obtained from get_gene's transcripts list.

    Args:
        transcript_id: Ensembl Transcript ID in format 'ENST' + 11 digits.
                       Example: "ENST00000269305" (TP53 canonical transcript).
                       Versioned IDs are accepted (e.g., "ENST00000269305.8").
        slim: If true, omit cross_references to reduce token count.
              Full mode: ~100-200 tokens, Slim mode: ~50 tokens.

    Returns:
        EnsemblTranscript with:
        - id, display_name, biotype, parent_gene
        - is_canonical: whether this is the canonical transcript
        - species, assembly_name, chromosome, start, end, strand
        - cross_references: UniProt, RefSeq, CCDS

        On error: ErrorEnvelope with code, message, recovery_hint.
        - UNRESOLVED_ENTITY: Invalid ID format or wrong ID type (ENSG passed instead of ENST)
        - ENTITY_NOT_FOUND: Valid format but transcript doesn't exist
        - RATE_LIMITED: Too many requests (retry after delay)
        - UPSTREAM_ERROR: Ensembl API unavailable (retry later)

    Example:
        >>> gene = await get_gene("ENSG00000141510")
        >>> transcript = await get_transcript(gene.transcripts[0])
        >>> print(transcript.display_name)  # "TP53-201"
        >>> print(transcript.is_canonical)  # True
    """
    client = await get_client()
    return await client.get_transcript(transcript_id=transcript_id, slim=slim)


if __name__ == "__main__":
    mcp.run()
