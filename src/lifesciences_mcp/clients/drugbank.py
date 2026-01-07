"""DrugBank API client implementing the Fuzzy-to-Fact protocol.

This module provides the DrugBankClient for querying the DrugBank database
for comprehensive drug and drug target information.

DrugBank has tiered API access:
- Public API: Basic access via go.drugbank.com
- Commercial API: Full access via api.drugbank.com (requires API key)
"""

import asyncio
import base64
import json
import logging
import os
import re
import time
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.drug import (
    Drug,
    DrugCrossReferences,
    DrugSearchCandidate,
)
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    PaginationEnvelope,
)

logger = logging.getLogger(__name__)

# API Configuration (T005)
PUBLIC_BASE_URL = "https://go.drugbank.com"
COMMERCIAL_BASE_URL = "https://api.drugbank.com/v1"

# DrugBank ID validation pattern (from research.md R3)
DRUGBANK_ID_PATTERN = re.compile(r"^DrugBank:DB\d{5}$")

# Rate limiting configuration (Constitution v1.1.0 MANDATORY)
RATE_LIMIT_DELAY = 0.1  # 10 req/s = 100ms between requests
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0  # Exponential backoff: 1s, 2s, 4s
MAX_BACKOFF = 60.0

# Search configuration
MIN_QUERY_LENGTH = 2
SCORE_DECAY = 0.05  # Score reduction per position in results


class DrugBankClient(LifeSciencesClient):
    """DrugBank API client implementing the Fuzzy-to-Fact protocol.

    DrugBank provides comprehensive drug and drug target information.
    Supports both public API (limited) and commercial API (full access with key).

    Rate limiting: 10 req/s with exponential backoff (Constitution v1.1.0)
    API Docs: https://go.drugbank.com/documentation

    Can be used as a context manager:
        async with DrugBankClient() as client:
            result = await client.search_drugs("aspirin")
    """

    def __init__(self) -> None:
        """Initialize the DrugBank client."""
        # Use public base URL; commercial endpoints handled per-request
        super().__init__(base_url=PUBLIC_BASE_URL)

        # API Key Authentication (T006)
        self._api_key = self._get_api_key()

        # Rate limiting state (T009)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

        # Log API mode
        if self._api_key:
            logger.info("DrugBankClient initialized with commercial API key")
        else:
            logger.warning("DrugBankClient initialized without API key - using public endpoints")

    async def __aenter__(self) -> "DrugBankClient":
        """Enter context manager."""
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """Exit context manager and cleanup resources."""
        await self.close()

    # =========================================================================
    # API Key Authentication (T006, T007, T008)
    # =========================================================================

    def _get_api_key(self) -> str | None:
        """Get DrugBank API key from environment variable (T006).

        Returns:
            API key if set, None otherwise.
        """
        api_key = os.environ.get("DRUGBANK_API_KEY")
        if not api_key:
            logger.debug("DRUGBANK_API_KEY not set - using public endpoints")
        return api_key

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including authentication if available (T007).

        Returns:
            Headers dict with Authorization if API key is set.
        """
        headers = {
            "User-Agent": "LifeSciencesMCP/1.0 (DrugBankClient)",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _select_base_url(self) -> str:
        """Select API base URL based on API key availability (T008).

        Returns:
            Commercial base URL if key is set, public otherwise.
        """
        if self._api_key:
            return COMMERCIAL_BASE_URL
        return PUBLIC_BASE_URL

    # =========================================================================
    # Rate Limiting (T009, T010)
    # =========================================================================

    async def _rate_limited_get(self, url: str, params: dict | None = None) -> httpx.Response:
        """Make a rate-limited GET request with exponential backoff (T009, T010).

        Implements proper rate limiting with the request inside the lock
        to prevent race conditions. Handles 429 and auth errors with backoff.

        Args:
            url: Full URL to request.
            params: Query parameters.

        Returns:
            HTTP response from the API.
        """
        headers = self._get_headers()

        # Initial request with rate limiting
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < RATE_LIMIT_DELAY:
                await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

            client = await self._get_client()
            response = await client.get(url, params=params, headers=headers)
            self._last_request_time = time.monotonic()

        # Exponential backoff on rate limit/auth errors (T010)
        for attempt in range(MAX_RETRIES):
            if response.status_code not in (429, 401, 403):
                break

            # Calculate backoff time
            retry_after = response.headers.get("Retry-After")
            wait_time = (
                int(retry_after) if retry_after else min(BACKOFF_FACTOR**attempt, MAX_BACKOFF)
            )

            logger.warning(
                f"DrugBank API returned {response.status_code}, "
                f"retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})"
            )

            # Sleep OUTSIDE lock to allow other requests to proceed
            await asyncio.sleep(wait_time)

            # Retry with lock - re-check time boundary to prevent thundering herd
            async with self._lock:
                # CRITICAL: Re-check timing after acquiring lock
                now = time.monotonic()
                elapsed = now - self._last_request_time
                if elapsed < RATE_LIMIT_DELAY:
                    await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

                response = await client.get(url, params=params, headers=headers)
                self._last_request_time = time.monotonic()

        return response

    # =========================================================================
    # Pagination (T011)
    # =========================================================================

    def _encode_cursor(self, page: int, per_page: int) -> str:
        """Encode pagination state as opaque cursor (T011).

        Args:
            page: Current page number (1-indexed).
            per_page: Items per page.

        Returns:
            Base64-encoded cursor string.
        """
        cursor_data = {"page": page, "per_page": per_page}
        return base64.b64encode(json.dumps(cursor_data).encode()).decode()

    def _decode_cursor(self, cursor: str | None) -> tuple[int, int]:
        """Decode cursor to pagination state (T011).

        Args:
            cursor: Base64-encoded cursor or None.

        Returns:
            Tuple of (page, per_page).
        """
        if cursor is None:
            return (1, 50)  # Default first page
        try:
            cursor_data = json.loads(base64.b64decode(cursor).decode())
            return (cursor_data.get("page", 1), cursor_data.get("per_page", 50))
        except (ValueError, json.JSONDecodeError):
            return (1, 50)

    # =========================================================================
    # Error Handling (Phase 6: T037, T038, T039)
    # =========================================================================

    def _create_error(
        self,
        code: ErrorCode,
        message: str,
        recovery_hint: str,
        invalid_input: str | None = None,
    ) -> ErrorEnvelope:
        """Create standardized ErrorEnvelope with recovery hints (T38, T39).

        Args:
            code: Error code from registry.
            message: Human-readable error message.
            recovery_hint: Agent-actionable guidance.
            invalid_input: The input that caused the error.

        Returns:
            Formatted ErrorEnvelope.
        """
        return ErrorEnvelope(
            error=ErrorDetail(
                code=code,
                message=message,
                recovery_hint=recovery_hint,
                invalid_input=invalid_input,
            )
        )

    def _handle_response_error(
        self, response: httpx.Response, context: str = ""
    ) -> ErrorEnvelope | None:
        """Check response for errors and return ErrorEnvelope if needed (T037).

        Args:
            response: HTTP response to check.
            context: Additional context for error messages.

        Returns:
            ErrorEnvelope if error, None if success.
        """
        if response.status_code == 200:
            return None

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            return self._create_error(
                ErrorCode.RATE_LIMITED,
                "DrugBank API rate limit exceeded.",
                f"Wait {retry_after}s before retrying.",
            )

        if response.status_code in (401, 403):
            return self._create_error(
                ErrorCode.UPSTREAM_ERROR,
                f"DrugBank API returned {response.status_code}.",
                "Commercial API access may be required for this feature. See go.drugbank.com",
            )

        if response.status_code == 404:
            return self._create_error(
                ErrorCode.ENTITY_NOT_FOUND,
                f"Drug not found in DrugBank database. {context}",
                "Verify the DrugBank ID at go.drugbank.com or use search_drugs to find alternatives.",
                context,
            )

        if response.status_code >= 500:
            return self._create_error(
                ErrorCode.UPSTREAM_ERROR,
                f"DrugBank API returned error {response.status_code}.",
                "DrugBank API temporarily unavailable. Retry in 60 seconds.",
            )

        return self._create_error(
            ErrorCode.UPSTREAM_ERROR,
            f"DrugBank API returned unexpected status {response.status_code}.",
            "Check the DrugBank API status or retry later.",
        )

    # =========================================================================
    # ID Validation (T025)
    # =========================================================================

    def _validate_drugbank_id(self, drugbank_id: str) -> ErrorEnvelope | None:
        """Validate DrugBank CURIE format (T025).

        Args:
            drugbank_id: DrugBank ID to validate.

        Returns:
            ErrorEnvelope if invalid, None if valid.
        """
        if not DRUGBANK_ID_PATTERN.match(drugbank_id):
            return self._create_error(
                ErrorCode.UNRESOLVED_ENTITY,
                f"Invalid DrugBank CURIE format: '{drugbank_id}'",
                "Use format 'DrugBank:DBXXXXX' (e.g., 'DrugBank:DB00945'). "
                "Use search_drugs to find valid IDs.",
                drugbank_id,
            )
        return None

    # =========================================================================
    # Cross-Reference Building (T032, T033)
    # =========================================================================

    def _build_cross_references(
        self, data: dict[str, Any], drugbank_id: str
    ) -> DrugCrossReferences:
        """Build cross-references from DrugBank response (T032).

        Maps DrugBank external identifiers to 22-key Agentic Biolink schema.
        Applies CURIE normalization per research.md R4.

        Args:
            data: DrugBank API response data.
            drugbank_id: The DrugBank CURIE for self-reference.

        Returns:
            DrugCrossReferences with mapped identifiers.
        """
        refs: dict[str, Any] = {}

        # Self-reference
        refs["drugbank"] = drugbank_id

        # ChEMBL mapping - normalize to CHEMBL:NNN format
        external_ids = data.get("external_identifiers", [])
        for ext_id in external_ids:
            resource = ext_id.get("resource", "")
            identifier = ext_id.get("identifier", "")

            if resource == "ChEMBL" and identifier:
                # Normalize to CHEMBL:NNN format (handle both CHEMBL25 and CHEMBL:25)
                if identifier.startswith("CHEMBL:"):
                    chembl_id = identifier  # Already normalized
                elif identifier.startswith("CHEMBL"):
                    # Extract numeric part and format as CURIE
                    chembl_id = f"CHEMBL:{identifier[6:]}"
                else:
                    chembl_id = f"CHEMBL:{identifier}"
                refs["chembl"] = chembl_id

            elif resource == "KEGG Drug" and identifier:
                refs["kegg"] = identifier

            elif resource == "PubChem Compound" and identifier:
                refs["pubchem_compound"] = str(identifier)

            elif resource == "PubChem Substance" and identifier:
                refs["pubchem_substance"] = str(identifier)

        # UniProt targets
        targets = data.get("targets", [])
        uniprot_ids = []
        for target in targets:
            polypeptides = target.get("polypeptides", [])
            for poly in polypeptides:
                if poly.get("source") == "Swiss-Prot":
                    uniprot_id = poly.get("id")
                    if uniprot_id:
                        uniprot_ids.append(f"UniProtKB:{uniprot_id}")
        if uniprot_ids:
            refs["uniprot"] = uniprot_ids

        # PDB structures
        pdb_ids = data.get("pdb_entries", [])
        if pdb_ids:
            refs["pdb"] = pdb_ids

        return DrugCrossReferences(**refs)

    # =========================================================================
    # Search Response Parsing (T018, T019)
    # =========================================================================

    def _parse_search_response(self, response: httpx.Response) -> list[dict] | None:
        """Parse search response from DrugBank API (T018).

        Handles both commercial JSON and public HTML/JSON responses.

        Args:
            response: HTTP response from search endpoint.

        Returns:
            List of drug data dicts, or None on parse error.
        """
        try:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()

            # For public endpoints, try to extract JSON from page
            # The public search page embeds results in script tags
            text = response.text
            if "application/json" not in content_type:
                # Try to find embedded JSON in the response
                # DrugBank public search returns HTML with embedded data
                json_match = re.search(r'data-drugs="([^"]*)"', text)
                if json_match:
                    json_str = json_match.group(1).replace("&quot;", '"')
                    return json.loads(json_str)

                # Alternative: look for script tag with drugs data
                json_match = re.search(r"var drugs = (\[.*?\]);", text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))

            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse DrugBank search response: {e}")
            return None

    def _transform_search_results(self, drugs: list[dict], query: str) -> list[DrugSearchCandidate]:
        """Transform search results to DrugSearchCandidate list (T019).

        Calculates relevance scores and sorts by score descending.

        Args:
            drugs: Raw drug data from API.
            query: Original search query for score calculation.

        Returns:
            List of DrugSearchCandidate sorted by relevance.
        """
        candidates = []
        query_lower = query.lower()

        for i, drug in enumerate(drugs):
            drug_id = drug.get("drugbank_id", drug.get("id", ""))

            # Ensure CURIE format
            if drug_id and not drug_id.startswith("DrugBank:"):
                drug_id = f"DrugBank:{drug_id}"

            # Skip invalid IDs
            if not DRUGBANK_ID_PATTERN.match(drug_id):
                continue

            name = drug.get("name", "")
            drug_type = drug.get("type", drug.get("drug_type"))
            categories = drug.get("categories", drug.get("groups", []))

            # Ensure categories is a list
            if isinstance(categories, str):
                categories = [categories]

            # Calculate relevance score
            name_lower = name.lower()
            if query_lower == name_lower:
                score = 1.0
            elif query_lower in name_lower:
                score = 0.9 - (i * SCORE_DECAY)
            else:
                score = max(0.1, 0.8 - (i * SCORE_DECAY))

            candidates.append(
                DrugSearchCandidate(
                    id=drug_id,
                    name=name,
                    drug_type=drug_type,
                    categories=categories if categories else None,
                    score=round(score, 2),
                )
            )

        # Sort by score descending
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates

    # =========================================================================
    # Drug Response Parsing (T027, T028)
    # =========================================================================

    def _parse_drug_response(self, response: httpx.Response) -> dict | None:
        """Parse drug detail response from DrugBank API (T027).

        Args:
            response: HTTP response from drug endpoint.

        Returns:
            Drug data dict, or None on parse error.
        """
        try:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()

            # For public endpoints, drug pages are HTML
            # Try to extract structured data
            text = response.text

            # Look for JSON-LD structured data
            json_match = re.search(
                r'<script type="application/ld\+json">(.*?)</script>', text, re.DOTALL
            )
            if json_match:
                return json.loads(json_match.group(1))

            # Fallback: parse HTML to extract fields
            # This is more fragile but works for public access
            return self._parse_drug_html(text)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse DrugBank drug response: {e}")
            return None

    def _parse_drug_html(self, html: str) -> dict | None:
        """Parse drug information from HTML page (fallback for public access).

        Args:
            html: Raw HTML content.

        Returns:
            Drug data dict, or None on parse failure.
        """
        # Simple regex-based extraction for key fields
        data: dict[str, Any] = {}

        # Extract drug name
        name_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
        if name_match:
            data["name"] = name_match.group(1).strip()

        # Extract description
        desc_match = re.search(r"<dt[^>]*>Description</dt>\s*<dd[^>]*>(.*?)</dd>", html, re.DOTALL)
        if desc_match:
            data["description"] = re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()

        # Extract indication
        ind_match = re.search(r"<dt[^>]*>Indication</dt>\s*<dd[^>]*>(.*?)</dd>", html, re.DOTALL)
        if ind_match:
            data["indication"] = re.sub(r"<[^>]+>", "", ind_match.group(1)).strip()

        # Extract mechanism
        mech_match = re.search(
            r"<dt[^>]*>Mechanism of action</dt>\s*<dd[^>]*>(.*?)</dd>", html, re.DOTALL
        )
        if mech_match:
            data["mechanism_of_action"] = re.sub(r"<[^>]+>", "", mech_match.group(1)).strip()

        # Extract half-life
        hl_match = re.search(r"<dt[^>]*>Half-life</dt>\s*<dd[^>]*>(.*?)</dd>", html, re.DOTALL)
        if hl_match:
            data["half_life"] = re.sub(r"<[^>]+>", "", hl_match.group(1)).strip()

        return data if data else None

    def _transform_drug(self, data: dict, drugbank_id: str, slim: bool = False) -> dict | Drug:
        """Transform API response to Drug model (T028).

        Args:
            data: Raw drug data from API.
            drugbank_id: The DrugBank CURIE.
            slim: If True, return minimal fields.

        Returns:
            Drug model or slim dict.
        """
        drug = Drug(
            id=drugbank_id,
            name=data.get("name", "Unknown"),
            drug_type=data.get("type", data.get("drug_type")),
            categories=data.get("categories", data.get("groups")),
            description=data.get("description"),
            indication=data.get("indication"),
            mechanism_of_action=data.get("mechanism_of_action"),
            pharmacodynamics=data.get("pharmacodynamics"),
            absorption=data.get("absorption"),
            metabolism=data.get("metabolism"),
            half_life=data.get("half_life"),
            cross_references=self._build_cross_references(data, drugbank_id),
        )

        if slim:
            return drug.to_slim_dict()

        return drug

    # =========================================================================
    # Public API: Fuzzy Search (T017, T020, T021)
    # =========================================================================

    async def search_drugs(
        self,
        query: str,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope | ErrorEnvelope:
        """Fuzzy search for drugs (Phase 1 of Fuzzy-to-Fact).

        Args:
            query: Search term (min 2 chars).
            slim: Return minimal fields (~20 tokens).
            cursor: Pagination cursor.
            page_size: Results per page (1-100).

        Returns:
            PaginationEnvelope with DrugSearchCandidate items, or ErrorEnvelope.
        """
        # Validate query length (T017)
        if len(query.strip()) < MIN_QUERY_LENGTH:
            return self._create_error(
                ErrorCode.AMBIGUOUS_QUERY,
                f"Query '{query}' is too short.",
                f"Minimum query length is {MIN_QUERY_LENGTH} characters.",
                query,
            )

        # Clamp page_size to valid range
        page_size = max(1, min(100, page_size))

        # Decode cursor
        page, _ = self._decode_cursor(cursor)

        try:
            # Build search URL based on API mode
            base_url = self._select_base_url()
            if self._api_key:
                # Commercial API
                search_url = f"{base_url}/drugs"
                params = {"q": query, "page": page, "per_page": page_size}
            else:
                # Public search endpoint
                search_url = f"{base_url}/unearth/q"
                params = {"query": query}

            response = await self._rate_limited_get(search_url, params)

            # Check for errors
            error = self._handle_response_error(response)
            if error:
                return error

            # Parse response
            drugs = self._parse_search_response(response)
            if drugs is None:
                return self._create_error(
                    ErrorCode.UPSTREAM_ERROR,
                    "Failed to parse DrugBank search response.",
                    "DrugBank API returned unexpected format. Retry later.",
                )

            # Transform to candidates
            candidates = self._transform_search_results(drugs, query)

            # Apply pagination for public API (no server-side pagination)
            if not self._api_key:
                start = (page - 1) * page_size
                end = start + page_size
                page_candidates = candidates[start:end]
                has_more = end < len(candidates)
            else:
                page_candidates = candidates
                # Commercial API handles pagination server-side
                has_more = len(candidates) == page_size

            # Create next cursor (T020)
            next_cursor = None
            if has_more:
                next_cursor = self._encode_cursor(page + 1, page_size)

            # Return pagination envelope (T020)
            return PaginationEnvelope.create(
                items=[
                    c.model_dump(exclude_none=True) if slim else c.model_dump()
                    for c in page_candidates
                ],
                cursor=next_cursor,
                total_count=len(candidates) if not self._api_key else None,
                page_size=page_size,
            )

        except httpx.TimeoutException:
            return self._create_error(
                ErrorCode.UPSTREAM_ERROR,
                "DrugBank API request timed out.",
                "Retry the request or use a shorter query.",
            )
        except httpx.RequestError as e:
            return self._create_error(
                ErrorCode.UPSTREAM_ERROR,
                f"DrugBank API request failed: {e}",
                "Check network connectivity and retry.",
            )
        except Exception as e:
            logger.exception(f"Unexpected error in search_drugs: {e}")
            return self._create_error(
                ErrorCode.UPSTREAM_ERROR,
                f"Unexpected error: {e}",
                "Report this issue and retry later.",
            )

    # =========================================================================
    # Public API: Strict Lookup (T026, T029)
    # =========================================================================

    async def get_drug(self, drugbank_id: str, slim: bool = False) -> dict | ErrorEnvelope:
        """Get drug by DrugBank CURIE (Phase 2 of Fuzzy-to-Fact).

        Args:
            drugbank_id: DrugBank CURIE (format: DrugBank:DBXXXXX).
            slim: Return minimal fields for token efficiency.

        Returns:
            Drug dict with cross_references, or ErrorEnvelope.
        """
        # Validate CURIE format (T025)
        validation_error = self._validate_drugbank_id(drugbank_id)
        if validation_error:
            return validation_error

        # Extract DrugBank ID from CURIE
        db_id = drugbank_id.replace("DrugBank:", "")

        try:
            # Build drug URL based on API mode
            base_url = self._select_base_url()
            if self._api_key:
                drug_url = f"{base_url}/drugs/{db_id}"
            else:
                drug_url = f"{base_url}/drugs/{db_id}"

            response = await self._rate_limited_get(drug_url)

            # Check for errors
            error = self._handle_response_error(response, drugbank_id)
            if error:
                return error

            # Parse response
            data = self._parse_drug_response(response)
            if data is None:
                return self._create_error(
                    ErrorCode.UPSTREAM_ERROR,
                    f"Failed to parse DrugBank response for {drugbank_id}.",
                    "DrugBank API returned unexpected format. Verify ID at go.drugbank.com",
                    drugbank_id,
                )

            # Transform to Drug model
            drug = self._transform_drug(data, drugbank_id, slim)

            # Return as dict for JSON serialization
            if isinstance(drug, Drug):
                return drug.model_dump(exclude_none=True)
            return drug

        except httpx.TimeoutException:
            return self._create_error(
                ErrorCode.UPSTREAM_ERROR,
                f"DrugBank API request timed out for {drugbank_id}.",
                "Retry the request.",
                drugbank_id,
            )
        except httpx.RequestError as e:
            return self._create_error(
                ErrorCode.UPSTREAM_ERROR,
                f"DrugBank API request failed: {e}",
                "Check network connectivity and retry.",
                drugbank_id,
            )
        except Exception as e:
            logger.exception(f"Unexpected error in get_drug: {e}")
            return self._create_error(
                ErrorCode.UPSTREAM_ERROR,
                f"Unexpected error: {e}",
                "Report this issue and retry later.",
                drugbank_id,
            )
