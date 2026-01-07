"""Open Targets Platform GraphQL API client implementing the Fuzzy-to-Fact protocol.

This module provides the OpenTargetsClient for querying the Open Targets
Platform for target-disease associations and evidence.

Key Features:
- GraphQL query execution with rate limiting (10 req/s)
- Cursor-based pagination with opaque cursors
- Error handling with actionable recovery hints
- Slim mode support for token budgeting

Rate limiting: 10 req/s with exponential backoff (Constitution v1.1.0)
API Docs: https://platform-docs.opentargets.org/data-access/graphql-api
"""

import asyncio
import base64
import json
import re
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    PaginationEnvelope,
)
from lifesciences_mcp.models.gene import CrossReferences
from lifesciences_mcp.models.target import (
    Association,
    Target,
    TargetSearchCandidate,
)

# Constants from research.md R1
GRAPHQL_ENDPOINT = "https://api.platform.opentargets.org/api/v4/graphql"
DEFAULT_TIMEOUT = 30.0  # FR-034: 30 second timeout

# Regex patterns from research.md R3
ENSEMBL_GENE_ID_PATTERN = re.compile(r"^ENSG\d{11}$")
# Open Targets uses multiple disease ontologies: EFO, MONDO, Orphanet, HP, DOID, OTAR
DISEASE_ID_PATTERN = re.compile(r"^(EFO|MONDO|Orphanet|HP|DOID|OTAR)_\d+$")

# Rate limiting constants from research.md R2
RATE_LIMIT_DELAY = 0.1  # 10 req/s = 100ms between requests
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0  # Exponential backoff: 1s, 2s, 4s
MAX_BACKOFF_DELAY = 60.0

# Scoring constants
SCORE_DECAY = 0.05  # Score reduction per position in results

# GraphQL query templates - updated for Open Targets Platform API v4
SEARCH_TARGETS_QUERY = """
query SearchTargets($queryString: String!, $size: Int!, $index: Int!) {
  search(queryString: $queryString, entityNames: ["target"], page: {size: $size, index: $index}) {
    hits {
      id
      name
      description
      entity
    }
    total
  }
}
"""

GET_TARGET_QUERY = """
query GetTarget($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    biotype
    functionDescriptions
    dbXrefs {
      source
      id
    }
  }
}
"""

GET_ASSOCIATIONS_QUERY = """
query GetAssociations($ensemblId: String!, $size: Int!, $index: Int!) {
  target(ensemblId: $ensemblId) {
    id
    associatedDiseases(page: {size: $size, index: $index}) {
      rows {
        disease {
          id
          name
        }
        score
      }
      count
    }
  }
}
"""

# Cross-reference mapping from research.md R4
OT_TO_REGISTRY_MAP: dict[str, str] = {
    "ensembl": "ensembl_gene",
    "hgnc": "hgnc",
    "uniprot_swissprot": "uniprot",
    "chembl": "chembl",
    "drugbank": "drugbank",
    "omim": "omim",
    "mondo": "mondo",
    "efo": "efo",
    "ncbi_gene": "entrez",
    "refseq": "refseq",
    "string": "string",
    "biogrid": "biogrid",
    "kegg": "kegg",
}


class OpenTargetsClient(LifeSciencesClient):
    """Open Targets Platform GraphQL API client.

    Implements the Fuzzy-to-Fact protocol for target-disease associations.
    Uses GraphQL API with rate limiting (10 req/s) and exponential backoff.

    Can be used as a context manager:
        async with OpenTargetsClient() as client:
            result = await client.search_targets("TP53")
    """

    def __init__(self) -> None:
        """Initialize the Open Targets client."""
        super().__init__(base_url=GRAPHQL_ENDPOINT, timeout=DEFAULT_TIMEOUT)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "OpenTargetsClient":
        """Enter context manager."""
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """Exit context manager and cleanup resources."""
        await self.close()

    # ==================== Pagination Helpers (T010) ====================

    def _encode_cursor(self, index: int, size: int) -> str:
        """Encode pagination state as opaque cursor (research.md R7).

        Args:
            index: Page index (0-based).
            size: Page size.

        Returns:
            Base64-encoded cursor string.
        """
        cursor_data = {"index": index, "size": size}
        return base64.b64encode(json.dumps(cursor_data).encode()).decode()

    def _decode_cursor(self, cursor: str | None) -> tuple[int, int]:
        """Decode cursor to pagination state (research.md R7).

        Args:
            cursor: Opaque cursor string, or None for first page.

        Returns:
            Tuple of (index, size) for pagination.
        """
        if cursor is None:
            return (0, 50)  # Default first page
        try:
            cursor_data = json.loads(base64.b64decode(cursor).decode())
            return (cursor_data["index"], cursor_data["size"])
        except (ValueError, KeyError):
            return (0, 50)  # Fallback to first page on invalid cursor

    # ==================== GraphQL Execution (T005-T006) ====================

    async def _execute_graphql(self, query: str, variables: dict[str, Any]) -> httpx.Response:
        """Execute a GraphQL query against the Open Targets API.

        Args:
            query: GraphQL query string.
            variables: Query variables dictionary.

        Returns:
            HTTP response from the API.

        Raises:
            httpx.HTTPError: On network or HTTP errors.
        """
        client = await self._get_client()
        # Use full URL to avoid httpx base_url path resolution issues
        response = await client.post(
            GRAPHQL_ENDPOINT,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
        )
        return response

    # ==================== Rate Limiting (T008-T009) ====================

    async def _rate_limited_graphql(
        self, query: str, variables: dict[str, Any]
    ) -> httpx.Response | ErrorEnvelope:
        """Execute a rate-limited GraphQL query with exponential backoff.

        Implements Constitution v1.1.0 MANDATORY rate limiting:
        - 10 req/s = 100ms minimum delay between requests
        - Exponential backoff on 429 errors
        - Thundering herd prevention via lock re-check

        Args:
            query: GraphQL query string.
            variables: Query variables dictionary.

        Returns:
            HTTP response or ErrorEnvelope on persistent failures.
        """
        # Initial request with rate limiting
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < RATE_LIMIT_DELAY:
                await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

            try:
                response = await self._execute_graphql(query, variables)
                self._last_request_time = asyncio.get_event_loop().time()
            except Exception as e:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.UPSTREAM_ERROR,
                        message=f"Failed to connect to Open Targets API: {e!s}",
                        recovery_hint="Check your network connection and try again.",
                    )
                )

        # Exponential backoff on rate limit errors (T009)
        for attempt in range(MAX_RETRIES):
            if response.status_code not in (429, 403):
                break

            # Calculate backoff time
            retry_after = response.headers.get("Retry-After")
            wait_time = float(retry_after) if retry_after else (BACKOFF_FACTOR**attempt)
            wait_time = min(wait_time, MAX_BACKOFF_DELAY)

            # Sleep OUTSIDE lock to allow other requests to proceed
            await asyncio.sleep(wait_time)

            # Retry with lock - re-check time boundary to prevent thundering herd
            async with self._lock:
                now = asyncio.get_event_loop().time()
                elapsed = now - self._last_request_time
                if elapsed < RATE_LIMIT_DELAY:
                    await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

                try:
                    response = await self._execute_graphql(query, variables)
                    self._last_request_time = asyncio.get_event_loop().time()
                except Exception as e:
                    return ErrorEnvelope(
                        error=ErrorDetail(
                            code=ErrorCode.UPSTREAM_ERROR,
                            message=f"Failed to connect to Open Targets API: {e!s}",
                            recovery_hint="Check your network connection and try again.",
                        )
                    )

        # If still rate limited after retries, return error
        if response.status_code == 429:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.RATE_LIMITED,
                    message="Open Targets API rate limit exceeded after retries",
                    recovery_hint=f"Wait {MAX_BACKOFF_DELAY}s before retrying",
                )
            )

        return response

    # ==================== Response Handling (T038) ====================

    def _handle_graphql_response(
        self, response: httpx.Response, invalid_input: str | None = None
    ) -> dict[str, Any] | ErrorEnvelope:
        """Handle GraphQL response and map errors to error codes (research.md R6).

        Args:
            response: HTTP response from GraphQL API.
            invalid_input: Optional input string for error messages.

        Returns:
            Parsed data or ErrorEnvelope on errors.
        """
        # Check HTTP status first
        if response.status_code == 429:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.RATE_LIMITED,
                    message="Open Targets API rate limit exceeded",
                    recovery_hint="Wait 60s before retrying",
                    invalid_input=invalid_input,
                )
            )

        if response.status_code >= 500:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Open Targets API returned error {response.status_code}",
                    recovery_hint="Open Targets API temporarily unavailable - retry in 60 seconds",
                    invalid_input=invalid_input,
                )
            )

        try:
            data = response.json()
        except ValueError:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message="Failed to parse Open Targets API response",
                    recovery_hint="Open Targets API may be experiencing issues - retry later",
                    invalid_input=invalid_input,
                )
            )

        # Check for GraphQL errors
        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"GraphQL error: {error_msg}",
                    recovery_hint="Check your query parameters and try again",
                    invalid_input=invalid_input,
                )
            )

        return data.get("data", {})

    # ==================== ID Validation (T024) ====================

    def _validate_ensembl_id(self, ensembl_id: str) -> ErrorEnvelope | None:
        """Validate Ensembl gene ID format (research.md R3).

        Args:
            ensembl_id: ID to validate.

        Returns:
            ErrorEnvelope if invalid, None if valid.
        """
        if not ENSEMBL_GENE_ID_PATTERN.match(ensembl_id):
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UNRESOLVED_ENTITY,
                    message=f"Invalid Ensembl gene ID format: '{ensembl_id}'",
                    recovery_hint=(
                        "Ensembl ID must match format ENSG[11 digits] (e.g., ENSG00000141510). "
                        "Use search_targets to find the correct ID."
                    ),
                    invalid_input=ensembl_id,
                )
            )
        return None

    # ==================== Cross-Reference Mapping (T026) ====================

    def _build_cross_references(self, ot_cross_refs: list[dict[str, Any]]) -> CrossReferences:
        """Map Open Targets crossReferences to 22-key registry (research.md R4).

        Applies CURIE normalization and omit-if-null pattern (Constitution III).

        Args:
            ot_cross_refs: List of cross-reference dicts from GraphQL response.

        Returns:
            CrossReferences model with mapped values.
        """
        refs_dict: dict[str, str | list[str]] = {}

        for xref in ot_cross_refs:
            source = xref.get("source", "").lower()
            xref_id = xref.get("id", "")

            if not source or not xref_id:
                continue

            # Map source to our registry key
            if source in OT_TO_REGISTRY_MAP:
                key = OT_TO_REGISTRY_MAP[source]

                # Apply CURIE normalization based on source
                normalized_id = self._normalize_curie(source, xref_id)

                # Handle multi-value vs single-value references
                if key in refs_dict:
                    # Append to existing list if it's a list, otherwise skip
                    if isinstance(refs_dict[key], list):
                        refs_dict[key].append(normalized_id)
                else:
                    refs_dict[key] = normalized_id

        return CrossReferences(**refs_dict)

    def _normalize_curie(self, source: str, xref_id: str) -> str:
        """Normalize cross-reference ID to CURIE format (research.md R4).

        Args:
            source: Source database name (lowercase).
            xref_id: Raw cross-reference ID.

        Returns:
            Normalized CURIE string.
        """
        # CURIE normalization rules from research.md
        if source == "hgnc" and not xref_id.startswith("HGNC:"):
            return f"HGNC:{xref_id}"
        if source == "uniprot_swissprot" and not xref_id.startswith("UniProtKB:"):
            return f"UniProtKB:{xref_id}"
        if source == "chembl" and not xref_id.startswith("CHEMBL:"):
            return f"CHEMBL:{xref_id}"
        if source == "drugbank" and not xref_id.startswith("DB:"):
            return f"DB:{xref_id}"
        # Other sources return as-is
        return xref_id

    # ==================== Search Targets (T017-T020) ====================

    async def search_targets(
        self,
        query: str,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope[TargetSearchCandidate] | ErrorEnvelope:
        """Fuzzy search for targets (Phase 1 of Fuzzy-to-Fact).

        Implements User Story 1: Fuzzy Target Search.

        Args:
            query: Search term (gene symbol, name, or natural language). Min 2 chars.
            slim: If true, return minimal fields (~20 tokens per entity).
            cursor: Opaque cursor for pagination.
            page_size: Results per page (1-100, default 50).

        Returns:
            PaginationEnvelope with TargetSearchCandidate items, or ErrorEnvelope.
        """
        # T017: Query validation - minimum 2 characters
        if len(query.strip()) < 2:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message=f"Query '{query}' is too short. Minimum 2 characters required.",
                    recovery_hint="Provide a more specific search term (e.g., 'TP53', 'BRCA1', 'kinase')",
                    invalid_input=query,
                )
            )

        # Clamp page_size to valid range
        page_size = max(1, min(100, page_size))

        # Decode cursor for pagination
        index, _ = self._decode_cursor(cursor)

        # Execute GraphQL query with rate limiting
        response = await self._rate_limited_graphql(
            SEARCH_TARGETS_QUERY,
            {"queryString": query, "size": page_size, "index": index},
        )

        # Check if we got an error envelope from rate limiting
        if isinstance(response, ErrorEnvelope):
            return response

        # Handle GraphQL response
        data = self._handle_graphql_response(response, query)
        if isinstance(data, ErrorEnvelope):
            return data

        # T018: Transform results to TargetSearchCandidate
        search_data = data.get("search", {})
        hits = search_data.get("hits", [])
        total = search_data.get("total", 0)

        candidates = []
        for i, hit in enumerate(hits):
            # Calculate synthetic relevance score
            score = max(0.1, 1.0 - (i * SCORE_DECAY))

            # Search API returns 'name' and 'description', map to approved_symbol/name
            candidate = TargetSearchCandidate(
                id=hit.get("id", ""),
                approved_symbol=hit.get("name"),  # name in search = approved symbol
                approved_name=hit.get("description"),  # description = approved name
                score=round(score, 2),
            )
            candidates.append(candidate)

        # T019: Calculate next cursor
        has_more = (index + 1) * page_size < total
        next_cursor = self._encode_cursor(index + 1, page_size) if has_more else None

        return PaginationEnvelope.create(
            items=candidates,
            cursor=next_cursor,
            total_count=total,
            page_size=page_size,
        )

    # ==================== Get Target (T024-T028) ====================

    async def get_target(
        self, ensembl_id: str, slim: bool = False
    ) -> Target | dict | ErrorEnvelope:
        """Get target by Ensembl gene ID (Phase 2 of Fuzzy-to-Fact).

        Implements User Story 2: Strict Target Lookup.

        Args:
            ensembl_id: Ensembl gene ID (format: ENSG[0-9]{11}).
            slim: Return minimal fields for token efficiency.

        Returns:
            Target record with cross_references, or ErrorEnvelope.
        """
        # T024: Validate Ensembl ID format
        validation_error = self._validate_ensembl_id(ensembl_id)
        if validation_error:
            return validation_error

        # Execute GraphQL query with rate limiting
        response = await self._rate_limited_graphql(
            GET_TARGET_QUERY,
            {"ensemblId": ensembl_id},
        )

        # Check if we got an error envelope from rate limiting
        if isinstance(response, ErrorEnvelope):
            return response

        # Handle GraphQL response
        data = self._handle_graphql_response(response, ensembl_id)
        if isinstance(data, ErrorEnvelope):
            return data

        # Check for null target (not found)
        target_data = data.get("target")
        if target_data is None:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"Target '{ensembl_id}' not found in Open Targets database",
                    recovery_hint=(
                        "Verify the Ensembl ID exists at platform.opentargets.org "
                        "or use search_targets to find alternatives."
                    ),
                    invalid_input=ensembl_id,
                )
            )

        # T27: Transform result to Target model
        cross_refs = self._build_cross_references(target_data.get("dbXrefs", []))

        # Build description from functionDescriptions
        descriptions = target_data.get("functionDescriptions", [])
        description = descriptions[0] if descriptions else None

        target = Target(
            id=target_data.get("id", ensembl_id),
            approved_symbol=target_data.get("approvedSymbol"),
            approved_name=target_data.get("approvedName"),
            biotype=target_data.get("biotype"),
            description=description,
            associated_diseases_count=None,  # Would require separate query
            cross_references=cross_refs,
        )

        # T28: Return slim or full mode
        if slim:
            return target.to_slim()
        return target

    # ==================== Get Associations (T031-T034) ====================

    async def get_associations(
        self,
        target_id: str,
        disease_id: str | None = None,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope[Association] | ErrorEnvelope:
        """Get target-disease associations (User Story 3).

        Args:
            target_id: Ensembl gene ID.
            disease_id: Optional EFO disease ID to filter.
            cursor: Pagination cursor.
            page_size: Results per page (1-100).

        Returns:
            PaginationEnvelope with Association records, or ErrorEnvelope.
        """
        # Validate target ID format
        validation_error = self._validate_ensembl_id(target_id)
        if validation_error:
            return validation_error

        # Validate disease_id format if provided
        if disease_id and not DISEASE_ID_PATTERN.match(disease_id):
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UNRESOLVED_ENTITY,
                    message=f"Invalid disease ID format: '{disease_id}'",
                    recovery_hint="Disease ID must match format EFO_/MONDO_/Orphanet_/HP_/DOID_/OTAR_[digits]",
                    invalid_input=disease_id,
                )
            )

        # Clamp page_size to valid range
        page_size = max(1, min(100, page_size))

        # Decode cursor for pagination
        index, _ = self._decode_cursor(cursor)

        # Execute GraphQL query with rate limiting
        response = await self._rate_limited_graphql(
            GET_ASSOCIATIONS_QUERY,
            {"ensemblId": target_id, "size": page_size, "index": index},
        )

        # Check if we got an error envelope from rate limiting
        if isinstance(response, ErrorEnvelope):
            return response

        # Handle GraphQL response
        data = self._handle_graphql_response(response, target_id)
        if isinstance(data, ErrorEnvelope):
            return data

        # Check for null target (not found)
        target_data = data.get("target")
        if target_data is None:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"Target '{target_id}' not found in Open Targets database",
                    recovery_hint=(
                        "Verify the Ensembl ID exists or use search_targets to find alternatives."
                    ),
                    invalid_input=target_id,
                )
            )

        # T32: Transform associations
        assoc_data = target_data.get("associatedDiseases", {})
        rows = assoc_data.get("rows", [])
        total = assoc_data.get("count", 0)

        associations = []
        for row in rows:
            disease = row.get("disease", {})
            disease_row_id = disease.get("id", "")

            # Filter by disease_id if specified
            if disease_id and disease_row_id != disease_id:
                continue

            association = Association(
                target_id=target_id,
                disease_id=disease_row_id,
                disease_name=disease.get("name", "Unknown"),
                score=row.get("score", 0.0),
                evidence_count=0,  # Not available in simplified query
                evidence_sources=[],
            )
            associations.append(association)

        # T33: Calculate next cursor
        has_more = (index + 1) * page_size < total
        next_cursor = self._encode_cursor(index + 1, page_size) if has_more else None

        return PaginationEnvelope.create(
            items=associations,
            cursor=next_cursor,
            total_count=total,
            page_size=page_size,
        )
