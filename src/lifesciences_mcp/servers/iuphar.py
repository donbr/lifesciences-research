"""IUPHAR/GtoPdb MCP Server.

This FastMCP server provides tools for querying pharmacological data from
Guide to PHARMACOLOGY (GtoPdb).

Tools:
- search_ligands: Fuzzy search for drugs, chemicals, peptides
- get_ligand: Strict lookup by IUPHAR CURIE
- search_targets: Fuzzy search for receptors, enzymes, ion channels
- get_target: Strict lookup by IUPHAR CURIE

Follows the Fuzzy-to-Fact protocol defined in ADR-001.
"""

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from lifesciences_mcp.clients.iuphar import IUPHARClient

# Initialize FastMCP server
mcp = FastMCP("IUPHAR/GtoPdb")

# Module-level singleton client (per ADR-004)
_client: IUPHARClient | None = None


def get_client() -> IUPHARClient:
    """Get or create the singleton IUPHARClient instance."""
    global _client
    if _client is None:
        _client = IUPHARClient()
    return _client


# =============================================================================
# User Story 1: Fuzzy Ligand Search
# =============================================================================


@mcp.tool()
async def search_ligands(
    query: Annotated[
        str,
        Field(
            min_length=2, description="Search query for ligand name (e.g., 'ibuprofen', 'NSAID')"
        ),
    ],
    type_filter: Annotated[
        str | None,
        Field(
            default=None,
            description="Optional ligand type filter (e.g., 'Synthetic organic', 'Peptide', 'Antibody')",
        ),
    ] = None,
    approved_only: Annotated[
        bool,
        Field(
            default=False,
            description="Filter for approved drugs only",
        ),
    ] = False,
    cursor: Annotated[
        str | None,
        Field(
            default=None,
            description="Pagination cursor from previous response",
        ),
    ] = None,
    page_size: Annotated[
        int,
        Field(
            default=50,
            ge=1,
            le=100,
            description="Results per page (default 50, max 100)",
        ),
    ] = 50,
) -> dict:
    """Search for pharmacological ligands (drugs, chemicals, peptides) using fuzzy name matching.

    This tool implements Phase 1 of the Fuzzy-to-Fact protocol for ligand discovery.
    Results are ranked by relevance with position-based scoring.

    Use cases:
    - Find approved drugs: search_ligands("aspirin", approved_only=True)
    - Search by drug class: search_ligands("NSAID")
    - Filter by type: search_ligands("insulin", type_filter="Peptide")
    - Browse all ligands: search_ligands("a", page_size=100)

    Once you have a candidate, use get_ligand(iuphar_id) for complete details.

    Examples:
        # Search for ibuprofen
        >>> search_ligands("ibuprofen")
        {
            "items": [
                {
                    "id": "IUPHAR:2713",
                    "name": "ibuprofen",
                    "type": "Synthetic organic",
                    "approved": true,
                    "score": 1.0
                }
            ],
            "pagination": {"cursor": null, "total_count": 1, "page_size": 50}
        }

        # Search for COX inhibitors
        >>> search_ligands("COX inhibitor")
        {
            "items": [
                {"id": "IUPHAR:2713", "name": "ibuprofen", ...},
                {"id": "IUPHAR:4139", "name": "aspirin", ...}
            ],
            "pagination": {...}
        }

    Returns:
        PaginationEnvelope with LigandSearchCandidate items, sorted by relevance.
        Each candidate includes: id (IUPHAR CURIE), name, type, approved status, score.
    """
    client = get_client()
    return await client.search_ligands(
        query=query,
        type_filter=type_filter,
        approved_only=approved_only,
        cursor=cursor,
        page_size=page_size,
    )


# =============================================================================
# User Story 2: Strict Ligand Lookup
# =============================================================================


@mcp.tool()
async def get_ligand(
    iuphar_id: Annotated[
        str,
        Field(
            pattern=r"^IUPHAR:\d+$",
            description="IUPHAR ligand CURIE (e.g., 'IUPHAR:2713' for ibuprofen)",
        ),
    ],
) -> dict:
    """Get complete ligand record by IUPHAR CURIE with full cross-references.

    This tool implements Phase 2 of the Fuzzy-to-Fact protocol for ligand retrieval.
    Requires an exact IUPHAR CURIE from search_ligands results.

    Use cases:
    - Get complete drug details after fuzzy search
    - Retrieve cross-references to ChEMBL, DrugBank, PubChem
    - Access regulatory information (approval status, WHO essential list)
    - Get brand names and synonyms

    Workflow:
        1. First: search_ligands("ibuprofen") → Get IUPHAR:2713
        2. Then: get_ligand("IUPHAR:2713") → Get complete record

    Examples:
        # Get ibuprofen details
        >>> get_ligand("IUPHAR:2713")
        {
            "id": "IUPHAR:2713",
            "ligand_id": 2713,
            "name": "ibuprofen",
            "approved_name": "ibuprofen",
            "type": "Synthetic organic",
            "approved": true,
            "approval_source": "FDA (1974)",
            "who_essential": true,
            "synonyms": ["Advil", "Motrin", "Nurofen"],
            "cross_references": {
                "chembl": "521",
                "drugbank": "DB01050",
                "pubchem_compound": "3672"
            }
        }

        # Invalid format (will fail)
        >>> get_ligand("ibuprofen")
        ERROR: Invalid IUPHAR CURIE format. Use search_ligands() first.

        # Non-existent ID (will fail)
        >>> get_ligand("IUPHAR:999999")
        ERROR: Ligand not found. Try get_target() instead.

    Returns:
        Complete Ligand entity with all available fields and cross-references.
        Fields with no data are omitted (never null).

    Errors:
        - UNRESOLVED_ENTITY: Invalid CURIE format → Use search_ligands() first
        - ENTITY_NOT_FOUND: ID not found → Try get_target() (shared ID space)
    """
    client = get_client()
    return await client.get_ligand(iuphar_id=iuphar_id)


# =============================================================================
# User Story 3: Fuzzy Target Search
# =============================================================================


@mcp.tool()
async def search_targets(
    query: Annotated[
        str,
        Field(
            min_length=2,
            description="Search query for target name (e.g., 'dopamine receptor', 'GPCR')",
        ),
    ],
    type_filter: Annotated[
        str | None,
        Field(
            default=None,
            description="Optional target type filter (e.g., 'GPCR', 'Enzyme', 'Ion channel')",
        ),
    ] = None,
    cursor: Annotated[
        str | None,
        Field(
            default=None,
            description="Pagination cursor from previous response",
        ),
    ] = None,
    page_size: Annotated[
        int,
        Field(
            default=50,
            ge=1,
            le=100,
            description="Results per page (default 50, max 100)",
        ),
    ] = 50,
) -> dict:
    """Search for pharmacological targets (receptors, enzymes, ion channels) using fuzzy name matching.

    This tool implements Phase 1 of the Fuzzy-to-Fact protocol for target discovery.
    Results are ranked by relevance with position-based scoring.

    Use cases:
    - Find receptors by name: search_targets("dopamine")
    - Search by gene symbol: search_targets("DRD2")
    - Filter by type: search_targets("receptor", type_filter="GPCR")
    - Browse all targets: search_targets("a", page_size=100)

    Note: The GtoPdb API works best with single-word queries. For multi-word searches,
    use the most specific term or filter through results client-side.

    Once you have a candidate, use get_target(iuphar_id) for complete details.

    Examples:
        # Search for dopamine targets
        >>> search_targets("dopamine")
        {
            "items": [
                {
                    "id": "IUPHAR:214",
                    "name": "D2 receptor",
                    "family": "GPCR",
                    "type": "GPCR",
                    "score": 1.0
                }
            ],
            "pagination": {"cursor": null, "total_count": 7, "page_size": 50}
        }

        # Search for GPCRs
        >>> search_targets("receptor", type_filter="GPCR")
        {
            "items": [
                {"id": "IUPHAR:214", "name": "D2 receptor", ...},
                {"id": "IUPHAR:1", "name": "5-HT1A receptor", ...}
            ],
            "pagination": {...}
        }

    Returns:
        PaginationEnvelope with TargetSearchCandidate items, sorted by relevance.
        Each candidate includes: id (IUPHAR CURIE), name, family, type, score.
    """
    client = get_client()
    return await client.search_targets(
        query=query,
        type_filter=type_filter,
        cursor=cursor,
        page_size=page_size,
    )


# =============================================================================
# User Story 4: Strict Target Lookup
# =============================================================================


@mcp.tool()
async def get_target(
    iuphar_id: Annotated[
        str,
        Field(
            pattern=r"^IUPHAR:\d+$",
            description="IUPHAR target CURIE (e.g., 'IUPHAR:215' for D2 receptor)",
        ),
    ],
) -> dict:
    """Get complete target record by IUPHAR CURIE with full cross-references.

    This tool implements Phase 2 of the Fuzzy-to-Fact protocol for target retrieval.
    Requires an exact IUPHAR CURIE from search_targets results.

    Use cases:
    - Get complete target details after fuzzy search
    - Retrieve cross-references to UniProt, Ensembl, HGNC, RefSeq
    - Access gene symbols and protein information
    - Link targets to external databases

    Workflow:
        1. First: search_targets("dopamine") → Get IUPHAR:215
        2. Then: get_target("IUPHAR:215") → Get complete record

    Examples:
        # Get D2 receptor details
        >>> get_target("IUPHAR:215")
        {
            "id": "IUPHAR:215",
            "target_id": 215,
            "name": "D2 receptor",
            "target_family": "GPCR",
            "family_ids": [20],
            "species": "Homo sapiens",
            "gene_symbol": "DRD2",
            "cross_references": {
                "uniprot": ["P14416"],
                "ensembl_gene": "ENSG00000149295",
                "hgnc": "HGNC:3023",
                "entrez": "1813",
                "refseq": ["NM_000795"]
            }
        }

        # Invalid format (will fail)
        >>> get_target("DRD2")
        ERROR: Invalid IUPHAR CURIE format. Use search_targets() first.

        # Non-existent ID (will fail)
        >>> get_target("IUPHAR:999999")
        ERROR: Target not found. Try get_ligand() instead.

    Returns:
        Complete Target entity with all available fields and cross-references.
        Fields with no data are omitted (never null).

    Errors:
        - UNRESOLVED_ENTITY: Invalid CURIE format → Use search_targets() first
        - ENTITY_NOT_FOUND: ID not found → Try get_ligand() (shared ID space)
    """
    client = get_client()
    return await client.get_target(iuphar_id=iuphar_id)
