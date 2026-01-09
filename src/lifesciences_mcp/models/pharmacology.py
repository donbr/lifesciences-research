"""Pharmacology domain models for IUPHAR/GtoPdb MCP Server.

This module defines Pydantic models for pharmacological entities (ligands and targets)
following the Agentic Biolink schema defined in ADR-001.

IUPHAR/GtoPdb (Guide to PHARMACOLOGY) provides curated data on:
- Ligands: Drugs, chemical compounds, peptides, antibodies
- Targets: Receptors, enzymes, ion channels, transporters

All models use the 22-key cross-reference registry for interoperability with
other life sciences databases (ChEMBL, DrugBank, UniProt, HGNC, Ensembl, etc.).
"""

import re
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator

from lifesciences_mcp.models.cross_references import CrossReferences

# IUPHAR CURIE pattern: "IUPHAR:12345"
IUPHAR_CURIE_PATTERN = re.compile(r"^IUPHAR:\d+$")

# HTML tag stripping pattern for target names
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


# =============================================================================
# Ligand Models
# =============================================================================


class LigandSearchCandidate(BaseModel):
    """Lightweight ligand match for fuzzy search results.

    Used in slim mode to reduce token usage (~20 tokens per entity).
    Contains only essential fields for agent decision-making.

    Implements Constitution Principle IV (Token Budgeting).
    """

    id: Annotated[
        str,
        Field(pattern=r"^IUPHAR:\d+$", description="IUPHAR ligand CURIE (e.g., 'IUPHAR:2713')"),
    ]
    name: str = Field(description="Ligand display name (e.g., 'ibuprofen')")
    type: str = Field(description="Ligand classification (e.g., 'Synthetic organic', 'Peptide')")
    approved: bool = Field(default=False, description="Whether ligand is an approved drug")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")

    @field_validator("id")
    @classmethod
    def validate_iuphar_curie(cls, v: str) -> str:
        """Validate IUPHAR CURIE format."""
        if not IUPHAR_CURIE_PATTERN.match(v):
            msg = f"Invalid IUPHAR CURIE format: {v}"
            raise ValueError(msg)
        return v


class Ligand(BaseModel):
    """Complete ligand record from GtoPdb with Agentic Biolink cross-references.

    Represents pharmacological compounds including drugs, metabolites, peptides,
    and antibodies from the IUPHAR/BPS Guide to PHARMACOLOGY.

    Full record returned by get_ligand (~100-200 tokens depending on cross-refs).

    Implements ADR-001 Section 4 (Agentic Biolink Schema) and
    Constitution Principle III (Schema Determinism).
    """

    # Core identifiers
    id: Annotated[str, Field(pattern=r"^IUPHAR:\d+$", description="IUPHAR ligand CURIE")]
    ligand_id: int = Field(description="Raw GtoPdb numeric identifier")

    # Names and classification
    name: str = Field(description="Display name (e.g., 'ibuprofen')")
    approved_name: str | None = Field(
        default=None, description="International Nonproprietary Name (INN) if available"
    )
    type: str = Field(description="Ligand classification")
    abbreviation: str | None = Field(
        default=None, description="Short name/abbreviation if available"
    )

    # Regulatory status
    approved: bool = Field(default=False, description="Regulatory approval status")
    approval_source: str | None = Field(
        default=None, description="Approval source (e.g., 'FDA (1974), EMA (2004)')"
    )
    who_essential: bool | None = Field(
        default=None, description="WHO essential medicine list status"
    )
    withdrawn: bool | None = Field(default=None, description="Drug withdrawal status")

    # Synonyms
    synonyms: list[str] | None = Field(
        default=None, description="Brand names and alternative names"
    )

    # Cross-references (uses 22-key registry from ADR-001)
    cross_references: CrossReferences = Field(
        default_factory=CrossReferences,
        description="External database identifiers (ChEMBL, DrugBank, PubChem)",
    )

    @field_validator("id")
    @classmethod
    def validate_iuphar_curie(cls, v: str) -> str:
        """Validate IUPHAR CURIE format."""
        if not IUPHAR_CURIE_PATTERN.match(v):
            msg = f"Invalid IUPHAR CURIE format: {v}"
            raise ValueError(msg)
        return v

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize to dict with exclude_none for omit-if-null pattern.

        Implements Constitution Principle III (Schema Determinism).
        """
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def to_search_candidate(self, score: float = 1.0) -> LigandSearchCandidate:
        """Convert to LigandSearchCandidate for search results."""
        return LigandSearchCandidate(
            id=self.id,
            name=self.name,
            type=self.type,
            approved=self.approved,
            score=score,
        )


# =============================================================================
# Target Models
# =============================================================================


class TargetSearchCandidate(BaseModel):
    """Lightweight target match for fuzzy search results.

    Used in slim mode to reduce token usage (~20 tokens per entity).
    Contains only essential fields for agent decision-making.

    Implements Constitution Principle IV (Token Budgeting).
    """

    id: Annotated[
        str,
        Field(pattern=r"^IUPHAR:\d+$", description="IUPHAR target CURIE (e.g., 'IUPHAR:215')"),
    ]
    name: str = Field(description="Target display name (HTML stripped, e.g., 'D2 receptor')")
    family: str = Field(description="Target family/class (e.g., 'GPCR', 'Enzyme')")
    type: str = Field(description="Full classification type")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")

    @field_validator("id")
    @classmethod
    def validate_iuphar_curie(cls, v: str) -> str:
        """Validate IUPHAR CURIE format."""
        if not IUPHAR_CURIE_PATTERN.match(v):
            msg = f"Invalid IUPHAR CURIE format: {v}"
            raise ValueError(msg)
        return v


class Target(BaseModel):
    """Complete target record from GtoPdb with Agentic Biolink cross-references.

    Represents pharmacological targets including GPCRs, ion channels, enzymes,
    transporters, and other proteins from the IUPHAR/BPS Guide to PHARMACOLOGY.

    Full record returned by get_target (~100-200 tokens depending on cross-refs).

    Implements ADR-001 Section 4 (Agentic Biolink Schema) and
    Constitution Principle III (Schema Determinism).
    """

    # Core identifiers
    id: Annotated[str, Field(pattern=r"^IUPHAR:\d+$", description="IUPHAR target CURIE")]
    target_id: int = Field(description="Raw GtoPdb numeric identifier")

    # Names and classification
    name: str = Field(description="Target display name (HTML stripped)")
    target_family: str = Field(description="Target family classification (GPCR, Enzyme, etc.)")
    family_ids: list[int] | None = Field(
        default=None, description="Parent family IDs for hierarchy navigation"
    )

    # Species and gene info
    species: str = Field(default="Homo sapiens", description="Primary species (defaults to human)")
    gene_symbol: str | None = Field(default=None, description="Human gene symbol if available")

    # Cross-references (uses 22-key registry from ADR-001)
    cross_references: CrossReferences = Field(
        default_factory=CrossReferences,
        description="External database identifiers (UniProt, Ensembl, HGNC)",
    )

    @field_validator("id")
    @classmethod
    def validate_iuphar_curie(cls, v: str) -> str:
        """Validate IUPHAR CURIE format."""
        if not IUPHAR_CURIE_PATTERN.match(v):
            msg = f"Invalid IUPHAR CURIE format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("name", mode="before")
    @classmethod
    def strip_html_from_name(cls, v: str) -> str:
        """Strip HTML tags from target name.

        GtoPdb uses HTML tags in target names (e.g., D<sub>2</sub> receptor).
        This validator removes all HTML tags for clean agent consumption.
        """
        return HTML_TAG_PATTERN.sub("", v)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize to dict with exclude_none for omit-if-null pattern.

        Implements Constitution Principle III (Schema Determinism).
        """
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def to_search_candidate(self, score: float = 1.0) -> TargetSearchCandidate:
        """Convert to TargetSearchCandidate for search results."""
        return TargetSearchCandidate(
            id=self.id,
            name=self.name,
            family=self.target_family,
            type=self.target_family,  # Same as family for consistency
            score=score,
        )
