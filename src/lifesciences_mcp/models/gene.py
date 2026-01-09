"""Gene-related Pydantic models for HGNC MCP Server.

Models follow the Agentic Biolink schema defined in ADR-001.
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# HGNC CURIE pattern: HGNC:NNNNN
HGNC_CURIE_PATTERN = re.compile(r"^HGNC:\d+$")

# Cross-reference regex patterns from ADR-001 Appendix A
from lifesciences_mcp.models.cross_references import CrossReferences 


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
