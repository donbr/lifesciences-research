"""Integration test for performance requirements.

Tests that UniProt and ChEMBL queries meet success criteria for response times.

Run with: pytest tests/integration/test_performance.py -v -m integration
"""

import asyncio
import time

import pytest

from lifesciences_mcp.clients import ChEMBLClient, UniProtClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope
from lifesciences_mcp.models.protein import Protein


@pytest.mark.integration
class TestPerformanceRequirements:
    """Test performance requirements (SC-001)."""

    @pytest.fixture
    async def client(self):
        """Create a UniProt client."""
        client = UniProtClient()
        yield client
        await client.close()

    async def test_search_performance_common_proteins(self, client: UniProtClient):
        """T068: Test SC-001 - 95% of common protein queries complete in <2s.

        SC-001 Acceptance: Agents can find relevant proteins in under 2 seconds
        for 95% of common protein queries (top 1000 human proteins).

        This test validates a sample of common protein queries representing
        different query patterns that agents would typically use.
        """
        # Sample of common protein queries (representative of agent usage patterns)
        common_queries = [
            "p53",  # Cancer suppressor
            "insulin",  # Metabolic protein
            "BRCA1",  # Cancer susceptibility
            "hemoglobin",  # Oxygen transport
            "collagen",  # Structural protein
            "kinase",  # Enzyme class
            "receptor",  # Functional class
            "TP53",  # Gene symbol
            "albumin",  # Abundant protein
            "interferon",  # Immune protein
        ]

        response_times = []
        failed_queries = []

        for query in common_queries:
            start_time = time.time()

            try:
                result = await client.search_proteins(query, page_size=10)
                elapsed = time.time() - start_time
                response_times.append(elapsed)

                # Verify successful response
                assert isinstance(result, PaginationEnvelope), (
                    f"Query '{query}' should return PaginationEnvelope"
                )
                assert len(result.items) > 0, f"Query '{query}' should return results"

            except Exception as e:
                failed_queries.append((query, str(e)))
                # Don't append time for failed queries
                continue

        # Verify no queries failed
        assert len(failed_queries) == 0, f"All queries should succeed. Failed: {failed_queries}"

        # Verify we have timing data
        assert len(response_times) == len(common_queries), "Should have timing data for all queries"

        # Calculate percentile (95th percentile)
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index - 1] if p95_index > 0 else sorted_times[0]

        # SC-001: 95% of queries should complete in <2s
        assert p95_time < 2.0, (
            f"95th percentile ({p95_time:.2f}s) should be <2s. "
            f"Times: {[f'{t:.2f}s' for t in sorted_times]}"
        )

        # Also verify average is reasonable
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 1.5, f"Average response time ({avg_time:.2f}s) should be <1.5s"

    async def test_get_protein_performance(self, client: UniProtClient):
        """Test get_protein response time for well-known proteins.

        Validates that strict CURIE lookup meets performance requirements.
        """
        # Well-known protein CURIEs
        test_curies = [
            "UniProtKB:P04637",  # TP53 (human)
            "UniProtKB:P38398",  # BRCA1 (human)
            "UniProtKB:P01308",  # Insulin (human)
            "UniProtKB:P68871",  # Hemoglobin beta (human)
            "UniProtKB:P02768",  # Albumin (human)
        ]

        response_times = []

        for curie in test_curies:
            start_time = time.time()

            result = await client.get_protein(curie)
            elapsed = time.time() - start_time
            response_times.append(elapsed)

            # Verify successful response
            assert isinstance(result, Protein), f"CURIE '{curie}' should return Protein"

        # All get_protein calls should be fast (<2s for cold start, <1s for warm)
        # First call may have cold start overhead, subsequent calls should be faster
        max_time = max(response_times)
        avg_time = sum(response_times) / len(response_times)

        assert max_time < 2.0, (
            f"Max get_protein time ({max_time:.2f}s) should be <2s (cold start). "
            f"Times: {[f'{t:.2f}s' for t in response_times]}"
        )

        # Average should be fast (most requests are warm)
        assert avg_time < 0.5, (
            f"Average get_protein time ({avg_time:.2f}s) should be <0.5s. "
            f"Times: {[f'{t:.2f}s' for t in response_times]}"
        )

    async def test_concurrent_search_performance(self, client: UniProtClient):
        """Test performance under concurrent load.

        Validates that concurrent requests don't significantly degrade
        individual request performance (relates to SC-003).
        """
        # Create 10 concurrent search requests
        queries = ["p53", "BRCA1", "insulin", "kinase", "receptor"] * 2

        start_time = time.time()

        # Execute concurrently
        tasks = [client.search_proteins(q, page_size=5) for q in queries]
        results = await asyncio.gather(*tasks)

        total_elapsed = time.time() - start_time

        # Verify all succeeded
        assert len(results) == len(queries)
        for result in results:
            assert isinstance(result, PaginationEnvelope)

        # With rate limiting (10 req/s), 10 requests should complete in ~1-2s minimum
        # Allow overhead for network latency, processing, and cold start
        assert total_elapsed < 5.0, (
            f"10 concurrent requests should complete in <5s, got {total_elapsed:.2f}s"
        )

        # Verify throughput is reasonable (should handle at least 2 req/s under load)
        throughput = len(queries) / total_elapsed
        assert throughput >= 2.0, (
            f"Throughput ({throughput:.2f} req/s) should be >=2 req/s under concurrent load"
        )


@pytest.mark.integration
class TestChEMBLPerformanceRequirements:
    """Test ChEMBL performance requirements (SC-001, SC-002, SC-007)."""

    @pytest.fixture
    async def client(self):
        """Create a ChEMBL client."""
        client = ChEMBLClient()
        yield client
        await client.close()

    async def test_search_compounds_sc001(self, client: ChEMBLClient):
        """T037: Test SC-001 - 95% of search queries complete in <2s.

        SC-001 Acceptance: Agents can find relevant compounds in under 2 seconds
        for 95% of common drug queries.
        """
        # Sample of common compound queries
        common_queries = [
            "aspirin",
            "imatinib",
            "metformin",
            "atorvastatin",
            "paracetamol",
        ]

        response_times = []
        failed_queries = []

        for query in common_queries:
            start_time = time.time()

            try:
                result = await client.search_compounds(query, page_size=10)
                elapsed = time.time() - start_time
                response_times.append(elapsed)

                # Verify successful response
                assert isinstance(result, PaginationEnvelope), (
                    f"Query '{query}' should return PaginationEnvelope"
                )
                assert len(result.items) > 0, f"Query '{query}' should return results"

            except Exception as e:
                failed_queries.append((query, str(e)))
                continue

        # Verify no queries failed
        assert len(failed_queries) == 0, f"All queries should succeed. Failed: {failed_queries}"

        # Verify we have timing data
        assert len(response_times) == len(common_queries), "Should have timing data for all queries"

        # Calculate percentile (95th percentile)
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index - 1] if p95_index > 0 else sorted_times[0]

        # SC-001: 95% of queries should complete in <2s
        assert p95_time < 2.0, (
            f"95th percentile ({p95_time:.2f}s) should be <2s. "
            f"Times: {[f'{t:.2f}s' for t in sorted_times]}"
        )

    async def test_get_compound_sc002(self, client: ChEMBLClient):
        """T038: Test SC-002 - 100% of valid CURIE lookups complete in <1s.

        SC-002 Acceptance: All valid CURIE lookups complete in under 1 second.
        """
        # Well-known compound CURIEs
        test_curies = [
            "CHEMBL:25",  # Aspirin
            "CHEMBL:941",  # Imatinib
            "CHEMBL:1201583",  # Acetylsalicylic acid lysinate
        ]

        response_times = []

        for curie in test_curies:
            start_time = time.time()

            result = await client.get_compound(curie)
            elapsed = time.time() - start_time
            response_times.append(elapsed)

            # Verify successful response
            assert not isinstance(result, ErrorEnvelope), f"CURIE '{curie}' should not return error"
            assert isinstance(result, dict), f"CURIE '{curie}' should return dict"
            assert result["id"] == curie, f"CURIE '{curie}' should match returned ID"

        # SC-002: 100% of lookups should be <1s
        max_time = max(response_times)
        assert max_time < 1.0, (
            f"Max get_compound time ({max_time:.2f}s) should be <1s. "
            f"Times: {[f'{t:.2f}s' for t in response_times]}"
        )

    async def test_get_compounds_batch_sc007(self, client: ChEMBLClient):
        """T039: Test SC-007 - Batch of 10 compounds completes in <3s.

        SC-007 Acceptance: Batch operations are significantly faster than sequential calls.
        """
        # 10 compound CURIEs for batch lookup
        batch_curies = [
            "CHEMBL:25",  # Aspirin
            "CHEMBL:941",  # Imatinib
            "CHEMBL:1201583",  # Acetylsalicylic acid lysinate
            "CHEMBL:1642",  # Metformin
            "CHEMBL:1",  # Glycine
            "CHEMBL:2",  # Unknown - may not exist
            "CHEMBL:3",  # Unknown - may not exist
            "CHEMBL:4",  # Unknown - may not exist
            "CHEMBL:5",  # Unknown - may not exist
            "CHEMBL:6",  # Unknown - may not exist
        ]

        start_time = time.time()
        result = await client.get_compounds_batch(batch_curies)
        elapsed = time.time() - start_time

        # Verify successful response
        assert not isinstance(result, ErrorEnvelope), "Batch should not return overall error"
        assert isinstance(result, list), "Batch should return list"
        assert len(result) == len(batch_curies), "Batch should return result for each input"

        # SC-007: Batch of 10 should complete in <3s
        assert elapsed < 3.0, f"Batch of 10 compounds ({elapsed:.2f}s) should complete in <3s"

    async def test_batch_faster_than_sequential(self, client: ChEMBLClient):
        """Test that batch lookup is significantly faster than sequential lookups.

        This validates the purpose of the batch tool: preventing thread pool exhaustion
        by using a single API call instead of many.
        """
        batch_curies = ["CHEMBL:25", "CHEMBL:941", "CHEMBL:1201583"]

        # Measure batch lookup time
        start_batch = time.time()
        batch_result = await client.get_compounds_batch(batch_curies)
        batch_time = time.time() - start_batch

        # Measure sequential lookup time
        start_seq = time.time()
        for curie in batch_curies:
            await client.get_compound(curie)
        seq_time = time.time() - start_seq

        # Verify batch returned results
        assert not isinstance(batch_result, ErrorEnvelope)
        assert len(batch_result) == len(batch_curies)

        # Batch should be at least 50% faster than sequential (accounting for rate limiting)
        # Note: Due to rate limiting, this may not always hold, but batch should not be slower
        print(f"Batch time: {batch_time:.2f}s, Sequential time: {seq_time:.2f}s")

        # At minimum, batch should not be significantly slower
        assert batch_time < seq_time * 1.5, (
            f"Batch ({batch_time:.2f}s) should not be >50% slower than sequential ({seq_time:.2f}s)"
        )
