"""ClinicalTrials.gov API client.

This module provides an async HTTP client for the ClinicalTrials.gov API v2.
Supports searching clinical trials and retrieving detailed trial information.

API Documentation: https://clinicaltrials.gov/api/v2/reference
Rate Limiting: Conservative 1 req/sec with exponential backoff
"""

import asyncio
import re
from typing import Any

import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models import (
    ErrorDetail,
    ErrorEnvelope,
    PaginationEnvelope,
    Trial,
    TrialLocation,
    TrialSearchCandidate,
)
from lifesciences_mcp.models.envelopes import ErrorCode


class ClinicalTrialsClient(LifeSciencesClient):
    """ClinicalTrials.gov API client.

    Provides access to clinical trial data including:
    - Trial search by condition, intervention, sponsor
    - Detailed trial protocol information
    - Study design and outcome measures
    - Facility locations and contact information

    Rate Limiting: 1 req/sec with exponential backoff (conservative, API allows ~50 req/min)
    Authentication: None required (public API)
    """

    CLINICALTRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2"

    # NCT ID format: NCT:NNNNNNNN (8 digits with colon)
    NCT_ID_PATTERN = re.compile(r"^NCT:\d{8}$")

    # Rate limiting: 1 req/sec (conservative)
    _last_request_time: float = 0.0
    _request_lock = asyncio.Lock()

    def __init__(self) -> None:
        """Initialize the ClinicalTrials client."""
        super().__init__(base_url=self.CLINICALTRIALS_BASE_URL)

    @staticmethod
    def validate_nct_id(nct_id: str) -> bool:
        """Validate NCT CURIE format.

        Args:
            nct_id: NCT identifier (e.g., "NCT:00461032")

        Returns:
            True if valid format, False otherwise
        """
        return bool(ClinicalTrialsClient.NCT_ID_PATTERN.match(nct_id))

    @staticmethod
    def normalize_nct_id(nct_id: str) -> str:
        """Normalize NCT ID to CURIE format.

        Args:
            nct_id: NCT identifier in various formats (e.g., "NCT00461032" or "NCT:00461032")

        Returns:
            Normalized NCT CURIE (e.g., "NCT:00461032")

        Raises:
            ValueError: If input cannot be normalized to valid format
        """
        # Remove whitespace
        nct_id = nct_id.strip()

        # If already in CURIE format, validate and return
        if ":" in nct_id:
            if not ClinicalTrialsClient.validate_nct_id(nct_id):
                raise ValueError(f"Invalid NCT CURIE format: {nct_id}")
            return nct_id

        # Convert NCT########  to NCT:########
        if nct_id.upper().startswith("NCT") and len(nct_id) == 11:
            curie = f"NCT:{nct_id[3:]}"
            if not ClinicalTrialsClient.validate_nct_id(curie):
                raise ValueError(f"Invalid NCT ID format: {nct_id}")
            return curie

        raise ValueError(
            f"Cannot normalize NCT ID '{nct_id}'. Expected format: 'NCT00461032' or 'NCT:00461032'"
        )

    async def _rate_limited_request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Make a rate-limited HTTP request.

        Implements 1 req/sec rate limiting with exponential backoff.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional httpx request parameters

        Returns:
            HTTP response

        Raises:
            httpx.HTTPStatusError: For HTTP errors after retries
        """
        async with self._request_lock:
            # Enforce 1 req/sec rate limit
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < 1.0:
                await asyncio.sleep(1.0 - time_since_last)

            # Get httpx client from base class
            client = await self._get_client()

            # Make request with exponential backoff on 429
            max_retries = 3
            for attempt in range(max_retries):
                response = await client.request(method, url, **kwargs)

                # Update last request time
                self._last_request_time = asyncio.get_event_loop().time()

                if response.status_code != 429:  # Not rate limited
                    return response

                # Exponential backoff on 429
                if attempt < max_retries - 1:
                    backoff_time = 2**attempt  # 1s, 2s, 4s
                    await asyncio.sleep(backoff_time)

            # Return last response (will be raised by caller if error)
            return response

    def _map_http_error(self, e: httpx.HTTPStatusError, context: str = "") -> ErrorEnvelope:
        """Map HTTP status codes to ErrorEnvelope.

        Args:
            e: HTTP status error
            context: Additional context for error message

        Returns:
            ErrorEnvelope with appropriate error code and recovery hint
        """
        status_code = e.response.status_code

        if status_code == 404:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message=f"Clinical trial not found. {context}",
                    recovery_hint="Verify the NCT ID is correct or search for trials using search_trials.",
                    invalid_input=context,
                ),
            )
        elif status_code == 429:
            retry_after = e.response.headers.get("Retry-After")
            hint = (
                f"Retry after {retry_after} seconds."
                if retry_after
                else "Retry after a few seconds."
            )
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.RATE_LIMITED,
                    message="ClinicalTrials.gov API rate limit exceeded.",
                    recovery_hint=hint,
                ),
            )
        elif status_code >= 500:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"ClinicalTrials.gov API returned error {status_code}.",
                    recovery_hint="ClinicalTrials.gov API may be temporarily unavailable. Retry later.",
                ),
            )
        else:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Unexpected HTTP error {status_code}: {e.response.text}",
                    recovery_hint="Check input parameters or retry later.",
                ),
            )

    async def search_trials(
        self,
        query: str,
        status: str | None = None,
        phase: str | None = None,
        condition: str | None = None,
        intervention: str | None = None,
        location: str | None = None,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope | ErrorEnvelope:
        """Fuzzy search for clinical trials.

        Args:
            query: Search term (natural language query or specific terms)
            status: Filter by recruitment status (RECRUITING, COMPLETED, etc.)
            phase: Filter by trial phase (PHASE1, PHASE2, PHASE3, PHASE4)
            condition: Filter by condition/disease name
            intervention: Filter by intervention/treatment name
            location: Filter by geographic location (city, state, or country)
            slim: If true, return minimal fields for token efficiency (default: False)
            cursor: Pagination cursor (opaque token from previous response)
            page_size: Results per page (1-200, default: 50)

        Returns:
            PaginationEnvelope with TrialSearchCandidate items or ErrorEnvelope on failure
        """
        # Build query parameters
        params: dict[str, Any] = {
            "query.term": query,
            "pageSize": min(page_size, 200),  # Cap at 200
            "countTotal": "true",
            "format": "json",
        }

        # Add filters
        if status:
            params["filter.overallStatus"] = status.upper().replace(" ", "_")
        if phase:
            params["filter.advanced"] = f"AREA[Phase]{phase}"
        if condition:
            params["query.cond"] = condition
        if intervention:
            params["query.intr"] = intervention
        if location:
            params["query.locn"] = location
        if cursor:
            params["pageToken"] = cursor

        # Field selection for token optimization
        if slim:
            # Minimal fields for slim mode (~100 tokens/candidate)
            params["fields"] = (
                "NCTId,BriefTitle,BriefSummary,Phase,OverallStatus,Condition,InterventionName"
            )
        else:
            # Default fields for search candidates (~200 tokens/candidate)
            params["fields"] = (
                "NCTId,OfficialTitle,BriefSummary,Phase,OverallStatus,Condition,InterventionName"
            )

        try:
            response = await self._rate_limited_request("GET", "/studies", params=params)
            response.raise_for_status()
            data = response.json()

            # Parse trials into TrialSearchCandidate
            trials = []
            for study in data.get("studies", []):
                protocol = study.get("protocolSection", {})
                ident = protocol.get("identificationModule", {})
                status_module = protocol.get("statusModule", {})
                conditions_module = protocol.get("conditionsModule", {})
                arms_module = protocol.get("armsInterventionsModule", {})

                # Extract NCT ID and normalize to CURIE
                nct_id = ident.get("nctId", "")
                if not nct_id:
                    continue  # Skip trials without NCT ID

                try:
                    nct_curie = self.normalize_nct_id(nct_id)
                except ValueError:
                    continue  # Skip invalid NCT IDs

                # Build TrialSearchCandidate
                candidate = TrialSearchCandidate(
                    id=nct_curie,
                    title=ident.get("officialTitle") or ident.get("briefTitle", ""),
                    brief_summary=ident.get("briefSummary", ""),
                    phase=status_module.get("phase"),
                    status=status_module.get("overallStatus", "UNKNOWN"),
                    conditions=conditions_module.get("conditions", []),
                    interventions=[i.get("name", "") for i in arms_module.get("interventions", [])],
                )
                trials.append(candidate)

            # Build pagination envelope
            return PaginationEnvelope.create(
                items=trials,
                cursor=data.get("nextPageToken"),
                total_count=data.get("totalCount"),
                page_size=page_size,
            )

        except httpx.HTTPStatusError as e:
            return self._map_http_error(e, f"query='{query}'")
        except Exception as e:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Unexpected error: {e!s}",
                    recovery_hint="Check input parameters or retry later.",
                ),
            )

    async def get_trial(self, nct_id: str) -> Trial | ErrorEnvelope:
        """Get complete trial record by NCT CURIE.

        Args:
            nct_id: NCT CURIE in format 'NCT:NNNNNNNN' (e.g., 'NCT:00461032')

        Returns:
            Trial record with full protocol details or ErrorEnvelope on failure
        """
        # Validate NCT ID format
        if not self.validate_nct_id(nct_id):
            # Check if it's a raw string query (Fuzzy-to-Fact violation)
            if not nct_id.startswith("NCT:"):
                return ErrorEnvelope(
                    success=False,
                    error=ErrorDetail(
                        code=ErrorCode.UNRESOLVED_ENTITY,
                        message=f"The input '{nct_id}' is not a valid NCT CURIE.",
                        recovery_hint="Call search_trials to resolve the identifier first, then use the returned NCT CURIE.",
                        invalid_input=nct_id,
                    ),
                )
            else:
                return ErrorEnvelope(
                    success=False,
                    error=ErrorDetail(
                        code=ErrorCode.UNRESOLVED_ENTITY,  # Malformed CURIE treated as unresolved
                        message=f"Invalid NCT CURIE format: '{nct_id}'. Expected format: NCT:NNNNNNNN (8 digits).",
                        recovery_hint="Verify the NCT ID format. Example: NCT:00461032",
                        invalid_input=nct_id,
                    ),
                )

        # Convert CURIE to API format (NCT:00461032 → NCT00461032)
        nct_number = nct_id.replace(":", "")

        try:
            response = await self._rate_limited_request(
                "GET", f"/studies/{nct_number}", params={"format": "json"}
            )
            response.raise_for_status()
            study = response.json()

            # Parse full trial data from protocolSection
            protocol_section = study.get("protocolSection", {})

            # Extract modules
            ident_module = protocol_section.get("identificationModule", {})
            status_module = protocol_section.get("statusModule", {})
            design_module = protocol_section.get("designModule", {})
            eligibility_module = protocol_section.get("eligibilityModule", {})
            outcomes_module = protocol_section.get("outcomesModule", {})
            sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
            conditions_module = protocol_section.get("conditionsModule", {})
            arms_module = protocol_section.get("armsInterventionsModule", {})
            references_module = protocol_section.get("referencesModule", {})

            # Build Trial object
            from lifesciences_mcp.models.trial import (
                EligibilityCriteria,
                Outcome,
                Sponsor,
                TrialProtocol,
            )

            # Parse protocol details
            design_info = design_module.get("designInfo", {})
            protocol = TrialProtocol(
                study_type=design_module.get("studyType", "UNKNOWN"),
                allocation=design_info.get("allocation"),
                intervention_model=design_info.get("interventionModel"),
                masking=design_info.get("maskingInfo", {}).get("masking"),
                primary_purpose=design_info.get("primaryPurpose"),
            )

            # Parse eligibility criteria
            eligibility = None
            if eligibility_module:
                eligibility = EligibilityCriteria(
                    criteria_text=eligibility_module.get("eligibilityCriteria"),
                    minimum_age=eligibility_module.get("minimumAge"),
                    maximum_age=eligibility_module.get("maximumAge"),
                    sex=eligibility_module.get("sex"),
                    accepts_healthy_volunteers=eligibility_module.get("healthyVolunteers", "No")
                    == "Yes",
                )

            # Parse outcomes
            primary_outcomes = []
            for outcome in outcomes_module.get("primaryOutcomes", []):
                primary_outcomes.append(
                    Outcome(
                        measure=outcome.get("measure", ""),
                        time_frame=outcome.get("timeFrame"),
                        description=outcome.get("description"),
                    )
                )

            secondary_outcomes = []
            for outcome in outcomes_module.get("secondaryOutcomes", []):
                secondary_outcomes.append(
                    Outcome(
                        measure=outcome.get("measure", ""),
                        time_frame=outcome.get("timeFrame"),
                        description=outcome.get("description"),
                    )
                )

            # Parse sponsors
            sponsors = []
            lead_sponsor = sponsor_module.get("leadSponsor", {})
            if lead_sponsor:
                sponsors.append(
                    Sponsor(
                        name=lead_sponsor.get("name", ""),
                        role="LEAD_SPONSOR",
                    )
                )
            for collab in sponsor_module.get("collaborators", []):
                sponsors.append(
                    Sponsor(
                        name=collab.get("name", ""),
                        role="COLLABORATOR",
                    )
                )

            # Parse cross-references (omit-if-null pattern)
            cross_refs = {}

            # PubMed IDs from references
            pubmed_ids = []
            for ref in references_module.get("references", []):
                pmid = ref.get("pmid")
                if pmid:
                    pubmed_ids.append(pmid)
            if pubmed_ids:
                cross_refs["pubmed"] = ",".join(pubmed_ids)

            # ClinicalTrials.gov registry link
            cross_refs["clinicaltrials_gov"] = f"https://clinicaltrials.gov/study/{nct_number}"

            # MeSH condition IDs (if available in derived section)
            derived_section = study.get("derivedSection", {})
            condition_browse = derived_section.get("conditionBrowseModule", {})
            mesh_conditions = []
            for mesh in condition_browse.get("meshes", []):
                mesh_id = mesh.get("id")
                if mesh_id:
                    mesh_conditions.append(mesh_id)
            if mesh_conditions:
                cross_refs["mesh_conditions"] = ",".join(mesh_conditions)

            # MeSH intervention IDs
            intervention_browse = derived_section.get("interventionBrowseModule", {})
            mesh_interventions = []
            for mesh in intervention_browse.get("meshes", []):
                mesh_id = mesh.get("id")
                if mesh_id:
                    mesh_interventions.append(mesh_id)
            if mesh_interventions:
                cross_refs["mesh_interventions"] = ",".join(mesh_interventions)

            # Build Trial object
            trial = Trial(
                id=nct_id,
                title=ident_module.get("officialTitle") or ident_module.get("briefTitle", ""),
                brief_summary=ident_module.get("briefSummary", ""),
                detailed_description=ident_module.get("detailedDescription"),
                protocol=protocol,
                eligibility_criteria=eligibility,
                primary_outcomes=primary_outcomes,
                secondary_outcomes=secondary_outcomes,
                sponsors=sponsors,
                phase=status_module.get("phase"),
                status=status_module.get("overallStatus", "UNKNOWN"),
                enrollment=status_module.get("enrollmentInfo", {}).get("count"),
                start_date=status_module.get("startDateStruct", {}).get("date"),
                completion_date=status_module.get("primaryCompletionDateStruct", {}).get("date"),
                last_update_date=status_module.get("lastUpdateSubmitDate"),
                conditions=conditions_module.get("conditions", []),
                interventions=[i.get("name", "") for i in arms_module.get("interventions", [])],
                cross_references=cross_refs,
            )

            return trial

        except httpx.HTTPStatusError as e:
            return self._map_http_error(e, nct_id)
        except Exception as e:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Unexpected error parsing trial data: {e!s}",
                    recovery_hint="The trial data may be malformed. Try another trial or report this issue.",
                ),
            )

    async def get_trial_locations(self, nct_id: str) -> list[TrialLocation] | ErrorEnvelope:
        """Get trial facility locations and contact information.

        Args:
            nct_id: NCT CURIE in format 'NCT:NNNNNNNN' (e.g., 'NCT:00461032')

        Returns:
            List of TrialLocation objects or ErrorEnvelope on failure
        """
        # Validate NCT ID format
        if not self.validate_nct_id(nct_id):
            if not nct_id.startswith("NCT:"):
                return ErrorEnvelope(
                    success=False,
                    error=ErrorDetail(
                        code=ErrorCode.UNRESOLVED_ENTITY,
                        message=f"The input '{nct_id}' is not a valid NCT CURIE.",
                        recovery_hint="Call search_trials to resolve the identifier first, then use the returned NCT CURIE.",
                        invalid_input=nct_id,
                    ),
                )
            else:
                return ErrorEnvelope(
                    success=False,
                    error=ErrorDetail(
                        code=ErrorCode.UNRESOLVED_ENTITY,  # Malformed CURIE treated as unresolved
                        message=f"Invalid NCT CURIE format: '{nct_id}'. Expected format: NCT:NNNNNNNN (8 digits).",
                        recovery_hint="Verify the NCT ID format. Example: NCT:00461032",
                        invalid_input=nct_id,
                    ),
                )

        # Convert CURIE to API format
        nct_number = nct_id.replace(":", "")

        try:
            # Request only location-related fields for token optimization
            response = await self._rate_limited_request(
                "GET",
                f"/studies/{nct_number}",
                params={
                    "format": "json",
                    "fields": "ContactsLocationsModule",
                },
            )
            response.raise_for_status()
            study = response.json()

            # Parse location data from contactsLocationsModule
            protocol_section = study.get("protocolSection", {})
            contacts_locations = protocol_section.get("contactsLocationsModule", {})

            locations = []
            for location in contacts_locations.get("locations", []):
                facility = location.get("facility", "")
                city = location.get("city", "")
                country = location.get("country", "")

                # State is optional (only for US/Canada)
                state = location.get("state")

                # Postal code is optional
                zip_code = location.get("zip")

                # Contact information (first contact if multiple)
                contacts = location.get("contacts", [])
                contact_name = None
                contact_phone = None
                contact_email = None

                if contacts:
                    first_contact = contacts[0]
                    contact_name = first_contact.get("name")
                    contact_phone = first_contact.get("phone")
                    contact_email = first_contact.get("email")

                # Recruitment status
                recruitment_status = location.get("status", "UNKNOWN")

                # Build TrialLocation object
                trial_location = TrialLocation(
                    facility_name=facility,
                    city=city,
                    state=state,
                    country=country,
                    zip=zip_code,
                    contact_name=contact_name,
                    contact_phone=contact_phone,
                    contact_email=contact_email,
                    recruitment_status=recruitment_status,
                )
                locations.append(trial_location)

            return locations

        except httpx.HTTPStatusError as e:
            return self._map_http_error(e, nct_id)
        except Exception as e:
            return ErrorEnvelope(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Unexpected error parsing location data for {nct_id}: {e!s}",
                    recovery_hint="The location data may be malformed. Try another trial or report this issue.",
                ),
            )
