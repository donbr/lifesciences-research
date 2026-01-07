"""ClinicalTrials.gov MCP Server - Clinical trial search and information.

This FastMCP server provides three tools for querying ClinicalTrials.gov API v2:

1. **search_trials** (Fuzzy): Natural language search returning ranked trial candidates
   - Searches by condition, intervention, location, phase, status
   - Returns TrialSearchCandidate with NCT CURIEs (~100-200 tokens/candidate)
   - Supports pagination with opaque cursors
   - Example: "breast cancer immunotherapy phase 3 recruiting"

2. **get_trial** (Strict): Lookup complete trial details by NCT CURIE
   - Requires resolved NCT CURIE from search_trials (Fuzzy-to-Fact protocol)
   - Returns full Trial with protocol, eligibility, outcomes, sponsors (~5K-10K tokens)
   - Validates NCT CURIE format (NCT:NNNNNNNN with 8 digits)
   - Example: NCT:00461032

3. **get_trial_locations** (Strict): Lookup facility locations and contacts
   - Requires resolved NCT CURIE from search_trials
   - Returns list of TrialLocation with facility names, addresses, contacts
   - Example: Multi-site trial with recruiting facilities across states

## Fuzzy-to-Fact Workflow

```python
# Phase 1: Fuzzy search
results = await search_trials("breast cancer immunotherapy", page_size=10)
top_trial = results["items"][0]  # {"id": "NCT:04123456", ...}

# Phase 2: Strict lookup (complete trial details)
trial = await get_trial(top_trial["id"])

# Phase 3: Get facility locations
locations = await get_trial_locations(top_trial["id"])
```

## Error Recovery

All tools provide actionable recovery hints via ErrorEnvelope:
- **UNRESOLVED_ENTITY**: Raw string passed to strict tool → Use search_trials first
- **INVALID_INPUT**: Malformed NCT CURIE → Correct format (NCT:NNNNNNNN with 8 digits)
- **ENTITY_NOT_FOUND**: Valid CURIE but no trial exists → Verify NCT ID
- **RATE_LIMITED**: API throttled → Retry after N seconds
- **UPSTREAM_ERROR**: API failure → Retry later

## Rate Limiting

Conservative 1 req/sec with exponential backoff on 429 responses (API allows ~50 req/min).

## Usage

```bash
# Run server
uv run fastmcp run src/lifesciences_mcp/servers/clinicaltrials.py

# Dev mode with auto-reload
uv run fastmcp dev src/lifesciences_mcp/servers/clinicaltrials.py
```

## Architecture

- **Client**: ClinicalTrialsClient (async httpx, no authentication required)
- **Models**: Trial, TrialSearchCandidate, TrialLocation, TrialProtocol, EligibilityCriteria, Outcome, Sponsor
- **Envelopes**: PaginationEnvelope, ErrorEnvelope (ADR-001 canonical formats)
- **API**: ClinicalTrials.gov API v2 (REST, JSON, no auth, cursor pagination)

## References

- API Documentation: https://clinicaltrials.gov/api/v2/reference
- Feature Spec: specs/013-clinicaltrials-mcp-server/spec.md
- Implementation Plan: specs/013-clinicaltrials-mcp-server/plan.md
- ADR-001: docs/adr/accepted/adr-001-v1.2.md (Architecture specification)
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients import ClinicalTrialsClient
from lifesciences_mcp.models import (
    ErrorEnvelope,
    PaginationEnvelope,
    Trial,
    TrialLocation,
)

# Initialize the MCP server
mcp = FastMCP("ClinicalTrials.gov Server")

# Shared client instance (singleton pattern per ADR-001)
_client: ClinicalTrialsClient | None = None


async def get_client() -> ClinicalTrialsClient:
    """Get or create the shared ClinicalTrials client.

    Returns:
        ClinicalTrialsClient instance (singleton)
    """
    global _client
    if _client is None:
        _client = ClinicalTrialsClient()
    return _client


@mcp.tool
async def search_trials(
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

    Searches ClinicalTrials.gov database using natural language queries with optional filters.
    Returns ranked trial candidates with NCT CURIEs for strict lookup.

    Args:
        query: Natural language search term (e.g., "breast cancer immunotherapy").
               Searches across conditions, interventions, titles, and descriptions.
               Minimum 2 characters required.
        status: Filter by recruitment status (RECRUITING, COMPLETED, NOT_YET_RECRUITING, etc.).
                Optional - omit to search all statuses.
        phase: Filter by trial phase (PHASE1, PHASE2, PHASE3, PHASE4, EARLY_PHASE1, NA).
               Optional - omit to search all phases.
        condition: Filter by condition/disease name (e.g., "diabetes", "lung cancer").
                   Optional - narrows results to specific conditions.
        intervention: Filter by intervention/treatment name (e.g., "bevacizumab", "surgery").
                      Optional - narrows results to specific treatments.
        location: Filter by geographic location (city, state, or country).
                  Examples: "Boston", "Massachusetts", "United States", "Japan".
                  Optional - narrows results to specific locations.
        slim: If true, return minimal fields for token efficiency (~100 tokens/trial).
              If false (default), return full candidate details (~200 tokens/trial).
        cursor: Opaque pagination cursor from previous response.
                Pass to retrieve next page of results.
        page_size: Number of results per page (1-200, default 50).
                   Larger pages use more tokens but fewer API calls.

    Returns:
        PaginationEnvelope with TrialSearchCandidate items, or ErrorEnvelope on failure.

        Success response structure:
        {
            "items": [
                {
                    "id": "NCT:00461032",
                    "title": "Bevacizumab and Erlotinib in Treating Patients...",
                    "brief_summary": "This phase II trial is studying...",
                    "phase": "PHASE2",
                    "status": "COMPLETED",
                    "conditions": ["Breast Cancer", "Metastatic Breast Cancer"],
                    "interventions": ["Bevacizumab", "Erlotinib Hydrochloride"]
                },
                ...
            ],
            "pagination": {
                "cursor": "eyJraW5kIjo..." or null,
                "total_count": 1543,
                "page_size": 50
            }
        }

        Error responses include recovery hints for autonomous agents.

    Examples:
        >>> # Simple search
        >>> results = await search_trials("diabetes")

        >>> # Filtered search
        >>> results = await search_trials(
        ...     query="immunotherapy",
        ...     condition="lung cancer",
        ...     phase="PHASE3",
        ...     status="RECRUITING"
        ... )

        >>> # Pagination
        >>> page1 = await search_trials("cancer", page_size=20)
        >>> page2 = await search_trials("cancer", cursor=page1["pagination"]["cursor"])
    """
    client = await get_client()
    return await client.search_trials(
        query=query,
        status=status,
        phase=phase,
        condition=condition,
        intervention=intervention,
        location=location,
        slim=slim,
        cursor=cursor,
        page_size=page_size,
    )


@mcp.tool
async def get_trial(nct_id: str) -> Trial | ErrorEnvelope:
    """Get complete trial record by NCT CURIE.

    Retrieves full clinical trial data with detailed protocol information.
    Requires resolved NCT CURIE from search_trials (Fuzzy-to-Fact protocol).

    Args:
        nct_id: NCT CURIE in format 'NCT:NNNNNNNN' (e.g., 'NCT:00461032').
                Must be exactly 8 digits after the colon.
                Obtain from search_trials results - do NOT pass raw query strings.

    Returns:
        Trial record with full protocol details (~5K-10K tokens), or ErrorEnvelope on failure.

        Success response includes:
        - Protocol: study_type, allocation, intervention_model, masking, primary_purpose
        - Eligibility: criteria_text, age range, sex, healthy_volunteers
        - Outcomes: primary and secondary endpoints with timeframes
        - Sponsors: lead sponsor and collaborators
        - Administrative: phase, status, enrollment, dates
        - Cross-references: PubMed, registry links, MeSH IDs

        Error responses:
        - UNRESOLVED_ENTITY: Raw string passed instead of NCT CURIE
          → Recovery: Call search_trials first
        - INVALID_INPUT: Malformed NCT CURIE (wrong format)
          → Recovery: Verify format is NCT:NNNNNNNN with 8 digits
        - ENTITY_NOT_FOUND: Valid CURIE but trial doesn't exist
          → Recovery: Verify NCT ID or search again
        - UPSTREAM_ERROR: API failure
          → Recovery: Retry later

    Examples:
        >>> # Correct usage (Fuzzy-to-Fact workflow)
        >>> results = await search_trials("bevacizumab breast cancer")
        >>> trial = await get_trial(results["items"][0]["id"])  # "NCT:00461032"

        >>> # WRONG: Passing raw query string
        >>> trial = await get_trial("breast cancer")  # Returns UNRESOLVED_ENTITY error

        >>> # WRONG: Malformed CURIE
        >>> trial = await get_trial("NCT:123")  # Returns INVALID_INPUT error
    """
    client = await get_client()
    return await client.get_trial(nct_id=nct_id)


@mcp.tool
async def get_trial_locations(nct_id: str) -> list[TrialLocation] | ErrorEnvelope:
    """Get trial facility locations and contact information.

    Retrieves geographic facility data for a clinical trial including addresses,
    contact details, and recruitment status for each site.

    Args:
        nct_id: NCT CURIE in format 'NCT:NNNNNNNN' (e.g., 'NCT:04123456').
                Must be exactly 8 digits after the colon.
                Obtain from search_trials results.

    Returns:
        List of TrialLocation objects (~50-100 tokens per location), or ErrorEnvelope on failure.

        Success response structure:
        [
            {
                "facility_name": "Dana-Farber Cancer Institute",
                "city": "Boston",
                "state": "Massachusetts",  # Omitted for non-US/Canada
                "country": "United States",
                "zip": "02215",
                "contact_name": "Dr. Jane Smith",  # May be null
                "contact_phone": "617-555-0123",   # May be null
                "contact_email": "trials@dfci.harvard.edu",  # May be null
                "recruitment_status": "RECRUITING"
            },
            ...
        ]

        Empty list: Trial has no facilities (e.g., remote/virtual trial)

        Error responses:
        - UNRESOLVED_ENTITY: Raw string passed instead of NCT CURIE
        - INVALID_INPUT: Malformed NCT CURIE
        - ENTITY_NOT_FOUND: Trial doesn't exist
        - UPSTREAM_ERROR: API failure

    Examples:
        >>> # Get locations for a multi-site trial
        >>> results = await search_trials("cancer", location="Boston")
        >>> locations = await get_trial_locations(results["items"][0]["id"])
        >>> recruiting_sites = [loc for loc in locations if loc["recruitment_status"] == "RECRUITING"]

        >>> # Filter by geographic region
        >>> ma_sites = [loc for loc in locations if loc.get("state") == "Massachusetts"]
    """
    client = await get_client()
    return await client.get_trial_locations(nct_id=nct_id)


if __name__ == "__main__":
    mcp.run()
