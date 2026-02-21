# Entrez MCP Client - Constitution Compliance Audit Report

**Audit Date:** 2026-02-06
**Auditor:** Agent 9 (Constitution Compliance Specialist)
**Audit Type:** READ-ONLY (no modifications)

## Executive Summary

The Entrez MCP client demonstrates **FULL COMPLIANCE** with all 6 Constitution Principles. The implementation follows the BioGRID reference pattern closely, with proper API-backed validation, token budgeting, and rate limiting.

## Compliance Summary

| Principle | Status | Notes |
|-----------|--------|-------|
| **Principle II - Fuzzy-to-Fact** | **PASS** | ✅ search_genes uses real API calls (esearch + esummary) |
| **Principle IV - Token Budgeting** | **PASS** | ✅ slim param + to_slim() method + server exposes slim |
| **Principle I - Async-First** | **PASS** | ✅ All I/O operations are async with httpx |
| **Principle III - Schema Determinism** | **PASS** | ✅ Pydantic models with null omission validator |
| **Principle V - Rate Limiting** | **PASS** | ✅ Adaptive rate limiting with exponential backoff |
| **Principle VI - Spec Artifacts** | **PASS** | ✅ Complete spec directory with 7 artifacts + 3 contracts |

**Overall Rating: PASS (100% compliance)**

---

## Detailed Findings

### CHECK 1: Principle II - Fuzzy-to-Fact (CRITICAL) ✅ PASS

**Requirement:** Search method MUST call API to confirm entity exists. Returns ENTITY_NOT_FOUND when not found.

**Evidence:**

**Client Implementation (`src/lifesciences_mcp/clients/entrez.py`)**:
```python
# Lines 476-577: search_genes method
async def search_genes(
    self,
    query: str,
    organism: str | None = None,
    page_size: int = 50,
    cursor: str | None = None,
) -> PaginationEnvelope[GeneSearchCandidate] | ErrorEnvelope:
    """Fuzzy search for genes (Phase 1 of Fuzzy-to-Fact).

    Uses esearch + esummary two-step pattern per research.md R2.
    """
    # Step 1: esearch to get ID list
    esearch_response = await self._esearch(
        term=query,
        organism=organism,
        retmax=page_size,
        retstart=offset,
    )

    # Step 2: esummary to get gene summaries
    esummary_response = await self._esummary(ids=id_list)
```

**Two-step API validation:**
1. `_esearch()` (lines 155-199) calls `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` to get gene IDs
2. `_esummary()` (lines 201-218) calls `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi` to fetch gene data

**Empty results handling (lines 524-531):**
```python
# Empty results - return empty envelope (not error per research.md R7)
if not id_list:
    return PaginationEnvelope.create(
        items=[],
        cursor=None,
        total_count=total_count,
        page_size=page_size,
    )
```

**Strict lookup with ENTITY_NOT_FOUND (lines 604-692):**
```python
async def get_gene(
    self, entrez_id: str, slim: bool = False
) -> EntrezGene | dict[str, Any] | ErrorEnvelope:
    """Get complete gene record by NCBIGene CURIE (Phase 2 of Fuzzy-to-Fact)."""

    # Validate CURIE format (Fuzzy-to-Fact enforcement)
    if not NCBI_GENE_CURIE_PATTERN.match(entrez_id):
        return self._create_error_envelope(
            code=ErrorCode.UNRESOLVED_ENTITY,
            message=f"The input '{entrez_id}' is not a valid NCBIGene CURIE.",
            recovery_hint="Call search_genes to resolve the identifier first...",
            invalid_input=entrez_id,
        )

    # Fetch full XML record
    xml_response = await self._efetch(gene_id=numeric_id)
    gene_data = self._parse_gene_xml(xml_response)

    if not gene_data or not gene_data.get("symbol"):
        return self._create_error_envelope(
            code=ErrorCode.ENTITY_NOT_FOUND,
            message="Gene not found in NCBI Gene database",
            recovery_hint="Verify the NCBIGene ID or use search_genes...",
            invalid_input=entrez_id,
        )
```

**Verdict: PASS** - Real API calls with proper error handling. No client-side regex-only validation.

---

### CHECK 2: Principle IV - Token Budgeting ✅ PASS

**Requirement:** Methods MUST support `slim: bool = False` parameter. Model MUST have `to_slim()` method. Server MUST expose slim parameter.

**Evidence:**

**1. Client method signature (line 604-606):**
```python
async def get_gene(
    self, entrez_id: str, slim: bool = False
) -> EntrezGene | dict[str, Any] | ErrorEnvelope:
```

**2. Client uses slim mode (lines 663-664):**
```python
if slim:
    return gene.to_slim()
```

**3. Model implements to_slim() (lines 260-270):**
```python
class EntrezGene(BaseModel):
    """Token Budget: ~115-300 tokens in full mode, ~25 tokens in slim mode"""

    def to_slim(self) -> dict[str, Any]:
        """Return minimal fields for token efficiency.

        Returns only id, symbol, name, organism (~25 tokens).
        """
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "organism": self.organism,
        }
```

**4. Server exposes slim parameter (lines 87-116):**
```python
@mcp.tool
async def get_gene(
    entrez_id: str,
    slim: bool = False,
) -> EntrezGene | dict[str, Any] | ErrorEnvelope:
    """Get complete gene record from NCBI Gene database by NCBIGene CURIE.

    Args:
        slim: If True, return minimal fields (id, symbol, name, organism)
              for token efficiency (~25 vs ~115-300 tokens).
    """
    client = await get_client()
    return await client.get_gene(entrez_id=entrez_id, slim=slim)
```

**Token budget documentation:**
- `GeneSearchCandidate`: ~30-40 tokens (slim), ~60-80 tokens (full) - Line 26
- `EntrezGene`: ~115-300 tokens (full), ~25 tokens (slim) - Line 180

**Verdict: PASS** - Complete token budgeting implementation with documented token counts.

---

### CHECK 3: Principle I - Async-First ✅ PASS

**Requirement:** All I/O operations MUST be async.

**Evidence:**

**1. Client uses async httpx (lines 23, 79-132):**
```python
import httpx

async def _rate_limited_get(
    self, path: str, params: dict[str, Any] | None = None
) -> httpx.Response:
    """Make a rate-limited GET request with exponential backoff."""
    response = await self._get(path, params=params)
```

**2. All API methods are async:**
- `_esearch()` - line 155
- `_esummary()` - line 201
- `_efetch()` - line 220
- `_elink()` - line 239
- `search_genes()` - line 476
- `get_gene()` - line 604
- `get_pubmed_links()` - line 693

**3. Server tools are async (lines 43-145):**
```python
@mcp.tool
async def search_genes(...) -> PaginationEnvelope[GeneSearchCandidate] | ErrorEnvelope:
    client = await get_client()
    return await client.search_genes(...)
```

**4. Context manager support (lines 67-75):**
```python
async def __aenter__(self) -> "EntrezClient":
    """Enter context manager."""
    return self

async def __aexit__(...) -> None:
    """Exit context manager and cleanup resources."""
    await self.close()
```

**Verdict: PASS** - All I/O is async. No blocking operations.

---

### CHECK 4: Principle III - Schema Determinism ✅ PASS

**Requirement:** Pydantic models MUST omit null/empty values. No `null` in JSON output.

**Evidence:**

**1. Cross-references model validator (lines 163-172):**
```python
class EntrezCrossReferences(BaseModel):
    """Constitution Principle III: Omit keys entirely if no reference exists."""

    @model_validator(mode="before")
    @classmethod
    def omit_null_values(cls, data: Any) -> Any:
        """Remove None, empty string, and empty list values.

        Constitution Principle III: Never include null cross-references.
        """
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None and v != "" and v != []}
        return data
```

**2. Client code respects null omission (line 368):**
```python
def _build_cross_references(self, xrefs: dict[str, str | list[str]]) -> EntrezCrossReferences:
    """Map NCBI Dbtag entries to CrossReferences model.

    Per Constitution Principle III: omit keys with no value.
    """
    result: dict[str, Any] = {}
    # Only add keys when values exist
```

**3. Optional fields use `None` defaults (lines 50-54, 204-243):**
```python
description: str | None = Field(None, ...)
summary: str | None = Field(None, ...)
map_location: str | None = Field(None, ...)
chromosome: str | None = Field(None, ...)
aliases: list[str] | None = Field(None, ...)
```

**Verdict: PASS** - Proper null omission with explicit validator and documentation.

---

### CHECK 5: Rate Limiting ✅ PASS

**Requirement:** Client MUST implement rate limiting with `asyncio.Lock` and exponential backoff on 429/503.

**Evidence:**

**1. Lock initialization (line 65):**
```python
def __init__(self) -> None:
    """Initialize the Entrez client with adaptive rate limiting."""
    self.api_key = os.getenv("NCBI_API_KEY")
    # 10 req/s with API key, 3 req/s without per research.md R4
    self.rate_limit_delay = 0.1 if self.api_key else 0.333
    self._last_request_time: float = 0.0
    self._lock = asyncio.Lock()
```

**2. Adaptive rate limiting (lines 62-63):**
```python
# 10 req/s with API key, 3 req/s without per research.md R4
self.rate_limit_delay = 0.1 if self.api_key else 0.333
```

**3. Rate-limited GET with lock (lines 77-132):**
```python
async def _rate_limited_get(
    self, path: str, params: dict[str, Any] | None = None
) -> httpx.Response:
    """Make a rate-limited GET request with exponential backoff.

    Implements proper rate limiting with the request inside the lock
    to prevent race conditions. Adds API key if available.
    """
    # Initial request with rate limiting
    async with self._lock:
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)

        response = await self._get(path, params=params)
        self._last_request_time = time.monotonic()

    # Exponential backoff on rate limit errors
    for attempt in range(self.MAX_RETRIES):
        if response.status_code not in (429, 503):
            break

        # Calculate backoff time per research.md R4
        retry_after = response.headers.get("Retry-After")
        wait_time = int(retry_after) if retry_after else (2**attempt)

        # Sleep OUTSIDE lock to allow other requests to proceed
        await asyncio.sleep(wait_time)

        # Retry with lock - re-check time boundary to prevent thundering herd
        async with self._lock:
            # CRITICAL: Re-check timing after acquiring lock
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

            response = await self._get(path, params=params)
            self._last_request_time = time.monotonic()
```

**4. Error handling for 429 (lines 580-585, 669-674, 738-743):**
```python
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        return self._create_error_envelope(
            code=ErrorCode.RATE_LIMITED,
            message="Exceeded NCBI rate limit",
            recovery_hint="Wait and retry. Add NCBI_API_KEY environment variable for 10 req/s limit (free from NCBI)",
        )
```

**Verdict: PASS** - Proper rate limiting with lock, exponential backoff, and adaptive delays based on API key presence.

---

### CHECK 6: Spec Artifacts ✅ PASS

**Requirement:** Must have spec directory with complete artifacts.

**Evidence:**

**Spec Directory: `/home/donbr/graphiti-org/lifesciences-research/specs/009-entrez-mcp-server/`**

**Core Artifacts (7 files):**
1. `spec.md` - Feature specification with acceptance criteria
2. `research.md` - API research and decision rationale
3. `plan.md` - Implementation plan with constitution compliance
4. `data-model.md` - Model definitions and token budgets
5. `tasks.md` - Implementation task breakdown
6. `quickstart.md` - Usage examples and workflows
7. `compliance-analysis-2026-01-03.md` - Previous compliance audit

**Contract Artifacts (3 YAML files):**
1. `contracts/search_genes.yaml` - Fuzzy search tool contract
2. `contracts/get_gene.yaml` - Strict lookup tool contract
3. `contracts/get_pubmed_links.yaml` - Literature links tool contract

**Verdict: PASS** - Complete spec artifacts following SpecKit SDLC pattern.

---

## Critical Findings Summary

**No critical issues found.** The Entrez implementation demonstrates reference-quality compliance:

1. **Fuzzy-to-Fact Compliance (Principle II):** Search uses TWO API calls (esearch + esummary) to validate entities. Strict lookup returns ENTITY_NOT_FOUND when gene doesn't exist. No regex-only shortcuts.

2. **Token Budgeting Compliance (Principle IV):** Complete implementation with:
   - `slim: bool = False` parameter on get_gene()
   - `to_slim()` method returning 4 fields (~25 tokens vs ~115-300 tokens)
   - Server exposes slim parameter with documentation
   - Token budgets documented in model docstrings

3. **Rate Limiting Excellence:** Adaptive rate limiting (3 req/s default, 10 req/s with API key), proper lock usage, exponential backoff on 429/503, and "Retry-After" header parsing.

4. **Schema Determinism:** Explicit `@model_validator` for null omission in cross-references model with Constitution Principle III citation in docstring.

5. **Spec Artifacts:** Complete SpecKit SDLC with 7 core artifacts + 3 YAML contracts.

---

## Remediation Required

**None.** This is a reference-quality implementation suitable for other servers to follow.

---

## Files Reviewed

| File Path | Purpose | Lines |
|-----------|---------|-------|
| `src/lifesciences_mcp/clients/entrez.py` | Client implementation with Fuzzy-to-Fact protocol | 761 |
| `src/lifesciences_mcp/models/entrez.py` | Pydantic models with token budgeting | 297 |
| `src/lifesciences_mcp/servers/entrez.py` | FastMCP server exposing 3 tools | 150 |
| `specs/009-entrez-mcp-server/` | Complete spec directory (7 artifacts + 3 contracts) | N/A |

**Total Implementation Lines:** 1,208 lines of production code
**Spec Artifacts:** 10 files (7 markdown + 3 YAML contracts)

---

## Recommendations

**No changes required.** Consider using Entrez as a reference implementation for:
- Two-step API validation pattern (esearch + esummary)
- Adaptive rate limiting based on API key presence
- XML parsing with defusedxml for security
- Comprehensive cross-reference extraction from external database tags

---

**Audit Completed:** 2026-02-06
**Audit Result:** PASS (100% Constitution Compliance)
**Auditor:** Agent 9 (Constitution Compliance Specialist)
