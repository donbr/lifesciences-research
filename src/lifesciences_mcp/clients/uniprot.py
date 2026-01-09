"""UniProt REST API client implementing the Fuzzy-to-Fact protocol.

This module provides the UniProtClient for querying the UniProt protein
database for protein search and cross-references.

Status: FROZEN - Do not modify during parallel implementation.
"""

import asyncio
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
from lifesciences_mcp.models.cross_references import CrossReferences
from lifesciences_mcp.models.protein import (
    Protein,
    ProteinSearchCandidate,
)


class UniProtClient(LifeSciencesClient):
    """UniProt REST API client implementing the Fuzzy-to-Fact protocol.

    Rate limited to 10 requests/second (conservative estimate from R4 research).
    Uses exponential backoff on 429 errors with thundering herd prevention.

    Can be used as a context manager:
        async with UniProtClient() as client:
            result = await client.search_proteins("p53")
    """

    # Constants extracted per T018 (code review lesson from HGNC)
    UNIPROT_BASE_URL = "https://rest.uniprot.org"
    RATE_LIMIT_DELAY = 0.1  # 10 req/s = 100ms between requests (from R4 research)
    AMBIGUOUS_THRESHOLD = 100  # Max results before query is considered ambiguous
    SCORE_DECAY = 0.05  # Score reduction per position in results
    MAX_RETRIES = 3  # Maximum retry attempts on rate limiting
    MAX_PAGE_SIZE = 500  # UniProt API limit (from R3 research)
    DEFAULT_SEARCH_FIELDS = "accession,id,gene_names,organism_name,protein_name"

    def __init__(self) -> None:
        """Initialize the UniProt client."""
        super().__init__(base_url=self.UNIPROT_BASE_URL)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "UniProtClient":
        """Enter context manager (T017 - context manager support)."""
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """Exit context manager and cleanup resources (T017)."""
        await self.close()

    async def _rate_limited_get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a rate-limited GET request with exponential backoff.

        Implements T015 (rate limiting), T016 (thundering herd prevention),
        and applies HGNC code review lessons.

        Args:
            path: API endpoint path.
            **kwargs: Additional request parameters.

        Returns:
            HTTP response from the API.
        """
        # Initial request with rate limiting
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

            response = await self._get(path, **kwargs)
            self._last_request_time = asyncio.get_event_loop().time()

        # Exponential backoff on rate limit errors (T015)
        for attempt in range(self.MAX_RETRIES):
            if response.status_code not in (429, 403):
                break

            # Calculate backoff time (2^attempt per HGNC review lesson)
            retry_after = response.headers.get("Retry-After")
            wait_time = int(retry_after) if retry_after else (2**attempt)

            # Sleep OUTSIDE lock to allow other requests to proceed
            await asyncio.sleep(wait_time)

            # Retry with lock - T016: re-check time boundary to prevent thundering herd
            async with self._lock:
                # CRITICAL: Re-check timing after acquiring lock
                # Other requests may have completed during our backoff sleep
                now = asyncio.get_event_loop().time()
                elapsed = now - self._last_request_time
                if elapsed < self.RATE_LIMIT_DELAY:
                    await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

                response = await self._get(path, **kwargs)
                self._last_request_time = asyncio.get_event_loop().time()

        return response

    def _map_cross_references(self, uniprot_refs: list[dict[str, Any]]) -> CrossReferences:
        """Map UniProt cross-references to 22-key registry (T020).

        Implements field mapping from R5 research findings.

        Args:
            uniprot_refs: List of cross-reference dicts from UniProt API.

        Returns:
            CrossReferences model with omit-if-null pattern per Constitution III.
        """
        # Extract single-value references
        hgnc = next((r["id"] for r in uniprot_refs if r["database"] == "HGNC"), None)
        entrez = next((r["id"] for r in uniprot_refs if r["database"] == "GeneID"), None)
        string = next((r["id"] for r in uniprot_refs if r["database"] == "STRING"), None)
        biogrid = next((r["id"] for r in uniprot_refs if r["database"] == "BioGRID"), None)

        # Extract multi-value references (arrays)
        pdb_ids = [r["id"] for r in uniprot_refs if r["database"] == "PDB"]
        omim_ids = [r["id"] for r in uniprot_refs if r["database"] == "MIM"]
        orphanet_ids = [r["id"] for r in uniprot_refs if r["database"] == "Orphanet"]
        refseq_ids = [r["id"] for r in uniprot_refs if r["database"] == "RefSeq"]

        # Extract Ensembl references (transcript IDs for now, gene extraction is future enhancement)
        ensembl_transcripts = [r["id"] for r in uniprot_refs if r["database"] == "Ensembl"]

        # Extract KEGG reference
        kegg = next((r["id"] for r in uniprot_refs if r["database"] == "KEGG"), None)

        # Build CrossReferences with omit-if-null pattern (Constitution III)
        refs_dict = {}
        if hgnc:
            refs_dict["hgnc"] = hgnc
        if entrez:
            refs_dict["entrez"] = entrez
        if ensembl_transcripts:
            # ensembl_transcript is list[str] in CrossReferences model
            refs_dict["ensembl_transcript"] = ensembl_transcripts
        if refseq_ids:
            # refseq is list[str] in CrossReferences model
            refs_dict["refseq"] = refseq_ids
        if pdb_ids:
            refs_dict["pdb"] = pdb_ids[:10]  # Limit to first 10 structures
        if kegg:
            refs_dict["kegg"] = kegg
        if omim_ids:
            refs_dict["omim"] = ",".join(omim_ids)
        if orphanet_ids:
            refs_dict["orphanet"] = ",".join(orphanet_ids)
        if string:
            refs_dict["string"] = string
        if biogrid:
            refs_dict["biogrid"] = biogrid

        return CrossReferences(**refs_dict)

    async def search_proteins(
        self,
        query: str,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope[ProteinSearchCandidate] | ErrorEnvelope:
        """Fuzzy search for proteins (Phase 1 of Fuzzy-to-Fact).

        Implements T025-T032 for User Story 1.

        Args:
            query: Search term (protein name, accession, gene, organism).
            slim: If true, return minimal fields (~20 tokens per entity).
            cursor: Opaque cursor for pagination (from UniProt response).
            page_size: Results per page (1-500, default 50).

        Returns:
            PaginationEnvelope with ProteinSearchCandidate items, or ErrorEnvelope.
        """
        # T026: Query validation - minimum 2 characters
        if len(query.strip()) < 2:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message=f"Query '{query}' is too short. Provide at least 2 characters for meaningful search.",
                    recovery_hint="Try a more specific query like 'p53', 'insulin', or 'BRCA1'",
                    invalid_input=query,
                )
            )

        # Clamp page_size to valid range (1-500 per R3 research)
        page_size = max(1, min(self.MAX_PAGE_SIZE, page_size))

        try:
            # T025: Construct search query
            params = {
                "query": query,
                "fields": self.DEFAULT_SEARCH_FIELDS,
                "size": str(page_size),
            }

            # Add cursor for pagination if provided
            if cursor:
                params["cursor"] = cursor

            # Call UniProt search API with rate limiting
            response = await self._rate_limited_get("/uniprotkb/search", params=params)

            # T031: Error handling
            if response.status_code == 429:
                return ErrorEnvelope.rate_limited()
            if response.status_code >= 500:
                return ErrorEnvelope.upstream_error(response.status_code)
            if response.status_code == 400:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.AMBIGUOUS_QUERY,
                        message=f"Invalid search query: {query}",
                        recovery_hint="Check your query syntax and try again",
                        invalid_input=query,
                    )
                )
            if response.status_code != 200:
                return ErrorEnvelope.upstream_error(response.status_code, "Unexpected response")

            data = response.json()
            results = data.get("results", [])

            # T027: Parse results to ProteinSearchCandidate
            candidates = []
            for i, result in enumerate(results):
                # Extract protein details
                accession = result.get("primaryAccession", "")
                uniprot_id = f"UniProtKB:{accession}"

                # Get protein name (from proteinDescription)
                protein_name = "Unknown"
                if "proteinDescription" in result:
                    desc = result["proteinDescription"]
                    if "recommendedName" in desc:
                        protein_name = desc["recommendedName"]["fullName"]["value"]
                    elif desc.get("submissionNames"):
                        protein_name = desc["submissionNames"][0]["fullName"]["value"]

                # Get organism
                organism = result.get("organism", {}).get("scientificName", "Unknown")

                # Extract gene names
                gene_names = []
                for gene in result.get("genes", []):
                    if "geneName" in gene:
                        gene_names.append(gene["geneName"]["value"])

                # T028: Calculate relevance score
                # UniProt doesn't provide explicit scores, so we calculate based on position
                # First result gets highest score, with decay per position
                score = max(0.1, 1.0 - (i * self.SCORE_DECAY))

                candidate = ProteinSearchCandidate(
                    id=uniprot_id,
                    name=protein_name,
                    organism=organism,
                    gene_names=gene_names if gene_names else None,
                    score=round(score, 2),
                )
                candidates.append(candidate)

            # T029: Extract pagination cursor from response
            next_cursor = data.get("cursor", None)

            # Return paginated response
            return PaginationEnvelope.create(
                items=candidates,
                cursor=next_cursor,
                total_count=None,  # UniProt doesn't provide total count
                page_size=page_size,
            )

        except httpx.TimeoutException:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message="Request to UniProt API timed out",
                    recovery_hint="Try again with a simpler query or increase timeout",
                )
            )
        except httpx.RequestError as e:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Network error: {e!s}",
                    recovery_hint="Check your network connection and try again",
                )
            )
        except (ValueError, KeyError) as e:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Failed to parse UniProt API response: {e!s}",
                    recovery_hint="The UniProt API may have changed. Please report this issue.",
                )
            )

    async def get_protein(self, uniprot_id: str, slim: bool = False) -> Protein | ErrorEnvelope:
        """Get complete protein record by UniProt CURIE (Phase 2 of Fuzzy-to-Fact).

        Implements User Story 2: Strict Protein Lookup (T037-T040).

        Args:
            uniprot_id: UniProt CURIE in format 'UniProtKB:XXXXXX' (e.g., 'UniProtKB:P04637').
            slim: If true, return minimal fields (id, name, organism only).

        Returns:
            Protein record with cross_references, or ErrorEnvelope.
        """
        # T037: Validate CURIE format (FR-003, FR-004)
        # Use regex from R6 research: ^UniProtKB:[A-Z][A-Z0-9]{5,9}$
        curie_pattern = re.compile(r"^UniProtKB:[A-Z][A-Z0-9]{5,9}$")
        if not curie_pattern.match(uniprot_id):
            # Return UNRESOLVED_ENTITY for invalid CURIE format (FR-004, FR-009)
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UNRESOLVED_ENTITY,
                    message=f"Invalid UniProt CURIE format: '{uniprot_id}'",
                    recovery_hint=(
                        "Use search_proteins to find valid UniProt IDs, then call "
                        "get_protein with the resolved CURIE (e.g., 'UniProtKB:P04637')"
                    ),
                    invalid_input=uniprot_id,
                )
            )

        # Extract accession from CURIE (remove 'UniProtKB:' prefix)
        accession = uniprot_id.split(":")[1]

        # T038: Fetch protein from UniProt API (R1: GET /uniprotkb/{accession}.json)
        try:
            response = await self._rate_limited_get(f"/uniprotkb/{accession}.json")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # T043: Handle 404 Not Found (FR-009)
            if e.response.status_code == 404:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.ENTITY_NOT_FOUND,
                        message=f"Protein '{uniprot_id}' not found in UniProt",
                        recovery_hint=(
                            f"The protein {uniprot_id} does not exist in UniProt. "
                            "Verify the accession or search for the protein by name using search_proteins."
                        ),
                        invalid_input=uniprot_id,
                    )
                )
            # T043: Handle 400 Bad Request (invalid accession format from API)
            elif e.response.status_code == 400:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.UNRESOLVED_ENTITY,
                        message=f"Invalid accession format: '{accession}'",
                        recovery_hint=(
                            "Use search_proteins to find valid UniProt IDs, then call "
                            "get_protein with the resolved CURIE"
                        ),
                        invalid_input=uniprot_id,
                    )
                )
            # Handle other HTTP errors
            else:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.UPSTREAM_ERROR,
                        message=f"UniProt API error: {e.response.status_code}",
                        recovery_hint="UniProt API is currently unavailable. Try again in a few moments.",
                        invalid_input=uniprot_id,
                    )
                )
        except Exception as e:
            # Handle connection errors, timeouts, etc.
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Failed to fetch protein: {e!s}",
                    recovery_hint="Check your network connection and try again.",
                    invalid_input=uniprot_id,
                )
            )

        # T039: Parse result to Protein model with cross_references
        data = response.json()

        # Extract basic protein information
        protein_description = data.get("proteinDescription", {})
        recommended_name = protein_description.get("recommendedName", {})
        full_name = recommended_name.get("fullName", {}).get("value", "Unknown")

        # Extract gene names
        genes = data.get("genes", [])
        gene_names = None
        if genes:
            gene_names = []
            for gene in genes:
                if "geneName" in gene:
                    gene_names.append(gene["geneName"]["value"])

        # Extract organism information
        organism = data.get("organism", {})
        organism_name = organism.get("scientificName", "Unknown")
        organism_id = organism.get("taxonId")

        # Extract sequence information
        sequence = data.get("sequence", {})
        sequence_length = sequence.get("length")

        # Extract function (comments section)
        function_text = None
        comments = data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    function_text = texts[0].get("value")
                    break

        # T039: Extract cross-references using _map_cross_references helper (T020)
        uniprot_refs = data.get("uniProtKBCrossReferences", [])
        cross_references = self._map_cross_references(uniprot_refs)

        # T040: Build Protein model (slim mode returns minimal fields)
        protein_dict = {
            "id": uniprot_id,
            "accession": accession,
            "name": full_name,
            "organism": organism_name,
        }

        # Add optional fields only if not in slim mode
        if not slim:
            protein_dict.update(
                {
                    "full_name": full_name,
                    "gene_names": gene_names,
                    "organism_id": organism_id,
                    "function": function_text,
                    "sequence_length": sequence_length,
                    "cross_references": cross_references,
                }
            )

        # Create and return Protein model
        return Protein(**protein_dict)
