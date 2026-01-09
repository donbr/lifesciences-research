---
description: Scaffold a new FastMCP server with standard Life Sciences project structure following ADR-001 patterns
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding. Expected format:
- `<api-name>` - e.g., "uniprot", "chembl", "opentargets"

If no argument provided, ask the user for the API name.

## Goal

Create the complete scaffolding for a new FastMCP MCP server following the Life Sciences project architecture defined in ADR-001. This skill implements Constitution Principle VI (Platform Skill Delegation) to ensure consistent project structure.

## Generated Structure

```
src/lifesciences_mcp/
├── clients/
│   └── <api>.py              # Client stub (ADR-006)
├── servers/
│   └── <api>.py              # FastMCP server with tool stubs
└── (existing files preserved)

tests/
├── unit/
│   └── test_<api>_models.py  # Unit test stubs
└── integration/
    └── test_<api>_api.py     # Integration test stubs
```

## Execution Steps

### 1. Validate Input

- Extract API name from arguments (lowercase, alphanumeric with underscores)
- Validate against existing servers in `src/lifesciences_mcp/servers/`
- If server already exists, abort with message

### 2. Read Existing Patterns

Read the following files to understand established patterns:
- `src/lifesciences_mcp/servers/hgnc.py` - Server pattern
- `src/lifesciences_mcp/clients/hgnc.py` - Client pattern
- `src/lifesciences_mcp/models/envelopes.py` - Envelope models
- `tests/integration/test_hgnc_api.py` - Test pattern

### 3. Generate Server File

Create `src/lifesciences_mcp/servers/<api>.py` with:

```python
"""<API_NAME> MCP Server - <Brief description>.

This server provides tools for <API purpose>:
- search_<entities>: Fuzzy search returning ranked candidates
- get_<entity>: Strict lookup by <ID_TYPE> CURIE

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/<api>.py
"""

from fastmcp import FastMCP

from lifesciences_mcp.clients import <API>Client
from lifesciences_mcp.models import (
    ErrorEnvelope,
    PaginationEnvelope,
)

# Initialize the MCP server
mcp = FastMCP("<API_NAME> Server")

# Shared client instance (connection pooling)
# Lifecycle managed by module-level singleton pattern
_client: <API>Client | None = None


async def get_client() -> <API>Client:
    """Get or create the shared <API> client."""
    global _client
    if _client is None:
        _client = <API>Client()
    return _client


@mcp.tool
async def search_<entities>(
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope | ErrorEnvelope:
    """Fuzzy search for <entities>.

    Args:
        query: Search term.
        slim: If true, return minimal fields (~20 tokens per entity).
        cursor: Opaque cursor for pagination.
        page_size: Number of results per page (1-100, default 50).

    Returns:
        PaginationEnvelope with items, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.search_<entities>(
        query=query,
        slim=slim,
        cursor=cursor,
        page_size=page_size,
    )


@mcp.tool
async def get_<entity>(<id_param>: str) -> dict | ErrorEnvelope:
    """Get complete <entity> record by <ID_TYPE> CURIE.

    Args:
        <id_param>: <ID_TYPE> CURIE in format '<PREFIX>:NNNNN'.

    Returns:
        <Entity> record, or ErrorEnvelope on failure.
    """
    client = await get_client()
    return await client.get_<entity>(<id_param>=<id_param>)


if __name__ == "__main__":
    mcp.run()
```

### 4. Generate Client Stub

Create `src/lifesciences_mcp/clients/<api>.py` (ADR-006 Single Writer):

```python
class <API>Client(LifeSciencesClient):
    """<API_NAME> API client implementing the Fuzzy-to-Fact protocol.

    Rate limiting: TODO (e.g., 10 req/s)
    """

    <API>_BASE_URL = "https://<api-url>"

    def __init__(self) -> None:
        """Initialize the <API> client."""
        super().__init__(base_url=self.<API>_BASE_URL)
        # Rate limiting state (Pattern: 009, 013)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    @staticmethod
    def validate_id(identifier: str) -> bool:
        """Validate CURIE format for this API.
        
        Ref: ADR-0001 (Core Identifiers)
        """
        # TODO: Implement regex validation
        # return bool(PATTERN.match(identifier))
        return True

    async def __aenter__(self) -> "<API>Client":
        """Enter context manager."""
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """Exit context manager and cleanup resources."""
        await self.close()

    async def _rate_limited_call(self, func: callable, *args, **kwargs) -> Any:
        """Execute API call with rate limiting and error mapping."""
        # Rate limiting logic (Constitution v1.1.0)
        async with self._lock:
            # TODO: Implement throttling delay
            # now = time.monotonic()
            # ...
            pass
            
        try:
             return await func(*args, **kwargs)
        except Exception as e:
             return self._map_api_error(e)

    def _map_api_error(self, error: Exception) -> ErrorEnvelope:
        """Map upstream API errors to canonical error codes."""
        # TODO: Implement error mapping logic
        # if "404" in str(error): ...
        return ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UPSTREAM_ERROR,
                message=str(error),
                recovery_hint="Check input and try again.",
            )
        )

    async def search_<entities>(
        self, 
        query: str, 
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50,
    ) -> PaginationEnvelope | ErrorEnvelope:
        """Fuzzy search for <entities> (Phase 1 of Fuzzy-to-Fact)."""
        # TODO: Implement search with rate limiting
        # return await self._rate_limited_call(...)
        raise NotImplementedError()

    async def get_<entity>(self, <id_param>: str) -> dict | ErrorEnvelope:
        """Get <entity> by ID (Phase 2 of Fuzzy-to-Fact)."""
        # TODO: Implement strict lookup
        # Validate ID format first
        # Return ErrorEnvelope.unresolved_entity() if invalid
        raise NotImplementedError()
```

### 5. Generate Test Stubs

Create `tests/integration/test_<api>_api.py`:

```python
"""Integration tests for <API_NAME> API client.

Run with: pytest tests/integration/test_<api>_api.py -v -m integration
"""

import pytest

from lifesciences_mcp.clients import <API>Client
from lifesciences_mcp.models import ErrorEnvelope, PaginationEnvelope


@pytest.mark.integration
class Test<API>ClientIntegration:
    """Integration tests for <API>Client."""

    @pytest.fixture
    async def client(self):
        """Create a <API> client."""
        client = <API>Client()
        yield client
        await client.close()

    async def test_search_<entities>(self, client: <API>Client):
        """Test fuzzy search."""
        # TODO: Replace "term" with a real query appropriate for this API
        result = await client.search_<entities>("term")
        
        # Verify envelope structure
        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

    async def test_get_<entity>(self, client: <API>Client):
        """Test strict lookup."""
        # TODO: Replace "ID:123" with a real valid CURIE
        result = await client.get_<entity>("ID:123")
        
        # Verify entity return type (dict or specific model)
        assert not isinstance(result, ErrorEnvelope)
        # assert result.id == "ID:123"

    async def test_get_<entity>_invalid_curie(self, client: <API>Client):
        """Test that raw string returns UNRESOLVED_ENTITY error."""
        result = await client.get_<entity>("invalid_format")

        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"

    async def test_fuzzy_to_fact_workflow(self, client: <API>Client):
        """Test complete Fuzzy-to-Fact protocol workflow."""
        # Step 1: Fuzzy search
        # TODO: Update query
        search_result = await client.search_<entities>("query")
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0
        
        top_hit = search_result.items[0]

        # Step 2: Strict lookup using ID from search
        entity = await client.get_<entity>(top_hit.id)
        assert not isinstance(entity, ErrorEnvelope)
        assert entity.id == top_hit.id
```

### 6. Update Package Exports

Add new client to `src/lifesciences_mcp/__init__.py`:

```python
from lifesciences_mcp.clients import <API>Client
```

And add to `__all__` list.

### 7. Generate SpecKit Feature Directory

Create `specs/<NNN>-<api>-mcp-server/` with template files:
- `spec.md` (empty template)
- `plan.md` (empty template)
- `tasks.md` (empty template)

Use next available feature number (scan existing `specs/` directories).

### 8. Output Summary

Print:
```
## Scaffold Complete: <API_NAME> MCP Server

Created files:
- src/lifesciences_mcp/servers/<api>.py
- src/lifesciences_mcp/clients/<api>.py
- tests/integration/test_<api>_api.py
- specs/<NNN>-<api>-mcp-server/ (feature directory)

Updated files:
- src/lifesciences_mcp/__init__.py (added export)

Next steps:
1. Run /speckit.specify to create the specification
2. Run /speckit.plan to design the implementation
3. Run /speckit.tasks to generate the task list
4. Run /speckit.implement to build the server
```

## Patterns Enforced

This skill enforces Constitution compliance:

| Principle | Enforcement |
|-----------|-------------|
| I. Async-First | All generated code uses async/await |
| II. Fuzzy-to-Fact | Template includes search + get tools |
| III. Schema Determinism | Uses canonical envelopes |
| IV. Token Budgeting | slim parameter included |
| VI. Platform Skill | This skill exists |

## Notes

- Server name derived from API name (lowercase, underscores)
- Client class name derived from API name (PascalCase + Client)
- Feature number auto-increments from existing specs/
- All TODO comments mark implementation points
- Run linter after generation: `uv run ruff check --fix src/ tests/`
