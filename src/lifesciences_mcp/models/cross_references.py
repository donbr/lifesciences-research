"""Core identifier models for Life Sciences MCP Server.

This module defines general-purpose identifier models and validation patterns
used across multiple domain models (Gene, Protein, Target, etc.).

Refactored from models/gene.py to decouple Protocol Types from Domain Types.
"""

import re

from pydantic import BaseModel, Field, model_validator

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

    # Genomic location
    ucsc: str | None = Field(
        default=None,
        description="UCSC Genome Browser ID (e.g., UCSC:uc001kfb.4)",
    )

    # Literature
    pubmed: list[str] | None = Field(
        default=None,
        description="Related PubMed IDs (e.g., PMID:123456)",
    )

    def model_dump(self, **kwargs) -> dict:
        """Override to exclude None values (ADR-001: omit keys with no value)."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)
