"""Pydantic models for NCBI Entrez MCP Server.

This module defines data models for NCBI Gene entities following the
Agentic Biolink schema (ADR-001 Section 4) and data-model.md specification.

Models:
- GeneSearchCandidate: Lightweight search result for fuzzy gene discovery
- EntrezGene: Complete gene record with cross-references
- EntrezCrossReferences: Cross-database links for Entrez genes

Reference: specs/009-entrez-mcp-server/data-model.md
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# CURIE validation pattern for NCBIGene identifiers per research.md R6
NCBI_GENE_CURIE_PATTERN = re.compile(r"^NCBIGene:\d+$")


class GeneSearchCandidate(BaseModel):
    """Lightweight gene search result for fuzzy discovery.

    Token Budget: ~30-40 tokens in slim mode, ~60-80 tokens in full mode

    This model is used in Phase 1 of the Fuzzy-to-Fact protocol,
    returned by search_genes to enable agent triage before strict lookup.
    """

    id: str = Field(
        ...,
        description="NCBIGene CURIE in format NCBIGene:<numeric_id>",
        examples=["NCBIGene:7157", "NCBIGene:672"],
    )

    symbol: str = Field(
        ...,
        description="Official gene symbol from NCBI Gene",
        examples=["TP53", "BRCA1", "EGFR"],
    )

    name: str = Field(
        ...,
        description="Full gene name/description",
        examples=["tumor protein p53", "BRCA1 DNA repair associated"],
    )

    description: str | None = Field(
        None,
        description="Additional gene description or designations",
        examples=["cellular tumor antigen p53; phosphoprotein p53; antigen NY-CO-13"],
    )

    organism: str = Field(
        ...,
        description="Scientific name of the organism",
        examples=["Homo sapiens", "Mus musculus"],
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (1.0 = first result, decreasing by position)",
    )

    @field_validator("id")
    @classmethod
    def validate_ncbi_gene_curie(cls, v: str) -> str:
        """Validate NCBIGene CURIE format."""
        if not NCBI_GENE_CURIE_PATTERN.match(v):
            raise ValueError(
                f"Invalid NCBIGene CURIE format. Expected 'NCBIGene:NNNNN' "
                f"where N is a numeric digit, got: {v}"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "NCBIGene:7157",
                    "symbol": "TP53",
                    "name": "tumor protein p53",
                    "description": "cellular tumor antigen p53; phosphoprotein p53",
                    "organism": "Homo sapiens",
                    "score": 1.0,
                }
            ]
        }
    }


class EntrezCrossReferences(BaseModel):
    """Cross-references to biological databases for Entrez genes.

    Follows the 22-key Agentic Biolink registry per ADR-001 Section 4.
    Constitution Principle III: Omit keys entirely if no reference exists.
    """

    hgnc: str | None = Field(
        None,
        description="HGNC gene nomenclature ID",
        examples=["HGNC:11998"],
    )

    ensembl_gene: str | None = Field(
        None,
        description="Ensembl gene ID",
        examples=["ENSG00000141510"],
    )

    ensembl_transcript: str | None = Field(
        None,
        description="Ensembl transcript ID",
        examples=["ENST00000269305"],
    )

    uniprot: str | list[str] | None = Field(
        None,
        description="UniProt accession(s)",
        examples=["UniProtKB:P04637", ["UniProtKB:P04637", "UniProtKB:P04637-2"]],
    )

    entrez: str | None = Field(
        None,
        description="NCBI Entrez Gene ID (for cross-reference from other entities)",
        examples=["7157"],
    )

    refseq: str | list[str] | None = Field(
        None,
        description="RefSeq accession(s)",
        examples=["NM_000546.6", ["NM_000546.6", "NP_000537.3"]],
    )

    omim: str | None = Field(
        None,
        description="OMIM gene/phenotype ID",
        examples=["191170"],
    )

    kegg: str | None = Field(
        None,
        description="KEGG gene ID",
        examples=["hsa:7157"],
    )

    string: str | None = Field(
        None,
        description="STRING protein ID",
        examples=["9606.ENSP00000269305"],
    )

    biogrid: str | None = Field(
        None,
        description="BioGRID gene/protein ID",
        examples=["113418"],
    )

    @model_validator(mode="before")
    @classmethod
    def omit_null_values(cls, data: Any) -> Any:
        """Remove None, empty string, and empty list values.

        Constitution Principle III: Never include null cross-references.
        """
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None and v != "" and v != []}
        return data

    model_config = {"extra": "allow"}  # Allow additional keys from 22-key registry


class EntrezGene(BaseModel):
    """Complete NCBI Gene record with Agentic Biolink cross-references.

    Token Budget: ~115-300 tokens in full mode, ~25 tokens in slim mode

    This model is used in Phase 2 of the Fuzzy-to-Fact protocol,
    returned by get_gene for complete gene information.
    """

    id: str = Field(
        ...,
        description="NCBIGene CURIE in format NCBIGene:<numeric_id>",
        examples=["NCBIGene:7157"],
    )

    symbol: str = Field(
        ...,
        description="Official gene symbol",
        examples=["TP53", "BRCA1"],
    )

    name: str = Field(
        ...,
        description="Full gene name/description",
        examples=["tumor protein p53"],
    )

    description: str | None = Field(
        None,
        description="Extended gene description from otherdesignations",
    )

    summary: str | None = Field(
        None,
        description="Functional summary of the gene (from Entrezgene_summary)",
    )

    map_location: str | None = Field(
        None,
        description="Cytogenetic map location",
        examples=["17p13.1", "17q21.31"],
    )

    chromosome: str | None = Field(
        None,
        description="Chromosome number or identifier",
        examples=["17", "X", "MT"],
    )

    aliases: list[str] | None = Field(
        None,
        description="Alternative gene symbols and names",
        examples=[["P53", "TRP53", "LFS1", "BCC7"]],
    )

    organism: str = Field(
        ...,
        description="Scientific name of the organism",
        examples=["Homo sapiens"],
    )

    taxon_id: int | None = Field(
        None,
        description="NCBI Taxonomy ID",
        examples=[9606, 10090],
    )

    cross_references: EntrezCrossReferences = Field(
        default_factory=EntrezCrossReferences,  # type: ignore[arg-type]
        description="Cross-references to other biological databases (22-key registry)",
    )

    @field_validator("id")
    @classmethod
    def validate_ncbi_gene_curie(cls, v: str) -> str:
        """Validate NCBIGene CURIE format."""
        if not NCBI_GENE_CURIE_PATTERN.match(v):
            raise ValueError(
                f"Invalid NCBIGene CURIE format. Expected 'NCBIGene:NNNNN' "
                f"where N is a numeric digit, got: {v}"
            )
        return v

    def to_slim(self) -> dict[str, Any]:
        """Return minimal fields for token efficiency.

        Returns only id, symbol, name, organism (~25 tokens).
        """
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "organism": self.organism,
        }

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "NCBIGene:7157",
                    "symbol": "TP53",
                    "name": "tumor protein p53",
                    "description": "cellular tumor antigen p53; phosphoprotein p53",
                    "summary": "This gene encodes a tumor suppressor protein...",
                    "map_location": "17p13.1",
                    "chromosome": "17",
                    "aliases": ["P53", "TRP53", "LFS1", "BCC7"],
                    "organism": "Homo sapiens",
                    "taxon_id": 9606,
                    "cross_references": {
                        "hgnc": "HGNC:11998",
                        "ensembl_gene": "ENSG00000141510",
                        "uniprot": "UniProtKB:P04637",
                        "refseq": "NM_000546.6",
                        "omim": "191170",
                    },
                }
            ]
        }
    }
