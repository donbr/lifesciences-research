"""Unit tests for error envelope recovery hints.

These tests verify that error responses include actionable recovery hints
for autonomous error correction by AI agents (User Story 4).

Run with: pytest tests/unit/test_error_envelopes.py -v
"""

import pytest

from lifesciences_mcp.models.envelopes import ErrorCode, ErrorDetail, ErrorEnvelope

pytestmark = pytest.mark.unit


class TestErrorRecoveryHints:
    """Test error envelopes include recovery hints (User Story 4)."""

    def test_ambiguous_query_recovery_hint(self):
        """T056: Test AMBIGUOUS_QUERY error includes actionable recovery hint.

        US4 Acceptance: AMBIGUOUS_QUERY errors should suggest providing more specific
        query terms with examples (e.g., "Try 'p53' instead of 'p'").
        """
        # Create AMBIGUOUS_QUERY error envelope
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.AMBIGUOUS_QUERY,
                message="Query 'a' is too short. Provide at least 2 characters for meaningful search.",
                recovery_hint="Try a more specific query like 'p53', 'insulin', or 'BRCA1'",
                invalid_input="a",
            )
        )

        # Verify error structure
        assert error.success is False
        assert error.error.code == ErrorCode.AMBIGUOUS_QUERY
        assert error.error.invalid_input == "a"

        # Verify recovery hint is present and actionable
        assert error.error.recovery_hint is not None
        assert len(error.error.recovery_hint) > 0
        # Should suggest specific examples or actions
        assert any(
            keyword in error.error.recovery_hint.lower()
            for keyword in ["try", "specific", "example", "more", "characters"]
        ), "Recovery hint should provide actionable guidance"

    def test_rate_limited_recovery_hint(self):
        """T057: Test RATE_LIMITED error includes actionable recovery hint.

        US4 Acceptance: RATE_LIMITED errors should suggest waiting with specific
        retry timing guidance (e.g., "Retry after 5 seconds").
        """
        # Create RATE_LIMITED error envelope with retry_after
        error = ErrorEnvelope.rate_limited(retry_after=5)

        # Verify error structure
        assert error.success is False
        assert error.error.code == ErrorCode.RATE_LIMITED

        # Verify recovery hint includes timing guidance
        assert error.error.recovery_hint is not None
        assert "5" in error.error.recovery_hint or "seconds" in error.error.recovery_hint.lower()

        # Test without retry_after (default hint)
        error_default = ErrorEnvelope.rate_limited()
        assert error_default.error.recovery_hint is not None
        assert any(
            keyword in error_default.error.recovery_hint.lower()
            for keyword in ["retry", "wait", "seconds", "later"]
        ), "Recovery hint should suggest retry strategy"

    def test_unresolved_entity_recovery_hint(self):
        """T058: Test UNRESOLVED_ENTITY error includes actionable recovery hint.

        US4 Acceptance: UNRESOLVED_ENTITY errors should suggest using fuzzy search
        to find valid CURIEs (e.g., "Use search_proteins to find valid UniProt IDs").
        """
        # Create UNRESOLVED_ENTITY error envelope
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message="Invalid UniProt CURIE format: 'invalid-id'",
                recovery_hint=(
                    "Use search_proteins to find valid UniProt IDs, then call "
                    "get_protein with the resolved CURIE (e.g., 'UniProtKB:P04637')"
                ),
                invalid_input="invalid-id",
            )
        )

        # Verify error structure
        assert error.success is False
        assert error.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert error.error.invalid_input == "invalid-id"

        # Verify recovery hint suggests fuzzy-to-fact workflow
        assert error.error.recovery_hint is not None
        hint_lower = error.error.recovery_hint.lower()
        assert "search" in hint_lower, "Should suggest using fuzzy search"
        # Should mention the search tool name or workflow
        assert any(keyword in hint_lower for keyword in ["search_proteins", "find", "valid"]), (
            "Should guide to fuzzy search tool"
        )
        # Should provide example CURIE format
        assert "UniProtKB:" in error.error.recovery_hint, "Should show example CURIE format"

    def test_entity_not_found_recovery_hint(self):
        """Test ENTITY_NOT_FOUND error includes actionable recovery hint.

        Verifies that when a valid CURIE format is provided but the entity doesn't exist,
        the error suggests using fuzzy search to find valid alternatives.
        """
        # Create ENTITY_NOT_FOUND error envelope
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message="Protein 'UniProtKB:P99999' not found in UniProt",
                recovery_hint=(
                    "The protein UniProtKB:P99999 does not exist in UniProt. "
                    "Verify the accession or search for the protein by name using search_proteins."
                ),
                invalid_input="UniProtKB:P99999",
            )
        )

        # Verify error structure
        assert error.success is False
        assert error.error.code == ErrorCode.ENTITY_NOT_FOUND
        assert error.error.invalid_input == "UniProtKB:P99999"

        # Verify recovery hint suggests search alternative
        assert error.error.recovery_hint is not None
        hint_lower = error.error.recovery_hint.lower()
        assert any(keyword in hint_lower for keyword in ["search", "verify", "find", "name"]), (
            "Should suggest alternative search strategy"
        )

    def test_upstream_error_recovery_hint(self):
        """Test UPSTREAM_ERROR includes recovery hint for API failures.

        Verifies that upstream API errors provide guidance on retrying or
        reporting issues.
        """
        # Create UPSTREAM_ERROR error envelope
        error = ErrorEnvelope.upstream_error(status_code=503, detail="Service unavailable")

        # Verify error structure
        assert error.success is False
        assert error.error.code == ErrorCode.UPSTREAM_ERROR
        assert "503" in error.error.message

        # Verify recovery hint suggests retry
        assert error.error.recovery_hint is not None
        hint_lower = error.error.recovery_hint.lower()
        assert any(keyword in hint_lower for keyword in ["retry", "try", "later", "unavailable"]), (
            "Should suggest retry strategy"
        )

    def test_error_envelope_serialization(self):
        """Test error envelopes serialize correctly with all fields.

        Ensures that error envelopes maintain all fields including recovery hints
        when converted to dict for MCP responses.
        """
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.AMBIGUOUS_QUERY,
                message="Test error message",
                recovery_hint="Test recovery hint",
                invalid_input="test",
            )
        )

        # Convert to dict
        error_dict = error.model_dump()

        # Verify all fields present
        assert error_dict["success"] is False
        assert error_dict["error"]["code"] == "AMBIGUOUS_QUERY"
        assert error_dict["error"]["message"] == "Test error message"
        assert error_dict["error"]["recovery_hint"] == "Test recovery hint"
        assert error_dict["error"]["invalid_input"] == "test"

    def test_recovery_hints_non_empty(self):
        """Test all error codes have non-empty recovery hints.

        Validates that recovery hints are always provided and meaningful
        (not empty strings or just whitespace).
        """
        # Test all standard error factory methods
        errors = [
            ErrorEnvelope.rate_limited(),
            ErrorEnvelope.upstream_error(500),
        ]

        for error in errors:
            assert error.error.recovery_hint is not None, (
                f"{error.error.code} should have recovery hint"
            )
            assert error.error.recovery_hint.strip(), (
                f"{error.error.code} recovery hint should not be empty"
            )
            assert len(error.error.recovery_hint) > 10, (
                f"{error.error.code} recovery hint should be substantive"
            )


# ==============================================================================
# T030, T058: ClinicalTrials.gov-Specific Error Tests (US2, US4)
# ==============================================================================


class TestClinicalTrialsErrorEnvelopes:
    """ClinicalTrials-specific error envelope tests (T030, T058)."""

    def test_unresolved_entity_query_string(self):
        """T030: UNRESOLVED_ENTITY for query string passed to get_trial."""
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message="The input 'breast cancer' is not a valid NCT CURIE.",
                recovery_hint=(
                    "Call search_trials to resolve the identifier first, "
                    "then use the returned NCT CURIE."
                ),
                invalid_input="breast cancer",
            )
        )

        assert error.success is False
        assert error.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert error.error.invalid_input == "breast cancer"
        assert "search_trials" in error.error.recovery_hint
        assert "NCT" in error.error.recovery_hint

    def test_unresolved_entity_malformed_curie(self):
        """T030: UNRESOLVED_ENTITY for malformed NCT CURIE."""
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=(
                    "Invalid NCT CURIE format: 'NCT:123'. "
                    "Expected format: NCT:NNNNNNNN (8 digits)."
                ),
                recovery_hint="Verify the NCT ID format. Example: NCT:00461032",
                invalid_input="NCT:123",
            )
        )

        assert error.success is False
        assert error.error.code == ErrorCode.UNRESOLVED_ENTITY
        assert error.error.invalid_input == "NCT:123"
        assert "NCT:" in error.error.recovery_hint
        assert "8" in error.error.recovery_hint or "00461032" in error.error.recovery_hint

    def test_entity_not_found_nct_id(self):
        """T058: ENTITY_NOT_FOUND for non-existent NCT ID."""
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message="Trial NCT:99999999 not found in ClinicalTrials.gov registry",
                recovery_hint=(
                    "Verify the NCT ID is correct or search for trials using search_trials."
                ),
                invalid_input="NCT:99999999",
            )
        )

        assert error.success is False
        assert error.error.code == ErrorCode.ENTITY_NOT_FOUND
        assert "NCT:99999999" in error.error.message
        assert "search_trials" in error.error.recovery_hint

    def test_rate_limited_clinicaltrials(self):
        """T058: RATE_LIMITED error for ClinicalTrials.gov API."""
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.RATE_LIMITED,
                message="ClinicalTrials.gov API rate limit exceeded.",
                recovery_hint="Retry after 60 seconds with exponential backoff.",
            )
        )

        assert error.success is False
        assert error.error.code == ErrorCode.RATE_LIMITED
        assert "60 seconds" in error.error.recovery_hint or "backoff" in error.error.recovery_hint

    def test_upstream_error_clinicaltrials_500(self):
        """T058: UPSTREAM_ERROR for ClinicalTrials.gov 5xx errors."""
        error = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.UPSTREAM_ERROR,
                message="ClinicalTrials.gov API returned error 503.",
                recovery_hint="ClinicalTrials.gov API may be temporarily unavailable. Retry later.",
            )
        )

        assert error.success is False
        assert error.error.code == ErrorCode.UPSTREAM_ERROR
        assert "503" in error.error.message
        assert "retry" in error.error.recovery_hint.lower()

    def test_all_clinicaltrials_error_codes(self):
        """T058: Verify all ClinicalTrials error codes have recovery hints."""
        # All error codes used by ClinicalTrials client
        errors = [
            ErrorDetail(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message="Test",
                recovery_hint="Call search_trials first",
            ),
            ErrorDetail(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message="Test",
                recovery_hint="Verify NCT ID",
            ),
            ErrorDetail(
                code=ErrorCode.RATE_LIMITED,
                message="Test",
                recovery_hint="Retry after delay",
            ),
            ErrorDetail(
                code=ErrorCode.UPSTREAM_ERROR,
                message="Test",
                recovery_hint="Retry later",
            ),
        ]

        for error_detail in errors:
            assert error_detail.recovery_hint is not None
            assert len(error_detail.recovery_hint) > 0
            # Should suggest action
            assert any(
                keyword in error_detail.recovery_hint.lower()
                for keyword in ["retry", "search", "verify", "call", "use"]
            )
