"""Pydantic models for Open Targets target and association entities.

This module provides models for the Fuzzy-to-Fact protocol:
- TargetSearchCandidate: Lightweight search results for fuzzy discovery
- Target: Complete target record with cross-references
- Association: Target-disease association with evidence scores

All models follow the Agentic Biolink schema (ADR-001 §4) and
Constitution Principle III (Schema Determinism).
"""

import re

from pydantic import BaseModel, Field, field_validator

from lifesciences_mcp.models.cross_references import CrossReferences

# Regex patterns for ID validation (from research.md R3)
ENSEMBL_GENE_ID_PATTERN = re.compile(r"^ENSG\d{11}$")
# Open Targets uses multiple disease ontologies: EFO, MONDO, Orphanet, HP, DOID, OTAR
DISEASE_ID_PATTERN = re.compile(r"^(EFO|MONDO|Orphanet|HP|DOID|OTAR)_\d+$")


class TargetSearchCandidate(BaseModel):
    """Lightweight target search result for fuzzy discovery.

    Token Budget: ~20-30 tokens in slim mode, ~40-50 tokens in full mode

    Implements User Story 1 (Fuzzy Target Search) per spec.md FR-002-FR-006.
    """

    id: str = Field(
        ...,
        description="Ensembl gene ID in format ENSG[11 digits] (e.g., 'ENSG00000141510')",
    )

    approved_symbol: str | None = Field(
        None,
        description="HGNC approved gene symbol (e.g., 'TP53', 'BRCA1')",
    )

    approved_name: str | None = Field(
        None,
        description="HGNC approved gene name",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (1.0 = perfect match, decreasing linearly)",
    )

    @field_validator("id")
    @classmethod
    def validate_ensembl_id(cls, v: str) -> str:
        """Validate Ensembl gene ID format."""
        if not ENSEMBL_GENE_ID_PATTERN.match(v):
            raise ValueError(f"Invalid Ensembl gene ID format: {v}. Must match ENSG[11 digits]")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "ENSG00000141510",
                    "approved_symbol": "TP53",
                    "approved_name": "tumor protein p53",
                    "score": 1.0,
                }
            ]
        }
    }


class Target(BaseModel):
    """Complete Open Targets target record with Agentic Biolink cross-references.

    Token Budget: ~115-300 tokens in full mode, ~20 tokens in slim mode

    Implements User Story 2 (Strict Target Lookup) per spec.md FR-007-FR-010.
    """

    id: str = Field(
        ...,
        description="Ensembl gene ID in format ENSG[11 digits]",
    )

    approved_symbol: str | None = Field(
        None,
        description="HGNC approved gene symbol",
    )

    approved_name: str | None = Field(
        None,
        description="HGNC approved gene name",
    )

    biotype: str | None = Field(
        None,
        description="Gene biotype (e.g., 'protein_coding', 'lncRNA')",
    )

    description: str | None = Field(
        None,
        description="Gene function description (excluded in slim mode)",
    )

    associated_diseases_count: int | None = Field(
        None,
        ge=0,
        description="Total number of associated diseases in Open Targets (excluded in slim mode)",
    )

    cross_references: CrossReferences = Field(
        default_factory=CrossReferences,
        description="Cross-references to other biological databases (22-key registry, excluded in slim mode)",
    )

    @field_validator("id")
    @classmethod
    def validate_ensembl_id(cls, v: str) -> str:
        """Validate Ensembl gene ID format."""
        if not ENSEMBL_GENE_ID_PATTERN.match(v):
            raise ValueError(f"Invalid Ensembl gene ID format: {v}. Must match ENSG[11 digits]")
        return v

    def to_slim(self) -> dict:
        """Return slim mode representation (~20 tokens).

        Excludes: description, associated_diseases_count, cross_references
        """
        return {
            "id": self.id,
            "approved_symbol": self.approved_symbol,
            "approved_name": self.approved_name,
            "biotype": self.biotype,
        }

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "ENSG00000141510",
                    "approved_symbol": "TP53",
                    "approved_name": "tumor protein p53",
                    "biotype": "protein_coding",
                    "description": "Tumor suppressor gene involved in cell cycle regulation",
                    "associated_diseases_count": 245,
                    "cross_references": {
                        "hgnc": "HGNC:11998",
                        "uniprot": "UniProtKB:P04637",
                        "ensembl_gene": "ENSG00000141510",
                        "entrez": "7157",
                        "omim": "191170",
                        "chembl": "CHEMBL:1993",
                    },
                }
            ]
        }
    }


class Association(BaseModel):
    """Target-disease association with aggregated evidence.

    Token Budget: ~60-80 tokens per association (no slim mode)

    Implements User Story 3 (Target-Disease Association Discovery) per spec.md FR-011-FR-013.
    """

    target_id: str = Field(
        ...,
        description="Ensembl gene ID",
    )

    disease_id: str = Field(
        ...,
        description="EFO disease ID (e.g., 'EFO_0000616' for neoplasm)",
    )

    disease_name: str = Field(
        ...,
        description="Human-readable disease name",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall association score (0.0-1.0, higher = stronger evidence)",
    )

    evidence_count: int = Field(
        ...,
        ge=0,
        description="Total number of evidence sources supporting this association",
    )

    evidence_sources: list[str] = Field(
        default_factory=list,
        description="Data type IDs (e.g., 'genetic_association', 'somatic_mutation')",
    )

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, v: str) -> str:
        """Validate Ensembl gene ID format."""
        if not ENSEMBL_GENE_ID_PATTERN.match(v):
            raise ValueError(f"Invalid Ensembl gene ID format: {v}. Must match ENSG[11 digits]")
        return v

    @field_validator("disease_id")
    @classmethod
    def validate_disease_id(cls, v: str) -> str:
        """Validate EFO disease ID format."""
        if not DISEASE_ID_PATTERN.match(v):
            raise ValueError(
                f"Invalid disease ID format: {v}. Must match EFO_/MONDO_/Orphanet_/HP_/DOID_/OTAR_[digits]"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "target_id": "ENSG00000141510",
                    "disease_id": "EFO_0000616",
                    "disease_name": "neoplasm",
                    "score": 0.85,
                    "evidence_count": 142,
                    "evidence_sources": ["genetic_association", "somatic_mutation", "drugs"],
                }
            ]
        }
    }
