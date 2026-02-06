"""BioGRID data models for genetic and protein interactions.

This module implements Pydantic models for BioGRID API responses following
ADR-001 Agentic Biolink schema and Constitution Principle III (Schema Determinism).

Token Budget:
- Full mode: ~100 tokens/interaction (all fields)
- Slim mode: ~15 tokens/interaction (symbol_b + experimental_system_type only)
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Gene symbol validation pattern (allows alphanumeric, hyphens, underscores, and special chars)
# BioGRID returns diverse gene symbols including viral genes and non-standard nomenclature
GENE_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9\-_@.]{0,29}$")


class BioGridSearchCandidate(BaseModel):
    """Gene search result confirmed to exist in BioGRID (Fuzzy Phase 1)."""

    symbol: str = Field(..., description="Gene symbol (uppercase normalized)")
    organism: str = Field(..., description="Organism name")
    taxon_id: int = Field(..., description="NCBI Taxonomy ID", gt=0)
    interaction_count: int = Field(
        ..., description="Total interactions in BioGRID for this gene", ge=0
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate gene symbol format."""
        if not GENE_SYMBOL_PATTERN.match(v):
            raise ValueError(f"Invalid gene symbol format: {v}")
        return v


class GeneticInteraction(BaseModel):
    """Single genetic or protein-protein interaction from BioGRID."""

    biogrid_interaction_id: int = Field(
        ..., description="Unique BioGRID interaction identifier", gt=0
    )
    symbol_a: str = Field(..., description="Query gene symbol")
    symbol_b: str = Field(..., description="Interacting partner symbol")
    experimental_system: str = Field(..., description="Experimental method used")
    experimental_system_type: Literal["physical", "genetic"] = Field(
        ..., description="Interaction category"
    )
    pubmed_id: int | None = Field(None, description="PubMed ID for supporting publication", gt=0)
    throughput: str | None = Field(None, description="Study type classification")
    organism_a_id: int = Field(..., description="NCBI Taxonomy ID for gene A", gt=0)
    organism_b_id: int = Field(..., description="NCBI Taxonomy ID for gene B", gt=0)
    entrez_gene_a: int | None = Field(None, description="Entrez Gene ID for gene A", gt=0)
    entrez_gene_b: int | None = Field(None, description="Entrez Gene ID for gene B", gt=0)

    @field_validator("symbol_a", "symbol_b")
    @classmethod
    def validate_symbols(cls, v: str) -> str:
        """Validate gene symbols match pattern."""
        if not GENE_SYMBOL_PATTERN.match(v):
            raise ValueError(f"Invalid gene symbol format: {v}")
        return v


class BioGridCrossReferences(BaseModel):
    """Cross-database identifiers for BioGRID query gene.

    Per Constitution Principle III: Omit keys entirely if no reference exists.
    Never use null or empty string.
    """

    model_config = ConfigDict(exclude_none=True)

    entrez: str | None = Field(None, description="Entrez Gene ID", pattern=r"^[0-9]+$")


class InteractionResult(BaseModel):
    """Complete interaction network response from BioGRID."""

    query_gene: str = Field(..., description="Gene symbol queried")
    interactions: list[GeneticInteraction] = Field(..., description="List of interactions")
    cross_references: BioGridCrossReferences = Field(..., description="Cross-database identifiers")
    physical_count: int = Field(..., description="Number of physical interactions", ge=0)
    genetic_count: int = Field(..., description="Number of genetic interactions", ge=0)
    total_count: int = Field(..., description="Total interactions returned", ge=0)

    @field_validator("query_gene")
    @classmethod
    def validate_query_gene(cls, v: str) -> str:
        """Validate query gene symbol."""
        if not GENE_SYMBOL_PATTERN.match(v):
            raise ValueError(f"Invalid gene symbol format: {v}")
        return v

    @field_validator("total_count")
    @classmethod
    def validate_counts(cls, v: int, info) -> int:
        """Validate total_count equals physical_count + genetic_count and len(interactions)."""
        data = info.data
        if "physical_count" in data and "genetic_count" in data:
            expected = data["physical_count"] + data["genetic_count"]
            if v != expected:
                raise ValueError(
                    f"total_count ({v}) must equal physical_count + genetic_count ({expected})"
                )
        if "interactions" in data:
            actual_count = len(data["interactions"])
            if v != actual_count:
                raise ValueError(f"total_count ({v}) must equal len(interactions) ({actual_count})")
        return v

    def to_slim(self) -> dict[str, Any]:
        """Return slim representation with minimal fields (~15 tokens/interaction).

        Constitution Principle IV: Token budgeting for context-constrained agents.
        Omits biogrid_interaction_id, symbol_a, experimental_system, pubmed_id,
        throughput, organism IDs, entrez IDs, and cross_references.
        """
        return {
            "query_gene": self.query_gene,
            "interactions": [
                {
                    "symbol_b": i.symbol_b,
                    "experimental_system_type": i.experimental_system_type,
                }
                for i in self.interactions
            ],
            "physical_count": self.physical_count,
            "genetic_count": self.genetic_count,
            "total_count": self.total_count,
        }
