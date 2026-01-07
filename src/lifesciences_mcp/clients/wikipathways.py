"""WikiPathways API client with rate limiting and exponential backoff.

This client implements:
- Async httpx client for WikiPathways REST API
- Conservative rate limiting (1 req/sec with asyncio.Lock)
- Exponential backoff for 429/503 responses
- Client-side cursor pagination (base64-encoded offsets)
- Bulk cross-reference file fetching and caching
- Cross-reference mapping to Agentic Biolink 22-key schema

Base URL: http://webservice.wikipathways.org
Bulk Files: https://www.wikipathways.org/json/
"""

import asyncio
import base64
import re
from datetime import datetime, timedelta
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models import (
    ComponentCounts,
    DataNode,
    ErrorEnvelope,
    PaginationEnvelope,
    Pathway,
    PathwayComponents,
    PathwaySearchCandidate,
    RevisionMetadata,
)

# Constants
WIKIPATHWAYS_BASE_URL = "http://webservice.wikipathways.org"
WIKIPATHWAYS_JSON_BASE = "https://www.wikipathways.org/json"
PATHWAY_ID_PATTERN = re.compile(r"^WP:WP\d+$")


class WikiPathwaysClient(LifeSciencesClient):
    """WikiPathways API client with rate limiting.

    Features:
    - 1 req/sec rate limiting with thundering herd prevention
    - Exponential backoff for 429/503 responses (3 retries, base 2s)
    - Client-side cursor pagination
    - Bulk cross-reference caching
    """

    def __init__(self) -> None:
        """Initialize the WikiPathways client."""
        super().__init__(
            base_url=WIKIPATHWAYS_BASE_URL,
            timeout=10.0,  # Per FR-048
            max_connections=5,
        )

        # Rate limiting (1 req/sec per research.md)
        self._rate_limit_lock = asyncio.Lock()
        self._last_request_time: datetime | None = None
        self._min_request_interval = timedelta(seconds=1)

        # Cross-reference cache (loaded on demand)
        self._xref_cache: dict[str, dict[str, Any]] | None = None
        self._xref_cache_lock = asyncio.Lock()

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limit with thundering herd prevention.

        Implements conservative 1 req/sec rate limiting per research.md §4.
        Uses double-check locking pattern to prevent thundering herd.
        """
        async with self._rate_limit_lock:
            if self._last_request_time:
                elapsed = datetime.now() - self._last_request_time
                if elapsed < self._min_request_interval:
                    sleep_time = (self._min_request_interval - elapsed).total_seconds()
                    await asyncio.sleep(sleep_time)

            # Re-check after lock acquisition (thundering herd prevention)
            if self._last_request_time:
                elapsed = datetime.now() - self._last_request_time
                if elapsed < self._min_request_interval:
                    sleep_time = (self._min_request_interval - elapsed).total_seconds()
                    await asyncio.sleep(sleep_time)

            self._last_request_time = datetime.now()

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff.

        Implements exponential backoff for 429/503 responses per research.md §4.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            max_retries: Maximum retry attempts (default 3)
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            ErrorEnvelope: On rate limit exhaustion or upstream errors
        """
        base_delay = 2.0  # Base delay 2 seconds

        for attempt in range(max_retries + 1):
            try:
                await self._enforce_rate_limit()
                client = await self._get_client()
                response = await client.request(method, url, **kwargs)

                # Handle rate limiting and service unavailable
                if response.status_code in (429, 503):
                    if attempt == max_retries:
                        raise ValueError(
                            "RATE_LIMITED: WikiPathways rate limit exceeded"
                        )

                    # Exponential backoff
                    delay = base_delay * (2**attempt)
                    await asyncio.sleep(delay)
                    continue

                return response

            except httpx.TimeoutException as e:
                if attempt == max_retries:
                    raise ValueError("UPSTREAM_ERROR: WikiPathways API timeout") from e
                await asyncio.sleep(base_delay * (2**attempt))

            except httpx.RequestError as e:
                if attempt == max_retries:
                    raise ValueError(f"UPSTREAM_ERROR: Request failed: {e}") from e
                await asyncio.sleep(base_delay * (2**attempt))

        # This should never be reached, but satisfy type checker
        raise ValueError("UPSTREAM_ERROR: Request failed after retries")

    def _encode_cursor(self, offset: int) -> str:
        """Encode offset as opaque cursor (base64).

        Args:
            offset: Pagination offset

        Returns:
            Base64-encoded cursor string
        """
        return base64.b64encode(str(offset).encode()).decode()

    def _decode_cursor(self, cursor: str) -> int:
        """Decode cursor to offset.

        Args:
            cursor: Base64-encoded cursor

        Returns:
            Pagination offset

        Raises:
            ValueError: If cursor is invalid
        """
        try:
            return int(base64.b64decode(cursor).decode())
        except (ValueError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid cursor format: {e}") from e

    def _validate_pathway_id(self, pathway_id: str) -> bool:
        """Validate pathway ID matches WP:WPNNNNN format.

        Args:
            pathway_id: Pathway identifier to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(PATHWAY_ID_PATTERN.match(pathway_id))

    async def _fetch_cross_references_bulk(self) -> dict[str, dict[str, Any]]:
        """Fetch and cache all pathway cross-references from JSON bulk file.

        Loads findPathwaysByXref.json once and caches for session lifetime.
        Thread-safe with async lock.

        Returns:
            Dictionary mapping pathway ID → cross-references dict
        """
        if self._xref_cache is not None:
            return self._xref_cache

        async with self._xref_cache_lock:
            # Double-check after lock acquisition
            if self._xref_cache is not None:
                return self._xref_cache

            # Fetch bulk file (no rate limiting - different domain)
            url = f"{WIKIPATHWAYS_JSON_BASE}/findPathwaysByXref.json"
            client = await self._get_client()
            response = await client.get(url)
            data = response.json()

            # Build pathway_id → cross_references lookup
            self._xref_cache = {}
            for pathway in data.get("pathwayInfo", []):
                pathway_id = pathway.get("id", "")
                if pathway_id:
                    self._xref_cache[pathway_id] = pathway

            return self._xref_cache

    def _map_cross_references(self, pathway_id: str, pathway_data: dict[str, Any]) -> dict[str, str | list[str]]:
        """Map WikiPathways cross-references to Agentic Biolink 22-key schema.

        Mapping per research.md §5:
        - ncbigene → entrez
        - ensembl → ensembl_gene
        - hgnc.symbol → hgnc
        - uniprot → uniprot (handle semicolon-separated isoforms)

        Args:
            pathway_id: Pathway identifier (WP### numeric portion)
            pathway_data: Pathway cross-reference data from bulk JSON

        Returns:
            Dict of cross-references using Agentic Biolink keys (omit-if-null pattern)
        """
        xrefs = {}

        # Map ncbigene → entrez
        if "ncbigene" in pathway_data:
            entries = pathway_data["ncbigene"].split(", ")
            xrefs["entrez"] = [e.replace("ncbigene:", "") for e in entries if e]

        # Map ensembl → ensembl_gene
        if "ensembl" in pathway_data:
            entries = pathway_data["ensembl"].split(", ")
            xrefs["ensembl_gene"] = [e.replace("ensembl:", "") for e in entries if e]

        # Map hgnc.symbol → hgnc
        if "hgnc" in pathway_data:
            entries = pathway_data["hgnc"].split(", ")
            xrefs["hgnc"] = [e.replace("hgnc.symbol:", "") for e in entries if e]

        # Map uniprot → uniprot (handle semicolon-separated isoforms)
        if "uniprot" in pathway_data:
            entries = pathway_data["uniprot"].split(", ")
            uniprot_list = []
            for entry in entries:
                # Remove uniprot: prefix, then split on semicolon and take first (canonical)
                primary = entry.replace("uniprot:", "").split(";")[0]
                if primary:
                    uniprot_list.append(primary)
            if uniprot_list:
                xrefs["uniprot"] = uniprot_list

        # Omit empty values per ADR-001 §4
        return {k: v for k, v in xrefs.items() if v}

    def _normalize_gene_symbol(self, gene_symbol: str) -> str:
        """Normalize gene symbol to uppercase.

        Args:
            gene_symbol: Gene symbol (e.g., "brca1", "TP53")

        Returns:
            Uppercase gene symbol (e.g., "BRCA1", "TP53")
        """
        return gene_symbol.upper()

    async def search_pathways(
        self,
        query: str,
        organism: str | None = None,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope | ErrorEnvelope:
        """Fuzzy search for pathways by name, description, or gene.

        Args:
            query: Search term (minimum 2 characters)
            organism: Optional organism filter (e.g., "Homo sapiens")
            cursor: Opaque cursor for pagination
            page_size: Results per page (1-100, default 50)

        Returns:
            PaginationEnvelope with PathwaySearchCandidate items, or ErrorEnvelope
        """
        # Validation
        if len(query) < 2:
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "AMBIGUOUS_QUERY",
                    "message": f"Query '{query}' is too short (minimum 2 characters required)",
                    "recovery_hint": "Use a more specific search term with at least 2 characters",
                    "invalid_input": query,
                },
            )

        # Validate page_size
        if page_size < 1 or page_size > 100:
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "AMBIGUOUS_QUERY",
                    "message": f"Invalid page_size {page_size}. Must be between 1-100",
                    "recovery_hint": "Use page_size between 1 and 100",
                    "invalid_input": str(page_size),
                },
            )

        try:
            # Build request parameters
            params = {"query": query, "format": "json"}
            if organism:
                params["species"] = organism

            # Make API request with retry logic
            response = await self._request_with_retry(
                "GET",
                "/findPathwaysByText",
                params=params,
            )

            # Check for error response
            if isinstance(response, ErrorEnvelope):
                return response

            # Parse response
            data = response.json()
            all_results = data.get("result", [])

            # Convert to PathwaySearchCandidate with position decay scoring
            candidates = []
            for position, item in enumerate(all_results):
                # Parse score (comes as {"0": "4.639924"})
                score_obj = item.get("score", {})
                base_score = float(score_obj.get("0", "0.0")) if score_obj else 0.0

                # Apply position decay: score - (position * 0.05)
                # Normalize to 0.0-1.0 range (WikiPathways scores typically 0-5)
                normalized_score = max(0.0, min(1.0, (base_score - (position * 0.05)) / 5.0))

                # Extract description (use name if no description available)
                description = item.get("name", "")[:200]  # First 200 chars

                # Create candidate with WP:WPNNNNN format
                wp_id = item.get("id", "")
                candidate = PathwaySearchCandidate(
                    id=f"WP:{wp_id}",
                    title=item.get("name", ""),
                    organism=item.get("species", ""),
                    description=description,
                    score=normalized_score,
                )
                candidates.append(candidate)

            # Client-side cursor pagination
            offset = self._decode_cursor(cursor) if cursor else 0
            page_candidates = candidates[offset : offset + page_size]

            # Calculate next cursor
            next_offset = offset + page_size
            next_cursor = self._encode_cursor(next_offset) if next_offset < len(candidates) else None

            # Return PaginationEnvelope
            return PaginationEnvelope(
                items=[candidate.model_dump() for candidate in page_candidates],
                pagination={
                    "cursor": next_cursor,
                    "total_count": len(candidates),
                    "page_size": page_size,
                },
            )

        except ValueError as e:
            # Handle cursor decode errors
            if "Invalid cursor" in str(e):
                return ErrorEnvelope(
                    success=False,
                    error={
                        "code": "AMBIGUOUS_QUERY",
                        "message": str(e),
                        "recovery_hint": "Use cursor from previous response or omit for first page",
                        "invalid_input": cursor or "",
                    },
                )
            # Re-raise other ValueError
            raise

        except Exception as e:
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "UPSTREAM_ERROR",
                    "message": f"Search failed: {e}",
                    "recovery_hint": "Check WikiPathways API status and retry",
                },
            )

    async def get_pathway(self, pathway_id: str) -> Pathway | ErrorEnvelope:
        """Get complete pathway record by WikiPathways CURIE.

        Args:
            pathway_id: WikiPathways CURIE in format 'WP:WPNNNNN'

        Returns:
            Pathway record with cross_references, or ErrorEnvelope
        """
        # Validation
        if not self._validate_pathway_id(pathway_id):
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "UNRESOLVED_ENTITY",
                    "message": f"Invalid pathway ID format '{pathway_id}'. Expected WP:WPNNNNN format",
                    "recovery_hint": "Call search_pathways to resolve pathway identifier first",
                    "invalid_input": pathway_id,
                },
            )

        try:
            # Extract numeric WP ID (e.g., "WP:WP534" -> "WP534")
            wp_numeric_id = pathway_id.replace("WP:", "")

            # 1. Get pathway metadata from /getPathwayInfo
            response = await self._request_with_retry(
                "GET",
                "/getPathwayInfo",
                params={"pwId": wp_numeric_id, "format": "json"},
            )

            # Check for error response
            if isinstance(response, ErrorEnvelope):
                return response

            data = response.json()
            pathway_info = data.get("pathwayInfo", {})

            # Check if pathway exists
            if not pathway_info or not pathway_info.get("id"):
                return ErrorEnvelope(
                    success=False,
                    error={
                        "code": "ENTITY_NOT_FOUND",
                        "message": f"Pathway {pathway_id} not found in WikiPathways database",
                        "recovery_hint": "Verify pathway ID or use search_pathways to find valid pathway",
                        "invalid_input": pathway_id,
                    },
                )

            # 2. Fetch cross-references from bulk JSON file
            xref_cache = await self._fetch_cross_references_bulk()
            pathway_xref_data = xref_cache.get(wp_numeric_id, {})
            cross_references = self._map_cross_references(wp_numeric_id, pathway_xref_data)

            # 3. Get component counts by calling getXrefList for different codes
            # Code L = genes, S = proteins, Ce = metabolites
            gene_count = 0
            protein_count = 0
            metabolite_count = 0

            try:
                # Get gene count (code L = NCBI Gene)
                gene_response = await self._request_with_retry(
                    "GET",
                    "/getXrefList",
                    params={"pwId": wp_numeric_id, "code": "L", "format": "json"},
                )
                if not isinstance(gene_response, ErrorEnvelope):
                    gene_data = gene_response.json()
                    gene_count = len(gene_data.get("xrefs", []))

                # Get protein count (code S = UniProt)
                protein_response = await self._request_with_retry(
                    "GET",
                    "/getXrefList",
                    params={"pwId": wp_numeric_id, "code": "S", "format": "json"},
                )
                if not isinstance(protein_response, ErrorEnvelope):
                    protein_data = protein_response.json()
                    protein_count = len(protein_data.get("xrefs", []))

                # Get metabolite count (code Ce = ChEBI)
                metabolite_response = await self._request_with_retry(
                    "GET",
                    "/getXrefList",
                    params={"pwId": wp_numeric_id, "code": "Ce", "format": "json"},
                )
                if not isinstance(metabolite_response, ErrorEnvelope):
                    metabolite_data = metabolite_response.json()
                    metabolite_count = len(metabolite_data.get("xrefs", []))

            except Exception:
                # If component count fetching fails, use zeros (non-critical)
                pass

            # 4. Build Pathway model
            pathway = Pathway(
                id=pathway_id,
                title=pathway_info.get("name", ""),
                organism=pathway_info.get("species", ""),
                description=pathway_info.get("name", "")[:200],  # Use name as description
                revision=RevisionMetadata(
                    version=pathway_info.get("revision", ""),
                    last_modified=None,  # Not available in API response
                    curators=[],  # Not available in API response
                ),
                component_counts=ComponentCounts(
                    gene_count=gene_count,
                    protein_count=protein_count,
                    metabolite_count=metabolite_count,
                    interaction_count=0,  # Not available without GPML parsing
                ),
                cross_references=cross_references,
                url=pathway_info.get("url", f"https://classic.wikipathways.org/index.php/Pathway:{wp_numeric_id}"),
            )

            return pathway

        except Exception as e:
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "UPSTREAM_ERROR",
                    "message": f"Pathway lookup failed: {e}",
                    "recovery_hint": "Check WikiPathways API status and retry",
                },
            )

    async def get_pathways_for_gene(
        self,
        gene_id: str,
        organism: str | None = None,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope | ErrorEnvelope:
        """Find all pathways containing a specific gene.

        Args:
            gene_id: Gene identifier (symbol, Entrez ID, or Ensembl ID)
            organism: Optional organism filter (exact scientific name match)
            cursor: Opaque cursor for pagination
            page_size: Results per page (1-100, default 50)

        Returns:
            PaginationEnvelope with PathwaySearchCandidate items, or ErrorEnvelope
        """
        # Validation
        if not gene_id or not gene_id.strip():
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "AMBIGUOUS_QUERY",
                    "message": "Gene ID cannot be empty",
                    "recovery_hint": "Provide a valid gene symbol, Entrez ID, or Ensembl ID",
                    "invalid_input": gene_id,
                },
            )

        # Validate page_size
        if page_size < 1 or page_size > 100:
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "AMBIGUOUS_QUERY",
                    "message": f"Invalid page_size {page_size}. Must be between 1-100",
                    "recovery_hint": "Use page_size between 1 and 100",
                    "invalid_input": str(page_size),
                },
            )

        try:
            # Normalize gene symbol to uppercase (per contract)
            normalized_gene = self._normalize_gene_symbol(gene_id.strip())

            # Build request parameters
            params = {"ids": normalized_gene, "format": "json"}

            # Make API request with retry logic
            response = await self._request_with_retry(
                "GET",
                "/findPathwaysByXref",
                params=params,
            )

            # Check for error response
            if isinstance(response, ErrorEnvelope):
                return response

            # Parse response
            data = response.json()
            all_results = data.get("result", [])

            # Filter by organism if provided (exact match)
            if organism:
                all_results = [r for r in all_results if r.get("species") == organism]

            # Convert to PathwaySearchCandidate with position decay scoring
            candidates = []
            for position, item in enumerate(all_results):
                # Parse score (comes as {"0": "4.639924"})
                score_obj = item.get("score", {})
                base_score = float(score_obj.get("0", "0.0")) if score_obj else 0.0

                # Apply position decay: score - (position * 0.05)
                # Normalize to 0.0-1.0 range (WikiPathways scores typically 0-5)
                normalized_score = max(0.0, min(1.0, (base_score - (position * 0.05)) / 5.0))

                # Extract description (use name if no description available)
                description = item.get("name", "")[:200]  # First 200 chars

                # Create candidate with WP:WPNNNNN format
                wp_id = item.get("id", "")
                candidate = PathwaySearchCandidate(
                    id=f"WP:{wp_id}",
                    title=item.get("name", ""),
                    organism=item.get("species", ""),
                    description=description,
                    score=normalized_score,
                )
                candidates.append(candidate)

            # Client-side cursor pagination
            offset = self._decode_cursor(cursor) if cursor else 0
            page_candidates = candidates[offset : offset + page_size]

            # Calculate next cursor
            next_offset = offset + page_size
            next_cursor = self._encode_cursor(next_offset) if next_offset < len(candidates) else None

            # Return PaginationEnvelope
            return PaginationEnvelope(
                items=[candidate.model_dump() for candidate in page_candidates],
                pagination={
                    "cursor": next_cursor,
                    "total_count": len(candidates),
                    "page_size": page_size,
                },
            )

        except ValueError as e:
            # Handle cursor decode errors
            if "Invalid cursor" in str(e):
                return ErrorEnvelope(
                    success=False,
                    error={
                        "code": "AMBIGUOUS_QUERY",
                        "message": str(e),
                        "recovery_hint": "Use cursor from previous response or omit for first page",
                        "invalid_input": cursor or "",
                    },
                )
            # Re-raise other ValueError
            raise

        except Exception as e:
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "UPSTREAM_ERROR",
                    "message": f"Gene lookup failed: {e}",
                    "recovery_hint": "Check WikiPathways API status and retry",
                },
            )

    async def get_pathway_components(
        self,
        pathway_id: str,
    ) -> PathwayComponents | ErrorEnvelope:
        """Extract all biological entities from pathway.

        Args:
            pathway_id: WikiPathways CURIE in format 'WP:WPNNNNN'

        Returns:
            PathwayComponents with genes, proteins, metabolites, interactions or ErrorEnvelope
        """
        # Validation
        if not self._validate_pathway_id(pathway_id):
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "UNRESOLVED_ENTITY",
                    "message": f"Invalid pathway ID format '{pathway_id}'. Expected WP:WPNNNNN format",
                    "recovery_hint": "Call search_pathways to resolve pathway identifier first",
                    "invalid_input": pathway_id,
                },
            )

        try:
            # Extract numeric WP ID (e.g., "WP:WP534" -> "WP534")
            wp_numeric_id = pathway_id.replace("WP:", "")

            # First, verify pathway exists
            verify_response = await self._request_with_retry(
                "GET",
                "/getPathwayInfo",
                params={"pwId": wp_numeric_id, "format": "json"},
            )

            if isinstance(verify_response, ErrorEnvelope):
                return verify_response

            verify_data = verify_response.json()
            pathway_info = verify_data.get("pathwayInfo", {})

            if not pathway_info or not pathway_info.get("id"):
                return ErrorEnvelope(
                    success=False,
                    error={
                        "code": "ENTITY_NOT_FOUND",
                        "message": f"Pathway {pathway_id} not found in WikiPathways database",
                        "recovery_hint": "Verify pathway ID or use search_pathways to find valid pathway",
                        "invalid_input": pathway_id,
                    },
                )

            # Fetch components by BridgeDb code
            genes: list[DataNode] = []
            proteins: list[DataNode] = []
            metabolites: list[DataNode] = []

            # BridgeDb codes: L=Entrez, H=HGNC, En=Ensembl, S=UniProt, Ce=ChEMBL, Ch=CHEBI
            code_mappings = [
                ("L", "Gene", "Entrez Gene", "ncbigene", "entrez"),
                ("H", "Gene", "HGNC", "hgnc", "hgnc"),
                ("En", "Gene", "Ensembl", "ensembl", "ensembl_gene"),
                ("S", "Protein", "UniProt", "uniprot", "uniprot"),
                ("Ce", "Metabolite", "ChEMBL", "chembl", "chembl"),
                ("Ch", "Metabolite", "CHEBI", "chebi", "chebi"),
            ]

            for code, entity_type, database, id_prefix, xref_key in code_mappings:
                try:
                    response = await self._request_with_retry(
                        "GET",
                        "/getXrefList",
                        params={"pwId": wp_numeric_id, "code": code, "format": "json"},
                    )

                    if isinstance(response, ErrorEnvelope):
                        continue  # Skip if this code fails

                    data = response.json()
                    xrefs = data.get("xrefs", [])

                    # API returns raw ID strings, not objects (AGE-131 fix)
                    for xref_id in xrefs:
                        # xref_id is a raw string like "1737", not an object
                        if not xref_id:
                            continue

                        # Use ID as label for now (TODO: fetch human-readable names)
                        xref_label = str(xref_id)

                        # Handle UniProt isoforms (split on semicolon, use first)
                        if id_prefix == "uniprot" and ";" in xref_id:
                            xref_id = xref_id.split(";")[0]

                        # Create DataNode
                        node = DataNode(
                            id=f"{id_prefix}:{xref_id}",
                            label=xref_label,
                            type=entity_type,
                            database=database,
                            cross_references={xref_key: xref_id},
                        )

                        # Add to appropriate list
                        if entity_type == "Gene":
                            genes.append(node)
                        elif entity_type == "Protein":
                            proteins.append(node)
                        elif entity_type == "Metabolite":
                            metabolites.append(node)

                except Exception:
                    # Skip failed API calls (non-critical)
                    continue

            # Build PathwayComponents (omit empty lists per ADR-001 §4)
            components_data = {}
            if genes:
                components_data["genes"] = genes
            if proteins:
                components_data["proteins"] = proteins
            if metabolites:
                components_data["metabolites"] = metabolites

            # Always include interactions (even if empty, per contract)
            components_data["interactions"] = []

            return PathwayComponents(**components_data)

        except Exception as e:
            return ErrorEnvelope(
                success=False,
                error={
                    "code": "UPSTREAM_ERROR",
                    "message": f"Component extraction failed: {e}",
                    "recovery_hint": "Check WikiPathways API status and retry",
                },
            )
