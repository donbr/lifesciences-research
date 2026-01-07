"""PubChem REST API client for chemical compound data.

This module provides an async client for querying PubChem's PUG REST API,
enabling fuzzy compound search and strict compound lookup operations.
"""

import asyncio
import base64
import json
import time
from collections import deque
from typing import Any
from urllib.parse import quote

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    PaginationEnvelope,
)
from lifesciences_mcp.models.pubchem_compound import (
    PUBCHEM_CURIE_PATTERN,
    PubChemCompound,
    PubChemSearchCandidate,
)


class PubChemClient(LifeSciencesClient):
    """Async client for PubChem PUG REST API.

    Implements dual rate limiting (5 req/s + 400 req/min) with exponential backoff
    following Constitution v1.1.0 guidelines.
    """

    # Configuration constants (T009-T010)
    PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    PROPERTY_LIST = "MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,Title"

    # Rate limiting configuration (Constitution v1.1.0 MANDATORY)
    RATE_LIMIT_PER_SECOND = 5  # Max 5 req/s
    RATE_LIMIT_PER_MINUTE = 400  # Max 400 req/min

    # Exponential backoff configuration (T015)
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 60.0  # seconds

    def __init__(self) -> None:
        """Initialize PubChem client with rate limiting (T008)."""
        super().__init__(
            base_url=self.PUBCHEM_BASE_URL,
            timeout=30.0,
        )

        # Per-second rate limiter (T011, T012)
        self._rate_lock = asyncio.Lock()
        self._last_request_time: float = 0.0

        # Per-minute rate limiter (rolling window) (T013)
        self._minute_window: deque[float] = deque(maxlen=400)

    async def _rate_limited_get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Execute GET with dual rate limiting (T014).

        Implements:
        - Per-second rate limiting (5 req/s with 200ms minimum interval)
        - Per-minute rate limiting (400 req/min with rolling window)
        - Thundering herd prevention (lock + re-check timing)
        - Exponential backoff on HTTP 503

        Args:
            url: The URL path to request (relative to base_url)
            **kwargs: Additional arguments to pass to httpx

        Returns:
            httpx.Response: The HTTP response

        Raises:
            httpx.HTTPStatusError: On non-retryable HTTP errors
        """
        async with self._rate_lock:  # T016: Thundering herd prevention
            now = time.monotonic()

            # Per-second limit (200ms minimum interval for 5 req/s) (T012)
            min_interval = 1.0 / self.RATE_LIMIT_PER_SECOND
            elapsed = now - self._last_request_time
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                # Add jitter for distributed systems safety (T017)
                import random

                jitter = random.uniform(0, sleep_time * 0.1)
                await asyncio.sleep(sleep_time + jitter)

            # Per-minute limit (rolling window) (T013)
            while len(self._minute_window) >= self.RATE_LIMIT_PER_MINUTE:
                oldest = self._minute_window[0]
                now = time.monotonic()  # Re-check after potential sleep
                if now - oldest < 60.0:
                    sleep_time = 60.0 - (now - oldest) + 0.1  # Small buffer
                    await asyncio.sleep(sleep_time)
                    now = time.monotonic()
                else:
                    self._minute_window.popleft()

            self._last_request_time = time.monotonic()
            self._minute_window.append(self._last_request_time)

        # Execute request with exponential backoff (T015)
        return await self._request_with_backoff(url, **kwargs)

    async def _request_with_backoff(self, url: str, **kwargs: Any) -> httpx.Response:
        """Execute HTTP GET with exponential backoff on HTTP 503 (T015).

        Args:
            url: The URL path to request
            **kwargs: Additional arguments to pass to httpx

        Returns:
            httpx.Response: The HTTP response (may have error status code - caller should check)

        Raises:
            httpx.HTTPStatusError: On non-retryable HTTP errors (except 404, 400)
        """
        import random

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._get(url, **kwargs)
                # Don't raise on 404 or 400 - caller will handle it
                if response.status_code not in (400, 404):
                    response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503 and attempt < self.MAX_RETRIES - 1:
                    # Exponential backoff: base 1s, max 60s (T015)
                    delay = min(
                        self.BASE_DELAY * (2**attempt),
                        self.MAX_DELAY,
                    )
                    # Add jitter (T017)
                    jitter = random.uniform(0, delay * 0.1)
                    await asyncio.sleep(delay + jitter)
                    continue
                raise

        # Should never reach here, but satisfy type checker
        msg = "Max retries exceeded"
        raise RuntimeError(msg)

    def _validate_pubchem_curie(self, pubchem_id: str) -> int | ErrorEnvelope:
        """Validate PubChem CURIE format and extract CID (T019).

        Args:
            pubchem_id: PubChem CURIE (e.g., "PubChem:CID2244")

        Returns:
            int: The numeric CID
            ErrorEnvelope: Error with UNRESOLVED_ENTITY code if invalid

        Examples:
            >>> _validate_pubchem_curie("PubChem:CID2244")
            2244
            >>> _validate_pubchem_curie("CID2244")  # Returns ErrorEnvelope
            >>> _validate_pubchem_curie("2244")  # Returns ErrorEnvelope
        """
        if not PUBCHEM_CURIE_PATTERN.match(pubchem_id):
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UNRESOLVED_ENTITY,
                    message=f"Invalid PubChem CURIE format: '{pubchem_id}'",
                    recovery_hint=(
                        "Use format 'PubChem:CID{number}' (e.g., 'PubChem:CID2244'). "
                        "CID must be numeric."
                    ),
                    invalid_input=pubchem_id,
                ),
            )

        # Extract CID number
        cid_str = pubchem_id.split("CID")[1]
        return int(cid_str)

    def _format_pubchem_curie(self, cid: int) -> str:
        """Format a CID as a PubChem CURIE (T020).

        Args:
            cid: Numeric CID

        Returns:
            str: Formatted CURIE (e.g., "PubChem:CID2244")
        """
        return f"PubChem:CID{cid}"

    def _map_http_error(
        self, status_code: int, response_text: str, original_input: str = ""
    ) -> ErrorEnvelope:
        """Map HTTP status codes to canonical error codes (T022-T026).

        Args:
            status_code: HTTP status code
            response_text: Response body text
            original_input: Original user input for invalid_input field

        Returns:
            ErrorEnvelope: Error with appropriate code and recovery hint
        """
        if status_code == 400:  # T023
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UNRESOLVED_ENTITY,
                    message=f"Bad request: {response_text}",
                    recovery_hint=(
                        "Check CURIE format. Use 'PubChem:CID{number}' (e.g., 'PubChem:CID2244')."
                    ),
                    invalid_input=original_input,
                ),
            )
        elif status_code == 404:  # T024
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"Compound not found: {original_input}",
                    recovery_hint=(
                        "CID not found in PubChem. Use search_compounds to find valid CIDs."
                    ),
                    invalid_input=original_input,
                ),
            )
        elif status_code == 503:  # T025
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.RATE_LIMITED,
                    message="PubChem server is busy or rate limit exceeded",
                    recovery_hint=(
                        "Wait 60 seconds before retrying. PubChem limits: 5 req/s, 400 req/min."
                    ),
                    invalid_input=original_input,
                ),
            )
        else:  # T026: 500, 502, timeout
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"PubChem API error (HTTP {status_code}): {response_text}",
                    recovery_hint="Retry request in 60 seconds. PubChem may be experiencing issues.",
                    invalid_input=original_input,
                ),
            )

    async def _search_by_name(self, name: str) -> list[int] | ErrorEnvelope:
        """Search for compounds by name and return CID list (T040).

        Args:
            name: Compound name to search for

        Returns:
            list[int]: List of CIDs, or ErrorEnvelope on error

        API Endpoint: GET /compound/name/{name}/cids/JSON
        """
        # URL encode the name (T041)
        encoded_name = quote(name)
        url = f"/compound/name/{encoded_name}/cids/JSON"

        try:
            response = await self._rate_limited_get(url)

            # Handle HTTP 404 as empty results (T043)
            if response.status_code == 404:
                return []

            if response.status_code != 200:
                return self._map_http_error(
                    response.status_code, response.text, original_input=name
                )

            # Parse IdentifierList.CID array (T042)
            data = response.json()
            cids = data.get("IdentifierList", {}).get("CID", [])
            return cids

        except httpx.TimeoutException:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message="Request to PubChem API timed out.",
                    recovery_hint="Retry after a short delay.",
                    invalid_input=name,
                ),
            )
        except httpx.RequestError as e:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Network error: {e!s}",
                    recovery_hint="Check network connectivity and retry.",
                    invalid_input=name,
                ),
            )

    async def _get_compound_properties(
        self, cids: list[int], properties: list[str]
    ) -> dict[int, dict[str, Any]] | ErrorEnvelope:
        """Get properties for a list of CIDs (T044, T045).

        Args:
            cids: List of CIDs
            properties: List of property names to fetch

        Returns:
            dict mapping CID to property dict, or ErrorEnvelope on error

        API Endpoint: POST /compound/cid/property/{properties}/JSON
        """
        if not cids:
            return {}

        # Build property list string
        prop_str = ",".join(properties)

        # Build comma-separated CID list
        cid_str = ",".join(str(cid) for cid in cids)

        url = f"/compound/cid/{cid_str}/property/{prop_str}/JSON"

        try:
            response = await self._rate_limited_get(url)

            # Handle error codes
            if response.status_code in (400, 404):
                # 404: Some CIDs not found
                # 400: Invalid CID format or value
                return self._map_http_error(
                    response.status_code, response.text, original_input=cid_str
                )

            if response.status_code != 200:
                return self._map_http_error(
                    response.status_code, response.text, original_input=cid_str
                )

            data = response.json()
            properties_list = data.get("PropertyTable", {}).get("Properties", [])

            # Map CID to properties
            result = {}
            for prop in properties_list:
                cid = prop.get("CID")
                if cid:
                    result[cid] = prop

            return result

        except httpx.TimeoutException:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message="Request to PubChem API timed out.",
                    recovery_hint="Retry after a short delay.",
                ),
            )
        except httpx.RequestError as e:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Network error: {e!s}",
                    recovery_hint="Check network connectivity and retry.",
                ),
            )

    def _encode_cursor(self, offset: int) -> str:
        """Encode cursor for pagination (T047).

        Args:
            offset: Current offset in results

        Returns:
            Base64-encoded cursor string
        """
        cursor_data = {"offset": offset}
        return base64.b64encode(json.dumps(cursor_data).encode()).decode()

    def _decode_cursor(self, cursor: str) -> int:
        """Decode cursor to offset (T047).

        Args:
            cursor: Base64-encoded cursor string

        Returns:
            Offset integer, or 0 if invalid cursor
        """
        try:
            cursor_data = json.loads(base64.b64decode(cursor).decode())
            return cursor_data.get("offset", 0)
        except (ValueError, json.JSONDecodeError, KeyError):
            return 0

    async def search_compounds(
        self,
        query: str,
        page_size: int = 50,
        cursor: str | None = None,
        slim: bool = True,
    ) -> PaginationEnvelope[PubChemSearchCandidate] | ErrorEnvelope:
        """Fuzzy search for compounds (Phase 1 of Fuzzy-to-Fact) (T050).

        Args:
            query: Search term (compound name, synonym, or identifier)
            page_size: Results per page (1-100)
            cursor: Opaque cursor for pagination
            slim: If true, minimal fields only (included for API consistency)

        Returns:
            PaginationEnvelope with PubChemSearchCandidate items, or ErrorEnvelope

        Examples:
            >>> result = await client.search_compounds("aspirin")
            >>> result["items"][0]["id"]  # "PubChem:CID2244"
        """
        # Validate minimum query length (T049)
        query = query.strip()
        if len(query) < 2:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message=f"Query too short: '{query}'",
                    recovery_hint="Minimum query length is 2 characters",
                    invalid_input=query,
                ),
            )

        # Clamp page_size to valid range
        page_size = max(1, min(100, page_size))

        # Decode cursor if provided (T046, T047)
        offset = 0
        if cursor:
            offset = self._decode_cursor(cursor)

        # Search by name to get CID list
        cids_result = await self._search_by_name(query)
        if isinstance(cids_result, ErrorEnvelope):
            return cids_result

        cids = cids_result

        # Handle empty results
        if not cids:
            return PaginationEnvelope.create(
                items=[],
                cursor=None,
                total_count=0,
                page_size=page_size,
            )

        # Get properties for all CIDs (Title and MolecularFormula)
        properties_result = await self._get_compound_properties(cids, ["Title", "MolecularFormula"])
        if isinstance(properties_result, ErrorEnvelope):
            return properties_result

        properties_map = properties_result

        # Build search candidates with linear decay scoring (T048)
        candidates = []
        for i, cid in enumerate(cids):
            # Linear decay scoring: score = max(0.1, 1.0 - (position * 0.05))
            score = max(0.1, 1.0 - (i * 0.05))

            # Get properties for this CID
            props = properties_map.get(cid, {})

            candidate = PubChemSearchCandidate(
                id=self._format_pubchem_curie(cid),
                name=props.get("Title"),
                molecular_formula=props.get("MolecularFormula"),
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
            next_cursor = self._encode_cursor(page_end)

        return PaginationEnvelope.create(
            items=page_items,
            cursor=next_cursor,
            total_count=total_count,
            page_size=page_size,
        )

    async def _get_compound_synonyms(self, cid: int) -> list[str] | ErrorEnvelope:
        """Get synonyms for a compound (T077-T079).

        Args:
            cid: Compound CID

        Returns:
            List of synonyms (limited to first 20 for token efficiency), or ErrorEnvelope on error

        API Endpoint: GET /compound/cid/{cid}/synonyms/JSON
        """
        url = f"/compound/cid/{cid}/synonyms/JSON"

        try:
            response = await self._rate_limited_get(url)

            if response.status_code == 404:
                # No synonyms available - return empty list
                return []

            if response.status_code != 200:
                return self._map_http_error(
                    response.status_code, response.text, original_input=str(cid)
                )

            # Parse InformationList.Information[0].Synonym array
            data = response.json()
            info_list = data.get("InformationList", {}).get("Information", [])
            if info_list:
                synonyms = info_list[0].get("Synonym", [])
                # Limit to first 20 synonyms for token efficiency
                return synonyms[:20]
            return []

        except httpx.TimeoutException:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message="Request to PubChem API timed out.",
                    recovery_hint="Retry after a short delay.",
                    invalid_input=str(cid),
                ),
            )
        except httpx.RequestError as e:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Network error: {e!s}",
                    recovery_hint="Check network connectivity and retry.",
                    invalid_input=str(cid),
                ),
            )

    async def _get_compound_xrefs(self, cid: int) -> dict | ErrorEnvelope:
        """Get cross-references for a compound (T111-T113).

        Args:
            cid: Compound CID

        Returns:
            Dict with xref data from PubChem, or ErrorEnvelope on error

        API Endpoint: GET /compound/cid/{cid}/xrefs/RegistryID/JSON
        """
        url = f"/compound/cid/{cid}/xrefs/RegistryID/JSON"

        try:
            response = await self._rate_limited_get(url)

            if response.status_code == 404:
                # No xrefs available - return empty dict
                return {}

            if response.status_code != 200:
                return self._map_http_error(
                    response.status_code, response.text, original_input=str(cid)
                )

            # Parse InformationList.Information[0] structure
            data = response.json()
            info_list = data.get("InformationList", {}).get("Information", [])
            if info_list:
                return info_list[0]
            return {}

        except httpx.TimeoutException:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message="Request to PubChem API timed out.",
                    recovery_hint="Retry after a short delay.",
                    invalid_input=str(cid),
                ),
            )
        except httpx.RequestError as e:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Network error: {e!s}",
                    recovery_hint="Check network connectivity and retry.",
                    invalid_input=str(cid),
                ),
            )

    def _extract_cross_references(
        self, cid: int, synonyms: list[str], xrefs: dict
    ) -> dict[str, list[str]]:
        r"""Extract cross-references from synonyms and xrefs (T114-T122).

        Args:
            cid: Compound CID
            synonyms: List of synonyms
            xrefs: Dict with xref data from PubChem

        Returns:
            Dict mapping cross-reference keys to lists of IDs.
            Only includes keys with non-empty values (omit-if-null pattern).

        Cross-reference extraction:
        - pubchem_compound: Self-reference (CID as string)
        - chembl: From synonyms matching ^CHEMBL(\d+)$ -> CHEMBL:{number}
        - drugbank: From synonyms matching ^DB\d{5}$
        - uniprot: From xrefs where SourceName contains "UniProt" -> UniProtKB:{registry_id}
        - pdb: From xrefs where SourceName contains "PDB"
        """
        import re

        cross_refs: dict[str, list[str]] = {}

        # Self-reference (always included)
        cross_refs["pubchem_compound"] = [str(cid)]

        # Extract ChEMBL IDs from synonyms
        chembl_pattern = re.compile(r"^CHEMBL(\d+)$")
        chembl_ids = []
        for syn in synonyms:
            match = chembl_pattern.match(syn)
            if match:
                chembl_ids.append(f"CHEMBL:{match.group(1)}")
        if chembl_ids:
            cross_refs["chembl"] = chembl_ids

        # Extract DrugBank IDs from synonyms
        drugbank_pattern = re.compile(r"^DB\d{5}$")
        drugbank_ids = []
        for syn in synonyms:
            if drugbank_pattern.match(syn):
                drugbank_ids.append(syn)
        if drugbank_ids:
            cross_refs["drugbank"] = drugbank_ids

        # Extract cross-references from xrefs
        if xrefs:
            # UniProt: from RegistryID where SourceName contains "UniProt"
            uniprot_ids = []
            pdb_ids = []

            # xrefs structure: {CID: int, RegistryID: [...]}
            registry_ids = xrefs.get("RegistryID", [])
            if isinstance(registry_ids, list):
                for entry in registry_ids:
                    if isinstance(entry, dict):
                        source_name = entry.get("SourceName", "")
                        registry_id = entry.get("RegistryID", "")

                        if "UniProt" in source_name and registry_id:
                            uniprot_ids.append(f"UniProtKB:{registry_id}")
                        elif "PDB" in source_name and registry_id:
                            pdb_ids.append(registry_id)

            if uniprot_ids:
                cross_refs["uniprot"] = uniprot_ids
            if pdb_ids:
                cross_refs["pdb"] = pdb_ids

        return cross_refs

    async def get_compound(
        self, pubchem_id: str, slim: bool = False
    ) -> PubChemCompound | ErrorEnvelope:
        """Get complete compound record by PubChem CURIE (T080-T092).

        This is Phase 2 of the Fuzzy-to-Fact protocol. Requires a resolved CURIE
        from search_compounds.

        Args:
            pubchem_id: PubChem CURIE (e.g., "PubChem:CID2244")
            slim: If true, return minimal fields (id, name, molecular_formula only)

        Returns:
            PubChemCompound with full data including cross_references, or ErrorEnvelope on error

        Examples:
            >>> compound = await client.get_compound("PubChem:CID2244")
            >>> compound.name  # "Aspirin"
            >>> compound.cross_references["chembl"]  # ["CHEMBL:25"]
        """
        # Validate CURIE and extract CID (T081)
        cid_result = self._validate_pubchem_curie(pubchem_id)
        if isinstance(cid_result, ErrorEnvelope):
            return cid_result
        cid = cid_result

        # Fetch properties (T082-T084)
        # Note: PubChem uses different names: SMILES (canonical), ConnectivitySMILES (isomeric)
        properties_result = await self._get_compound_properties(
            [cid],
            [
                "Title",
                "IUPACName",
                "MolecularFormula",
                "MolecularWeight",
                "CanonicalSMILES",
                "IsomericSMILES",
                "InChI",
                "InChIKey",
            ],
        )
        if isinstance(properties_result, ErrorEnvelope):
            # Replace CID with full CURIE in error
            properties_result.error.invalid_input = pubchem_id
            return properties_result

        # Check if compound was found
        if cid not in properties_result:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"PubChem compound not found: {pubchem_id}",
                    recovery_hint="CID not found in PubChem. Verify CURIE from search_compounds results.",
                    invalid_input=pubchem_id,
                ),
            )

        properties = properties_result[cid]

        # Fetch synonyms (T085-T086)
        synonyms_result = await self._get_compound_synonyms(cid)
        if isinstance(synonyms_result, ErrorEnvelope):
            return synonyms_result
        synonyms = synonyms_result

        # Fetch xrefs (T087-T088)
        xrefs_result = await self._get_compound_xrefs(cid)
        if isinstance(xrefs_result, ErrorEnvelope):
            return xrefs_result
        xrefs = xrefs_result

        # Extract cross-references (T089)
        cross_references = self._extract_cross_references(cid, synonyms, xrefs)

        # Build PubChemCompound model (T090)
        # Map API field names to model fields (API uses different names)
        compound = PubChemCompound(
            id=pubchem_id,
            name=properties.get("Title"),
            iupac_name=properties.get("IUPACName"),
            molecular_formula=properties.get("MolecularFormula"),
            molecular_weight=properties.get("MolecularWeight"),
            # PubChem API returns SMILES (canonical), not CanonicalSMILES
            canonical_smiles=properties.get("CanonicalSMILES") or properties.get("SMILES"),
            # PubChem API returns ConnectivitySMILES (isomeric), not IsomericSMILES
            isomeric_smiles=properties.get("IsomericSMILES")
            or properties.get("ConnectivitySMILES"),
            inchi=properties.get("InChI"),
            inchikey=properties.get("InChIKey"),
            synonyms=synonyms,
            cross_references=cross_references,
        )

        # Return slim or full (T091-T092)
        if slim:
            return PubChemCompound(**compound.to_slim())

        return compound
