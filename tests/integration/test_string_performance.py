"""Performance tests for STRING DB API client.

These tests validate non-functional requirements (NFRs) for performance.
Run with: pytest tests/integration/test_string_performance.py -m integration -v

NFR-002: Response time P95 < 5 seconds for network queries
"""

import asyncio
import time
from statistics import quantiles

import pytest

from lifesciences_mcp.clients import STRINGClient
from lifesciences_mcp.models.interaction import InteractionNetwork


@pytest.mark.integration
@pytest.mark.string
@pytest.mark.timeout(120)
async def test_network_query_performance_nfr002(check_string_available):
    """Test NFR-002: P95 response time < 5 seconds for network queries.

    Performs 20 network queries and validates that 95th percentile is under 5 seconds.
    Uses well-known proteins with varying network sizes for realistic workload.

    The sleep before each timed section drains the client-side rate limiter so that
    measurements reflect true API response time, not internal throttling.
    """
    client = STRINGClient(species=9606)

    # Test proteins with varying network complexity
    test_proteins = [
        "TP53",  # Highly connected (tumor suppressor)
        "BRCA1",  # Moderately connected (DNA repair)
        "MDM2",  # Well-connected (p53 regulator)
        "ATM",  # Well-connected (DNA damage response)
        "EGFR",  # Highly connected (growth factor receptor)
    ]

    response_times = []

    try:
        # Warm-up phase: 2 untimed queries to absorb DNS, TLS, and connection pool setup
        for protein_symbol in test_proteins[:2]:
            search_result = await client.search_proteins(protein_symbol)
            if search_result.items:
                await client.get_interactions(
                    search_result.items[0].id,
                    required_score=400,
                    limit=10,
                )
            await asyncio.sleep(1.2)

        # Perform 20 queries (4 iterations x 5 proteins)
        for iteration in range(4):
            for protein_symbol in test_proteins:
                # Search for protein
                search_result = await client.search_proteins(protein_symbol)
                if not search_result.items:
                    continue

                protein_id = search_result.items[0].id

                # Sleep BEFORE the timed section to drain the rate limiter.
                # The client enforces 1 req/s; sleeping here ensures elapsed > 1.0s
                # since search_proteins(), so get_interactions() won't be throttled.
                await asyncio.sleep(1.2)

                # Measure network query time (rate limiter already drained)
                start_time = time.perf_counter()
                result = await client.get_interactions(
                    protein_id,
                    required_score=400,  # Medium confidence
                    limit=100,  # Reasonable limit for performance test
                )
                end_time = time.perf_counter()

                elapsed = end_time - start_time
                response_times.append(elapsed)

                # Verify valid response
                assert isinstance(result, InteractionNetwork)
                assert result.interaction_count >= 0

                # Per-query diagnostics for debugging future failures
                print(
                    f"  [{iteration+1}.{test_proteins.index(protein_symbol)+1}] "
                    f"{protein_symbol:<6} {elapsed:.3f}s "
                    f"({result.interaction_count} interactions)"
                )

    finally:
        await client.close()

    # Calculate P95 (95th percentile)
    assert len(response_times) >= 10, f"Need at least 10 samples, got {len(response_times)}"

    # quantiles() returns n-1 cut points for n quantiles
    # For P95, we need 20 quantiles (giving 19 cut points, 18th is P95)
    percentiles = quantiles(response_times, n=20)
    p95 = percentiles[18]  # 95th percentile (index 18 of 19 cut points)

    # NFR-002: P95 < 5 seconds
    # True API response is typically 0.3-1.5s. The 5s threshold tolerates occasional
    # retries on 429/503 while still catching real performance regressions.
    assert p95 < 5.0, (
        f"NFR-002 FAILED: P95 response time {p95:.2f}s exceeds 5.0s threshold. "
        f"Min: {min(response_times):.2f}s, Max: {max(response_times):.2f}s, "
        f"Median: {quantiles(response_times, n=2)[0]:.2f}s"
    )

    # Log performance metrics for visibility
    print("\nNFR-002 Performance Test PASSED")
    print(f"   Queries: {len(response_times)}")
    print(f"   Min: {min(response_times):.2f}s")
    print(f"   Median: {quantiles(response_times, n=2)[0]:.2f}s")
    print(f"   P95: {p95:.2f}s")
    print(f"   Max: {max(response_times):.2f}s")
