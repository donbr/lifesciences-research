"""BioGRID API client for genetic and protein interactions.

This client provides access to BioGRID's interaction database with rate limiting
and error handling following ADR-001 async-first architecture.
"""

import asyncio
import os
import time

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.biogrid import (
    GENE_SYMBOL_PATTERN,
    BioGridCrossReferences,
    BioGridSearchCandidate,
    GeneticInteraction,
    InteractionResult,
)
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    Pagination,
    PaginationEnvelope,
)


def _safe_int(value: str | int | None) -> int | None:
    """Safely convert value to int, treating '-' and empty strings as None."""
    if value is None or value == "" or value == "-":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class BioGridClient(LifeSciencesClient):
    """Async client for BioGRID API with rate limiting and error handling.

    Rate limited to 2 requests/second per BioGRID best practices.
    Uses exponential backoff on 429/503 errors with Retry-After header support.
    """

    BASE_URL = "https://webservice.thebiogrid.org"
    RATE_LIMIT = 0.5  # 2 req/sec = 0.5 seconds between requests
    MAX_RETRIES = 3  # Maximum retry attempts on rate limiting/server errors

    def __init__(self, api_key: str | None = None):
        """Initialize BioGRID client with API key.

        Args:
            api_key: BioGRID API key. If None, reads from BIOGRID_API_KEY env var.

        Raises:
            ValueError: If API key is not provided or found in environment.
        """
        super().__init__(base_url="https://webservice.thebiogrid.org")
        self.api_key = api_key or os.getenv("BIOGRID_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BIOGRID_API_KEY is required. Get a free key at https://webservice.thebiogrid.org/"
            )

        self._rate_limit_lock = asyncio.Lock()
        self._last_request_time = 0.0

    async def _rate_limited_get(self, url: str, params: dict) -> httpx.Response:
        """Make rate-limited GET request with exponential backoff.

        Implements proper rate limiting with the request inside the lock
        to prevent race conditions. Uses exponential backoff for 429/503 errors.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            HTTP response from the API.
        """
        # Add API key to params
        params_with_key = {**params, "accesskey": self.api_key}

        # Initial request with rate limiting
        async with self._rate_limit_lock:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self.RATE_LIMIT:
                await asyncio.sleep(self.RATE_LIMIT - elapsed)

            client = await self._get_client()
            response = await client.get(url, params=params_with_key)
            self._last_request_time = time.monotonic()

        # Exponential backoff on rate limit/server errors
        for attempt in range(self.MAX_RETRIES):
            if response.status_code not in (429, 503):
                break

            # Calculate backoff time - use Retry-After header if present (T056)
            retry_after = response.headers.get("Retry-After")
            wait_time = int(retry_after) if retry_after else (2**attempt)

            # Sleep OUTSIDE lock to allow other requests to proceed
            await asyncio.sleep(wait_time)

            # Retry with lock - re-check time boundary to prevent thundering herd
            async with self._rate_limit_lock:
                elapsed = time.monotonic() - self._last_request_time
                if elapsed < self.RATE_LIMIT:
                    await asyncio.sleep(self.RATE_LIMIT - elapsed)

                client = await self._get_client()
                response = await client.get(url, params=params_with_key)
                self._last_request_time = time.monotonic()

        return response

    async def search_genes(
        self, query: str, organism: int = 9606
    ) -> PaginationEnvelope[BioGridSearchCandidate] | ErrorEnvelope:
        """Validate gene symbol for BioGRID queries (Fuzzy Phase 1).

        Args:
            query: Gene symbol to validate
            organism: NCBI Taxonomy ID (default: 9606 for Homo sapiens)

        Returns:
            PaginationEnvelope with validated gene or ErrorEnvelope on error
        """
        # Validation: query too short
        if len(query) < 2:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message="Query must be at least 2 characters",
                    recovery_hint="Provide at least 2 characters for gene symbol search",
                    invalid_input=query,
                )
            )

        # Normalize to uppercase
        symbol = query.upper()

        # Validate format
        if not GENE_SYMBOL_PATTERN.match(symbol):
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message=f"Invalid gene symbol format: {symbol}",
                    recovery_hint="Gene symbols must be 1-15 characters, alphanumeric with hyphens allowed",
                    invalid_input=query,
                )
            )

        # Create candidate (validation phase - actual BioGRID query happens in get_interactions)
        organism_names = {
            9606: "Homo sapiens",
            10090: "Mus musculus",
            7227: "Drosophila melanogaster",
        }
        candidate = BioGridSearchCandidate(
            symbol=symbol,
            organism=organism_names.get(organism, f"Organism {organism}"),
            taxon_id=organism,
            is_valid=True,
        )

        return PaginationEnvelope(
            items=[candidate],
            pagination=Pagination(cursor=None, total_count=1, page_size=1),
        )

    async def get_interactions(
        self,
        gene_symbol: str,
        organism: int = 9606,
        max_results: int = 10000,
        include_interspecies: bool = False,
    ) -> InteractionResult | ErrorEnvelope:
        """Get genetic/protein interactions for a gene symbol (Strict Phase 2).

        Args:
            gene_symbol: Validated gene symbol
            organism: NCBI Taxonomy ID (default: 9606)
            max_results: Max interactions to return (default/max: 10000)
            include_interspecies: Include interspecies interactions (default: False)

        Returns:
            InteractionResult with interactions or ErrorEnvelope on error
        """
        # Normalize and validate
        symbol = gene_symbol.upper()
        if not GENE_SYMBOL_PATTERN.match(symbol):
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message=f"Invalid gene symbol format: {symbol}",
                    recovery_hint="Use search_genes to validate gene symbol first",
                    invalid_input=gene_symbol,
                )
            )

        # Enforce max limit
        limit = min(max_results, 10000)

        try:
            # Query BioGRID API
            url = f"{self.BASE_URL}/interactions/"
            params = {
                "geneList": symbol,
                "taxId": organism,
                "includeInterspecies": "true" if include_interspecies else "false",
                "format": "json",
            }

            response = await self._rate_limited_get(url, params)

            # Check for errors after retries exhausted
            if response.status_code == 429:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.RATE_LIMITED,
                        message="BioGRID API rate limit exceeded after retries",
                        recovery_hint="Wait 1 second before retrying. Rate limit: 2 req/sec",
                        invalid_input=gene_symbol,
                    )
                )
            if response.status_code == 503:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.UPSTREAM_ERROR,
                        message="BioGRID API temporarily unavailable after retries",
                        recovery_hint="Service is overloaded. Wait and retry in 30 seconds",
                        invalid_input=gene_symbol,
                    )
                )
            response.raise_for_status()
            data = response.json()

            # Parse interactions
            interactions = []
            entrez_gene_a = None

            for interaction_id, interaction_data in list(data.items())[:limit]:
                # Extract Entrez ID from first interaction
                if entrez_gene_a is None:
                    entrez_gene_a = _safe_int(interaction_data.get("ENTREZ_GENE_A"))

                # Parse interaction
                interaction = GeneticInteraction(
                    biogrid_interaction_id=int(interaction_id),
                    symbol_a=interaction_data.get("OFFICIAL_SYMBOL_A", "").upper(),
                    symbol_b=interaction_data.get("OFFICIAL_SYMBOL_B", "").upper(),
                    experimental_system=interaction_data.get("EXPERIMENTAL_SYSTEM", ""),
                    experimental_system_type=interaction_data.get(
                        "EXPERIMENTAL_SYSTEM_TYPE", "physical"
                    ).lower(),
                    pubmed_id=_safe_int(interaction_data.get("PUBMED_ID")),
                    throughput=interaction_data.get("THROUGHPUT") or None,
                    organism_a_id=_safe_int(interaction_data.get("ORGANISM_A_ID")) or organism,
                    organism_b_id=_safe_int(interaction_data.get("ORGANISM_B_ID")) or organism,
                    entrez_gene_a=_safe_int(interaction_data.get("ENTREZ_GENE_A")),
                    entrez_gene_b=_safe_int(interaction_data.get("ENTREZ_GENE_B")),
                )
                interactions.append(interaction)

            # Check if no interactions found
            if not interactions:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.ENTITY_NOT_FOUND,
                        message=f"No interactions found for gene: {symbol}",
                        recovery_hint="Verify gene symbol is correct and has known interactions in BioGRID",
                        invalid_input=gene_symbol,
                    )
                )

            # Calculate counts
            physical_count = sum(
                1 for i in interactions if i.experimental_system_type == "physical"
            )
            genetic_count = sum(1 for i in interactions if i.experimental_system_type == "genetic")

            # Build cross-references (omit if None per Constitution)
            cross_refs = BioGridCrossReferences(
                entrez=str(entrez_gene_a) if entrez_gene_a else None
            )

            return InteractionResult(
                query_gene=symbol,
                interactions=interactions,
                cross_references=cross_refs,
                physical_count=physical_count,
                genetic_count=genetic_count,
                total_count=len(interactions),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.UPSTREAM_ERROR,
                        message="BioGRID API authentication failed",
                        recovery_hint="Check BIOGRID_API_KEY is valid. Get free key at https://webservice.thebiogrid.org/",
                        invalid_input=gene_symbol,
                    )
                )
            else:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.UPSTREAM_ERROR,
                        message=f"BioGRID API error: {e.response.status_code}",
                        recovery_hint="Check BioGRID API status or try again later",
                        invalid_input=gene_symbol,
                    )
                )
        except Exception as e:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Unexpected error: {e!r}",
                    recovery_hint="Check network connection and BioGRID API status",
                    invalid_input=gene_symbol,
                )
            )
