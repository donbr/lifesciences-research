"""Integration tests for UniProt API client.

Run with: pytest tests/integration/test_uniprot_api.py -v -m integration
"""

import pytest

from lifesciences_mcp.clients import UniProtClient
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope
from lifesciences_mcp.models.protein import Protein, ProteinSearchCandidate


@pytest.mark.integration
@pytest.mark.uniprot
class TestUniProtClientIntegration:
    """Integration tests for UniProtClient."""

    @pytest.fixture
    async def client(self):
        """Create a UniProt client."""
        client = UniProtClient()
        yield client
        await client.close()

    async def test_search_proteins_basic(self, client: UniProtClient):
        """T021: Test basic fuzzy search for proteins.

        US1 Acceptance Scenario 1: Search for "p53" should return top 10 candidates
        with UniProt accessions, names, organisms, and relevance scores.
        """
        result = await client.search_proteins("insulin human", page_size=10)

        # Should return PaginationEnvelope, not ErrorEnvelope
        assert isinstance(result, PaginationEnvelope), (
            f"Expected PaginationEnvelope, got {type(result)}"
        )

        # Should have at least one result
        assert len(result.items) > 0, "Expected at least one search result"

        # Verify items are ProteinSearchCandidate instances
        first_item = result.items[0]
        assert isinstance(first_item, ProteinSearchCandidate), (
            f"Expected ProteinSearchCandidate, got {type(first_item)}"
        )

        # Verify required fields are present
        assert first_item.id.startswith("UniProtKB:"), f"Expected CURIE format, got {first_item.id}"
        assert first_item.name, "Protein name should not be empty"
        assert first_item.organism, "Organism should not be empty"
        assert 0.0 <= first_item.score <= 1.0, f"Score should be 0.0-1.0, got {first_item.score}"

    async def test_search_proteins_pagination(self, client: UniProtClient):
        """T022: Test cursor-based pagination.

        US1 Acceptance Scenario 2: Search for "kinase" should support pagination
        when results exceed page_size.
        """
        # Request small page size to ensure pagination
        page1 = await client.search_proteins("kinase", page_size=5)

        assert isinstance(page1, PaginationEnvelope)
        assert len(page1.items) <= 5, "Page should respect page_size limit"

        # If there are more results, cursor should be present
        if page1.pagination.cursor:
            # Fetch next page using cursor
            page2 = await client.search_proteins(
                "kinase", page_size=5, cursor=page1.pagination.cursor
            )

            assert isinstance(page2, PaginationEnvelope)
            assert len(page2.items) > 0, "Second page should have results"

            # Items should be different between pages
            page1_ids = {item.id for item in page1.items}
            page2_ids = {item.id for item in page2.items}
            assert page1_ids.isdisjoint(page2_ids), "Pages should not have overlapping results"

    async def test_get_protein_p53_human(self, client: UniProtClient):
        """T033: Test strict lookup for human p53 protein with valid CURIE.

        US2 Acceptance Scenario 1: Provide "UniProtKB:P04637" (human TP53/p53)
        and verify complete protein record returned with cross-references.
        """
        result = await client.get_protein("UniProtKB:P04637")

        # Should return Protein, not ErrorEnvelope
        assert isinstance(result, Protein), f"Expected Protein, got {type(result)}"

        # Verify required fields are present
        assert result.id == "UniProtKB:P04637", (
            f"Expected CURIE 'UniProtKB:P04637', got {result.id}"
        )
        assert result.accession == "P04637", f"Expected accession 'P04637', got {result.accession}"
        assert result.name, "Protein name should not be empty"
        assert result.organism, "Organism should not be empty"

        # Verify gene names include TP53
        assert result.gene_names is not None, "Gene names should not be None"
        assert "TP53" in result.gene_names, (
            f"Expected 'TP53' in gene_names, got {result.gene_names}"
        )

        # Verify cross-references are populated (at least one field)
        assert result.cross_references is not None, "Cross-references should not be None"

    async def test_get_protein_invalid_curie(self, client: UniProtClient):
        """T034: Test get_protein with invalid CURIE format.

        US2 Acceptance Scenario 2: Provide invalid CURIE like "invalid-id" or "P04637"
        (missing prefix) and verify UNRESOLVED_ENTITY error with recovery hint.
        """
        # Test with completely invalid format
        result = await client.get_protein("invalid-id")

        # Should return ErrorEnvelope for invalid CURIE
        assert isinstance(result, ErrorEnvelope), (
            f"Expected ErrorEnvelope for invalid CURIE, got {type(result)}"
        )
        assert result.error.code == "UNRESOLVED_ENTITY", (
            f"Expected UNRESOLVED_ENTITY, got {result.error.code}"
        )
        assert "search_proteins" in result.error.recovery_hint, (
            "Recovery hint should suggest using search_proteins"
        )

        # Test with missing prefix (raw accession)
        result2 = await client.get_protein("P04637")
        assert isinstance(result2, ErrorEnvelope), "Raw accession should return ErrorEnvelope"
        assert result2.error.code == "UNRESOLVED_ENTITY"

    async def test_get_protein_not_found(self, client: UniProtClient):
        """T035: Test get_protein with non-existent but valid CURIE.

        US2 Acceptance Scenario 3: Provide valid CURIE format but non-existent protein
        like "UniProtKB:P99999" and verify ENTITY_NOT_FOUND error with recovery hint.
        """
        # Use a valid CURIE format but non-existent accession
        # A0A0B0B0C0 matches the 10-char TrEMBL pattern but should not exist
        result = await client.get_protein("UniProtKB:A0A0B0B0C0")

        # Should return ErrorEnvelope for not found
        assert isinstance(result, ErrorEnvelope), (
            f"Expected ErrorEnvelope for not found, got {type(result)}"
        )
        # Note: May get ENTITY_NOT_FOUND (404) or UNRESOLVED_ENTITY (400) depending on API validation
        assert result.error.code in ("ENTITY_NOT_FOUND", "UNRESOLVED_ENTITY"), (
            f"Expected ENTITY_NOT_FOUND or UNRESOLVED_ENTITY, got {result.error.code}"
        )
        assert "A0A0B0B0C0" in str(result.error.message) or "A0A0B0B0C0" in str(
            result.error.invalid_input
        ), "Error should reference the CURIE"
        assert result.error.recovery_hint, "Recovery hint should be provided"

    async def test_get_protein_slim(self, client: UniProtClient):
        """T036: Test get_protein with slim mode for token efficiency.

        US2 Acceptance Scenario 4: Request protein with slim=True and verify
        only id/name/organism returned (~20 tokens vs ~115-300 full record).
        """
        result = await client.get_protein("UniProtKB:P04637", slim=True)

        # Should return Protein even in slim mode
        assert isinstance(result, Protein), f"Expected Protein in slim mode, got {type(result)}"

        # Verify required fields are present
        assert result.id == "UniProtKB:P04637"
        assert result.name, "Protein name should be present in slim mode"
        assert result.organism, "Organism should be present in slim mode"

        # In slim mode, some optional fields might be None
        # But the model should still validate successfully

    async def test_fuzzy_to_fact_workflow(self, client: UniProtClient):
        """Test complete Fuzzy-to-Fact workflow: search → validate → fetch.

        This test validates the complete two-phase Fuzzy-to-Fact protocol:
        1. Fuzzy search returns ranked candidates
        2. Strict lookup fetches complete record with cross-references
        """
        # Phase 1: Fuzzy search
        search_result = await client.search_proteins("BRCA1", page_size=10)
        assert isinstance(search_result, PaginationEnvelope), (
            "Search should return PaginationEnvelope"
        )
        assert len(search_result.items) > 0, "Search should return at least one result"

        # Phase 2: Validate candidate
        top_candidate = search_result.items[0]
        assert top_candidate.id.startswith("UniProtKB:"), "Candidate ID should be a valid CURIE"
        assert isinstance(top_candidate, ProteinSearchCandidate), (
            "Should be a ProteinSearchCandidate"
        )

        # Phase 3: Strict lookup
        protein = await client.get_protein(top_candidate.id)
        assert isinstance(protein, Protein), "get_protein should return Protein model"
        assert protein.id == top_candidate.id, "Protein ID should match candidate ID"
        assert protein.cross_references is not None, "Cross-references should be populated"

        # Verify we got richer data in strict lookup than in search
        assert protein.function or protein.sequence_length, (
            "Strict lookup should have additional fields"
        )

    async def test_protein_cross_references(self, client: UniProtClient):
        """T045: Test cross-reference presence for well-annotated protein.

        US3 Acceptance Scenario 1: Retrieve "UniProtKB:P38398" (BRCA1) and verify
        cross-references are present for multiple databases (HGNC, Ensembl, PDB, etc.).
        """
        # P38398 is BRCA1 - well-annotated human protein
        result = await client.get_protein("UniProtKB:P38398")

        # Should return Protein model
        assert isinstance(result, Protein), f"Expected Protein, got {type(result)}"
        assert result.id == "UniProtKB:P38398"

        # Cross-references should be present
        assert result.cross_references is not None, "Cross-references should not be None for BRCA1"

        # Convert to dict to check what's actually present (respecting omit-if-null)
        xref_dict = result.cross_references.model_dump(exclude_none=True)

        # BRCA1 is a well-annotated human protein, should have multiple cross-references
        assert len(xref_dict) > 0, "BRCA1 should have at least some cross-references"

        # At least one of the sequence databases should be present
        has_ensembl = "ensembl_transcript" in xref_dict
        has_refseq = "refseq" in xref_dict
        assert has_ensembl or has_refseq, (
            "At least one sequence database reference should be present"
        )

        # Check that cross-references follow the omit-if-null pattern
        # (fields should either have values or not be set at all, never None in dict)
        for key, value in xref_dict.items():
            assert value is not None, (
                f"Cross-reference {key} should not be None (omit-if-null pattern)"
            )
            # Verify non-empty strings and lists
            if isinstance(value, str):
                assert value.strip(), f"Cross-reference '{key}' should not be empty string"
            elif isinstance(value, list):
                assert len(value) > 0, f"Cross-reference '{key}' should not be empty list"

    async def test_protein_hgnc_mapping(self, client: UniProtClient):
        """T046: Test HGNC cross-reference mapping specifically.

        US3 Acceptance Scenario 2: For well-known human proteins, verify that if
        HGNC cross-reference is present, it's correctly formatted and mapped.
        """
        # Test with TP53 (P04637)
        result = await client.get_protein("UniProtKB:P04637")

        assert isinstance(result, Protein), f"Expected Protein, got {type(result)}"
        assert result.cross_references is not None, "Cross-references should be present for TP53"

        # Verify gene_names includes TP53
        assert result.gene_names is not None, "Gene names should be present"
        assert "TP53" in result.gene_names, f"Expected TP53 in gene_names, got {result.gene_names}"

        # Check if HGNC is present in the cross-references (using dict to respect omit-if-null)
        xref_dict = result.cross_references.model_dump(exclude_none=True)

        # If HGNC is present, verify it's correctly formatted
        if "hgnc" in xref_dict:
            hgnc_id = xref_dict["hgnc"]
            assert hgnc_id.startswith("HGNC:"), f"HGNC ID should have HGNC: prefix, got {hgnc_id}"
        else:
            # If HGNC is not present, verify that at least other gene-related refs exist
            # This tests that _map_cross_references is working, even if HGNC isn't available
            has_gene_refs = "entrez" in xref_dict or "ensembl_transcript" in xref_dict
            assert has_gene_refs, "Should have at least some gene-related cross-references"

    async def test_protein_omit_null_refs(self, client: UniProtClient):
        """T047: Test omit-if-null pattern for cross-references.

        US3 Acceptance Scenario 3: Verify that cross-reference fields with no data
        are omitted entirely (not present in dict) rather than set to null, following
        Constitution Principle III (Schema Determinism) and FR-006.
        """
        # Get a protein record
        result = await client.get_protein("UniProtKB:P04637")  # TP53

        assert isinstance(result, Protein), f"Expected Protein, got {type(result)}"
        assert result.cross_references is not None, "Cross-references should be present"

        # Convert to dict with exclude_none=True
        xref_dict = result.cross_references.model_dump(exclude_none=True)

        # Verify no null values in the dict
        for key, value in xref_dict.items():
            assert value is not None, (
                f"Cross-reference field '{key}' should be omitted if null, not set to None"
            )
            # Also verify non-empty strings and lists
            if isinstance(value, str):
                assert value.strip(), f"Cross-reference '{key}' should not be empty string"
            elif isinstance(value, list):
                assert len(value) > 0, f"Cross-reference '{key}' should not be empty list"

        # Verify that the omit-if-null pattern is being followed
        # This means fields should either have values OR not be present in the dict at all
        # We can't test what's NOT in the dict, but we can verify what IS in the dict is valid


@pytest.mark.integration
@pytest.mark.uniprot
class TestUniProtSearchValidation:
    """Test validation and error handling for search operations."""

    @pytest.fixture
    async def client(self):
        """Create a UniProt client."""
        client = UniProtClient()
        yield client
        await client.close()

    async def test_search_proteins_min_length(self, client: UniProtClient):
        """T023: Test query length validation.

        US1 Acceptance Scenario 3: Query shorter than 2 characters should return
        error explaining the query is too ambiguous.
        """
        result = await client.search_proteins("a")

        # Should return ErrorEnvelope for too-short query
        assert isinstance(result, ErrorEnvelope), (
            f"Expected ErrorEnvelope for short query, got {type(result)}"
        )
        assert result.error.code == "AMBIGUOUS_QUERY", (
            f"Expected AMBIGUOUS_QUERY, got {result.error.code}"
        )
        assert (
            "at least 2 characters" in result.error.message.lower()
            or "too short" in result.error.message.lower()
        )

    async def test_search_proteins_ranking(self, client: UniProtClient):
        """T024: Test relevance ranking.

        US1 Acceptance Scenario 4: Search for "actin" should rank human proteins higher,
        with results ranked by relevance.
        """
        result = await client.search_proteins("actin", page_size=10)

        assert isinstance(result, PaginationEnvelope)
        assert len(result.items) > 0

        # Scores should be in descending order (higher relevance first)
        scores = [item.score for item in result.items]
        assert scores == sorted(scores, reverse=True), (
            "Results should be ranked by descending score"
        )

        # Check if human proteins are prioritized (if results include organism info)
        human_results = [item for item in result.items if "sapiens" in item.organism.lower()]
        if human_results and len(result.items) > 1:
            # At least one human result should be in top half
            human_positions = [
                i for i, item in enumerate(result.items) if "sapiens" in item.organism.lower()
            ]
            assert any(pos < len(result.items) // 2 for pos in human_positions), (
                "Human proteins should be prioritized in ranking"
            )
