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
- `src/lifesciences_mcp/client.py` - Client pattern
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
    # TODO: Implement search logic
    raise NotImplementedError("Implement search_<entities>")


@mcp.tool
async def get_<entity>(<id_param>: str) -> dict | ErrorEnvelope:
    """Get complete <entity> record by <ID_TYPE> CURIE.

    Args:
        <id_param>: <ID_TYPE> CURIE in format '<PREFIX>:NNNNN'.

    Returns:
        <Entity> record, or ErrorEnvelope on failure.
    """
    client = await get_client()
    # TODO: Implement lookup logic
    raise NotImplementedError("Implement get_<entity>")


if __name__ == "__main__":
    mcp.run()
```

### 4. Generate Client Stub

Add to `src/lifesciences_mcp/client.py` (append, don't overwrite):

```python
class <API>Client(LifeSciencesClient):
    """<API_NAME> API client.

    TODO: Add rate limiting and endpoint configuration.
    """

    <API>_BASE_URL = "https://<api-url>"

    def __init__(self) -> None:
        """Initialize the <API> client."""
        super().__init__(base_url=self.<API>_BASE_URL)

    async def search_<entities>(self, query: str, **kwargs) -> PaginationEnvelope | ErrorEnvelope:
        """Fuzzy search for <entities>."""
        # TODO: Implement
        raise NotImplementedError()

    async def get_<entity>(self, <id_param>: str) -> dict | ErrorEnvelope:
        """Get <entity> by ID."""
        # TODO: Implement
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
        # TODO: Implement test
        pytest.skip("Not implemented")

    async def test_get_<entity>(self, client: <API>Client):
        """Test strict lookup."""
        # TODO: Implement test
        pytest.skip("Not implemented")
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
- tests/integration/test_<api>_api.py
- specs/<NNN>-<api>-mcp-server/ (feature directory)

Updated files:
- src/lifesciences_mcp/client.py (added <API>Client stub)
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
