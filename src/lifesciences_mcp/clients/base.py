"""Base client for all Life Sciences API clients.

This module provides the shared LifeSciencesClient base class with:
- Async httpx client with connection pooling
- Session lifecycle management
- Common error handling patterns

Status: FROZEN - Do not modify during parallel implementation.
"""

from typing import Any

import httpx


class LifeSciencesClient:
    """Base async HTTP client for life sciences APIs.

    Provides connection pooling and common HTTP functionality.
    Subclasses implement API-specific logic.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_connections: int = 10,
    ) -> None:
        """Initialize the client.

        Args:
            base_url: Base URL for the API.
            timeout: Request timeout in seconds.
            max_connections: Maximum concurrent connections.
        """
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None
        self._timeout = timeout
        self._max_connections = max_connections

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(
                max_connections=self._max_connections,
                max_keepalive_connections=self._max_connections,
            )
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self._timeout),
                limits=limits,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request."""
        client = await self._get_client()
        return await client.get(path, **kwargs)
