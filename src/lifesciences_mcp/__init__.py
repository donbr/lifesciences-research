"""Life Sciences MCP - FastMCP wrappers for life sciences APIs.

This package provides MCP servers for querying biological databases:
- HGNC: Gene nomenclature and symbol resolution
- UniProt: Protein sequence and annotation data
- ChEMBL: Compound and bioactivity data
- Open Targets: Target-disease associations and evidence
- DrugBank: Drug and drug target information
- PubChem: Chemical compound data and cross-references
- IUPHAR/GtoPdb: Pharmacological ligands and targets
- WikiPathways: Biological pathway database

Usage:
    # Run HGNC server
    uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py

    # Run UniProt server
    uv run fastmcp run src/lifesciences_mcp/servers/uniprot.py

    # Run ChEMBL server
    uv run fastmcp run src/lifesciences_mcp/servers/chembl.py

    # Run Open Targets server
    uv run fastmcp run src/lifesciences_mcp/servers/opentargets.py

    # Run DrugBank server
    uv run fastmcp run src/lifesciences_mcp/servers/drugbank.py

    # Run PubChem server
    uv run fastmcp run src/lifesciences_mcp/servers/pubchem.py

    # Run IUPHAR server
    uv run fastmcp run src/lifesciences_mcp/servers/iuphar.py

    # Run WikiPathways server
    uv run fastmcp run src/lifesciences_mcp/servers/wikipathways.py
"""

__version__ = "0.1.0"

# Re-export key components for convenience
from lifesciences_mcp.clients import (
    ChEMBLClient,
    ClinicalTrialsClient,
    DrugBankClient,
    HGNCClient,
    IUPHARClient,
    LifeSciencesClient,
    OpenTargetsClient,
    PubChemClient,
    UniProtClient,
    WikiPathwaysClient,
)
from lifesciences_mcp.models import (
    Compound,
    CompoundSearchCandidate,
    CrossReferences,
    ErrorEnvelope,
    Gene,
    Ligand,
    LigandSearchCandidate,
    PaginationEnvelope,
    PharmacologicalTarget,
    PharmacologicalTargetSearchCandidate,
    Protein,
    ProteinSearchCandidate,
    PubChemCompound,
    PubChemSearchCandidate,
    SearchCandidate,
)

__all__ = [
    "ChEMBLClient",
    "ClinicalTrialsClient",
    "Compound",
    "CompoundSearchCandidate",
    "CrossReferences",
    "DrugBankClient",
    "ErrorEnvelope",
    "Gene",
    "HGNCClient",
    "IUPHARClient",
    "LifeSciencesClient",
    "Ligand",
    "LigandSearchCandidate",
    "OpenTargetsClient",
    "PaginationEnvelope",
    "PharmacologicalTarget",
    "PharmacologicalTargetSearchCandidate",
    "Protein",
    "ProteinSearchCandidate",
    "PubChemClient",
    "PubChemCompound",
    "PubChemSearchCandidate",
    "SearchCandidate",
    "UniProtClient",
    "WikiPathwaysClient",
]
