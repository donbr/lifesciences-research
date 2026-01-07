"""Ensembl-related Pydantic models for Ensembl MCP Server.

Models follow the Agentic Biolink schema defined in ADR-001.
See specs/008-ensembl-mcp-server/data-model.md for entity definitions.

Entities:
- GeneSearchCandidate: Lightweight gene for fuzzy search results
- EnsemblGene: Complete gene record with cross-references
- EnsemblTranscript: Transcript record with cross-references
- EnsemblCrossReferences: External database identifiers per ADR-001
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# Ensembl ID patterns per research.md R3
ENSEMBL_GENE_PATTERN = re.compile(r"^ENSG\d{11}$")
ENSEMBL_TRANSCRIPT_PATTERN = re.compile(r"^ENST\d{11}$")

# Cross-reference regex patterns from ADR-001 Appendix A
HGNC_PATTERN = re.compile(r"^HGNC:\d+$")
UNIPROT_PATTERN = re.compile(r"^[A-Z0-9]{6,10}$")
ENTREZ_PATTERN = re.compile(r"^\d+$")
REFSEQ_PATTERN = re.compile(r"^[NX][MPRG]_\d+(\.\d+)?$")
OMIM_PATTERN = re.compile(r"^\d{6}$")
PDB_PATTERN = re.compile(r"^[0-9][A-Z0-9]{3}$")
KEGG_PATTERN = re.compile(r"^[a-z]{3,4}:\d+$")
CHEMBL_PATTERN = re.compile(r"^CHEMBL\d+$")
STRING_PATTERN = re.compile(r"^\d+\.[A-Za-z0-9]+$")
BIOGRID_PATTERN = re.compile(r"^\d+$")


class EnsemblCrossReferences(BaseModel):
    """External database identifiers per ADR-001 22-key registry.

    Keys are omitted if no value exists (never null or empty string).
    All values are validated against their respective regex patterns.

    This is Ensembl-specific, containing the 12 Ensembl-relevant keys.
    """

    # Core identifiers
    hgnc: str | None = Field(
        default=None,
        description="HGNC ID with prefix (e.g., HGNC:11998)",
    )
    ensembl_gene: str | None = Field(
        default=None,
        description="Ensembl Gene ID (self-reference for transcripts)",
    )
    ensembl_transcript: list[str] | None = Field(
        default=None,
        description="Ensembl Transcript IDs",
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

    # Disease/phenotype
    omim: str | None = Field(
        default=None,
        description="OMIM ID",
    )

    # Structural
    pdb: list[str] | None = Field(
        default=None,
        description="PDB structure IDs",
    )

    # Pathway/drug
    kegg: str | None = Field(
        default=None,
        description="KEGG gene ID",
    )
    chembl: str | None = Field(
        default=None,
        description="ChEMBL target ID",
    )

    # Interactions
    string: str | None = Field(
        default=None,
        description="STRING protein ID",
    )
    biogrid: str | None = Field(
        default=None,
        description="BioGRID protein ID",
    )

    @model_validator(mode="after")
    def omit_empty_values(self) -> "EnsemblCrossReferences":
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


class GeneSearchCandidate(BaseModel):
    """Lightweight gene representation for fuzzy search results.

    Used in search_genes to return ranked candidates with minimal tokens (~25 tokens).
    """

    id: Annotated[str, Field(pattern=r"^ENSG\d{11}$", description="Ensembl Gene ID")]
    symbol: str = Field(description="Official gene symbol")
    name: str = Field(description="Gene description/name")
    biotype: str = Field(description="Gene biotype (e.g., protein_coding)")
    species: str = Field(description="Species name (e.g., homo_sapiens)")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")

    @field_validator("id")
    @classmethod
    def validate_ensembl_gene_id(cls, v: str) -> str:
        """Validate Ensembl Gene ID format."""
        if not ENSEMBL_GENE_PATTERN.match(v):
            msg = f"Invalid Ensembl Gene ID format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: float) -> float:
        """Validate score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            msg = f"Score must be between 0.0 and 1.0, got: {v}"
            raise ValueError(msg)
        return round(v, 2)


class EnsemblGene(BaseModel):
    """Complete gene record from Ensembl with Agentic Biolink cross-references.

    This is the full record returned by get_gene (~150-350 tokens depending on xrefs).
    """

    id: Annotated[str, Field(pattern=r"^ENSG\d{11}$", description="Ensembl Gene ID")]
    symbol: str = Field(description="Official gene symbol")
    name: str = Field(description="Gene description/name")
    biotype: str = Field(description="Gene biotype (e.g., protein_coding, lncRNA)")
    species: str = Field(description="Species name (e.g., homo_sapiens)")
    assembly_name: str = Field(description="Genome assembly (e.g., GRCh38)")
    chromosome: str = Field(description="Chromosome/seq_region_name")
    start: int = Field(description="Genomic start position")
    end: int = Field(description="Genomic end position")
    strand: int = Field(description="Strand (+1 or -1)")
    transcripts: list[str] | None = Field(
        default=None,
        description="List of Ensembl Transcript IDs for this gene",
    )
    cross_references: EnsemblCrossReferences = Field(
        default_factory=EnsemblCrossReferences,
        description="External database identifiers",
    )

    @field_validator("id")
    @classmethod
    def validate_ensembl_gene_id(cls, v: str) -> str:
        """Validate Ensembl Gene ID format."""
        if not ENSEMBL_GENE_PATTERN.match(v):
            msg = f"Invalid Ensembl Gene ID format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("strand")
    @classmethod
    def validate_strand(cls, v: int) -> int:
        """Validate strand is +1 or -1."""
        if v not in (1, -1):
            msg = f"Strand must be 1 or -1, got: {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_coordinates(self) -> "EnsemblGene":
        """Validate start is less than end."""
        if self.start >= self.end:
            msg = f"Start ({self.start}) must be less than end ({self.end})"
            raise ValueError(msg)
        return self

    def to_search_candidate(self, score: float = 1.0) -> GeneSearchCandidate:
        """Convert to GeneSearchCandidate for search results."""
        return GeneSearchCandidate(
            id=self.id,
            symbol=self.symbol,
            name=self.name,
            biotype=self.biotype,
            species=self.species,
            score=score,
        )


class EnsemblTranscript(BaseModel):
    """Transcript record from Ensembl with cross-references.

    Returned by get_transcript (~100-200 tokens depending on xrefs).
    """

    id: Annotated[str, Field(pattern=r"^ENST\d{11}$", description="Ensembl Transcript ID")]
    display_name: str = Field(description="Transcript display name (e.g., TP53-201)")
    biotype: str = Field(description="Transcript biotype")
    parent_gene: Annotated[
        str, Field(pattern=r"^ENSG\d{11}$", description="Parent Ensembl Gene ID")
    ]
    is_canonical: bool = Field(default=False, description="Is canonical transcript")
    species: str = Field(description="Species name")
    assembly_name: str = Field(description="Genome assembly")
    chromosome: str = Field(description="Chromosome")
    start: int = Field(description="Genomic start position")
    end: int = Field(description="Genomic end position")
    strand: int = Field(description="Strand (+1 or -1)")
    cross_references: EnsemblCrossReferences = Field(
        default_factory=EnsemblCrossReferences,
        description="External database identifiers",
    )

    @field_validator("id")
    @classmethod
    def validate_ensembl_transcript_id(cls, v: str) -> str:
        """Validate Ensembl Transcript ID format."""
        if not ENSEMBL_TRANSCRIPT_PATTERN.match(v):
            msg = f"Invalid Ensembl Transcript ID format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("parent_gene")
    @classmethod
    def validate_parent_gene_id(cls, v: str) -> str:
        """Validate parent gene ID format."""
        if not ENSEMBL_GENE_PATTERN.match(v):
            msg = f"Invalid parent Ensembl Gene ID format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("strand")
    @classmethod
    def validate_strand(cls, v: int) -> int:
        """Validate strand is +1 or -1."""
        if v not in (1, -1):
            msg = f"Strand must be 1 or -1, got: {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_coordinates(self) -> "EnsemblTranscript":
        """Validate start is less than end."""
        if self.start >= self.end:
            msg = f"Start ({self.start}) must be less than end ({self.end})"
            raise ValueError(msg)
        return self
