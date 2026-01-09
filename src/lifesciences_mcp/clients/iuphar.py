"""IUPHAR/GtoPdb API client for pharmacological data.

This module provides async client for the Guide to PHARMACOLOGY (GtoPdb) REST API.

GtoPdb is a community resource providing curated pharmacological data on:
- 12,000+ ligands (drugs, chemicals, peptides, antibodies)
- 3,000+ targets (receptors, enzymes, ion channels, transporters)
- 50,000+ ligand-target interactions

Rate limiting: Conservative 1 req/s for community resource sustainability.
"""

import asyncio
import base64
import json
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.envelopes import ErrorCode, ErrorDetail, ErrorEnvelope
from lifesciences_mcp.models.cross_references import CrossReferences
from lifesciences_mcp.models.pharmacology import HTML_TAG_PATTERN


class IUPHARClient(LifeSciencesClient):
    """Async client for IUPHAR/GtoPdb REST API.

    Implements the Fuzzy-to-Fact protocol for pharmacological data:
    - Ligand search and retrieval (drugs, chemicals, peptides)
    - Target search and retrieval (receptors, enzymes, ion channels)
    - Cross-reference mapping to 22-key Agentic Biolink schema

    Rate limiting: 1 req/s (conservative for community resource).
    """

    BASE_URL = "https://www.guidetopharmacology.org/services"
    RATE_LIMIT_DELAY = 1.0  # 1 request per second
    MAX_RETRIES = 3

    def __init__(self) -> None:
        """Initialize IUPHAR client with rate limiting."""
        super().__init__(base_url=self.BASE_URL, timeout=30.0)
        self._lock = asyncio.Lock()
        self._last_request_time = 0.0

    async def _rate_limited_get(self, path: str, retries: int = 0, **kwargs: Any) -> httpx.Response:
        """Make rate-limited GET request with exponential backoff.

        Implements:
        - 1 req/s rate limiting (FR-022)
        - Exponential backoff on errors (2^attempt seconds)
        - Thundering herd prevention (re-check time after lock acquire)
        """
        async with self._lock:
            # Thundering herd prevention: re-check elapsed time after acquiring lock
            loop = asyncio.get_event_loop()
            now = loop.time()
            elapsed = now - self._last_request_time

            if elapsed < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

            try:
                response = await self._get(path, **kwargs)
                self._last_request_time = loop.time()

                # Retry on 429 or 503 with exponential backoff
                if response.status_code in (429, 503) and retries < self.MAX_RETRIES:
                    backoff_delay = 2**retries
                    await asyncio.sleep(backoff_delay)
                    return await self._rate_limited_get(path, retries + 1, **kwargs)

                return response

            except (httpx.TimeoutException, httpx.ConnectError):
                # Retry on network errors with exponential backoff
                if retries < self.MAX_RETRIES:
                    backoff_delay = 2**retries
                    await asyncio.sleep(backoff_delay)
                    return await self._rate_limited_get(path, retries + 1, **kwargs)
                raise

    def _encode_cursor(self, offset: int) -> str:
        """Encode pagination cursor (base64 JSON)."""
        cursor_data = {"offset": offset}
        cursor_json = json.dumps(cursor_data)
        return base64.b64encode(cursor_json.encode()).decode()

    def _decode_cursor(self, cursor: str) -> int:
        """Decode pagination cursor to offset."""
        try:
            cursor_json = base64.b64decode(cursor).decode()
            cursor_data = json.loads(cursor_json)
            return cursor_data.get("offset", 0)
        except (ValueError, KeyError):
            return 0

    def _calculate_score(self, position: int) -> float:
        """Calculate position-based relevance score.

        Formula: 1.0 - (position * 0.05), minimum 0.1
        First result = 1.0, second = 0.95, ..., 18th+ = 0.1
        """
        score = 1.0 - (position * 0.05)
        return max(score, 0.1)

    def _map_ligand_cross_references(self, db_links: list[dict]) -> CrossReferences:
        r"""Map GtoPdb ligand database links to 22-key Agentic Biolink schema.

        Mappings:
        - ChEMBL Ligand -> chembl (strip "CHEMBL" prefix if present)
        - DrugBank Ligand -> drugbank (format: DB\d{5})
        - PubChem CID -> pubchem_compound (numeric)
        """
        refs_dict: dict[str, Any] = {}

        for link in db_links:
            database = link.get("database", "")
            accession = link.get("accession", "")

            if not accession:
                continue

            if database == "ChEMBL Ligand":
                # Strip "CHEMBL" prefix if present (e.g., "CHEMBL521" -> "521")
                refs_dict["chembl"] = accession.replace("CHEMBL", "")
            elif database == "DrugBank Ligand":
                refs_dict["drugbank"] = accession
            elif database == "PubChem CID":
                refs_dict["pubchem_compound"] = accession

        return CrossReferences(**refs_dict)

    def _map_target_cross_references(self, db_links: list[dict]) -> CrossReferences:
        """Map GtoPdb target database links to 22-key Agentic Biolink schema.

        Filters to human species only (multi-species data present).

        Mappings:
        - UniProtKB -> uniprot (list format per ADR-001)
        - Ensembl Gene -> ensembl_gene
        - Entrez Gene -> entrez
        - RefSeq Nucleotide -> refseq (list format)
        - ChEMBL Target -> chembl
        - OMIM -> omim
        - Orphanet -> orphanet
        """
        refs_dict: dict[str, Any] = {}
        uniprot_ids: list[str] = []
        refseq_ids: list[str] = []

        for link in db_links:
            species = link.get("species", "")
            if species != "Human":
                continue  # Filter to human only

            database = link.get("database", "")
            accession = link.get("accession", "")

            if not accession:
                continue

            if database == "UniProtKB":
                uniprot_ids.append(accession)
            elif database == "Ensembl Gene":
                refs_dict["ensembl_gene"] = accession
            elif database == "Entrez Gene":
                refs_dict["entrez"] = accession
            elif database == "RefSeq Nucleotide":
                refseq_ids.append(accession)
            elif database == "ChEMBL Target":
                refs_dict["chembl"] = accession.replace("CHEMBL", "")
            elif database == "OMIM":
                refs_dict["omim"] = accession
            elif database == "Orphanet":
                # Normalize to CURIE format (e.g., "ORPHA121177" -> "ORPHA:121177")
                if accession.startswith("ORPHA") and ":" not in accession:
                    accession = f"ORPHA:{accession[5:]}"
                refs_dict["orphanet"] = accession

        # Set list fields if populated
        if uniprot_ids:
            refs_dict["uniprot"] = uniprot_ids
        if refseq_ids:
            refs_dict["refseq"] = refseq_ids

        return CrossReferences(**refs_dict)

    def _strip_html_tags(self, text: str) -> str:
        """Strip HTML tags from text (e.g., D<sub>2</sub> -> D2)."""
        return HTML_TAG_PATTERN.sub("", text)

    def _handle_http_error(
        self, response: httpx.Response, entity_type: str = "entity"
    ) -> ErrorEnvelope:
        """Convert HTTP errors to ErrorEnvelope with recovery hints.

        Args:
            response: HTTP response with error status
            entity_type: "ligand" or "target" for context-specific hints
        """
        status = response.status_code

        if status == 404:
            # ENTITY_NOT_FOUND: ID exists but wrong entity type
            other_type = "target" if entity_type == "ligand" else "ligand"
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"{entity_type.capitalize()} not found with provided ID",
                    recovery_hint=f"Try get_{other_type} instead - IUPHAR IDs are shared between ligands and targets",
                    invalid_input=response.url.path,
                ),
            )

        if status in (429, 503):
            # RATE_LIMITED: Too many requests or service unavailable
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.RATE_LIMITED,
                    message="GtoPdb rate limit exceeded or service temporarily unavailable",
                    recovery_hint="Retry with exponential backoff (already implemented in client)",
                    invalid_input=None,
                ),
            )

        # UPSTREAM_ERROR: Generic API failure
        return ErrorEnvelope(
            success=False,
            error=ErrorDetail(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"GtoPdb API error: HTTP {status}",
                recovery_hint="Check GtoPdb service status at https://www.guidetopharmacology.org",
                invalid_input=None,
            ),
        )

    # =========================================================================
    # Ligand API Methods (User Story 1 & 2)
    # =========================================================================

    async def _fetch_ligands(
        self,
        name: str | None = None,
        type_filter: str | None = None,
        approved_only: bool = False,
    ) -> list[dict]:
        """Fetch ligands from GtoPdb API with optional filters.

        Args:
            name: Fuzzy substring match on ligand name
            type_filter: Filter by ligand classification (e.g., "Synthetic organic")
            approved_only: Filter for approved drugs only

        Returns:
            List of ligand dictionaries from API response
        """
        params = {}
        if name:
            params["name"] = name
        if type_filter:
            params["type"] = type_filter
        if approved_only:
            params["approved"] = "true"

        response = await self._rate_limited_get("/ligands", params=params)

        # Handle empty results
        # Note: GtoPdb API may return 204 or 404 for no results
        if response.status_code in (204, 404):
            return []

        # Handle errors
        if response.status_code != 200:
            raise ValueError(f"API error: {response.status_code}")

        return response.json()

    async def _fetch_ligand_synonyms(self, ligand_id: int) -> list[str]:
        """Fetch synonyms for a ligand.

        Args:
            ligand_id: Numeric GtoPdb ligand ID

        Returns:
            List of synonym strings
        """
        response = await self._rate_limited_get(f"/ligands/{ligand_id}/synonyms")

        # Handle 204 No Content (no synonyms)
        if response.status_code == 204:
            return []

        # Handle errors
        if response.status_code != 200:
            return []

        data = response.json()
        # Extract synonym names from response
        return [item.get("name", "") for item in data if item.get("name")]

    async def search_ligands(
        self,
        query: str,
        type_filter: str | None = None,
        approved_only: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> dict:
        """Search for ligands using fuzzy name matching.

        Implements User Story 1 (Fuzzy Ligand Search) with client-side pagination.

        Args:
            query: Search query (minimum 2 characters)
            type_filter: Optional ligand type filter (e.g., "Synthetic organic")
            approved_only: Filter for approved drugs only
            cursor: Pagination cursor (base64-encoded offset)
            page_size: Results per page (default 50, max 100)

        Returns:
            PaginationEnvelope with LigandSearchCandidate items
        """
        from lifesciences_mcp.models.envelopes import PaginationEnvelope
        from lifesciences_mcp.models.pharmacology import LigandSearchCandidate

        # Validate query length
        if len(query) < 2:
            raise ValueError("Query must be at least 2 characters")

        # Clamp page_size
        page_size = min(page_size, 100)

        # Fetch all matching ligands
        ligands = await self._fetch_ligands(
            name=query, type_filter=type_filter, approved_only=approved_only
        )

        # Client-side pagination
        offset = self._decode_cursor(cursor) if cursor else 0
        total_count = len(ligands)
        page_ligands = ligands[offset : offset + page_size]

        # Build search candidates with position-based scoring
        candidates = []
        for i, ligand in enumerate(page_ligands):
            score = self._calculate_score(offset + i)
            candidate = LigandSearchCandidate(
                id=f"IUPHAR:{ligand.get('ligandId')}",
                name=ligand.get("name", ""),
                type=ligand.get("type", ""),
                approved=ligand.get("approved", False),
                score=score,
            )
            candidates.append(candidate)

        # Generate next cursor
        next_cursor = None
        if offset + page_size < total_count:
            next_cursor = self._encode_cursor(offset + page_size)

        # Return pagination envelope
        return PaginationEnvelope.create(
            items=candidates,
            cursor=next_cursor,
            total_count=total_count,
            page_size=page_size,
        ).model_dump()

    async def _fetch_ligand_detail(self, ligand_id: int) -> dict:
        """Fetch detailed ligand information by numeric ID.

        Args:
            ligand_id: Numeric GtoPdb ligand ID

        Returns:
            Ligand detail dictionary from API response

        Raises:
            ValueError: If ligand not found (404)
        """
        response = await self._rate_limited_get(f"/ligands/{ligand_id}")

        if response.status_code == 404:
            raise ValueError(f"Ligand not found: {ligand_id}")

        if response.status_code != 200:
            raise ValueError(f"API error: {response.status_code}")

        return response.json()

    async def _fetch_ligand_db_links(self, ligand_id: int) -> list[dict]:
        """Fetch database cross-references for a ligand.

        Args:
            ligand_id: Numeric GtoPdb ligand ID

        Returns:
            List of database link dictionaries
        """
        response = await self._rate_limited_get(f"/ligands/{ligand_id}/databaseLinks")

        # Handle 204 No Content (no cross-references)
        if response.status_code == 204:
            return []

        if response.status_code != 200:
            return []

        return response.json()

    async def get_ligand(self, iuphar_id: str) -> dict:
        """Get complete ligand record by IUPHAR CURIE.

        Implements User Story 2 (Strict Ligand Lookup) with full cross-references.

        Args:
            iuphar_id: IUPHAR CURIE (e.g., "IUPHAR:2713")

        Returns:
            Complete Ligand entity with cross_references, or ErrorEnvelope on failure
        """
        from lifesciences_mcp.models.envelopes import ErrorDetail, ErrorEnvelope
        from lifesciences_mcp.models.pharmacology import IUPHAR_CURIE_PATTERN, Ligand

        # Validate CURIE format (reject raw strings) - T204
        if not IUPHAR_CURIE_PATTERN.match(iuphar_id):
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UNRESOLVED_ENTITY,
                    message=f"Invalid IUPHAR CURIE format: '{iuphar_id}'",
                    recovery_hint="Use search_ligands() to find the correct IUPHAR CURIE (format: 'IUPHAR:12345')",
                    invalid_input=iuphar_id,
                ),
            ).model_dump()

        # Extract numeric ID from CURIE
        ligand_id = int(iuphar_id.split(":")[1])

        # Fetch ligand detail and cross-references in parallel
        try:
            ligand_data = await self._fetch_ligand_detail(ligand_id)
            db_links = await self._fetch_ligand_db_links(ligand_id)
            synonyms = await self._fetch_ligand_synonyms(ligand_id)
        except ValueError as e:
            if "not found" in str(e):
                # Return ErrorEnvelope for 404
                return self._handle_http_error(
                    type(
                        "Response",
                        (),
                        {
                            "status_code": 404,
                            "url": type("URL", (), {"path": f"/ligands/{ligand_id}"}),
                        },
                    )(),
                    entity_type="ligand",
                ).model_dump()
            raise

        # Map cross-references
        cross_refs = self._map_ligand_cross_references(db_links)

        # Build Ligand entity
        ligand = Ligand(
            id=iuphar_id,
            ligand_id=ligand_id,
            name=ligand_data.get("name", ""),
            approved_name=ligand_data.get("approvedName"),
            type=ligand_data.get("type", ""),
            abbreviation=ligand_data.get("abbreviation"),
            approved=ligand_data.get("approved", False),
            approval_source=ligand_data.get("approvalSource"),
            who_essential=ligand_data.get("whoEssential"),
            withdrawn=ligand_data.get("withdrawn"),
            synonyms=synonyms if synonyms else None,
            cross_references=cross_refs,
        )

        return ligand.model_dump()

    # =========================================================================
    # Target API Methods (User Story 3 & 4)
    # =========================================================================

    async def _fetch_targets(
        self,
        name: str | None = None,
        type_filter: str | None = None,
        gene_symbol: str | None = None,
    ) -> list[dict]:
        """Fetch targets from GtoPdb API with optional filters.

        Args:
            name: Fuzzy substring match on target name
            type_filter: Filter by target type/family (e.g., "GPCR", "Enzyme")
            gene_symbol: Filter by gene symbol

        Returns:
            List of target dictionaries from API response
        """
        params = {}
        if name:
            params["name"] = name
        if type_filter:
            params["type"] = type_filter
        if gene_symbol:
            params["geneSymbol"] = gene_symbol

        response = await self._rate_limited_get("/targets", params=params)

        # Handle empty results
        # Note: GtoPdb targets endpoint returns 404 for no results (unlike ligands which return 204)
        if response.status_code in (204, 404):
            return []

        # Handle other errors
        if response.status_code != 200:
            raise ValueError(f"API error: {response.status_code}")

        return response.json()

    async def search_targets(
        self,
        query: str,
        type_filter: str | None = None,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> dict:
        """Search for pharmacological targets using fuzzy name matching.

        Implements User Story 3 (Fuzzy Target Search) with client-side pagination.

        Args:
            query: Search query (minimum 2 characters)
            type_filter: Optional target type filter (e.g., "GPCR", "Enzyme")
            cursor: Pagination cursor (base64-encoded offset)
            page_size: Results per page (default 50, max 100)

        Returns:
            PaginationEnvelope with TargetSearchCandidate items
        """
        from lifesciences_mcp.models.envelopes import PaginationEnvelope
        from lifesciences_mcp.models.pharmacology import TargetSearchCandidate

        # Validate query length
        if len(query) < 2:
            raise ValueError("Query must be at least 2 characters")

        # Clamp page_size
        page_size = min(page_size, 100)

        # Fetch all matching targets
        targets = await self._fetch_targets(name=query, type_filter=type_filter)

        # Client-side pagination
        offset = self._decode_cursor(cursor) if cursor else 0
        total_count = len(targets)
        page_targets = targets[offset : offset + page_size]

        # Build search candidates with position-based scoring
        candidates = []
        for i, target in enumerate(page_targets):
            score = self._calculate_score(offset + i)

            # Strip HTML tags from target name (e.g., D<sub>2</sub> -> D2)
            name = target.get("name", "")
            name = self._strip_html_tags(name)

            # API provides type (e.g., "GPCR", "Enzyme") - use for both family and type
            target_type = target.get("type", "")

            candidate = TargetSearchCandidate(
                id=f"IUPHAR:{target.get('targetId')}",
                name=name,
                family=target_type,  # Broad category (GPCR, Enzyme, etc.)
                type=target_type,  # Full classification (same as family in API response)
                score=score,
            )
            candidates.append(candidate)

        # Generate next cursor
        next_cursor = None
        if offset + page_size < total_count:
            next_cursor = self._encode_cursor(offset + page_size)

        # Return pagination envelope
        return PaginationEnvelope.create(
            items=candidates,
            cursor=next_cursor,
            total_count=total_count,
            page_size=page_size,
        ).model_dump()

    async def _fetch_target_detail(self, target_id: int) -> dict:
        """Fetch detailed target information by numeric ID.

        Args:
            target_id: Numeric GtoPdb target ID

        Returns:
            Target detail dictionary from API response

        Raises:
            ValueError: If target not found (404)
        """
        response = await self._rate_limited_get(f"/targets/{target_id}")

        if response.status_code == 404:
            raise ValueError(f"Target not found: {target_id}")

        if response.status_code != 200:
            raise ValueError(f"API error: {response.status_code}")

        return response.json()

    async def _fetch_target_db_links(self, target_id: int) -> list[dict]:
        """Fetch database cross-references for a target.

        Args:
            target_id: Numeric GtoPdb target ID

        Returns:
            List of database link dictionaries
        """
        response = await self._rate_limited_get(f"/targets/{target_id}/databaseLinks")

        # Handle 204 No Content (no cross-references)
        if response.status_code == 204:
            return []

        if response.status_code != 200:
            return []

        return response.json()

    async def get_target(self, iuphar_id: str) -> dict:
        """Get complete target record by IUPHAR CURIE.

        Implements User Story 4 (Strict Target Lookup) with full cross-references.

        Args:
            iuphar_id: IUPHAR CURIE (e.g., "IUPHAR:215")

        Returns:
            Complete Target entity with cross_references, or ErrorEnvelope on failure
        """
        from lifesciences_mcp.models.envelopes import ErrorDetail, ErrorEnvelope
        from lifesciences_mcp.models.pharmacology import IUPHAR_CURIE_PATTERN, Target

        # Validate CURIE format (reject raw strings) - T205
        if not IUPHAR_CURIE_PATTERN.match(iuphar_id):
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UNRESOLVED_ENTITY,
                    message=f"Invalid IUPHAR CURIE format: '{iuphar_id}'",
                    recovery_hint="Use search_targets() to find the correct IUPHAR CURIE (format: 'IUPHAR:12345')",
                    invalid_input=iuphar_id,
                ),
            ).model_dump()

        # Extract numeric ID from CURIE
        target_id = int(iuphar_id.split(":")[1])

        # Fetch target detail and cross-references in parallel
        try:
            target_data = await self._fetch_target_detail(target_id)
            db_links = await self._fetch_target_db_links(target_id)
        except ValueError as e:
            if "not found" in str(e):
                # Return ErrorEnvelope for 404
                return self._handle_http_error(
                    type(
                        "Response",
                        (),
                        {
                            "status_code": 404,
                            "url": type("URL", (), {"path": f"/targets/{target_id}"}),
                        },
                    )(),
                    entity_type="target",
                ).model_dump()
            raise

        # Map cross-references
        cross_refs = self._map_target_cross_references(db_links)

        # Strip HTML tags from target name
        name = target_data.get("name", "")
        name = self._strip_html_tags(name)

        # Build Target entity
        target = Target(
            id=iuphar_id,
            target_id=target_id,
            name=name,
            target_family=target_data.get("type", ""),  # e.g., "GPCR", "Enzyme"
            family_ids=target_data.get("familyIds"),  # List of parent family IDs
            gene_symbol=target_data.get("geneSymbol"),  # May be None
            cross_references=cross_refs,
        )

        return target.model_dump()
