"""Performance tests for BioGRID API client.

Tests NFR-004: P95 latency < 3 seconds for interaction queries.

Run with: pytest tests/integration/test_biogrid_performance.py -m integration -v

Requires BIOGRID_API_KEY environment variable.
"""

import os
import time

import pytest

from lifesciences_mcp.clients import BioGridClient
from lifesciences_mcp.models.biogrid import InteractionResult

# Skip if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("BIOGRID_API_KEY"),
    reason="BIOGRID_API_KEY not set. Get free key at https://webservice.thebiogrid.org/",
)


@pytest.mark.integration
async def test_performance_interaction_query_nfr004():
    """Test NFR-004: P95 latency < 3 seconds for interaction queries.

    This test validates that 95% of interaction queries complete within 3 seconds.
    """
    client = BioGridClient()

    try:
        # Test genes with varying interaction counts
        test_genes = [
            "TP53",  # Well-studied gene with many interactions
            "MDM2",  # Moderately studied
            "BRCA1",  # Well-studied
            "ATM",  # Well-studied
            "EGFR",  # Well-studied
        ]

        latencies = []

        for gene in test_genes:
            start_time = time.monotonic()
            result = await client.get_interactions(gene, organism=9606, max_results=1000)
            end_time = time.monotonic()

            latency = end_time - start_time
            latencies.append(latency)

            assert isinstance(result, InteractionResult)
            print(f"{gene}: {latency:.2f}s ({len(result.interactions)} interactions)")

        # Calculate P95
        latencies_sorted = sorted(latencies)
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies_sorted[p95_index]

        print(f"\nP95 latency: {p95_latency:.2f}s")
        print(f"Max latency: {max(latencies):.2f}s")
        print(f"Mean latency: {sum(latencies) / len(latencies):.2f}s")

        # NFR-004: P95 must be < 3 seconds
        assert p95_latency < 3.0, (
            f"NFR-004 FAILED: P95 latency ({p95_latency:.2f}s) exceeds 3 second threshold"
        )

    finally:
        await client.close()


@pytest.mark.integration
async def test_performance_max_interactions_nfr003():
    """Test NFR-003: Max interactions per request is capped at 10,000.

    BioGRID implementation should not return more than 10,000 interactions
    even for highly connected proteins like TP53.
    """
    client = BioGridClient()

    try:
        # TP53 has many interactions - test with max limit
        result = await client.get_interactions("TP53", organism=9606, max_results=10000)

        assert isinstance(result, InteractionResult)

        # NFR-003: Verify returned interactions don't exceed 10k limit
        assert len(result.interactions) <= 10000, (
            f"NFR-003 FAILED: Returned {len(result.interactions)} interactions, "
            f"exceeds 10,000 limit"
        )

        print(f"TP53 interactions: {len(result.interactions)} (max 10,000)")
        print(f"Total available: {result.total_count}")

        # Test smaller limit
        result_small = await client.get_interactions("TP53", organism=9606, max_results=100)

        assert len(result_small.interactions) <= 100, (
            f"Limit parameter not respected: requested 100, got {len(result_small.interactions)}"
        )

        print(f"With limit=100: {len(result_small.interactions)} interactions")

    finally:
        await client.close()
