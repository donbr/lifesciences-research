# DrugBank MCP Server - Constitution Compliance Audit

**Date:** 2026-02-06
**Status:** ⚠️ BLOCKED (API key required)
**Auditor:** Claude Agent 5 (Read-Only Audit)
**Reference Implementation:** BioGRID MCP Server

---

## Executive Summary

The DrugBank MCP server implementation demonstrates **FULL COMPLIANCE** with all six Constitution Principles. The client makes real API calls in the search method (Principle II), implements token budgeting with `slim` parameter (Principle IV), uses async-first architecture (Principle I), enforces schema determinism (Principle III), has proper rate limiting (Principle V), and maintains comprehensive spec artifacts (Principle VI).

**Note:** DrugBank requires a commercial API key (`DRUGBANK_API_KEY`) for production use. Implementation is complete but integration testing is blocked.

---

## Compliance Summary

| Check | Status | Notes |
|-------|--------|-------|
| ✅ **Principle II: Fuzzy-to-Fact** | **PASS** | Real API call at line 663 with error handling |
| ✅ **Principle IV: Token Budgeting** | **PASS** | `slim` param + `to_slim_dict()` method |
| ✅ **Principle I: Async-First** | **PASS** | All methods async, proper lock usage |
| ✅ **Principle III: Schema Determinism** | **PASS** | Pydantic models with validators |
| ✅ **Principle V: Rate Limiting** | **PASS** | `_rate_limited_get()` with exponential backoff |
| ✅ **Principle VI: Spec Artifacts** | **PASS** | 11 artifacts in `specs/005-drugbank-mcp-server/` |

---

## Critical Findings

### ✅ CHECK 1: Principle II — Fuzzy-to-Fact Protocol (PASS)

**Requirement:** Search method MUST call API to confirm entity exists. Returns `ENTITY_NOT_FOUND` when not found.

**Evidence:**

**File:** `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/drugbank.py`

**Lines 651-677:** Real API call in `search_drugs()` method
```python
try:
    # Build search URL based on API mode
    base_url = self._select_base_url()
    if self._api_key:
        # Commercial API
        search_url = f"{base_url}/drugs"
        params = {"q": query, "page": page, "per_page": page_size}
    else:
        # Public search endpoint
        search_url = f"{base_url}/unearth/q"
        params = {"query": query}

    response = await self._rate_limited_get(search_url, params)  # ← REAL API CALL

    # Check for errors
    error = self._handle_response_error(response)
    if error:
        return error

    # Parse response
    drugs = self._parse_search_response(response)
    if drugs is None:
        return self._create_error(
            ErrorCode.UPSTREAM_ERROR,
            "Failed to parse DrugBank search response.",
            "DrugBank API returned unexpected format. Retry later.",
        )
```

**Lines 293-299:** Proper `ENTITY_NOT_FOUND` handling
```python
if response.status_code == 404:
    return self._create_error(
        ErrorCode.ENTITY_NOT_FOUND,
        f"Drug not found in DrugBank database. {context}",
        "Verify the DrugBank ID at go.drugbank.com or use search_drugs to find alternatives.",
        context,
    )
```

**Analysis:**
- ✅ Line 663 makes real HTTP request via `_rate_limited_get()`
- ✅ Lines 666-668 check for API errors (404, 429, 5xx)
- ✅ Lines 293-299 return `ENTITY_NOT_FOUND` with recovery hints
- ✅ Lines 679-680 transform API results to candidates with scores
- ✅ No client-side only validation (unlike early HGNC implementation)

**Comparison to BioGRID (Reference):**

BioGRID uses `format=count` for lightweight existence check:
```python
params = {
    "geneList": symbol,
    "taxId": organism,
    "searchNames": "true",
    "format": "count",  # Returns integer count (~200ms)
}
response = await self._rate_limited_get(url, params)
```

DrugBank uses full search endpoint:
```python
if self._api_key:
    search_url = f"{base_url}/drugs"
    params = {"q": query, "page": page, "per_page": page_size}
else:
    search_url = f"{base_url}/unearth/q"
    params = {"query": query}
```

Both approaches are **Constitution-compliant** — the key requirement is making a real API call, not the specific endpoint used.

**Verdict:** ✅ **PASS** — Full Fuzzy-to-Fact compliance with real API verification.

---

### ✅ CHECK 2: Principle IV — Token Budgeting (PASS)

**Requirement:** Methods expose `slim: bool` param. Models have `to_slim()` method. Server exposes `slim` in tool signature.

**Evidence:**

**File:** `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/models/drug.py`

**Lines 210-220:** `to_slim_dict()` method on `Drug` model
```python
def to_slim_dict(self) -> dict:
    """Return slim mode representation (~20 tokens)."""
    result = {
        "id": self.id,
        "name": self.name,
    }
    if self.drug_type:
        result["drug_type"] = self.drug_type
    if self.categories:
        result["categories"] = self.categories
    return result
```

**Lines 132-138:** Token budget documented in docstring
```python
class Drug(BaseModel):
    """Complete DrugBank drug record with Agentic Biolink cross-references.

    Token Budget: ~115-300 tokens in full mode, ~20 tokens in slim mode

    Used in Phase 2 (Fact) of the Fuzzy-to-Fact protocol.
    """
```

**File:** `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/drugbank.py`

**Lines 618-624:** `slim` parameter in client method signature
```python
async def search_drugs(
    self,
    query: str,
    slim: bool = False,  # ← Token budgeting parameter
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
```

**Lines 583-612:** `slim` parameter in `_transform_drug()` method
```python
def _transform_drug(self, data: dict, drugbank_id: str, slim: bool = False) -> dict | Drug:
    """Transform API response to Drug model (T028).

    Args:
        data: Raw drug data from API.
        drugbank_id: The DrugBank CURIE.
        slim: If True, return minimal fields.

    Returns:
        Drug model or slim dict.
    """
    drug = Drug(
        id=drugbank_id,
        name=data.get("name", "Unknown"),
        drug_type=data.get("type", data.get("drug_type")),
        categories=data.get("categories", data.get("groups")),
        description=data.get("description"),
        indication=data.get("indication"),
        mechanism_of_action=data.get("mechanism_of_action"),
        pharmacodynamics=data.get("pharmacodynamics"),
        absorption=data.get("absorption"),
        metabolism=data.get("metabolism"),
        half_life=data.get("half_life"),
        cross_references=self._build_cross_references(data, drugbank_id),
    )

    if slim:
        return drug.to_slim_dict()  # ← Uses model method

    return drug
```

**File:** `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/servers/drugbank.py`

**Lines 34-62:** Server exposes `slim` parameter in both tools
```python
@mcp.tool
async def search_drugs(
    query: str,
    slim: bool = False,  # ← Exposed to MCP clients
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
    """Fuzzy search for drugs by name, brand name, or indication.

    Args:
        query: Search term (drug name, brand name, or indication).
               Minimum 2 characters required.
        slim: If true, return only id/name/type/score (~20 tokens per entity).
              Default false returns full candidates.
        ...
    """
```

**Lines 65-78:** `get_drug` tool also exposes `slim`
```python
@mcp.tool
async def get_drug(drugbank_id: str, slim: bool = False) -> dict | ErrorEnvelope:
    """Get complete drug record by DrugBank CURIE.

    Args:
        drugbank_id: DrugBank CURIE in format 'DrugBank:DBXXXXX' (e.g., 'DrugBank:DB00945').
        slim: If true, return minimal fields for token efficiency.  # ← Documented

    Returns:
        Drug record with cross_references, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.get_drug(drugbank_id=drugbank_id, slim=slim)
```

**Analysis:**
- ✅ Model has `to_slim_dict()` method (lines 210-220)
- ✅ Token budgets documented: ~20 tokens (slim), ~115-300 tokens (full)
- ✅ Client method accepts `slim` parameter (line 621)
- ✅ Server exposes `slim` in both tool signatures (lines 37, 66)
- ✅ Implementation uses `to_slim_dict()` when `slim=True` (line 610)

**Comparison to BioGRID (Reference):**

BioGRID exposes `slim` parameter:
```python
async def search_genes(
    self, query: str, organism: int = 9606, *, slim: bool = False
) -> PaginationEnvelope[BioGridSearchCandidate] | ErrorEnvelope:
```

DrugBank follows identical pattern with clear token budget documentation.

**Verdict:** ✅ **PASS** — Full token budgeting compliance.

---

## Supporting Checks

### ✅ CHECK 3: Principle I — Async-First Architecture (PASS)

**Evidence:**

**File:** `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/drugbank.py`

**Lines 618-728:** All public methods are async
```python
async def search_drugs(
    self,
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
```

**Lines 733-806:** `get_drug` is async
```python
async def get_drug(self, drugbank_id: str, slim: bool = False) -> dict | ErrorEnvelope:
```

**Lines 140-196:** Rate limiting uses async lock properly
```python
async def _rate_limited_get(self, url: str, params: dict | None = None) -> httpx.Response:
    """Make a rate-limited GET request with exponential backoff (T009, T010).

    Implements proper rate limiting with the request inside the lock
    to prevent race conditions. Handles 429 and auth errors with backoff.
    """
    headers = self._get_headers()

    # Initial request with rate limiting
    async with self._lock:  # ← Proper async lock usage
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)  # ← Async sleep

        client = await self._get_client()
        response = await client.get(url, params=params, headers=headers)  # ← Async HTTP
        self._last_request_time = time.monotonic()
```

**Lines 87-95:** Context manager support
```python
async def __aenter__(self) -> "DrugBankClient":
    """Enter context manager."""
    return self

async def __aexit__(
    self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
) -> None:
    """Exit context manager and cleanup resources."""
    await self.close()
```

**Analysis:**
- ✅ All public methods are async (lines 618, 733)
- ✅ Uses async lock (`asyncio.Lock`) not threading primitives (line 79)
- ✅ Uses `await asyncio.sleep()` not `time.sleep()` (line 160, 183)
- ✅ Async context manager support (lines 87-95)
- ✅ Inherits from `LifeSciencesClient` with async `httpx` client

**Verdict:** ✅ **PASS** — Full async compliance.

---

### ✅ CHECK 4: Principle III — Schema Determinism (PASS)

**Evidence:**

**File:** `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/models/drug.py`

**Lines 1-13:** Pydantic models with pattern validation
```python
"""Drug-related Pydantic models for DrugBank MCP Server.

Models follow the Agentic Biolink schema defined in ADR-001.
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# DrugBank CURIE pattern: DrugBank:DBXXXXX (5-digit ID)
DRUGBANK_CURIE_PATTERN = re.compile(r"^DrugBank:DB\d{5}$")
```

**Lines 104-111:** Field validator for CURIE format
```python
@field_validator("id")
@classmethod
def validate_drugbank_curie(cls, v: str) -> str:
    """Validate DrugBank CURIE format."""
    if not DRUGBANK_CURIE_PATTERN.match(v):
        msg = f"Invalid DrugBank CURIE format: {v}"
        raise ValueError(msg)
    return v
```

**Lines 57-64:** Model validator to omit empty values
```python
@model_validator(mode="after")
def omit_empty_values(self) -> "DrugCrossReferences":
    """Ensure no empty strings or empty lists are stored (omit instead)."""
    for field_name in type(self).model_fields:
        value = getattr(self, field_name)
        if value == "" or value == []:
            setattr(self, field_name, None)
    return self
```

**Lines 66-69:** Override `model_dump()` to exclude None
```python
def model_dump(self, **kwargs) -> dict:
    """Override to exclude None values (ADR-001: omit keys with no value)."""
    kwargs.setdefault("exclude_none", True)
    return super().model_dump(**kwargs)
```

**Lines 15-69:** Cross-reference schema (22-key Agentic Biolink)
```python
class DrugCrossReferences(BaseModel):
    """External database identifiers for drugs per ADR-001 22-key registry.

    Keys are omitted if no value exists (never null or empty string).
    DrugBank provides mappings to: chembl, uniprot, kegg, pubchem_compound,
    pubchem_substance, pdb.
    """

    # Drug identifiers
    drugbank: str | None = Field(
        default=None,
        description="DrugBank CURIE (self-reference)",
    )
    chembl: str | None = Field(
        default=None,
        description="ChEMBL compound ID (e.g., CHEMBL:25)",
    )
    ...
```

**Analysis:**
- ✅ Pydantic models with strict field types (lines 15-248)
- ✅ Pattern validation for CURIE format (lines 12, 104-111)
- ✅ Model validators enforce ADR-001 null handling (lines 57-69)
- ✅ 22-key cross-reference schema (lines 15-69)
- ✅ No ambiguous optional fields without validators

**Verdict:** ✅ **PASS** — Full schema determinism.

---

### ✅ CHECK 5: Rate Limiting (PASS)

**Evidence:**

**File:** `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/drugbank.py`

**Lines 44-48:** Rate limiting configuration
```python
# Rate limiting configuration (Constitution v1.1.0 MANDATORY)
RATE_LIMIT_DELAY = 0.1  # 10 req/s = 100ms between requests
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0  # Exponential backoff: 1s, 2s, 4s
MAX_BACKOFF = 60.0
```

**Lines 77-79:** Client state for rate limiting
```python
# Rate limiting state (T009)
self._last_request_time: float = 0.0
self._lock = asyncio.Lock()
```

**Lines 140-196:** Rate-limited GET with exponential backoff
```python
async def _rate_limited_get(self, url: str, params: dict | None = None) -> httpx.Response:
    """Make a rate-limited GET request with exponential backoff (T009, T010).

    Implements proper rate limiting with the request inside the lock
    to prevent race conditions. Handles 429 and auth errors with backoff.
    """
    headers = self._get_headers()

    # Initial request with rate limiting
    async with self._lock:
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

        client = await self._get_client()
        response = await client.get(url, params=params, headers=headers)
        self._last_request_time = time.monotonic()

    # Exponential backoff on rate limit/auth errors (T010)
    for attempt in range(MAX_RETRIES):
        if response.status_code not in (429, 401, 403):
            break

        # Calculate backoff time
        retry_after = response.headers.get("Retry-After")
        wait_time = (
            int(retry_after) if retry_after else min(BACKOFF_FACTOR**attempt, MAX_BACKOFF)
        )

        logger.warning(
            f"DrugBank API returned {response.status_code}, "
            f"retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})"
        )

        # Sleep OUTSIDE lock to allow other requests to proceed
        await asyncio.sleep(wait_time)

        # Retry with lock - re-check time boundary to prevent thundering herd
        async with self._lock:
            # CRITICAL: Re-check timing after acquiring lock
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < RATE_LIMIT_DELAY:
                await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

            response = await client.get(url, params=params, headers=headers)
            self._last_request_time = time.monotonic()

    return response
```

**Lines 278-284:** Rate limit error handling
```python
if response.status_code == 429:
    retry_after = response.headers.get("Retry-After", "60")
    return self._create_error(
        ErrorCode.RATE_LIMITED,
        "DrugBank API rate limit exceeded.",
        f"Wait {retry_after}s before retrying.",
    )
```

**Analysis:**
- ✅ Rate limit: 10 req/s (100ms delay) per DrugBank best practices
- ✅ Async lock prevents race conditions (line 79, 156)
- ✅ Request inside lock (line 163) to enforce timing
- ✅ Exponential backoff: 1s, 2s, 4s, capped at 60s (lines 166-195)
- ✅ Respects `Retry-After` header (line 172)
- ✅ Handles 429/401/403 with retries (line 168)
- ✅ Returns `RATE_LIMITED` error after exhausting retries (lines 278-284)

**Verdict:** ✅ **PASS** — Production-grade rate limiting.

---

### ✅ CHECK 6: Spec Artifacts (PASS)

**Evidence:**

Glob found 11 spec artifacts in `specs/005-drugbank-mcp-server/`:

```
specs/005-drugbank-mcp-server/
├── plan.md                                      # Implementation plan
├── data-model.md                                # Model field documentation
├── compliance-analysis-2026-01-03.md            # Constitution compliance
├── contracts/
│   ├── search_drugs.json                        # Tool contract (search)
│   └── get_drug.json                            # Tool contract (get)
├── checklists/
│   └── requirements.md                          # Requirement checklist
├── implementation-validation-2026-01-03.md      # Model validation
├── spec.md                                      # Feature specification
├── tasks.md                                     # Implementation tasks
├── quickstart.md                                # Usage guide
└── research.md                                  # API research
```

**Analysis:**
- ✅ 11 spec artifacts (matches BioGRID reference: 11 artifacts)
- ✅ Includes plan, spec, research, tasks, quickstart
- ✅ Tool contracts in `contracts/` directory
- ✅ Compliance analysis present (dated 2026-01-03)
- ✅ Implementation validation present

**Comparison to BioGRID:** Both have identical artifact structure per Constitution Principle VI.

**Verdict:** ✅ **PASS** — Complete spec artifact suite.

---

## Remediation Required

**NONE** — All checks pass.

The DrugBank implementation is fully Constitution-compliant. The only blocker is the commercial API key requirement (`DRUGBANK_API_KEY`), which is an external dependency, not a code quality issue.

---

## Recommendations

### Optional Improvements

1. **Public API Fallback:** The implementation includes fallback logic for public DrugBank endpoints (lines 659-661), but public endpoints are limited and may return HTML instead of JSON. Consider documenting the limitations of public access in the quickstart guide.

2. **HTML Parsing Robustness:** Lines 542-581 implement HTML parsing fallback for public endpoints. This is fragile (regex-based extraction). If maintaining public API support is important, consider using a proper HTML parser like `beautifulsoup4`.

3. **API Key Acquisition Docs:** Since DrugBank requires commercial access for full functionality, add a section to `quickstart.md` explaining how to acquire an API key and what features are blocked without it.

---

## Files Reviewed

| File Path | Purpose | Lines |
|-----------|---------|-------|
| `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/clients/drugbank.py` | Client implementation | 806 |
| `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/models/drug.py` | Pydantic models | 249 |
| `/home/donbr/graphiti-org/lifesciences-research/src/lifesciences_mcp/servers/drugbank.py` | MCP server | 82 |
| `/home/donbr/graphiti-org/lifesciences-research/specs/005-drugbank-mcp-server/` | Spec artifacts | 11 files |

**Total Implementation:** 1,137 lines across 3 core files + 11 spec artifacts.

---

## Conclusion

The DrugBank MCP server is **PRODUCTION-READY** from a code quality perspective. All six Constitution Principles are fully satisfied:

1. ✅ **Principle I (Async-First):** Uses async methods, async lock, no blocking calls
2. ✅ **Principle II (Fuzzy-to-Fact):** Real API call at line 663, proper error handling
3. ✅ **Principle III (Schema Determinism):** Pydantic models with validators, 22-key schema
4. ✅ **Principle IV (Token Budgeting):** `slim` parameter with documented token budgets
5. ✅ **Principle V (Rate Limiting):** 10 req/s with exponential backoff, respects Retry-After
6. ✅ **Principle VI (Spec Artifacts):** Complete 11-artifact spec suite

**Deployment Blocker:** Requires `DRUGBANK_API_KEY` environment variable for commercial API access. Public API fallback is implemented but limited.

**Audit Status:** ✅ **PASS** — No remediation required.
