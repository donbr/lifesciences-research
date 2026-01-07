"""Provenance models for tracking MCP data lineage.

This module provides Pydantic models for structured provenance metadata,
enabling verification, reproducibility, and temporal tracking of MCP-derived data.

Example usage:
    >>> from lifesciences_mcp.models.provenance import Provenance, MCPClaim
    >>>
    >>> prov = Provenance(
    ...     source="chembl.get_compound",
    ...     timestamp=datetime.now(),
    ...     curie="CHEMBL:1946170",
    ...     api_version="ChEMBL v33",
    ...     confidence_score=1.0
    ... )
    >>>
    >>> claim = MCPClaim(
    ...     claim="Regorafenib is approved for hepatocellular carcinoma",
    ...     value=4,  # max_phase
    ...     provenance=prov
    ... )

Architecture Decision Record:
    - ADR-001 §11: Provenance tracking for data lineage
    - Omit-if-null pattern: Optional fields are None, not empty strings
    - ISO 8601 timestamps for temporal consistency
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Provenance(BaseModel):
    """Structured provenance metadata for MCP-derived data.

    Attributes:
        source: MCP tool name in format "server.tool" (e.g., "chembl.get_compound")
        timestamp: ISO 8601 timestamp of API call (when data was retrieved)
        curie: Entity CURIE that was queried (e.g., "CHEMBL:1946170")
        api_version: API version string if available (e.g., "ChEMBL v33")
        confidence_score: Fuzzy search confidence score (0.0-1.0), None for strict lookups
    """

    source: str = Field(
        ...,
        description="MCP tool name (e.g., 'chembl.get_compound', 'hgnc.search_genes')",
        pattern=r"^[a-z_]+\.[a-z_]+$",
    )
    timestamp: datetime = Field(
        ...,
        description="ISO 8601 timestamp of API call",
    )
    curie: str = Field(
        ...,
        description="Entity CURIE queried (e.g., 'CHEMBL:1946170', 'HGNC:11998')",
        pattern=r"^[A-Z][A-Za-z0-9]*:[A-Za-z0-9_\-\.]+$",
    )
    api_version: str | None = Field(
        None,
        description="API version if available (e.g., 'ChEMBL v33', 'UniProt 2024_01')",
    )
    confidence_score: float | None = Field(
        None,
        description="Fuzzy search score (0.0-1.0). None for strict lookups. 1.0 = exact match.",
        ge=0.0,
        le=1.0,
    )

    def to_citation_string(self) -> str:
        """Generate human-readable citation string.

        Returns:
            Citation string like "source: chembl.get_compound, curie: CHEMBL:1946170, timestamp: 2026-01-05T14:32:15Z"

        Example:
            >>> prov = Provenance(source="chembl.get_compound", timestamp=datetime.now(), curie="CHEMBL:1946170")
            >>> prov.to_citation_string()
            'source: chembl.get_compound, curie: CHEMBL:1946170, timestamp: 2026-01-05T14:32:15Z'
        """
        parts = [
            f"source: {self.source}",
            f"curie: {self.curie}",
            f"timestamp: {self.timestamp.isoformat()}",
        ]
        if self.api_version:
            parts.append(f"api_version: {self.api_version}")
        if self.confidence_score is not None:
            parts.append(f"confidence: {self.confidence_score:.2f}")
        return ", ".join(parts)


class MCPClaim(BaseModel):
    """Base class for all MCP-derived claims with provenance.

    Attributes:
        claim: Human-readable claim statement
        value: The data value (can be primitive or complex type)
        provenance: Data lineage metadata

    Example:
        >>> claim = MCPClaim(
        ...     claim="Regorafenib is approved (Phase 4) for hepatocellular carcinoma",
        ...     value=4,  # max_phase
        ...     provenance=Provenance(...)
        ... )
    """

    claim: str = Field(
        ...,
        description="Human-readable claim statement",
        min_length=1,
    )
    value: Any = Field(
        ...,
        description="The data value (primitive or complex type)",
    )
    provenance: Provenance = Field(
        ...,
        description="Data lineage metadata",
    )

    def to_citation_format(self) -> str:
        """Generate citation-formatted string for reports.

        Returns:
            String like "Regorafenib (max_phase=4, source: chembl.get_compound, CHEMBL:1946170, 2026-01-05T14:32:15Z)"

        Example:
            >>> claim.to_citation_format()
            'Regorafenib is approved (max_phase=4, source: chembl.get_compound, CHEMBL:1946170, 2026-01-05T14:32:15Z)'
        """
        return f"{self.claim} ({self.provenance.to_citation_string()})"


class BatchProvenance(BaseModel):
    """Provenance for batch operations (e.g., chembl.get_compounds_batch).

    Attributes:
        source: MCP tool name
        timestamp: ISO 8601 timestamp of API call
        curies: List of entity CURIEs queried
        batch_size: Number of entities in batch
        api_version: API version if available
    """

    source: str = Field(
        ...,
        description="MCP tool name (e.g., 'chembl.get_compounds_batch')",
        pattern=r"^[a-z_]+\.[a-z_]+$",
    )
    timestamp: datetime = Field(
        ...,
        description="ISO 8601 timestamp of API call",
    )
    curies: list[str] = Field(
        ...,
        description="List of entity CURIEs queried",
        min_length=1,
    )
    batch_size: int = Field(
        ...,
        description="Number of entities in batch",
        ge=1,
    )
    api_version: str | None = Field(
        None,
        description="API version if available",
    )

    def to_citation_string(self) -> str:
        """Generate human-readable citation string for batch operations.

        Returns:
            Citation string with batch metadata

        Example:
            >>> batch_prov.to_citation_string()
            'source: chembl.get_compounds_batch, batch_size: 5, curies: CHEMBL:25,CHEMBL:939,...'
        """
        curie_preview = ",".join(self.curies[:3])
        if len(self.curies) > 3:
            curie_preview += f",... ({len(self.curies)} total)"
        return f"source: {self.source}, batch_size: {self.batch_size}, curies: {curie_preview}, timestamp: {self.timestamp.isoformat()}"
