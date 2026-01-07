"""Canonical envelope models per ADR-001 Section 8.

These models define the standard response formats for all Life Sciences MCP tools:
- PaginationEnvelope: For list/search operations
- ErrorEnvelope: For all error responses
"""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Standard error codes from ADR-001 Appendix B."""

    UNRESOLVED_ENTITY = "UNRESOLVED_ENTITY"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    INVALID_CROSS_REFERENCE = "INVALID_CROSS_REFERENCE"


class ErrorDetail(BaseModel):
    """Error detail object within ErrorEnvelope."""

    code: ErrorCode = Field(description="Error code from registry")
    message: str = Field(description="Human-readable error message")
    recovery_hint: str = Field(description="Agent-actionable guidance for recovery")
    invalid_input: str | None = Field(default=None, description="The input that caused the error")


class ErrorEnvelope(BaseModel):
    """Canonical error envelope per ADR-001 Section 8.

    All error responses from Life Sciences MCP tools use this format.
    The recovery_hint field enables agent self-correction.
    """

    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(description="Error details with recovery hint")

    @classmethod
    def unresolved_entity(cls, invalid_input: str) -> "ErrorEnvelope":
        """Create UNRESOLVED_ENTITY error for raw string passed to strict tool."""
        return cls(
            error=ErrorDetail(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=f"The input '{invalid_input}' is not a valid HGNC CURIE.",
                recovery_hint="Call search_genes to resolve the identifier first.",
                invalid_input=invalid_input,
            )
        )

    @classmethod
    def entity_not_found(cls, hgnc_id: str) -> "ErrorEnvelope":
        """Create ENTITY_NOT_FOUND error for valid CURIE with no record."""
        return cls(
            error=ErrorDetail(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message=f"No gene found for HGNC ID '{hgnc_id}'.",
                recovery_hint="Verify the HGNC ID format or try a synonym search.",
                invalid_input=hgnc_id,
            )
        )

    @classmethod
    def ambiguous_query(cls, query: str, result_count: int) -> "ErrorEnvelope":
        """Create AMBIGUOUS_QUERY error for too many or too few results."""
        return cls(
            error=ErrorDetail(
                code=ErrorCode.AMBIGUOUS_QUERY,
                message=f"Query '{query}' returned {result_count} results.",
                recovery_hint="Refine query with more specific terms.",
                invalid_input=query,
            )
        )

    @classmethod
    def rate_limited(cls, retry_after: int | None = None) -> "ErrorEnvelope":
        """Create RATE_LIMITED error for upstream API throttling."""
        hint = "Retry after a few seconds."
        if retry_after:
            hint = f"Retry after {retry_after} seconds."
        return cls(
            error=ErrorDetail(
                code=ErrorCode.RATE_LIMITED,
                message="HGNC API rate limit exceeded.",
                recovery_hint=hint,
            )
        )

    @classmethod
    def upstream_error(cls, status_code: int, detail: str | None = None) -> "ErrorEnvelope":
        """Create UPSTREAM_ERROR for HGNC API failures."""
        message = f"HGNC API returned error {status_code}."
        if detail:
            message = f"{message} {detail}"
        return cls(
            error=ErrorDetail(
                code=ErrorCode.UPSTREAM_ERROR,
                message=message,
                recovery_hint="HGNC API may be temporarily unavailable. Retry later.",
            )
        )


class Pagination(BaseModel):
    """Pagination metadata within PaginationEnvelope."""

    cursor: str | None = Field(default=None, description="Opaque cursor for next page; null = end")
    total_count: int | None = Field(default=None, description="Total items if known")
    page_size: int = Field(default=50, description="Items per page")


class PaginationEnvelope(BaseModel, Generic[T]):
    """Canonical pagination envelope per ADR-001 Section 8.

    All list/search operations return this format with items and pagination metadata.
    """

    items: list[T] = Field(description="Data payload")
    pagination: Pagination = Field(description="Pagination metadata")

    @classmethod
    def create(
        cls,
        items: list[T],
        cursor: str | None = None,
        total_count: int | None = None,
        page_size: int = 50,
    ) -> "PaginationEnvelope[T]":
        """Create a pagination envelope with the given items and metadata."""
        return cls(
            items=items,
            pagination=Pagination(
                cursor=cursor,
                total_count=total_count,
                page_size=page_size,
            ),
        )
