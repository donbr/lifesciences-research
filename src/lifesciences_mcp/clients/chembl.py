"""ChEMBL API client implementing the Fuzzy-to-Fact protocol.

This module provides the ChEMBLClient for querying the ChEMBL database
for compound and bioactivity data.

Key implementation details:
- Uses `chembl_webresource_client` SDK (synchronous) wrapped with run_in_executor
- Rate limiting: 10 req/s with exponential backoff (Constitution v1.1.0)
- Thread pool: default ThreadPoolExecutor (ADR-001 §2 exception)

Owner: Agent 1 during parallel implementation.
"""

import asyncio
import base64
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, ClassVar

from chembl_webresource_client.new_client import new_client

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.compound import Compound, CompoundSearchCandidate
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    PaginationEnvelope,
)

logger = logging.getLogger(__name__)

# CURIE validation pattern
CHEMBL_CURIE_PATTERN = re.compile(r"^CHEMBL:[0-9]+$")


class ChEMBLClient(LifeSciencesClient):
    """ChEMBL API client with async wrapping of synchronous SDK.

    ChEMBL provides bioactivity data for compounds and targets.

    NOTE: ChEMBL uses a synchronous SDK (chembl_webresource_client).
    Per ADR-001 §2, SDK calls are wrapped with run_in_executor.

    Rate limiting: 10 req/s with exponential backoff (Constitution v1.1.0)
    API Docs: https://www.ebi.ac.uk/chembl/ws
    """

    CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

    # Rate limiting configuration (Constitution v1.1.0 MANDATORY)
    RATE_LIMIT_REQUESTS = 10  # requests per second
    RATE_LIMIT_PERIOD = 1.0  # second

    # Exponential backoff configuration
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 60.0  # seconds

    # Cross-reference mapping from ChEMBL to 22-key registry
    XREF_MAPPING: ClassVar[dict[str, str]] = {
        "UniProt": "uniprot",
        "PDBe": "pdb",
        "PubChem": "pubchem_compound",
        "DrugBank": "drugbank",
    }


    def __init__(self) -> None:
        """Initialize the ChEMBL client with SDK and rate limiting.

        The client inherits a default timeout of 30.0s from LifeSciencesClient,
        which is enforced on all synchronous SDK calls via asyncio.wait_for.
        """
        super().__init__(base_url=self.CHEMBL_BASE_URL)

        # Initialize ChEMBL SDK (synchronous)
        # Note: ChEMBL SDK lacks type stubs, so we ignore attribute access error
        self._molecule = new_client.molecule  # type: ignore[attr-defined]
        self._drug_indication = new_client.drug_indication  # type: ignore[attr-defined]

        # Lazy-init ThreadPoolExecutor (use Python defaults)
        self._executor: ThreadPoolExecutor | None = None

        # Rate limiting state (Constitution v1.1.0)
        self._rate_lock = asyncio.Lock()
        self._last_request_time: float = 0.0

    def _get_executor(self) -> ThreadPoolExecutor:
        """Get or create the thread pool executor."""
        if self._executor is None:
            # Use Python defaults: min(32, (os.cpu_count() or 1) + 4)
            self._executor = ThreadPoolExecutor()
        return self._executor

    async def _rate_limited_sdk_call(self, sdk_func: Any) -> Any:
        """Execute SDK call with rate limiting and run_in_executor wrapping.

        This method:
        1. Acquires lock for request serialization
        2. Enforces 100ms minimum delay between requests (10 req/s)
        3. Uses thundering herd prevention (re-check after acquiring lock)
        4. Wraps synchronous SDK call in run_in_executor

        Args:
            sdk_func: A callable that invokes the synchronous ChEMBL SDK

        Returns:
            The result from the SDK call
        """
        async with self._rate_lock:
            # Thundering herd prevention: re-check timing after acquiring lock
            now = time.monotonic()
            min_interval = 1.0 / self.RATE_LIMIT_REQUESTS  # 100ms for 10 req/s

            elapsed = now - self._last_request_time
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

            # Update last request time before making call
            self._last_request_time = time.monotonic()

        # Execute SDK call in thread pool
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(self._get_executor(), sdk_func),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            # Raise generic exception with "timeout" keyword to trigger retry/mapping logic
            raise TimeoutError(f"ChEMBL SDK request timeout after {self._timeout}s")


    async def _sdk_call_with_backoff(self, sdk_func: Any) -> Any:
        """Execute SDK call with exponential backoff for rate limit errors.

        Handles 429 (Rate Limited) and 503 (Service Unavailable) with retry.

        Args:
            sdk_func: A callable that invokes the synchronous ChEMBL SDK

        Returns:
            The result from the SDK call

        Raises:
            Exception: After max retries exhausted
        """
        last_exception: Exception | None = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return await self._rate_limited_sdk_call(sdk_func)
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Check for rate limit or server errors (timeouts not retried to avoid compounding delays)
                is_rate_limited = "429" in error_str or "rate" in error_str
                is_server_error = any(code in error_str for code in ["500", "502", "503"])

                if (is_rate_limited or is_server_error) and attempt < self.MAX_RETRIES:
                    delay = min(
                        self.BASE_DELAY * (2**attempt),
                        self.MAX_DELAY,
                    )
                    logger.warning(
                        f"ChEMBL API error (attempt {attempt + 1}/{self.MAX_RETRIES + 1}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in backoff loop")

    def _validate_chembl_curie(self, chembl_id: str) -> str | ErrorEnvelope:
        """Validate ChEMBL CURIE format and extract numeric ID.

        Args:
            chembl_id: ChEMBL CURIE (e.g., "CHEMBL:25")

        Returns:
            Numeric ID string (e.g., "25") or ErrorEnvelope if invalid
        """
        if not CHEMBL_CURIE_PATTERN.match(chembl_id):
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UNRESOLVED_ENTITY,
                    message=f"Invalid ChEMBL CURIE format: '{chembl_id}'",
                    recovery_hint="Invalid ChEMBL CURIE format. Use 'CHEMBL:NNNNN' (e.g., 'CHEMBL:25')",
                    invalid_input=chembl_id,
                )
            )
        # Extract numeric ID after "CHEMBL:"
        return chembl_id.split(":")[1]

    def _map_sdk_error(self, error: Exception, input_value: str | None = None) -> ErrorEnvelope:
        """Map ChEMBL SDK exceptions to canonical error codes.

        Args:
            error: The exception from SDK call
            input_value: The input that caused the error (for error envelope)

        Returns:
            ErrorEnvelope with appropriate error code and recovery hint
        """
        error_str = str(error).lower()

        # 404 Not Found
        if "404" in error_str or "not found" in error_str:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"ChEMBL compound not found: {input_value}",
                    recovery_hint="ChEMBL ID not found. Verify the compound exists at www.ebi.ac.uk/chembl",
                    invalid_input=input_value,
                )
            )

        # 429 Rate Limited
        if "429" in error_str or "rate" in error_str:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.RATE_LIMITED,
                    message="ChEMBL API rate limit exceeded",
                    recovery_hint="ChEMBL API rate limit exceeded. Wait 60s before retrying",
                    invalid_input=input_value,
                )
            )

        # 500/502/503 Server Errors
        if any(code in error_str for code in ["500", "502", "503", "timeout"]):
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"ChEMBL API error: {error}",
                    recovery_hint="ChEMBL API temporarily unavailable. Retry in 60 seconds",
                    invalid_input=input_value,
                )
            )

        # Default: upstream error
        return ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"ChEMBL API error: {error}",
                recovery_hint="ChEMBL API error occurred. Check the input and try again",
                invalid_input=input_value,
            )
        )

    def _transform_to_search_candidate(
        self, sdk_result: dict[str, Any], index: int
    ) -> CompoundSearchCandidate:
        """Transform SDK search result to CompoundSearchCandidate.

        Args:
            sdk_result: Raw result from ChEMBL SDK
            index: Result index for score calculation

        Returns:
            CompoundSearchCandidate model
        """
        # Extract ChEMBL ID and format as CURIE
        # SDK returns "CHEMBL25" format, we need "CHEMBL:25" format
        raw_id = sdk_result.get("molecule_chembl_id", "")
        if raw_id and raw_id.startswith("CHEMBL"):
            # Convert "CHEMBL25" to "CHEMBL:25"
            numeric_part = raw_id[6:]  # Remove "CHEMBL" prefix
            curie = f"CHEMBL:{numeric_part}"
        else:
            curie = f"CHEMBL:UNKNOWN_{index}"

        # Get name (prefer pref_name, fallback to raw ChEMBL ID)
        name = sdk_result.get("pref_name") or raw_id

        # Get molecular formula from molecule_properties
        props = sdk_result.get("molecule_properties") or {}
        molecular_formula = props.get("molecular_formula")

        # Calculate relevance score (linear decay from 1.0)
        # First result = 1.0, decreasing by 0.05 per position, minimum 0.1
        score = max(0.1, 1.0 - (index * 0.05))

        return CompoundSearchCandidate(
            id=curie,
            name=name,
            molecular_formula=molecular_formula,
            score=score,
        )

    def _build_cross_references(self, sdk_result: dict[str, Any]) -> dict[str, list[str]]:
        """Build cross-references dict from ChEMBL SDK result.

        Maps ChEMBL's cross_references array to flat object using 22-key registry.
        Omits keys entirely if no cross-reference exists (Constitution Principle III).

        Args:
            sdk_result: Raw result from ChEMBL SDK

        Returns:
            Dict mapping registry keys to lists of CURIEs
        """
        xrefs: dict[str, list[str]] = {}

        # Add self-reference (SDK returns "CHEMBL25", we need "CHEMBL:25")
        raw_id = sdk_result.get("molecule_chembl_id")
        if raw_id and raw_id.startswith("CHEMBL"):
            numeric_part = raw_id[6:]  # Remove "CHEMBL" prefix
            xrefs["chembl"] = [f"CHEMBL:{numeric_part}"]

        # Process cross_references array
        raw_xrefs = sdk_result.get("cross_references") or []
        for xref in raw_xrefs:
            xref_name = xref.get("xref_name", "")
            xref_id = xref.get("xref_id", "")

            if not xref_name or not xref_id:
                continue

            # Map to our registry key
            registry_key = self.XREF_MAPPING.get(xref_name)
            if not registry_key:
                continue

            # Normalize CURIE format
            normalized_id = self._normalize_xref_id(registry_key, xref_id)

            # Add to cross-references (omit-if-null pattern)
            if registry_key not in xrefs:
                xrefs[registry_key] = []
            if normalized_id not in xrefs[registry_key]:
                xrefs[registry_key].append(normalized_id)

        return xrefs

    def _normalize_xref_id(self, registry_key: str, xref_id: str) -> str:
        """Normalize cross-reference ID to CURIE format.

        Args:
            registry_key: Our registry key (e.g., "uniprot", "drugbank")
            xref_id: Raw ID from ChEMBL

        Returns:
            Normalized CURIE string
        """
        if registry_key == "uniprot":
            # Add UniProtKB: prefix if not present
            if not xref_id.startswith("UniProtKB:"):
                return f"UniProtKB:{xref_id}"
            return xref_id

        if registry_key == "drugbank":
            # Normalize to DB:NNNNN format
            clean_id = xref_id.replace("DB", "").replace(":", "").strip()
            return f"DB:{clean_id.zfill(5)}"

        if registry_key == "pdb":
            # PDB IDs are uppercase, no prefix
            return xref_id.upper()

        # Default: return as-is
        return xref_id

    def _transform_to_compound(
        self,
        sdk_result: dict[str, Any],
        slim: bool = False,
        indications: list[str] | None = None,
    ) -> Compound:
        """Transform SDK result to Compound model.

        Args:
            sdk_result: Raw result from ChEMBL SDK
            slim: If True, exclude cross_references and synonyms
            indications: List of approved indications (Mesh headings)

        Returns:
            Compound model
        """
        # Extract ChEMBL ID and format as CURIE
        # SDK returns "CHEMBL25" format, we need "CHEMBL:25" format
        raw_id = sdk_result.get("molecule_chembl_id", "")
        if raw_id and raw_id.startswith("CHEMBL"):
            numeric_part = raw_id[6:]  # Remove "CHEMBL" prefix
            curie = f"CHEMBL:{numeric_part}"
        else:
            curie = f"CHEMBL:{raw_id}"

        # Get name
        name = sdk_result.get("pref_name")

        # Get molecule properties
        props = sdk_result.get("molecule_properties") or {}
        molecular_formula = props.get("molecular_formula")
        molecular_weight = props.get("full_mwt")
        if molecular_weight:
            try:
                molecular_weight = float(molecular_weight)
            except (ValueError, TypeError):
                molecular_weight = None

        # Get max_phase
        max_phase = sdk_result.get("max_phase")
        if max_phase is not None:
            try:
                max_phase = int(float(max_phase))
            except (ValueError, TypeError):
                max_phase = None

        # Get structure data
        structures = sdk_result.get("molecule_structures") or {}
        smiles = structures.get("canonical_smiles")
        inchi = structures.get("standard_inchi")

        # Get synonyms
        synonyms: list[str] = []
        if not slim:
            raw_synonyms = sdk_result.get("molecule_synonyms") or []
            for syn in raw_synonyms:
                syn_name = syn.get("molecule_synonym") if isinstance(syn, dict) else syn
                if syn_name and syn_name not in synonyms:
                    synonyms.append(syn_name)

        # Build cross-references (skip in slim mode)
        cross_references: dict[str, list[str]] = {}
        if not slim:
            cross_references = self._build_cross_references(sdk_result)

        return Compound(
            id=curie,
            name=name,
            molecular_formula=molecular_formula,
            molecular_weight=molecular_weight,
            smiles=smiles,
            inchi=inchi,
            canonical_name=None,  # ChEMBL doesn't provide canonical IUPAC names directly
            max_phase=max_phase,
            indications=indications or [],
            synonyms=synonyms,
            cross_references=cross_references,
        )

    def _encode_cursor(self, offset: int) -> str:
        """Encode pagination offset as cursor string."""
        data = json.dumps({"offset": offset})
        return base64.b64encode(data.encode()).decode()

    def _decode_cursor(self, cursor: str | None) -> int:
        """Decode cursor string to offset."""
        if not cursor:
            return 0
        try:
            data = json.loads(base64.b64decode(cursor).decode())
            return data.get("offset", 0)
        except Exception:
            return 0

    async def search_compounds(
        self,
        query: str,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope[CompoundSearchCandidate] | ErrorEnvelope:
        """Fuzzy search for compounds.

        Args:
            query: Search term (min 2 chars).
            slim: Return minimal fields (~20 tokens).
            cursor: Pagination cursor.
            page_size: Results per page (1-100).

        Returns:
            PaginationEnvelope with CompoundSearchCandidate items, or ErrorEnvelope.
        """
        # Validate query length (AMBIGUOUS_QUERY error)
        if len(query) < 2:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message=f"Query too short: '{query}'",
                    recovery_hint="Minimum query length is 2 characters",
                    invalid_input=query,
                )
            )

        # Clamp page_size to valid range
        page_size = max(1, min(100, page_size))

        # Decode pagination offset
        offset = self._decode_cursor(cursor)

        try:
            # Search using SDK (wrapped with rate limiting)
            def sdk_search() -> list[dict[str, Any]]:
                results = list(self._molecule.search(query))
                return results

            all_results: list[dict[str, Any]] = await self._sdk_call_with_backoff(sdk_search)

            # Apply pagination
            total_count = len(all_results)
            paginated = all_results[offset : offset + page_size]

            # Transform results to candidates
            candidates = [
                self._transform_to_search_candidate(result, i) for i, result in enumerate(paginated)
            ]

            # Calculate next cursor
            next_offset = offset + page_size
            next_cursor = self._encode_cursor(next_offset) if next_offset < total_count else None

            return PaginationEnvelope.create(
                items=candidates,
                cursor=next_cursor,
                total_count=total_count,
                page_size=page_size,
            )

        except Exception as e:
            return self._map_sdk_error(e, query)

    async def get_compound(
        self, chembl_id: str, slim: bool = False
    ) -> dict[str, Any] | ErrorEnvelope:
        """Get compound by ChEMBL CURIE.

        Args:
            chembl_id: ChEMBL CURIE (format: CHEMBL:NNNNN).
            slim: Return minimal fields for token efficiency.

        Returns:
            Compound dict with cross_references, or ErrorEnvelope.
        """
        # Validate CURIE format
        validation_result = self._validate_chembl_curie(chembl_id)
        if isinstance(validation_result, ErrorEnvelope):
            return validation_result

        numeric_id = validation_result
        # SDK expects "CHEMBL25" format, not just "25"
        sdk_id = f"CHEMBL{numeric_id}"

        try:
            # Fetch compound using SDK (wrapped with rate limiting)
            def sdk_get() -> dict[str, Any]:
                return self._molecule.get(sdk_id)

            sdk_result: dict[str, Any] = await self._sdk_call_with_backoff(sdk_get)

            if not sdk_result:
                return ErrorEnvelope(
                    error=ErrorDetail(
                        code=ErrorCode.ENTITY_NOT_FOUND,
                        message=f"ChEMBL compound not found: {chembl_id}",
                        recovery_hint="ChEMBL ID not found. Verify the compound exists at www.ebi.ac.uk/chembl",
                        invalid_input=chembl_id,
                    )
                )

            # Fetch indications if not slim (requires separate API call)
            indications: list[str] = []
            if not slim:
                try:
                    def sdk_get_indications() -> list[dict[str, Any]]:
                        return list(self._drug_indication.filter(molecule_chembl_id=sdk_id))

                    ind_results: list[dict[str, Any]] = await self._sdk_call_with_backoff(
                        sdk_get_indications
                    )
                    # Extract unique Mesh headings (filter None for type safety)
                    headings: set[str] = {
                        h for i in ind_results if (h := i.get("mesh_heading")) is not None
                    }
                    indications = sorted(headings)
                except Exception as e:
                    logger.warning(f"Failed to fetch indications for {chembl_id}: {e}")

            # Transform to Compound model
            compound = self._transform_to_compound(
                sdk_result, slim=slim, indications=indications
            )

            # Return as dict (slim mode returns minimal fields)
            if slim:
                return compound.to_slim()
            return compound.model_dump()

        except Exception as e:
            return self._map_sdk_error(e, chembl_id)

    async def get_compounds_batch(
        self, chembl_ids: list[str], slim: bool = True
    ) -> list[dict[str, Any]] | ErrorEnvelope:
        """Batch lookup for multiple compounds.

        Uses SDK's filter() for efficient single API call.

        Args:
            chembl_ids: List of ChEMBL CURIEs.
            slim: Return minimal fields (default True for batch).

        Returns:
            List of Compound dicts (or individual ErrorEnvelopes for failures).
        """
        if not chembl_ids:
            return []

        if len(chembl_ids) > 100:
            return ErrorEnvelope(
                error=ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_QUERY,
                    message="Batch size exceeds maximum of 100",
                    recovery_hint="Split request into batches of 100 or fewer compounds",
                    invalid_input=str(len(chembl_ids)),
                )
            )

        # Validate all CURIEs first
        sdk_ids: list[str] = []  # SDK expects "CHEMBL25" format
        results: list[dict[str, Any]] = []
        sdk_id_to_curie: dict[str, str] = {}

        for chembl_id in chembl_ids:
            validation_result = self._validate_chembl_curie(chembl_id)
            if isinstance(validation_result, ErrorEnvelope):
                # Add error to results list for this specific ID
                results.append(validation_result.model_dump())
            else:
                # Convert "25" to "CHEMBL25" for SDK
                sdk_id = f"CHEMBL{validation_result}"
                sdk_ids.append(sdk_id)
                sdk_id_to_curie[sdk_id] = chembl_id

        if not sdk_ids:
            # All IDs were invalid
            return results

        try:
            # Batch fetch using SDK filter (single API call)
            def sdk_batch_get() -> list[dict[str, Any]]:
                return list(self._molecule.filter(molecule_chembl_id__in=sdk_ids))

            sdk_results: list[dict[str, Any]] = await self._sdk_call_with_backoff(sdk_batch_get)

            # Map results by ChEMBL ID (SDK returns "CHEMBL25" format)
            results_by_id: dict[str, dict[str, Any]] = {}
            for sdk_result in sdk_results:
                mol_id = sdk_result.get("molecule_chembl_id", "")
                results_by_id[mol_id] = sdk_result

            # Build results list preserving order
            for sdk_id in sdk_ids:
                curie = sdk_id_to_curie[sdk_id]
                if sdk_id in results_by_id:
                    compound = self._transform_to_compound(results_by_id[sdk_id], slim=slim)
                    if slim:
                        results.append(compound.to_slim())
                    else:
                        results.append(compound.model_dump())
                else:
                    # Compound not found
                    results.append(
                        ErrorEnvelope(
                            error=ErrorDetail(
                                code=ErrorCode.ENTITY_NOT_FOUND,
                                message=f"ChEMBL compound not found: {curie}",
                                recovery_hint="ChEMBL ID not found. Verify CURIE from search_compounds results.",
                                invalid_input=curie,
                            )
                        ).model_dump()
                    )

            return results

        except Exception as e:
            return self._map_sdk_error(e, str(chembl_ids))

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        await super().close()
        if self._executor is not None:
            self._executor.shutdown(wait=False)
            self._executor = None
