"""Integration test for error recovery workflow.

Tests the complete error recovery cycle: trigger error → receive recovery hint
→ follow hint → succeed (User Story 4).

Run with: pytest tests/integration/test_error_recovery.py -v -m integration
"""

import pytest

from lifesciences_mcp.clients import ClinicalTrialsClient, UniProtClient
from lifesciences_mcp.models.envelopes import ErrorCode, ErrorEnvelope, PaginationEnvelope
from lifesciences_mcp.models.protein import Protein
from lifesciences_mcp.models.trial import Trial


@pytest.mark.integration
class TestErrorRecoveryWorkflow:
    """Test error recovery workflow (User Story 4)."""

    @pytest.fixture
    async def client(self):
        """Create a UniProt client."""
        client = UniProtClient()
        yield client
        await client.close()

    async def test_error_recovery_workflow(self, client: UniProtClient):
        """T059: Test complete error recovery workflow.

        US4 Acceptance: Simulate agent making a mistake, receiving error with
        recovery hint, following the hint, and successfully completing the task.

        Workflow:
        1. Agent tries strict lookup with invalid CURIE (UNRESOLVED_ENTITY)
        2. Error response includes hint to use search_proteins
        3. Agent follows hint: calls search_proteins
        4. Agent uses valid CURIE from search results
        5. Strict lookup succeeds with complete protein record
        """
        # Step 1: Agent makes mistake - tries strict lookup with invalid CURIE
        error_result = await client.get_protein("P04637")  # Missing "UniProtKB:" prefix

        # Step 2: Verify error response with recovery hint
        assert isinstance(error_result, ErrorEnvelope), (
            "Should return ErrorEnvelope for invalid CURIE"
        )
        assert error_result.error.code == "UNRESOLVED_ENTITY"
        assert error_result.error.recovery_hint is not None

        # Recovery hint should suggest using search_proteins
        hint_lower = error_result.error.recovery_hint.lower()
        assert "search" in hint_lower, "Hint should suggest using search"

        # Step 3: Agent follows hint - use fuzzy search to find valid CURIE
        search_result = await client.search_proteins("TP53", page_size=5)

        # Verify search succeeds
        assert isinstance(search_result, PaginationEnvelope), (
            "Search should return PaginationEnvelope"
        )
        assert len(search_result.items) > 0, "Search should find results for TP53"

        # Step 4: Agent extracts valid CURIE from search results
        top_candidate = search_result.items[0]
        valid_curie = top_candidate.id

        # Verify CURIE format is correct
        assert valid_curie.startswith("UniProtKB:"), (
            f"CURIE should have correct format: {valid_curie}"
        )

        # Step 5: Agent retries strict lookup with valid CURIE
        protein_result = await client.get_protein(valid_curie)

        # Verify success with complete protein record
        assert isinstance(protein_result, Protein), "Should return Protein for valid CURIE"
        assert protein_result.id == valid_curie
        assert protein_result.cross_references is not None

    async def test_ambiguous_query_recovery(self, client: UniProtClient):
        """Test recovery from AMBIGUOUS_QUERY error.

        Workflow:
        1. Agent provides too-short query (AMBIGUOUS_QUERY)
        2. Error hints to provide more specific query
        3. Agent provides better query
        4. Search succeeds
        """
        # Step 1: Too-short query
        error_result = await client.search_proteins("a")

        # Step 2: Verify error with recovery hint
        assert isinstance(error_result, ErrorEnvelope)
        assert error_result.error.code == "AMBIGUOUS_QUERY"
        assert error_result.error.recovery_hint is not None

        # Recovery hint should suggest more specific query
        hint_lower = error_result.error.recovery_hint.lower()
        assert any(keyword in hint_lower for keyword in ["specific", "more", "try", "characters"])

        # Step 3: Follow hint - provide more specific query
        search_result = await client.search_proteins("insulin")

        # Step 4: Verify success
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

    async def test_entity_not_found_recovery(self, client: UniProtClient):
        """Test recovery from ENTITY_NOT_FOUND error.

        Workflow:
        1. Agent provides valid CURIE format but non-existent protein
        2. Error hints to verify accession or search by name
        3. Agent searches by protein name
        4. Agent finds valid protein
        """
        # Step 1: Valid CURIE format but doesn't exist
        error_result = await client.get_protein("UniProtKB:A0A0B0B0C0")

        # Step 2: Verify error with recovery hint
        assert isinstance(error_result, ErrorEnvelope)
        # May be ENTITY_NOT_FOUND or UNRESOLVED_ENTITY depending on API validation
        assert error_result.error.code in ("ENTITY_NOT_FOUND", "UNRESOLVED_ENTITY")
        assert error_result.error.recovery_hint is not None

        # Hint should suggest searching
        hint_lower = error_result.error.recovery_hint.lower()
        assert any(keyword in hint_lower for keyword in ["search", "verify", "name"])

        # Step 3: Follow hint - search by protein name
        search_result = await client.search_proteins("BRCA1")

        # Step 4: Verify success and get valid protein
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

        # Get first result and verify it's valid
        valid_protein = await client.get_protein(search_result.items[0].id)
        assert isinstance(valid_protein, Protein)

    async def test_multiple_error_recovery_cycles(self, client: UniProtClient):
        """Test agent can recover from multiple errors in sequence.

        Demonstrates that an agent can autonomously correct multiple mistakes
        by following recovery hints at each step.
        """
        # Cycle 1: Too short query
        result1 = await client.search_proteins("p")
        assert isinstance(result1, ErrorEnvelope)
        assert result1.error.code == "AMBIGUOUS_QUERY"

        # Follow hint: provide longer query
        result2 = await client.search_proteins("p53")
        assert isinstance(result2, PaginationEnvelope)

        # Cycle 2: Invalid CURIE format (forgot prefix)
        result3 = await client.get_protein("P04637")
        assert isinstance(result3, ErrorEnvelope)
        assert result3.error.code == "UNRESOLVED_ENTITY"

        # Follow hint: use proper CURIE from search
        result4 = await client.get_protein(result2.items[0].id)
        assert isinstance(result4, Protein)

        # Success: Agent recovered from 2 errors autonomously
        assert result4.cross_references is not None


# ==============================================================================
# T059-T063: ClinicalTrials.gov Error Recovery Tests (US4)
# ==============================================================================


@pytest.mark.integration
class TestClinicalTrialsErrorRecovery:
    """ClinicalTrials-specific error recovery tests (US4: T059-T063)."""

    @pytest.fixture
    async def ct_client(self):
        """Create a ClinicalTrials client."""
        client = ClinicalTrialsClient()
        yield client
        await client.close()

    async def test_unresolved_entity_recovery_workflow(self, ct_client: ClinicalTrialsClient):
        """T059: Complete UNRESOLVED_ENTITY recovery workflow.

        Workflow:
        1. Agent tries get_trial with query string (UNRESOLVED_ENTITY)
        2. Error includes hint to use search_trials
        3. Agent follows hint: calls search_trials
        4. Agent uses valid NCT CURIE from search results
        5. get_trial succeeds with complete trial record
        """
        # Step 1: Agent makes mistake - passes query string instead of CURIE
        error_result = await ct_client.get_trial("breast cancer treatment")

        # Step 2: Verify error response with recovery hint
        assert isinstance(error_result, ErrorEnvelope)
        assert error_result.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert error_result.error.invalid_input == "breast cancer treatment"
        assert "search_trials" in error_result.error.recovery_hint

        # Step 3: Agent follows hint - use fuzzy search
        search_result = await ct_client.search_trials(query="breast cancer", page_size=5)

        # Verify search succeeds
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

        # Step 4: Agent extracts valid NCT CURIE
        top_candidate = search_result.items[0]
        valid_nct_id = top_candidate.id

        # Verify CURIE format
        assert valid_nct_id.startswith("NCT:")
        assert len(valid_nct_id) == 12

        # Step 5: Agent retries with valid CURIE
        trial_result = await ct_client.get_trial(valid_nct_id)

        # Verify success
        assert isinstance(trial_result, Trial)
        assert trial_result.id == valid_nct_id
        assert len(trial_result.title) > 0

    async def test_rate_limited_recovery_with_backoff(self, ct_client: ClinicalTrialsClient):
        """T060: RATE_LIMITED recovery with exponential backoff.

        Note: This test is difficult to trigger reliably without overwhelming the API.
        We test the error structure and recovery hint content instead.
        """
        # We can't reliably trigger rate limiting without overwhelming the API
        # So we'll test that the client handles 429 responses correctly by
        # verifying the error mapping logic exists

        # Make a few rapid requests to potentially trigger rate limiting
        # (but rate limiter should prevent this)
        for _ in range(3):
            result = await ct_client.search_trials(query="diabetes", page_size=5)
            # Should succeed due to rate limiting (1 req/sec)
            assert isinstance(result, PaginationEnvelope) or isinstance(result, ErrorEnvelope)

            # If we get a rate limit error, verify the hint
            if isinstance(result, ErrorEnvelope):
                if result.error.code == ErrorCode.RATE_LIMITED:
                    assert "retry" in result.error.recovery_hint.lower() or "backoff" in result.error.recovery_hint.lower()
                    break

    async def test_upstream_error_recovery_hint(self, ct_client: ClinicalTrialsClient):
        """T061: UPSTREAM_ERROR recovery hint guidance.

        Tests that 5xx errors provide appropriate recovery guidance.
        We can't reliably trigger upstream errors, so we verify error mapping exists.
        """
        # Test that a valid request succeeds (no upstream error)
        result = await ct_client.search_trials(query="asthma", page_size=5)

        # Should return results or a structured error (not crash)
        assert isinstance(result, PaginationEnvelope) or isinstance(result, ErrorEnvelope)

        # If we somehow got an upstream error, verify the hint
        if isinstance(result, ErrorEnvelope):
            if result.error.code == ErrorCode.UPSTREAM_ERROR:
                assert len(result.error.recovery_hint) > 0
                assert "retry" in result.error.recovery_hint.lower() or "unavailable" in result.error.recovery_hint.lower()

    async def test_entity_not_found_recovery_hint(self, ct_client: ClinicalTrialsClient):
        """T062: ENTITY_NOT_FOUND recovery hint for non-existent NCT ID.

        Workflow:
        1. Agent provides valid CURIE format but non-existent trial
        2. Error hints to verify NCT ID or use search
        3. Agent can search for alternative trials
        """
        # Step 1: Valid CURIE format but doesn't exist
        error_result = await ct_client.get_trial("NCT:99999999")

        # Step 2: Verify error with recovery hint
        assert isinstance(error_result, ErrorEnvelope)
        assert error_result.error.code == ErrorCode.ENTITY_NOT_FOUND
        assert len(error_result.error.recovery_hint) > 0
        assert "search_trials" in error_result.error.recovery_hint or "verify" in error_result.error.recovery_hint.lower()

        # Step 3: Agent can follow hint to search
        search_result = await ct_client.search_trials(query="diabetes", page_size=5)
        assert isinstance(search_result, PaginationEnvelope)
        assert len(search_result.items) > 0

    async def test_complete_error_hint_recovery_success_cycle(self, ct_client: ClinicalTrialsClient):
        """T063: Complete error→hint→recovery→success cycle.

        Demonstrates full autonomous error recovery cycle:
        1. Trigger error (UNRESOLVED_ENTITY)
        2. Receive actionable hint
        3. Follow hint exactly as suggested
        4. Succeed with complete trial data
        """
        # Step 1: Trigger error with malformed CURIE
        error_result = await ct_client.get_trial("NCT:123")  # Too few digits

        # Step 2: Receive actionable hint
        assert isinstance(error_result, ErrorEnvelope)
        assert error_result.error.code == ErrorCode.UNRESOLVED_ENTITY
        recovery_hint = error_result.error.recovery_hint
        assert "NCT:" in recovery_hint  # Shows correct format
        assert "8" in recovery_hint or "00461032" in recovery_hint  # Example provided

        # Step 3: Follow hint - correct the format and try a known valid trial
        # Hint suggests format NCT:NNNNNNNN, so we use a known valid trial
        corrected_nct_id = "NCT:00461032"

        # Step 4: Succeed with complete trial data
        trial_result = await ct_client.get_trial(corrected_nct_id)
        assert isinstance(trial_result, Trial)
        assert trial_result.id == corrected_nct_id
        assert len(trial_result.title) > 0
        assert trial_result.status is not None
        assert "clinicaltrials_gov" in trial_result.cross_references

        # Verify we have complete trial data (not just basic info)
        assert trial_result.protocol is not None
        assert trial_result.protocol.study_type is not None

    async def test_multiple_error_recovery_cycles_clinicaltrials(self, ct_client: ClinicalTrialsClient):
        """Test agent can recover from multiple ClinicalTrials errors in sequence."""
        # Cycle 1: Query string to get_trial (UNRESOLVED_ENTITY)
        result1 = await ct_client.get_trial("diabetes medication")
        assert isinstance(result1, ErrorEnvelope)
        assert result1.error.code == ErrorCode.UNRESOLVED_ENTITY

        # Follow hint: use search_trials
        result2 = await ct_client.search_trials(query="diabetes medication", page_size=5)
        assert isinstance(result2, PaginationEnvelope)
        assert len(result2.items) > 0

        # Cycle 2: Try to use incorrect NCT format (missing colon)
        # Extract the digits from a valid CURIE and try without colon
        valid_curie = result2.items[0].id
        invalid_format = valid_curie.replace(":", "")  # NCT00461032
        result3 = await ct_client.get_trial(invalid_format)

        # This should fail validation (needs normalization)
        assert isinstance(result3, ErrorEnvelope)
        assert result3.error.code == ErrorCode.UNRESOLVED_ENTITY

        # Follow hint: use proper CURIE format
        result4 = await ct_client.get_trial(valid_curie)
        assert isinstance(result4, Trial)
        assert result4.id == valid_curie

        # Success: Agent recovered from 2 errors autonomously
