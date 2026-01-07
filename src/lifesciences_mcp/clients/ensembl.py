"""Ensembl REST API client implementing the Fuzzy-to-Fact protocol.

This module provides the EnsemblClient for querying Ensembl's REST API
for gene and transcript data with cross-references.

Key features:
- Async httpx client with connection pooling
- Rate limiting at 15 req/s (Ensembl limit)
- Exponential backoff with Retry-After header support
- Fuzzy-to-Fact protocol enforcement

See specs/008-ensembl-mcp-server/research.md for API research.
"""

import asyncio
import base64
import json
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.ensembl import (
    ENSEMBL_GENE_PATTERN,
    ENSEMBL_TRANSCRIPT_PATTERN,
    EnsemblCrossReferences,
    EnsemblGene,
    EnsemblTranscript,
    GeneSearchCandidate,
)
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    PaginationEnvelope,
)

# Species aliases per research.md R7
SPECIES_ALIASES = {
    "human": "homo_sapiens",
    "mouse": "mus_musculus",
    "rat": "rattus_norvegicus",
    "zebrafish": "danio_rerio",
    "drosophila": "drosophila_melanogaster",
    "c. elegans": "caenorhabditis_elegans",
    "c.elegans": "caenorhabditis_elegans",
    "worm": "caenorhabditis_elegans",
    "fly": "drosophila_melanogaster",
    "yeast": "saccharomyces_cerevisiae",
    "chicken": "gallus_gallus",
    "pig": "sus_scrofa",
    "dog": "canis_familiaris",
    "cow": "bos_taurus",
}


class EnsemblClient(LifeSciencesClient):
    """Ensembl REST API client implementing the Fuzzy-to-Fact protocol.

    Rate limited to 15 requests/second per Ensembl documentation.
    Uses exponential backoff on 429 errors with Retry-After header support.

    Can be used as a context manager:
        async with EnsemblClient() as client:
            result = await client.search_genes("BRCA1")
    """

    ENSEMBL_BASE_URL = "https://rest.ensembl.org"
    RATE_LIMIT_DELAY = 1.0 / 15  # 15 req/s = 66.67ms between requests
    MAX_RETRIES = 3  # Maximum retry attempts on rate limiting
    SCORE_DECAY = 0.05  # Score reduction per position in results

    def __init__(self) -> None:
        """Initialize the Ensembl client."""
        super().__init__(base_url=self.ENSEMBL_BASE_URL)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "EnsemblClient":
        """Enter context manager."""
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """Exit context manager and cleanup resources."""
        await self.close()

    def _normalize_species(self, species: str) -> str:
        """Normalize species name to Ensembl format.

        Args:
            species: Species name or alias.

        Returns:
            Normalized Ensembl species name (lowercase with underscores).
        """
        normalized = species.lower().strip().replace(" ", "_")
        return SPECIES_ALIASES.get(normalized, normalized)

    async def _rate_limited_get(self, path: str, params: dict | None = None) -> httpx.Response:
        """Make a rate-limited GET request with exponential backoff.

        Implements proper rate limiting with the request inside the lock
        to prevent race conditions.

        Args:
            path: API endpoint path.
            params: Optional query parameters.

        Returns:
            HTTP response from the API.
        """
        headers = {"Content-Type": "application/json"}

        # Initial request with rate limiting
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

            response = await self._get(path, params=params, headers=headers)
            self._last_request_time = asyncio.get_event_loop().time()

        # Exponential backoff on rate limit errors
        for attempt in range(self.MAX_RETRIES):
            if response.status_code not in (429, 503):
                break

            # Calculate backoff time
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    wait_time = float(retry_after)
                except ValueError:
                    wait_time = 2**attempt
            else:
                wait_time = 2**attempt

            # Sleep OUTSIDE lock to allow other requests to proceed
            await asyncio.sleep(wait_time)

            # Retry with lock - re-check time boundary to prevent thundering herd
            async with self._lock:
                # CRITICAL: Re-check timing after acquiring lock
                now = asyncio.get_event_loop().time()
                elapsed = now - self._last_request_time
                if elapsed < self.RATE_LIMIT_DELAY:
                    await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

                response = await self._get(path, params=params, headers=headers)
                self._last_request_time = asyncio.get_event_loop().time()

        return response

    def _create_error_envelope(
        self,
        code: ErrorCode,
        message: str,
        recovery_hint: str,
        invalid_input: str | None = None,
    ) -> ErrorEnvelope:
        """Create a standardized error envelope.

        Args:
            code: Error code from registry.
            message: Human-readable message.
            recovery_hint: Agent-actionable guidance.
            invalid_input: Optional input that caused the error.

        Returns:
            ErrorEnvelope with consistent format.
        """
        return ErrorEnvelope(
            error=ErrorDetail(
                code=code,
                message=message,
                recovery_hint=recovery_hint,
                invalid_input=invalid_input,
            )
        )

    def _map_cross_references(self, xrefs: list[dict]) -> EnsemblCrossReferences:
        """Map Ensembl xrefs response to CrossReferences model.

        Per ADR-001: omit keys with no value (never null/empty).

        Args:
            xrefs: List of cross-reference objects from Ensembl API.

        Returns:
            EnsemblCrossReferences with populated fields.
        """
        refs: dict[str, Any] = {}

        for xref in xrefs:
            dbname = xref.get("dbname", "")
            primary_id = xref.get("primary_id", "")

            if not primary_id:
                continue

            if dbname == "HGNC":
                refs["hgnc"] = f"HGNC:{primary_id}"
            elif dbname in ("Uniprot/SWISSPROT", "Uniprot/SPTREMBL"):
                refs.setdefault("uniprot", []).append(primary_id)
            elif dbname == "EntrezGene":
                refs["entrez"] = primary_id
            elif dbname.startswith("RefSeq"):
                refs.setdefault("refseq", []).append(primary_id)
            elif dbname in ("MIM_GENE", "MIM_MORBID"):
                refs["omim"] = primary_id
            elif dbname == "PDB":
                refs.setdefault("pdb", []).append(primary_id)
            elif dbname.startswith("KEGG"):
                refs["kegg"] = primary_id
            elif dbname == "ChEMBL":
                refs["chembl"] = primary_id

        return EnsemblCrossReferences(**refs)

    async def search_genes(
        self,
        query: str,
        species: str = "homo_sapiens",
        page_size: int = 50,
        cursor: str | None = None,
        slim: bool = False,
    ) -> PaginationEnvelope[GeneSearchCandidate] | ErrorEnvelope:
        """Fuzzy search for genes (Phase 1 of Fuzzy-to-Fact).

        Uses Ensembl /xrefs/symbol/{species}/{symbol} endpoint.

        Args:
            query: Search term (gene symbol or name).
            species: Species name or alias (default: homo_sapiens).
            page_size: Results per page (1-100).
            cursor: Opaque cursor for pagination.
            slim: If true, minimal fields only (not used for search, included for API consistency).

        Returns:
            PaginationEnvelope with GeneSearchCandidate items, or ErrorEnvelope.
        """
        # Validate query length
        query = query.strip()
        if len(query) < 2:
            return self._create_error_envelope(
                code=ErrorCode.AMBIGUOUS_QUERY,
                message=f"Query '{query}' is too short (minimum 2 characters).",
                recovery_hint="Provide at least 2 characters or refine your search term.",
                invalid_input=query,
            )

        # Clamp page_size to valid range
        page_size = max(1, min(100, page_size))

        # Normalize species
        normalized_species = self._normalize_species(species)

        try:
            # Decode cursor for offset if provided
            offset = 0
            if cursor:
                try:
                    cursor_data = json.loads(base64.b64decode(cursor).decode())
                    offset = cursor_data.get("offset", 0)
                except (ValueError, json.JSONDecodeError):
                    offset = 0

            # Call Ensembl xrefs/symbol endpoint
            response = await self._rate_limited_get(f"/xrefs/symbol/{normalized_species}/{query}")

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                hint = "Wait for the time specified in Retry-After header before retrying."
                if retry_after:
                    hint = f"Wait {retry_after} seconds before retrying."
                return self._create_error_envelope(
                    code=ErrorCode.RATE_LIMITED,
                    message="Exceeded Ensembl rate limit (15 requests/second).",
                    recovery_hint=hint,
                )

            if response.status_code >= 500:
                return self._create_error_envelope(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Ensembl API returned error {response.status_code}.",
                    recovery_hint="Ensembl service may be temporarily unavailable. Retry after a few seconds.",
                )

            if response.status_code == 400:
                # Symbol not found - return empty results
                return PaginationEnvelope.create(
                    items=[],
                    cursor=None,
                    total_count=0,
                    page_size=page_size,
                )

            if response.status_code != 200:
                return self._create_error_envelope(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Ensembl API returned error {response.status_code}.",
                    recovery_hint="Retry after a short delay.",
                )

            data = response.json()

            # Filter to only genes
            gene_results = [item for item in data if item.get("type") == "gene"]

            # For each gene ID, we need to fetch details
            candidates = []
            for i, item in enumerate(gene_results):
                gene_id = item.get("id", "")
                if not ENSEMBL_GENE_PATTERN.match(gene_id):
                    continue

                # Calculate relevance score based on position
                score = max(0.1, 1.0 - (i * self.SCORE_DECAY))

                # We need to fetch gene details to get symbol and name
                gene_details = await self._get_gene_details(gene_id)
                if gene_details:
                    candidate = GeneSearchCandidate(
                        id=gene_id,
                        symbol=gene_details.get("display_name", ""),
                        name=gene_details.get("description", ""),
                        biotype=gene_details.get("biotype", ""),
                        species=gene_details.get("species", normalized_species),
                        score=round(score, 2),
                    )
                    candidates.append(candidate)

            # Apply client-side pagination
            total_count = len(candidates)
            page_start = offset
            page_end = offset + page_size
            page_items = candidates[page_start:page_end]

            # Create next cursor if more results available
            next_cursor = None
            if page_end < total_count:
                cursor_data = {"offset": page_end}
                next_cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

            return PaginationEnvelope.create(
                items=page_items,
                cursor=next_cursor,
                total_count=total_count,
                page_size=page_size,
            )

        except httpx.TimeoutException:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message="Request to Ensembl API timed out.",
                recovery_hint="Retry after a short delay.",
            )
        except httpx.RequestError as e:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"Network error: {e!s}",
                recovery_hint="Check network connectivity and retry.",
            )

    async def _get_gene_details(self, gene_id: str) -> dict | None:
        """Fetch basic gene details from lookup endpoint.

        Args:
            gene_id: Ensembl Gene ID.

        Returns:
            Gene details dict or None if not found.
        """
        try:
            response = await self._rate_limited_get(f"/lookup/id/{gene_id}")
            if response.status_code == 200:
                return response.json()
        except (httpx.TimeoutException, httpx.RequestError):
            pass
        return None

    async def get_gene(self, ensembl_id: str, slim: bool = False) -> EnsemblGene | ErrorEnvelope:
        """Get complete gene record by Ensembl Gene ID (Phase 2 of Fuzzy-to-Fact).

        Args:
            ensembl_id: Ensembl Gene ID in format 'ENSG + 11 digits'.
            slim: If true, omit cross_references to reduce token count.

        Returns:
            EnsemblGene record with cross_references, or ErrorEnvelope.
        """
        # Strip version if present (ENSG00000141510.12 -> ENSG00000141510)
        ensembl_id = ensembl_id.split(".")[0]

        # Validate Ensembl Gene ID format (Fuzzy-to-Fact enforcement)
        if not ENSEMBL_GENE_PATTERN.match(ensembl_id):
            return self._create_error_envelope(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=f"Invalid Ensembl Gene ID format: '{ensembl_id}'.",
                recovery_hint="Use search_genes to find valid Ensembl Gene IDs. Format: ENSG + 11 digits (e.g., ENSG00000141510).",
                invalid_input=ensembl_id,
            )

        try:
            # Fetch gene details with transcript expansion
            response = await self._rate_limited_get(
                f"/lookup/id/{ensembl_id}",
                params={"expand": "1"},
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                hint = "Wait for the time specified in Retry-After header before retrying."
                if retry_after:
                    hint = f"Wait {retry_after} seconds before retrying."
                return self._create_error_envelope(
                    code=ErrorCode.RATE_LIMITED,
                    message="Exceeded Ensembl rate limit (15 requests/second).",
                    recovery_hint=hint,
                )

            if response.status_code >= 500:
                return self._create_error_envelope(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Ensembl API returned error {response.status_code}.",
                    recovery_hint="Ensembl service may be temporarily unavailable. Retry after a few seconds.",
                )

            if response.status_code == 400:
                # Ensembl returns 400 for "not found"
                return self._create_error_envelope(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"Gene '{ensembl_id}' not found in Ensembl.",
                    recovery_hint="Verify the ID or use search_genes to find valid gene identifiers.",
                    invalid_input=ensembl_id,
                )

            if response.status_code != 200:
                return self._create_error_envelope(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Ensembl API returned error {response.status_code}.",
                    recovery_hint="Retry after a short delay.",
                )

            data = response.json()

            # Extract transcript IDs
            transcripts = None
            if "Transcript" in data:
                transcripts = [t["id"] for t in data["Transcript"] if "id" in t]

            # Fetch cross-references if not slim mode
            cross_refs = EnsemblCrossReferences()
            if not slim:
                xrefs_response = await self._rate_limited_get(f"/xrefs/id/{ensembl_id}")
                if xrefs_response.status_code == 200:
                    xrefs_data = xrefs_response.json()
                    cross_refs = self._map_cross_references(xrefs_data)

            # Build EnsemblGene model
            gene = EnsemblGene(
                id=ensembl_id,
                symbol=data.get("display_name", ""),
                name=data.get("description", ""),
                biotype=data.get("biotype", ""),
                species=data.get("species", ""),
                assembly_name=data.get("assembly_name", ""),
                chromosome=data.get("seq_region_name", ""),
                start=data.get("start", 0),
                end=data.get("end", 0),
                strand=data.get("strand", 1),
                transcripts=transcripts,
                cross_references=cross_refs,
            )

            return gene

        except httpx.TimeoutException:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message="Request to Ensembl API timed out.",
                recovery_hint="Retry after a short delay.",
            )
        except httpx.RequestError as e:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"Network error: {e!s}",
                recovery_hint="Check network connectivity and retry.",
            )

    async def get_transcript(
        self, transcript_id: str, slim: bool = False
    ) -> EnsemblTranscript | ErrorEnvelope:
        """Get transcript record by Ensembl Transcript ID.

        Args:
            transcript_id: Ensembl Transcript ID in format 'ENST + 11 digits'.
            slim: If true, omit cross_references to reduce token count.

        Returns:
            EnsemblTranscript record, or ErrorEnvelope.
        """
        # Strip version if present (ENST00000269305.8 -> ENST00000269305)
        transcript_id = transcript_id.split(".")[0]

        # Check if user accidentally passed a gene ID
        if ENSEMBL_GENE_PATTERN.match(transcript_id):
            return self._create_error_envelope(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=f"'{transcript_id}' is a Gene ID, not a Transcript ID.",
                recovery_hint="Use get_gene to look up gene records. For transcripts, use ENST IDs from the gene's transcripts list.",
                invalid_input=transcript_id,
            )

        # Validate Ensembl Transcript ID format
        if not ENSEMBL_TRANSCRIPT_PATTERN.match(transcript_id):
            return self._create_error_envelope(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=f"Invalid Ensembl Transcript ID format: '{transcript_id}'.",
                recovery_hint="Use get_gene to retrieve transcript IDs from a gene record. Format: ENST + 11 digits (e.g., ENST00000269305).",
                invalid_input=transcript_id,
            )

        try:
            # Fetch transcript details
            response = await self._rate_limited_get(f"/lookup/id/{transcript_id}")

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                hint = "Wait for the time specified in Retry-After header before retrying."
                if retry_after:
                    hint = f"Wait {retry_after} seconds before retrying."
                return self._create_error_envelope(
                    code=ErrorCode.RATE_LIMITED,
                    message="Exceeded Ensembl rate limit (15 requests/second).",
                    recovery_hint=hint,
                )

            if response.status_code >= 500:
                return self._create_error_envelope(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Ensembl API returned error {response.status_code}.",
                    recovery_hint="Ensembl service may be temporarily unavailable. Retry after a few seconds.",
                )

            if response.status_code == 400:
                return self._create_error_envelope(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"Transcript '{transcript_id}' not found in Ensembl.",
                    recovery_hint="Verify the ID or use get_gene to find transcript IDs for a gene.",
                    invalid_input=transcript_id,
                )

            if response.status_code != 200:
                return self._create_error_envelope(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Ensembl API returned error {response.status_code}.",
                    recovery_hint="Retry after a short delay.",
                )

            data = response.json()

            # Get parent gene ID
            parent_gene = data.get("Parent", "")

            # Fetch cross-references if not slim mode
            cross_refs = EnsemblCrossReferences()
            if not slim:
                xrefs_response = await self._rate_limited_get(f"/xrefs/id/{transcript_id}")
                if xrefs_response.status_code == 200:
                    xrefs_data = xrefs_response.json()
                    cross_refs = self._map_cross_references(xrefs_data)
                    # Add parent gene to cross-refs
                    if parent_gene:
                        cross_refs.ensembl_gene = parent_gene

            # Build EnsemblTranscript model
            transcript = EnsemblTranscript(
                id=transcript_id,
                display_name=data.get("display_name", ""),
                biotype=data.get("biotype", ""),
                parent_gene=parent_gene,
                is_canonical=data.get("is_canonical", 0) == 1,
                species=data.get("species", ""),
                assembly_name=data.get("assembly_name", ""),
                chromosome=data.get("seq_region_name", ""),
                start=data.get("start", 0),
                end=data.get("end", 0),
                strand=data.get("strand", 1),
                cross_references=cross_refs,
            )

            return transcript

        except httpx.TimeoutException:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message="Request to Ensembl API timed out.",
                recovery_hint="Retry after a short delay.",
            )
        except httpx.RequestError as e:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"Network error: {e!s}",
                recovery_hint="Check network connectivity and retry.",
            )
