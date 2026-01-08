"""End-to-End (E2E) validation suite for the deployed FastMCP Cloud instance.

This module validates the live deployment (HTTP/SSE transport, Cloudflare, Env Vars).
It runs against the URL defined in the `FASTMCP_CLOUD_ENDPOINT` environment variable.

Usage:
    FASTMCP_CLOUD_ENDPOINT=https://lifesciences-research.fastmcp.app/mcp uv run pytest -v -s tests/e2e/test_competency_questions_cloud.py

Note:
    We select a representative subset of Competency Questions (one per core provider)
    to verify that the endpoint is reachable and tools are functioning correctly.
"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastmcp import Client
from dotenv import load_dotenv

from tests.utils import to_dict

load_dotenv()

# Default URL for the deployed instance (can be overridden by env var)
DEFAULT_URL = os.getenv("FASTMCP_CLOUD_ENDPOINT", "https://lifesciences-research.fastmcp.app/mcp")

pytestmark = pytest.mark.e2e


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[Client, None]:
    """Create a shared FastMCP Client connection for the module."""
    url = os.getenv("FASTMCP_CLOUD_ENDPOINT", DEFAULT_URL)
    print(f"\nConnecting to MCP Server: {url}")

    async with Client(url) as c:
        yield c


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_connectivity(client: Client):
    """Verify basic connectivity and tool listing."""
    print("  > Listing tools...")
    tools = await client.list_tools()
    tool_names = [t.name for t in tools]
    print(f"    Found {len(tool_names)} tools")

    assert len(tool_names) > 0, "No tools found on the server"
    assert "hgnc_search_genes" in tool_names, "HGNC tools missing"
    assert "uniprot_get_protein" in tool_names, "UniProt tools missing"
    assert "chembl_search_compounds" in tool_names, "ChEMBL tools missing"


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_cq1_hgnc_search(client: Client):
    """CQ-1: Resolve TP53 (HGNC)."""
    print("  > Searching HGNC for 'TP53'...")
    result = await client.call_tool("hgnc_search_genes", arguments={"query": "TP53", "page_size": 1})
    assert result.is_error is False, f"Tool call failed: {result}"

    data = to_dict(result.data)
    items = data.get("items")

    assert items, "No results for TP53"
    first_item = to_dict(items[0])
    print(f"    Found: {first_item.get('id')} ({first_item.get('symbol')})")

    assert first_item["id"] == "HGNC:11998"
    assert first_item["symbol"] == "TP53"


@pytest.mark.asyncio
@pytest.mark.timeout(45)
async def test_cq5_biogrid_interactions(client: Client):
    """CQ-5: KRAS interactors (BioGRID)."""
    # BioGRID requires an API key on the server side.
    # We assume the cloud deployment has this configured.
    print("  > Searching BioGRID for 'KRAS'...")
    search = await client.call_tool("biogrid_search_genes", arguments={"query": "KRAS"})
    assert search.is_error is False

    # Get validated symbol
    s_data = to_dict(search.data)
    s_items = s_data.get("items")
    assert s_items

    first_item = to_dict(s_items[0])
    symbol = first_item["symbol"]
    print(f"    Validated Symbol: {symbol}")

    # Get interactions
    # Use a small max_results to be fast
    print(f"  > Fetching interactions for {symbol}...")
    interactions = await client.call_tool("biogrid_get_interactions", arguments={"gene_symbol": symbol, "max_results": 2})

    if interactions.is_error:
        # If API key is missing on the server, this might fail.
        # We allow a graceful failure if it's explicitly an auth error, but warn.
        err = str(interactions)
        if "API key" in err or "UPSTREAM_ERROR" in err:
            pytest.skip(f"BioGRID tool failed (likely missing API key on server): {err}")
        pytest.fail(f"BioGRID interaction lookup failed: {err}")

    i_data = to_dict(interactions.data)
    # Check physical_count or interactions list
    assert i_data.get("query_gene") == "KRAS"
    count = len(i_data.get("interactions", []))
    print(f"    Found {count} interactions")
    assert count > 0


@pytest.mark.asyncio
@pytest.mark.timeout(45)
async def test_cq13_workflow_wikipathways_chembl(client: Client):
    """CQ-13: Workflow test (WikiPathways -> ChEMBL).

    1. Search 'Apoptosis' pathway
    2. Search 'Venetoclax' compound
    """
    # 1. WikiPathways
    print("  > Searching WikiPathways for 'Apoptosis'...")
    wp_res = await client.call_tool("wikipathways_search_pathways", arguments={"query": "Apoptosis", "organism": "Homo sapiens"})
    assert wp_res.is_error is False
    wp_data = to_dict(wp_res.data)
    wp_items = wp_data.get("items")
    assert wp_items is not None, "No items found"

    assert any("Apoptosis" in to_dict(i)["title"] for i in wp_items)
    print("    Apoptosis pathway found")

    # 2. ChEMBL
    print("  > Searching ChEMBL for 'Venetoclax'...")
    ch_res = await client.call_tool("chembl_search_compounds", arguments={"query": "Venetoclax"})
    assert ch_res.is_error is False
    ch_data = to_dict(ch_res.data)
    ch_items = ch_data.get("items")
    assert ch_items
    top_hit = to_dict(ch_items[0])
    print(f"    Found: {top_hit.get('id')} ({top_hit.get('name')})")
    assert top_hit["id"] == "CHEMBL:3137309"
