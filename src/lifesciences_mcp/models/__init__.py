"""Pydantic models for Life Sciences MCP."""

from lifesciences_mcp.models.biogrid import (
    BioGridCrossReferences,
    BioGridSearchCandidate,
    GeneticInteraction,
    InteractionResult,
)
from lifesciences_mcp.models.compound import Compound, CompoundSearchCandidate
from lifesciences_mcp.models.drug import (
    Drug,
    DrugCrossReferences,
    DrugSearchCandidate,
)
from lifesciences_mcp.models.ensembl import (
    EnsemblCrossReferences,
    EnsemblGene,
    EnsemblTranscript,
)
from lifesciences_mcp.models.ensembl import (
    GeneSearchCandidate as EnsemblGeneSearchCandidate,
)
from lifesciences_mcp.models.entrez import (
    NCBI_GENE_CURIE_PATTERN,
    EntrezCrossReferences,
    EntrezGene,
)
from lifesciences_mcp.models.entrez import (
    GeneSearchCandidate as EntrezGeneSearchCandidate,
)
from lifesciences_mcp.models.depmap import (
    CellModel,
    DepMapCrossReferences,
    DependencyRecord,
    GenotypeCohort,
    GenotypeContrast,
)
from lifesciences_mcp.models.envelopes import (
    ErrorDetail,
    ErrorEnvelope,
    Pagination,
    PaginationEnvelope,
)
from lifesciences_mcp.models.cross_references import CrossReferences
from lifesciences_mcp.models.gene import Gene, SearchCandidate
from lifesciences_mcp.models.interaction import (
    EvidenceScores,
    Interaction,
    InteractionCrossReferences,
    InteractionNetwork,
    InteractionSearchCandidate,
)
from lifesciences_mcp.models.pharmacology import (
    Ligand,
    LigandSearchCandidate,
)
from lifesciences_mcp.models.pharmacology import (
    Target as PharmacologicalTarget,
)
from lifesciences_mcp.models.pharmacology import (
    TargetSearchCandidate as PharmacologicalTargetSearchCandidate,
)
from lifesciences_mcp.models.protein import Protein, ProteinSearchCandidate
from lifesciences_mcp.models.pubchem_compound import (
    PUBCHEM_CURIE_PATTERN,
    PubChemCompound,
    PubChemSearchCandidate,
)
from lifesciences_mcp.models.target import Association, Target, TargetSearchCandidate
from lifesciences_mcp.models.pathway import (
    ComponentCounts,
    Pathway,
    PathwaySearchCandidate,
    RevisionMetadata,
)
from lifesciences_mcp.models.pathway_components import (
    DataNode,
    Interaction as PathwayInteraction,
    PathwayComponents,
)
from lifesciences_mcp.models.trial import (
    EligibilityCriteria,
    Outcome,
    Sponsor,
    Trial,
    TrialProtocol,
    TrialSearchCandidate,
)
from lifesciences_mcp.models.trial_location import TrialLocation

__all__ = [
    "NCBI_GENE_CURIE_PATTERN",
    "PUBCHEM_CURIE_PATTERN",
    "Association",
    "BioGridCrossReferences",
    "BioGridSearchCandidate",
    "Compound",
    "CompoundSearchCandidate",
    "ComponentCounts",
    "CrossReferences",
    "DataNode",
    "Drug",
    "DrugCrossReferences",
    "DrugSearchCandidate",
    "EligibilityCriteria",
    "EnsemblCrossReferences",
    "EnsemblGene",
    "EnsemblGeneSearchCandidate",
    "EnsemblTranscript",
    "EntrezCrossReferences",
    "EntrezGene",
    "EntrezGeneSearchCandidate",
    "ErrorDetail",
    "ErrorEnvelope",
    "EvidenceScores",
    "Gene",
    "GeneticInteraction",
    "Interaction",
    "InteractionCrossReferences",
    "InteractionNetwork",
    "InteractionResult",
    "InteractionSearchCandidate",
    "Ligand",
    "LigandSearchCandidate",
    "Outcome",
    "Pagination",
    "PaginationEnvelope",
    "Pathway",
    "PathwayComponents",
    "PathwayInteraction",
    "PathwaySearchCandidate",
    "PharmacologicalTarget",
    "PharmacologicalTargetSearchCandidate",
    "Protein",
    "ProteinSearchCandidate",
    "PubChemCompound",
    "PubChemSearchCandidate",
    "RevisionMetadata",
    "SearchCandidate",
    "Sponsor",
    "Target",
    "TargetSearchCandidate",
    "CellModel",
    "DepMapCrossReferences",
    "DependencyRecord",
    "GenotypeCohort",
    "GenotypeContrast",
    "Trial",
    "TrialLocation",
    "TrialProtocol",
    "TrialSearchCandidate",
]
