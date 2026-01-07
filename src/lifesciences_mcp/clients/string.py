"""STRING DB REST API client implementing the Fuzzy-to-Fact protocol.

This module provides the STRINGClient for querying protein-protein
interaction networks from the STRING database.

STRING API Documentation: https://string-db.org/help/api/

Status: NEW - Tier 1 implementation.
"""

import asyncio
import base64
import json
import time
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    PaginationEnvelope,
)
from lifesciences_mcp.models.interaction import (
    STRING_CURIE_PATTERN,
    EvidenceScores,
    Interaction,
    InteractionCrossReferences,
    InteractionNetwork,
    InteractionSearchCandidate,
)


class STRINGClient(LifeSciencesClient):
    """STRING DB REST API client implementing the Fuzzy-to-Fact protocol.

    Rate limited to 1 request/second per STRING documentation.
    Uses exponential backoff on 429 errors.

    Can be used as a context manager:
        async with STRINGClient() as client:
            result = await client.search_proteins("TP53")
    """

    STRING_BASE_URL = "https://string-db.org/api"
    RATE_LIMIT_DELAY = 1.0  # 1 req/s = 1000ms between requests
    DEFAULT_SPECIES = 9606  # Homo sapiens
    DEFAULT_SCORE_THRESHOLD = 400  # Medium confidence (STRING uses 0-1000)
    MAX_RETRIES = 3
    AMBIGUOUS_THRESHOLD = 100

    def __init__(self, species: int = DEFAULT_SPECIES) -> None:
        """Initialize the STRING client.

        Args:
            species: NCBI Taxonomy ID (default 9606 for human).
        """
        super().__init__(base_url=self.STRING_BASE_URL)
        self.species = species
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "STRINGClient":
        """Enter context manager."""
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """Exit context manager and cleanup resources."""
        await self.close()

    async def _rate_limited_get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make a rate-limited GET request with exponential backoff.

        Args:
            path: API endpoint path.
            params: Query parameters.

        Returns:
            HTTP response from the API.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

            response = await self._get(path, params=params)
            self._last_request_time = time.monotonic()

        # Exponential backoff on rate limit errors
        for attempt in range(self.MAX_RETRIES):
            if response.status_code not in (429, 503):
                break

            retry_after = response.headers.get("Retry-After")
            wait_time = int(retry_after) if retry_after else (2**attempt)

            await asyncio.sleep(wait_time)

            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_request_time
                if elapsed < self.RATE_LIMIT_DELAY:
                    await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

                response = await self._get(path, params=params)
                self._last_request_time = time.monotonic()

        return response

    async def search_proteins(
        self,
        query: str,
        species: int | None = None,
        limit: int = 10,
        cursor: str | None = None,
    ) -> PaginationEnvelope[InteractionSearchCandidate] | ErrorEnvelope:
        """Fuzzy search for proteins by name/symbol (Phase 1 of Fuzzy-to-Fact).

        Args:
            query: Protein name, gene symbol, or identifier.
            species: NCBI Taxonomy ID (default: client's species).
            limit: Maximum results to return (1-100).
            cursor: Opaque cursor for pagination.

        Returns:
            PaginationEnvelope with InteractionSearchCandidate items, or ErrorEnvelope.
        """
        if len(query.strip()) < 2:
            return ErrorEnvelope.ambiguous_query(query, 0)

        limit = max(1, min(100, limit))
        species = species or self.species

        # Decode cursor for offset
        offset = 0
        if cursor:
            try:
                cursor_data = json.loads(base64.b64decode(cursor).decode())
                offset = cursor_data.get("offset", 0)
            except (ValueError, json.JSONDecodeError):
                offset = 0

        try:
            # STRING /resolve endpoint for identifier resolution
            params = {
                "identifiers": query,
                "species": species,
                "format": "json",
            }
            response = await self._rate_limited_get("/json/resolve", params)

            if response.status_code == 429:
                return ErrorEnvelope.rate_limited()
            if response.status_code >= 500:
                return ErrorEnvelope.upstream_error(response.status_code)
            if response.status_code != 200:
                return ErrorEnvelope.upstream_error(response.status_code, response.text)

            data = response.json()

            if not data:
                return PaginationEnvelope.create(
                    items=[],
                    cursor=None,
                    total_count=0,
                    page_size=limit,
                )

            # Check for ambiguous results
            if len(data) > self.AMBIGUOUS_THRESHOLD and len(query.strip()) < 3:
                return ErrorEnvelope.ambiguous_query(query, len(data))

            # Convert to InteractionSearchCandidate models
            candidates = []
            for i, item in enumerate(data):
                string_id = item.get("stringId", "")
                if not string_id:
                    continue

                # Calculate relevance score based on position and query match
                query_match = item.get("queryItem", "").lower()
                preferred_name = item.get("preferredName", "").lower()
                exact_match = query.lower() in (query_match, preferred_name)
                base_score = 1.0 if exact_match else 0.8
                score = max(0.1, base_score - (i * 0.05))

                candidate = InteractionSearchCandidate(
                    id=f"STRING:{string_id}",
                    preferred_name=item.get("preferredName", ""),
                    annotation=item.get("annotation"),
                    taxon_id=item.get("ncbiTaxonId", species),
                    score=round(score, 2),
                )
                candidates.append(candidate)

            # Apply pagination
            total_count = len(candidates)
            page_start = offset
            page_end = offset + limit
            page_items = candidates[page_start:page_end]

            # Create next cursor
            next_cursor = None
            if page_end < total_count:
                cursor_data = {"offset": page_end}
                next_cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

            return PaginationEnvelope.create(
                items=page_items,
                cursor=next_cursor,
                total_count=total_count,
                page_size=limit,
            )

        except httpx.TimeoutException:
            return ErrorEnvelope.upstream_error(504, "Request timeout")
        except httpx.RequestError as e:
            return ErrorEnvelope.upstream_error(502, str(e))

    async def get_interactions(
        self,
        string_id: str,
        required_score: int | None = None,
        limit: int = 10,
    ) -> InteractionNetwork | ErrorEnvelope:
        """Get protein-protein interactions by STRING CURIE (Phase 2 of Fuzzy-to-Fact).

        Note: STRING API uses 0-1000 scale for filtering (required_score parameter),
        but returns confidence scores normalized to 0-1 range in the response.

        Args:
            string_id: STRING CURIE in format 'STRING:<taxid>.ENSP<id>'.
            required_score: Minimum combined score threshold (0-1000, default 400).
                           Used to filter interactions; higher = more confident.
            limit: Maximum interactions to return (enforced client-side).

        Returns:
            InteractionNetwork with interactions (scores normalized 0-1), or ErrorEnvelope.
        """
        # Validate CURIE format
        if not STRING_CURIE_PATTERN.match(string_id):
            return self._unresolved_entity_error(string_id)

        # Extract protein ID from CURIE
        protein_id = string_id.replace("STRING:", "")
        required_score = required_score or self.DEFAULT_SCORE_THRESHOLD

        try:
            # Get interactions
            params = {
                "identifiers": protein_id,
                "species": self.species,
                "required_score": required_score,
                "limit": limit,
                "format": "json",
            }
            response = await self._rate_limited_get("/json/network", params)

            if response.status_code == 429:
                return ErrorEnvelope.rate_limited()
            if response.status_code >= 500:
                return ErrorEnvelope.upstream_error(response.status_code)
            if response.status_code != 200:
                return ErrorEnvelope.upstream_error(response.status_code, response.text)

            data = response.json()

            if not data:
                return self._entity_not_found_error(string_id)

            # Parse interactions
            interactions = []
            preferred_name = ""
            annotation = None
            taxon_id = self.species

            for item in data:
                string_id_a = item.get("stringId_A", "")
                string_id_b = item.get("stringId_B", "")

                # Extract query protein info from first result
                if not preferred_name:
                    if string_id_a == protein_id:
                        preferred_name = item.get("preferredName_A", "")
                    elif string_id_b == protein_id:
                        preferred_name = item.get("preferredName_B", "")

                # Parse taxon_id (API returns it as string)
                raw_taxon = item.get("ncbiTaxonId", self.species)
                taxon_id = int(raw_taxon) if isinstance(raw_taxon, str) else raw_taxon

                interaction = Interaction(
                    string_id_a=string_id_a,
                    string_id_b=string_id_b,
                    preferred_name_a=item.get("preferredName_A", ""),
                    preferred_name_b=item.get("preferredName_B", ""),
                    taxon_id=taxon_id,
                    score=float(item.get("score", 0)),  # STRING API returns 0-1 scale
                    evidence=EvidenceScores(
                        nscore=float(item.get("nscore", 0)),
                        fscore=float(item.get("fscore", 0)),
                        pscore=float(item.get("pscore", 0)),
                        ascore=float(item.get("ascore", 0)),
                        escore=float(item.get("escore", 0)),
                        dscore=float(item.get("dscore", 0)),
                        tscore=float(item.get("tscore", 0)),
                    ),
                )
                interactions.append(interaction)

            # Client-side truncation (NFR-003): STRING API ignores limit parameter
            # Truncate to requested limit to prevent token exhaustion
            if len(interactions) > limit:
                interactions = interactions[:limit]

            # Build network image URL
            network_image_url = self._build_network_image_url(protein_id, taxon_id, limit)

            # Build cross-references (would need additional API call for full refs)
            cross_refs = self._build_cross_references(protein_id)

            return InteractionNetwork(
                id=string_id,
                preferred_name=preferred_name,
                annotation=annotation,
                taxon_id=taxon_id,
                interaction_count=len(interactions),
                interactions=interactions,
                network_image_url=network_image_url,
                cross_references=cross_refs,
            )

        except httpx.TimeoutException:
            return ErrorEnvelope.upstream_error(504, "Request timeout")
        except httpx.RequestError as e:
            return ErrorEnvelope.upstream_error(502, str(e))

    def get_network_image_url(
        self,
        identifiers: str | list[str],
        species: int | None = None,
        add_nodes: int = 10,
        network_flavor: str = "confidence",
    ) -> str:
        """Generate a STRING network visualization URL.

        Args:
            identifiers: Gene symbol(s) or STRING ID(s).
            species: NCBI Taxonomy ID.
            add_nodes: Number of additional nodes to include.
            network_flavor: Visual style ('confidence', 'evidence', 'actions').

        Returns:
            URL string for the network image.
        """
        species = species or self.species

        if isinstance(identifiers, list):
            identifiers = "%0d".join(identifiers)

        return (
            f"{self.STRING_BASE_URL}/highres_image/network"
            f"?identifiers={identifiers}"
            f"&species={species}"
            f"&add_nodes={add_nodes}"
            f"&network_flavor={network_flavor}"
        )

    def _build_network_image_url(self, protein_id: str, taxon_id: int, add_nodes: int = 10) -> str:
        """Build the network visualization URL for a protein."""
        return (
            f"{self.STRING_BASE_URL}/highres_image/network"
            f"?identifiers={protein_id}"
            f"&species={taxon_id}"
            f"&add_nodes={add_nodes}"
        )

    def _build_cross_references(self, protein_id: str) -> InteractionCrossReferences | None:
        """Build cross-references from STRING protein ID.

        Note: STRING protein IDs are Ensembl Protein IDs (ENSP).
        Full cross-reference resolution would require additional API calls.
        """
        # Extract Ensembl protein ID - can derive gene ID pattern
        if ".ENSP" in protein_id:
            # STRING format is taxid.ENSP<id>
            # We can't directly derive gene ID without additional lookup
            return InteractionCrossReferences(
                ensembl_gene=None,
                uniprot=None,
                hgnc=None,
            )
        return None

    def _unresolved_entity_error(self, invalid_input: str) -> ErrorEnvelope:
        """Create UNRESOLVED_ENTITY error for STRING."""
        return ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=f"The input '{invalid_input}' is not a valid STRING CURIE.",
                recovery_hint="Call search_proteins to resolve the identifier first. Expected format: STRING:<taxid>.ENSP<id>",
                invalid_input=invalid_input,
            )
        )

    def _entity_not_found_error(self, string_id: str) -> ErrorEnvelope:
        """Create ENTITY_NOT_FOUND error for STRING."""
        return ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message=f"No interactions found for STRING ID '{string_id}'.",
                recovery_hint="Verify the STRING ID format or try lowering the required_score threshold.",
                invalid_input=string_id,
            )
        )
