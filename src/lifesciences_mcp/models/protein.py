"""Protein data models for UniProt API responses.

This module provides Pydantic models for representing protein entities from UniProt,
including complete protein records and lightweight search candidates.
"""

import re

from pydantic import BaseModel, Field, field_validator

from lifesciences_mcp.models.cross_references import CrossReferences

# UniProt CURIE validation pattern (from R6 research)
# Format: UniProtKB:[A-Z][A-Z0-9]{5,9}
# Examples: UniProtKB:P04637 (6-char), UniProtKB:A0A123B4C5 (10-char)
UNIPROT_CURIE_PATTERN = re.compile(r"^UniProtKB:[A-Z][A-Z0-9]{5,9}$")


class ProteinSearchCandidate(BaseModel):
    """Lightweight protein match for fuzzy search results.

    Represents a candidate protein from search results with minimal fields
    to reduce token usage (~20 tokens per entity in slim mode).
    """

    id: str = Field(
        ...,
        description="UniProt CURIE in format 'UniProtKB:XXXXXX' (e.g., 'UniProtKB:P04637')",
    )
    name: str = Field(..., description="Protein name")
    organism: str = Field(..., description="Scientific name (e.g., 'Homo sapiens')")
    gene_names: list[str] | None = Field(default=None, description="Associated gene symbols")
    score: float = Field(..., description="Relevance score (0.0-1.0)", ge=0.0, le=1.0)

    @field_validator("score")
    @classmethod
    def validate_score_bounds(cls, v: float) -> float:
        """Ensure score is within valid bounds."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {v}")
        return v


class Protein(BaseModel):
    """Complete protein record from UniProt with Agentic Biolink cross-references.

    Represents a full protein entity with all available metadata, including
    cross-references to related databases (HGNC, Ensembl, PDB, etc.).
    """

    id: str = Field(
        ...,
        description="UniProt CURIE in format 'UniProtKB:XXXXXX' (e.g., 'UniProtKB:P04637')",
    )
    accession: str = Field(..., description="Raw UniProt accession ID (e.g., 'P04637')")
    name: str = Field(..., description="Protein name")
    full_name: str | None = Field(default=None, description="Recommended full name")
    gene_names: list[str] | None = Field(default=None, description="Associated gene symbols")
    organism: str = Field(..., description="Scientific name (e.g., 'Homo sapiens')")
    organism_id: int | None = Field(default=None, description="NCBI Taxonomy ID")
    function: str | None = Field(default=None, description="Functional description")
    sequence_length: int | None = Field(default=None, description="Amino acid sequence length")
    cross_references: CrossReferences = Field(
        default_factory=CrossReferences,
        description="Cross-references to external databases using 22-key registry",
    )

    @field_validator("id")
    @classmethod
    def validate_curie_format(cls, v: str) -> str:
        """Validate UniProt CURIE format using R6 research pattern.

        Format: UniProtKB:[A-Z][A-Z0-9]{5,9}
        - Must start with 'UniProtKB:'
        - Followed by uppercase letter
        - Then 5-9 uppercase letters or digits
        - Total accession length: 6-10 characters

        Examples:
            ✓ UniProtKB:P04637 (6-char Swiss-Prot)
            ✓ UniProtKB:A0A123B4C5 (10-char TrEMBL)
            ✗ P04637 (missing prefix)
            ✗ UniProtKB:p04637 (lowercase)
        """
        if not UNIPROT_CURIE_PATTERN.match(v):
            raise ValueError(
                f"Invalid UniProt CURIE format. Expected 'UniProtKB:XXXXXX' "
                f"where X is 6-10 uppercase alphanumeric characters starting "
                f"with a letter, got: {v}"
            )
        return v
