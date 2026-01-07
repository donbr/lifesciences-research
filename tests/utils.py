"""Shared test utilities and helper functions."""

from typing import Any


def to_dict(result: Any) -> dict | Any:
    """Convert Pydantic model to dict, or return as-is if already dict/other.

    Helper to normalize responses between client (Pydantic objects) and
    MCP (dicts or Pydantic objects depending on library).
    """
    return result.model_dump() if hasattr(result, "model_dump") else result
