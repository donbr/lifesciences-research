"""HGNC REST API client implementing the Fuzzy-to-Fact protocol.

This module provides the HGNCClient for querying the HUGO Gene Nomenclature
Committee database for gene symbol resolution and cross-references.

Status: FROZEN - Do not modify during parallel implementation.
"""

import asyncio
import base64
import json
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.envelopes import (
    ErrorEnvelope,
    PaginationEnvelope,
)
from lifesciences_mcp.models.gene import (
    HGNC_CURIE_PATTERN,
    CrossReferences,
    Gene,
    SearchCandidate,
)


class HGNCClient(LifeSciencesClient):
    """HGNC REST API client implementing the Fuzzy-to-Fact protocol.

    Rate limited to 10 requests/second per HGNC documentation.
    Uses exponential backoff on 429/403/503 errors.

    Can be used as a context manager:
        async with HGNCClient() as client:
            result = await client.search_genes("BRCA1")
    """

    HGNC_BASE_URL = "https://rest.genenames.org"
    RATE_LIMIT_DELAY = 0.1  # 10 req/s = 100ms between requests
    AMBIGUOUS_THRESHOLD = 100  # Max results before query is considered ambiguous
    SCORE_DECAY = 0.05  # Score reduction per position in results
    MAX_RETRIES = 3  # Maximum retry attempts on rate limiting

    def __init__(self) -> None:
        """Initialize the HGNC client."""
        super().__init__(base_url=self.HGNC_BASE_URL)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "HGNCClient":
        """Enter context manager."""
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """Exit context manager and cleanup resources."""
        await self.close()

    async def _rate_limited_get(self, path: str) -> httpx.Response:
        """Make a rate-limited GET request with exponential backoff.

        Implements proper rate limiting with the request inside the lock
        to prevent race conditions.

        Args:
            path: API endpoint path.

        Returns:
            HTTP response from the API.
        """
        # Initial request with rate limiting
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

            response = await self._get(path)
            self._last_request_time = asyncio.get_event_loop().time()

        # Exponential backoff on rate limit errors
        for attempt in range(self.MAX_RETRIES):
            if response.status_code not in (429, 403, 503):
                break

            # Calculate backoff time
            retry_after = response.headers.get("Retry-After")
            wait_time = int(retry_after) if retry_after else (2**attempt)

            # Sleep OUTSIDE lock to allow other requests to proceed
            await asyncio.sleep(wait_time)

            # Retry with lock - re-check time boundary to prevent thundering herd
            async with self._lock:
                # CRITICAL: Re-check timing after acquiring lock
                # Other requests may have completed during our backoff sleep
                now = asyncio.get_event_loop().time()
                elapsed = now - self._last_request_time
                if elapsed < self.RATE_LIMIT_DELAY:
                    await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

                response = await self._get(path)
                self._last_request_time = asyncio.get_event_loop().time()

        return response

    async def search_genes(
        self,
        query: str,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope[SearchCandidate] | ErrorEnvelope:
        """Fuzzy search for genes (Phase 1 of Fuzzy-to-Fact).

        Searches multiple HGNC fields with alias boosting:
        1. First searches alias_symbol field for exact alias matches (boosted to score=1.0)
        2. Then searches general endpoint for symbol/name matches
        3. Merges results with alias matches prioritized

        This ensures common aliases like "p53" resolve to TP53 first.

        Args:
            query: Search term (gene symbol, name, or natural language).
            slim: If true, return minimal fields (~20 tokens per entity).
            cursor: Opaque cursor for pagination.
            page_size: Results per page (1-100).

        Returns:
            PaginationEnvelope with SearchCandidate items, or ErrorEnvelope.
        """
        # Validate query length
        if len(query.strip()) < 2:
            return ErrorEnvelope.ambiguous_query(query, 0)

        # Clamp page_size to valid range
        page_size = max(1, min(100, page_size))

        try:
            # Decode cursor for offset if provided
            # NOTE: HGNC /search/ endpoint does NOT support server-side pagination
            # (no start/rows params) so we use client-side slicing
            offset = 0
            if cursor:
                try:
                    cursor_data = json.loads(base64.b64decode(cursor).decode())
                    offset = cursor_data.get("offset", 0)
                except (ValueError, json.JSONDecodeError):
                    offset = 0

            # Step 1: Search by alias_symbol for exact alias matches (boosted)
            alias_docs = await self._search_by_alias(query)
            alias_hgnc_ids = {str(doc.get("hgnc_id")) for doc in alias_docs}

            # Step 2: General search for symbol/name matches
            response = await self._rate_limited_get(f"/search/{query}")

            if response.status_code == 429:
                return ErrorEnvelope.rate_limited()
            if response.status_code >= 500:
                return ErrorEnvelope.upstream_error(response.status_code)
            if response.status_code != 200:
                return ErrorEnvelope.upstream_error(response.status_code, response.text)

            data = response.json()
            general_docs = data.get("response", {}).get("docs", [])
            total_count = data.get("response", {}).get("numFound", len(general_docs))

            # Adjust total_count for alias matches not in general results
            new_alias_count = len([d for d in alias_docs if str(d.get("hgnc_id")) not in {str(g.get("hgnc_id")) for g in general_docs}])
            total_count += new_alias_count

            # Check for ambiguous results
            if total_count > self.AMBIGUOUS_THRESHOLD and len(query.strip()) < 3:
                return ErrorEnvelope.ambiguous_query(query, total_count)

            # Step 3: Build candidates with alias matches first (boosted to score=1.0)
            candidates = []
            seen_ids: set[str] = set()

            # Add alias matches first with perfect score
            for doc in alias_docs:
                hgnc_id = str(doc["hgnc_id"])
                if not hgnc_id.startswith("HGNC:"):
                    hgnc_id = f"HGNC:{hgnc_id}"

                if hgnc_id not in seen_ids:
                    candidate = SearchCandidate(
                        id=hgnc_id,
                        symbol=doc.get("symbol", ""),
                        name=doc.get("name", ""),
                        score=1.0,  # Alias matches get perfect score
                    )
                    candidates.append(candidate)
                    seen_ids.add(hgnc_id)

            # Add general results (excluding duplicates, with position-based scoring)
            # Exact symbol matches get 1.0, others start at 0.95 max
            query_upper = query.upper().strip()
            general_position = 0
            for doc in general_docs:
                hgnc_id = str(doc["hgnc_id"])
                if not hgnc_id.startswith("HGNC:"):
                    hgnc_id = f"HGNC:{hgnc_id}"

                if hgnc_id not in seen_ids:
                    symbol = doc.get("symbol", "")

                    # Exact symbol match gets perfect score
                    if symbol.upper() == query_upper:
                        score = 1.0
                    else:
                        # Position-based scoring - max 0.95 so exact matches always rank first
                        score = max(0.1, 0.95 - (general_position * self.SCORE_DECAY))
                        general_position += 1

                    candidate = SearchCandidate(
                        id=hgnc_id,
                        symbol=symbol,
                        name=doc.get("name", ""),
                        score=round(score, 2),
                    )
                    candidates.append(candidate)
                    seen_ids.add(hgnc_id)

            # Sort by score descending to ensure exact/alias matches appear first
            candidates.sort(key=lambda c: c.score, reverse=True)

            # Apply client-side pagination (HGNC doesn't support server-side pagination)
            page_start = offset
            page_end = offset + page_size
            page_items = candidates[page_start:page_end]

            # Create next cursor if more results available
            next_cursor = None
            if page_end < len(candidates):
                cursor_data = {"offset": page_end}
                next_cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

            return PaginationEnvelope.create(
                items=page_items,
                cursor=next_cursor,
                total_count=total_count,
                page_size=page_size,
            )

        except httpx.TimeoutException:
            return ErrorEnvelope.upstream_error(504, "Request timeout")
        except httpx.RequestError as e:
            return ErrorEnvelope.upstream_error(502, str(e))

    async def _search_by_alias(self, query: str) -> list[dict[str, Any]]:
        """Search HGNC by alias_symbol field.

        Args:
            query: Search term to match against alias symbols.

        Returns:
            List of matching HGNC documents.
        """
        try:
            response = await self._rate_limited_get(f"/search/alias_symbol/{query}")
            if response.status_code == 200:
                data = response.json()
                return data.get("response", {}).get("docs", [])
        except Exception:
            pass  # Fall through on alias search failure
        return []

    async def get_gene(self, hgnc_id: str) -> Gene | ErrorEnvelope:
        """Get complete gene record by HGNC CURIE (Phase 2 of Fuzzy-to-Fact).

        Args:
            hgnc_id: HGNC CURIE in format 'HGNC:NNNNN'.

        Returns:
            Gene record with cross_references, or ErrorEnvelope.
        """
        # Validate CURIE format (Fuzzy-to-Fact enforcement)
        if not HGNC_CURIE_PATTERN.match(hgnc_id):
            return ErrorEnvelope.unresolved_entity(hgnc_id)

        # Extract numeric ID from CURIE
        numeric_id = hgnc_id.replace("HGNC:", "")

        try:
            response = await self._rate_limited_get(f"/fetch/hgnc_id/{numeric_id}")

            if response.status_code == 429:
                return ErrorEnvelope.rate_limited()
            if response.status_code >= 500:
                return ErrorEnvelope.upstream_error(response.status_code)
            if response.status_code != 200:
                return ErrorEnvelope.upstream_error(response.status_code, response.text)

            data = response.json()
            docs = data.get("response", {}).get("docs", [])

            if not docs:
                return ErrorEnvelope.entity_not_found(hgnc_id)

            doc = docs[0]

            # Build cross-references from HGNC response
            cross_refs = self._build_cross_references(doc)

            # Build Gene model
            gene = Gene(
                id=hgnc_id,
                symbol=doc.get("symbol", ""),
                name=doc.get("name", ""),
                status=doc.get("status", "Approved"),
                locus_type=doc.get("locus_type"),
                locus_group=doc.get("locus_group"),
                location=doc.get("location"),
                alias_symbols=doc.get("alias_symbol") or None,
                alias_names=doc.get("alias_name") or None,
                prev_symbols=doc.get("prev_symbol") or None,
                prev_names=doc.get("prev_name") or None,
                cross_references=cross_refs,
            )

            return gene

        except httpx.TimeoutException:
            return ErrorEnvelope.upstream_error(504, "Request timeout")
        except httpx.RequestError as e:
            return ErrorEnvelope.upstream_error(502, str(e))

    def _build_cross_references(self, doc: dict[str, Any]) -> CrossReferences:
        """Map HGNC response fields to CrossReferences model.

        Per ADR-001: omit keys with no value (never null/empty).
        """
        return CrossReferences(
            ensembl_gene=doc.get("ensembl_gene_id"),
            uniprot=doc.get("uniprot_ids") or None,
            entrez=doc.get("entrez_id"),
            refseq=doc.get("refseq_accession") or None,
            omim=self._extract_omim(doc.get("omim_id")),
        )

    def _extract_omim(self, omim_value: Any) -> str | None:
        """Extract OMIM ID, handling list format from HGNC."""
        if not omim_value:
            return None
        if isinstance(omim_value, list) and omim_value:
            return str(omim_value[0])
        return str(omim_value) if omim_value else None
