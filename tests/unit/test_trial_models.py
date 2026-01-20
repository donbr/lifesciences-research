"""Unit tests for ClinicalTrials.gov trial models.

These tests verify model validation and serialization without API calls.

Run with:
    uv run pytest tests/unit/test_trial_models.py -v
"""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.trial import (
    EligibilityCriteria,
    Outcome,
    Sponsor,
    Trial,
    TrialProtocol,
    TrialSearchCandidate,
)

pytestmark = [pytest.mark.unit, pytest.mark.clinicaltrials]

# ==============================================================================
# T013: TrialSearchCandidate Tests (US1)
# ==============================================================================


class TestTrialSearchCandidate:
    """Unit tests for TrialSearchCandidate model (T013)."""

    def test_valid_search_candidate(self):
        """Valid candidate with all required fields."""
        candidate = TrialSearchCandidate(
            id="NCT:00461032",
            title="Montelukast Back to School Asthma Study",
            brief_summary="A randomized, double-blind, placebo-controlled trial.",
            phase="PHASE3",
            status="COMPLETED",
            conditions=["Asthma"],
            interventions=["Montelukast 5 mg", "Placebo"],
        )
        assert candidate.id == "NCT:00461032"
        assert candidate.title == "Montelukast Back to School Asthma Study"
        assert candidate.phase == "PHASE3"
        assert len(candidate.conditions) == 1
        assert len(candidate.interventions) == 2

    def test_valid_nct_id_patterns(self):
        """Valid NCT CURIE patterns are accepted."""
        valid_ids = [
            "NCT:00461032",
            "NCT:01234567",
            "NCT:99999999",
            "NCT:00000001",
        ]
        for nct_id in valid_ids:
            candidate = TrialSearchCandidate(
                id=nct_id,
                title="Test Trial",
                brief_summary="Test summary",
                status="RECRUITING",
            )
            assert candidate.id == nct_id

    def test_invalid_nct_id_patterns_rejected(self):
        """Invalid NCT CURIE patterns are rejected."""
        invalid_ids = [
            "NCT00461032",  # Missing colon
            "NCT:0046103",  # Too few digits (7)
            "NCT:004610322",  # Too many digits (9)
            "nct:00461032",  # Lowercase
            "00461032",  # No NCT prefix
            "NCT:",  # No digits
            "",  # Empty
            "breast cancer",  # Query string
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError) as exc_info:
                TrialSearchCandidate(
                    id=invalid_id,
                    title="Test",
                    brief_summary="Test",
                    status="RECRUITING",
                )
            assert "Invalid NCT CURIE format" in str(exc_info.value)

    def test_optional_phase_null(self):
        """Phase can be None for observational studies."""
        candidate = TrialSearchCandidate(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Test summary",
            phase=None,
            status="RECRUITING",
        )
        assert candidate.phase is None

    def test_default_empty_lists(self):
        """Conditions and interventions default to empty lists."""
        candidate = TrialSearchCandidate(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Test summary",
            status="RECRUITING",
        )
        assert candidate.conditions == []
        assert candidate.interventions == []

    def test_multiple_conditions_and_interventions(self):
        """Multiple conditions and interventions are supported."""
        candidate = TrialSearchCandidate(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Test summary",
            status="RECRUITING",
            conditions=["Diabetes", "Obesity", "Hypertension"],
            interventions=["Drug A", "Drug B", "Lifestyle Intervention"],
        )
        assert len(candidate.conditions) == 3
        assert len(candidate.interventions) == 3

    def test_serialization_round_trip(self):
        """Model can be serialized and deserialized."""
        candidate = TrialSearchCandidate(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Test summary",
            phase="PHASE2",
            status="RECRUITING",
            conditions=["Asthma"],
            interventions=["Drug X"],
        )
        data = candidate.model_dump()
        restored = TrialSearchCandidate(**data)
        assert restored == candidate


# ==============================================================================
# T028, T029: Trial Model Tests (US2)
# ==============================================================================


class TestTrial:
    """Unit tests for Trial model (T028, T029)."""

    def test_valid_trial(self):
        """Valid trial with all required fields."""
        trial = Trial(
            id="NCT:00461032",
            title="Montelukast Back to School Asthma Study",
            brief_summary="A randomized, double-blind, placebo-controlled trial.",
            protocol=TrialProtocol(
                study_type="INTERVENTIONAL",
                allocation="RANDOMIZED",
                intervention_model="PARALLEL",
                masking="DOUBLE",
                primary_purpose="TREATMENT",
            ),
            status="COMPLETED",
            phase="PHASE3",
            enrollment=1162,
            conditions=["Asthma"],
            interventions=["Montelukast 5 mg", "Placebo"],
        )
        assert trial.id == "NCT:00461032"
        assert trial.protocol.study_type == "INTERVENTIONAL"
        assert trial.enrollment == 1162

    def test_omit_if_null_pattern_detailed_description(self):
        """T029: Null fields are omitted per ADR-001 (detailed_description)."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            detailed_description=None,  # Should be omitted
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
        )
        assert trial.detailed_description is None
        # Verify it's excluded from serialized output
        data = trial.model_dump(exclude_none=True)
        assert "detailed_description" not in data

    def test_omit_if_null_pattern_eligibility_criteria(self):
        """T029: Null eligibility_criteria is omitted."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            eligibility_criteria=None,
            status="RECRUITING",
        )
        data = trial.model_dump(exclude_none=True)
        assert "eligibility_criteria" not in data

    def test_omit_if_null_pattern_optional_protocol_fields(self):
        """T029: Optional protocol fields can be None."""
        protocol = TrialProtocol(
            study_type="OBSERVATIONAL",
            allocation=None,
            intervention_model=None,
            masking=None,
            primary_purpose=None,
        )
        assert protocol.allocation is None
        data = protocol.model_dump(exclude_none=True)
        assert "allocation" not in data
        assert "intervention_model" not in data

    def test_omit_if_null_pattern_dates(self):
        """T029: Null date fields are omitted."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
            start_date=None,
            completion_date=None,
            last_update_date=None,
        )
        data = trial.model_dump(exclude_none=True)
        assert "start_date" not in data
        assert "completion_date" not in data
        assert "last_update_date" not in data

    def test_empty_outcomes_default(self):
        """Empty outcomes lists are supported."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
        )
        assert trial.primary_outcomes == []
        assert trial.secondary_outcomes == []

    def test_multiple_outcomes(self):
        """Multiple primary and secondary outcomes are supported."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
            primary_outcomes=[
                Outcome(measure="Primary outcome 1", time_frame="8 weeks"),
                Outcome(measure="Primary outcome 2", time_frame="6 months"),
            ],
            secondary_outcomes=[
                Outcome(measure="Secondary outcome 1", time_frame="1 year"),
            ],
        )
        assert len(trial.primary_outcomes) == 2
        assert len(trial.secondary_outcomes) == 1

    def test_multiple_sponsors(self):
        """Multiple sponsors (lead + collaborators) are supported."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
            sponsors=[
                Sponsor(name="Organon and Company", role="LEAD_SPONSOR"),
                Sponsor(name="NIH", role="COLLABORATOR"),
                Sponsor(name="University of California", role="COLLABORATOR"),
            ],
        )
        assert len(trial.sponsors) == 3
        assert trial.sponsors[0].role == "LEAD_SPONSOR"

    def test_cross_references_empty_dict_default(self):
        """Cross-references default to empty dict."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
        )
        assert trial.cross_references == {}

    def test_cross_references_with_pubmed(self):
        """Cross-references can include PubMed IDs."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
            cross_references={
                "pubmed": "20674830,21234567",
                "clinicaltrials_gov": "https://clinicaltrials.gov/study/NCT00461032",
            },
        )
        assert "pubmed" in trial.cross_references
        assert "clinicaltrials_gov" in trial.cross_references

    def test_cross_references_with_mesh(self):
        """Cross-references can include MeSH IDs."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
            cross_references={
                "mesh_conditions": "D001249,D012140",
                "mesh_interventions": "C093875",
            },
        )
        assert "mesh_conditions" in trial.cross_references
        assert "mesh_interventions" in trial.cross_references

    def test_invalid_nct_id_rejected(self):
        """Invalid NCT CURIE is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Trial(
                id="NCT00461032",  # Missing colon
                title="Test Trial",
                brief_summary="Brief summary",
                protocol=TrialProtocol(study_type="INTERVENTIONAL"),
                status="RECRUITING",
            )
        assert "Invalid NCT CURIE format" in str(exc_info.value)

    def test_extra_fields_allowed(self):
        """Extra fields are allowed for forward compatibility."""
        trial = Trial(
            id="NCT:00461032",
            title="Test Trial",
            brief_summary="Brief summary",
            protocol=TrialProtocol(study_type="INTERVENTIONAL"),
            status="RECRUITING",
            future_field="Some future data",  # Extra field
        )
        assert trial.future_field == "Some future data"  # type: ignore


# ==============================================================================
# Helper Model Tests
# ==============================================================================


class TestTrialProtocol:
    """Unit tests for TrialProtocol model."""

    def test_valid_protocol(self):
        """Valid protocol with all fields."""
        protocol = TrialProtocol(
            study_type="INTERVENTIONAL",
            allocation="RANDOMIZED",
            intervention_model="PARALLEL",
            masking="DOUBLE",
            primary_purpose="TREATMENT",
        )
        assert protocol.study_type == "INTERVENTIONAL"
        assert protocol.masking == "DOUBLE"

    def test_minimal_protocol(self):
        """Protocol with only required field."""
        protocol = TrialProtocol(study_type="OBSERVATIONAL")
        assert protocol.study_type == "OBSERVATIONAL"
        assert protocol.allocation is None


class TestEligibilityCriteria:
    """Unit tests for EligibilityCriteria model."""

    def test_valid_eligibility(self):
        """Valid eligibility criteria."""
        eligibility = EligibilityCriteria(
            criteria_text="Inclusion: Adults age 18+\nExclusion: Pregnancy",
            minimum_age="18 Years",
            maximum_age="65 Years",
            sex="ALL",
            accepts_healthy_volunteers=False,
        )
        assert eligibility.minimum_age == "18 Years"
        assert eligibility.sex == "ALL"
        assert not eligibility.accepts_healthy_volunteers

    def test_all_fields_optional_except_healthy_volunteers(self):
        """All fields except accepts_healthy_volunteers can be None."""
        eligibility = EligibilityCriteria()
        assert eligibility.criteria_text is None
        assert eligibility.minimum_age is None
        assert not eligibility.accepts_healthy_volunteers  # Defaults to False


class TestOutcome:
    """Unit tests for Outcome model."""

    def test_valid_outcome(self):
        """Valid outcome with all fields."""
        outcome = Outcome(
            measure="Mean Percentage of Days With Worsening Asthma",
            time_frame="8 weeks",
            description="Detailed description of outcome measure",
        )
        assert outcome.measure == "Mean Percentage of Days With Worsening Asthma"
        assert outcome.time_frame == "8 weeks"

    def test_optional_fields(self):
        """Optional fields can be None."""
        outcome = Outcome(measure="Primary outcome measure")
        assert outcome.time_frame is None
        assert outcome.description is None


class TestSponsor:
    """Unit tests for Sponsor model."""

    def test_valid_sponsor(self):
        """Valid sponsor with required fields."""
        sponsor = Sponsor(name="Organon and Company", role="LEAD_SPONSOR")
        assert sponsor.name == "Organon and Company"
        assert sponsor.role == "LEAD_SPONSOR"

    def test_collaborator_role(self):
        """Collaborator role is supported."""
        sponsor = Sponsor(name="NIH", role="COLLABORATOR")
        assert sponsor.role == "COLLABORATOR"
