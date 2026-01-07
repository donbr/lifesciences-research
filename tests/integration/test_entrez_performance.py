"""Performance tests for NCBI Entrez MCP Server.

Validates SC-001: 95% of queries complete in < 2 seconds.

Run with: pytest tests/integration/test_entrez_performance.py -v -m integration
"""

import time

import pytest

from lifesciences_mcp.clients import EntrezClient


@pytest.mark.integration
class TestEntrezPerformance:
    """Performance tests validating SC-001 success criterion."""

    @pytest.fixture
    async def client(self):
        """Create an Entrez client."""
        client = EntrezClient()
        yield client
        await client.close()

    async def test_search_genes_performance(self, client: EntrezClient):
        """Validate that 95% of search_genes queries complete in < 2 seconds (SC-001)."""
        # Test queries - mix of common and specific genes
        test_queries = [
            "BRCA1",
            "TP53",
            "EGFR",
            "KRAS",
            "ALK",
            "tumor suppressor",
            "kinase",
            "receptor",
            "transcription factor",
            "DNA repair",
            "CDK2",
            "MYC",
            "PTEN",
            "BRAF",
            "HER2",
            "insulin",
            "p53",
            "beta actin",
            "hemoglobin",
            "cytochrome",
        ]

        response_times = []

        # Run each query and measure time
        for query in test_queries:
            start = time.time()
            await client.search_genes(query, organism="human")
            elapsed = time.time() - start
            response_times.append(elapsed)

        # Calculate 95th percentile
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index]

        # Validate SC-001: 95% of queries < 2 seconds
        assert p95_time < 2.0, (
            f"SC-001 FAILED: 95th percentile time was {p95_time:.2f}s, "
            f"expected < 2.0s. Times: {sorted_times}"
        )

        # Report statistics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        print(f"\nPerformance Statistics:")
        print(f"  Total queries: {len(response_times)}")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Max time: {max_time:.3f}s")
        print(f"  95th percentile: {p95_time:.3f}s")
        print(f"  SC-001 Status: PASS ({p95_time:.3f}s < 2.0s)")

    async def test_get_gene_performance(self, client: EntrezClient):
        """Validate that get_gene queries complete in < 2 seconds."""
        # Test with several well-known gene IDs
        test_gene_ids = [
            "NCBIGene:7157",  # TP53
            "NCBIGene:672",   # BRCA1
            "NCBIGene:1956",  # EGFR
            "NCBIGene:3845",  # KRAS
            "NCBIGene:238",   # ALK
            "NCBIGene:5728",  # PTEN
            "NCBIGene:673",   # BRAF
            "NCBIGene:4609",  # MYC
            "NCBIGene:1017",  # CDK2
            "NCBIGene:2064",  # ERBB2/HER2
        ]

        response_times = []

        for gene_id in test_gene_ids:
            start = time.time()
            await client.get_gene(gene_id)
            elapsed = time.time() - start
            response_times.append(elapsed)

        # All lookups should be fast
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index]

        assert p95_time < 2.0, (
            f"get_gene 95th percentile was {p95_time:.2f}s, expected < 2.0s"
        )

        avg_time = sum(response_times) / len(response_times)
        print(f"\nget_gene Performance:")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  95th percentile: {p95_time:.3f}s")

    async def test_get_pubmed_links_performance(self, client: EntrezClient):
        """Validate that get_pubmed_links queries complete in < 2 seconds."""
        # Test with genes that have many publications
        test_gene_ids = [
            "NCBIGene:7157",  # TP53 - highly studied
            "NCBIGene:672",   # BRCA1 - highly studied
            "NCBIGene:1956",  # EGFR
            "NCBIGene:3845",  # KRAS
            "NCBIGene:238",   # ALK
        ]

        response_times = []

        for gene_id in test_gene_ids:
            start = time.time()
            await client.get_pubmed_links(gene_id, limit=10)
            elapsed = time.time() - start
            response_times.append(elapsed)

        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index]

        assert p95_time < 2.0, (
            f"get_pubmed_links 95th percentile was {p95_time:.2f}s, expected < 2.0s"
        )

        avg_time = sum(response_times) / len(response_times)
        print(f"\nget_pubmed_links Performance:")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  95th percentile: {p95_time:.3f}s")

    async def test_rate_limiting_performance(self, client: EntrezClient):
        """Validate that rate limiting doesn't cause excessive delays."""
        # Perform 5 rapid sequential searches
        # With 3 req/s limit, this should take ~1.5 seconds
        # With 10 req/s limit, this should take ~0.5 seconds

        start = time.time()
        for i in range(5):
            await client.search_genes(f"gene{i}", page_size=5)
        total_time = time.time() - start

        # Should take at least (5-1) * rate_limit_delay
        # For 3 req/s (0.333s delay), min time ~1.33s
        # For 10 req/s (0.1s delay), min time ~0.4s
        min_expected = 4 * client.rate_limit_delay

        assert total_time >= min_expected, (
            f"Rate limiting not enforced: took {total_time:.2f}s, "
            f"expected at least {min_expected:.2f}s"
        )

        # Should not take more than 2x the minimum (allows for network variance)
        max_expected = min_expected * 2.5
        assert total_time < max_expected, (
            f"Rate limiting too slow: took {total_time:.2f}s, "
            f"expected less than {max_expected:.2f}s"
        )

        print(f"\nRate Limiting Performance:")
        print(f"  5 sequential queries: {total_time:.3f}s")
        print(f"  Rate limit delay: {client.rate_limit_delay:.3f}s")
        print(f"  Expected range: {min_expected:.3f}s - {max_expected:.3f}s")
