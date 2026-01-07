"""Gene-related Pydantic models for HGNC MCP Server.

Models follow the Agentic Biolink schema defined in ADR-001.
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# HGNC CURIE pattern: HGNC:NNNNN
HGNC_CURIE_PATTERN = re.compile(r"^HGNC:\d+$")

# Cross-reference regex patterns from ADR-001 Appendix A
CROSS_REF_PATTERNS = {
    "ensembl_gene": re.compile(r"^ENSG\d{11}$"),
    "ensembl_transcript": re.compile(r"^ENST\d{11}$"),
    "uniprot": re.compile(r"^[A-Z0-9]{6,10}$"),
    "entrez": re.compile(r"^\d+$"),
    "refseq": re.compile(r"^[NX][MR]_\d+$"),
    "omim": re.compile(r"^\d{6}$"),
    "chembl": re.compile(r"^CHEMBL\d+$"),
    "pubchem_compound": re.compile(r"^\d+$"),
}


class CrossReferences(BaseModel):
    """External database identifiers per ADR-001 22-key registry.

    Keys are omitted if no value exists (never null or empty string).
    All values are validated against their respective regex patterns.
    """

    # Core identifiers
    ensembl_gene: str | None = Field(
        default=None,
        description="Ensembl gene ID (e.g., ENSG00000012048)",
    )
    ensembl_transcript: list[str] | None = Field(
        default=None,
        description="Ensembl transcript IDs",
    )
    uniprot: list[str] | None = Field(
        default=None,
        description="UniProt accessions",
    )
    entrez: str | None = Field(
        default=None,
        description="NCBI Entrez gene ID",
    )
    refseq: list[str] | None = Field(
        default=None,
        description="RefSeq accessions",
    )
    hgnc: str | None = Field(
        default=None,
        description="HGNC gene ID (e.g., HGNC:5)",
    )

    # Disease/phenotype
    omim: str | None = Field(
        default=None,
        description="OMIM ID",
    )
    orphanet: str | None = Field(
        default=None,
        description="Orphanet rare disease ID (e.g., ORPHA:558)",
    )
    mondo: str | None = Field(
        default=None,
        description="MONDO disease ontology ID",
    )
    efo: str | None = Field(
        default=None,
        description="Experimental Factor Ontology ID",
    )

    # Drug/compound
    chembl: str | None = Field(
        default=None,
        description="ChEMBL target/compound ID",
    )
    drugbank: str | None = Field(
        default=None,
        description="DrugBank ID (e.g., DB01050)",
    )
    pubchem_compound: str | None = Field(
        default=None,
        description="PubChem compound ID",
    )
    pubchem_substance: str | None = Field(
        default=None,
        description="PubChem substance ID",
    )

    # Pathway databases
    kegg: str | None = Field(
        default=None,
        description="KEGG gene ID",
    )
    kegg_pathway: list[str] | None = Field(
        default=None,
        description="KEGG pathway IDs",
    )

    # Interaction databases
    string: str | None = Field(
        default=None,
        description="STRING protein ID",
    )
    biogrid: str | None = Field(
        default=None,
        description="BioGRID gene ID",
    )
    stitch: str | None = Field(
        default=None,
        description="STITCH chemical-protein interaction ID",
    )
    iuphar: str | None = Field(
        default=None,
        description="IUPHAR/GtoPdb ligand or target ID",
    )

    # Structural
    pdb: list[str] | None = Field(
        default=None,
        description="Protein Data Bank IDs",
    )

    @model_validator(mode="after")
    def omit_empty_values(self) -> "CrossReferences":
        """Ensure no empty strings or empty lists are stored (omit instead)."""
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if value == "" or value == []:
                setattr(self, field_name, None)
        return self

    def model_dump(self, **kwargs) -> dict:
        """Override to exclude None values (ADR-001: omit keys with no value)."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class SearchCandidate(BaseModel):
    """Lightweight gene representation for fuzzy search results.

    Used in slim mode to reduce token usage (~20 tokens per entity).
    """

    id: Annotated[str, Field(pattern=r"^HGNC:\d+$", description="HGNC CURIE")]
    symbol: str = Field(description="Official gene symbol")
    name: str = Field(description="Full gene name")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")

    @field_validator("id")
    @classmethod
    def validate_hgnc_curie(cls, v: str) -> str:
        """Validate HGNC CURIE format."""
        if not HGNC_CURIE_PATTERN.match(v):
            msg = f"Invalid HGNC CURIE format: {v}"
            raise ValueError(msg)
        return v


class Gene(BaseModel):
    """Complete gene record from HGNC with Agentic Biolink cross-references.

    This is the full record returned by get_gene (~115-300 tokens depending on cross-refs).
    """

    id: Annotated[str, Field(pattern=r"^HGNC:\d+$", description="HGNC CURIE")]
    symbol: str = Field(description="Official gene symbol")
    name: str = Field(description="Full gene name")
    status: str = Field(description="Approval status: Approved, Withdrawn, Entry Withdrawn")
    locus_type: str | None = Field(default=None, description="Gene type classification")
    locus_group: str | None = Field(default=None, description="Gene group classification")
    location: str | None = Field(default=None, description="Chromosomal location")
    alias_symbols: list[str] | None = Field(default=None, description="Alternative symbols")
    alias_names: list[str] | None = Field(default=None, description="Alternative names")
    prev_symbols: list[str] | None = Field(default=None, description="Previous symbols")
    prev_names: list[str] | None = Field(default=None, description="Previous names")
    cross_references: CrossReferences = Field(
        default_factory=CrossReferences,
        description="External database identifiers",
    )

    @field_validator("id")
    @classmethod
    def validate_hgnc_curie(cls, v: str) -> str:
        """Validate HGNC CURIE format."""
        if not HGNC_CURIE_PATTERN.match(v):
            msg = f"Invalid HGNC CURIE format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate gene status."""
        valid_statuses = {"Approved", "Withdrawn", "Entry Withdrawn"}
        if v not in valid_statuses:
            msg = f"Invalid status: {v}. Must be one of {valid_statuses}"
            raise ValueError(msg)
        return v

    def to_search_candidate(self, score: float = 1.0) -> SearchCandidate:
        """Convert to SearchCandidate for search results."""
        return SearchCandidate(
            id=self.id,
            symbol=self.symbol,
            name=self.name,
            score=score,
        )
