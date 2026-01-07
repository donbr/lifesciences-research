"""Unit tests for ClinicalTrials.gov trial location models.

These tests verify model validation and serialization without API calls.

Run with:
    uv run pytest tests/unit/test_trial_location_models.py -v
"""

import pytest

from lifesciences_mcp.models.trial_location import TrialLocation

# ==============================================================================
# T046, T047: TrialLocation Tests (US3)
# ==============================================================================


class TestTrialLocation:
    """Unit tests for TrialLocation model (T046, T047)."""

    def test_valid_location_with_all_fields(self):
        """Valid location with all fields populated."""
        location = TrialLocation(
            facility_name="Investigational Site 001",
            city="Birmingham",
            state="Alabama",
            country="United States",
            zip="35209",
            contact_name="Dr. John Doe",
            contact_phone="555-123-4567",
            contact_email="john.doe@example.com",
            recruitment_status="RECRUITING",
        )
        assert location.facility_name == "Investigational Site 001"
        assert location.city == "Birmingham"
        assert location.state == "Alabama"
        assert location.country == "United States"
        assert location.zip == "35209"
        assert location.contact_name == "Dr. John Doe"
        assert location.recruitment_status == "RECRUITING"

    def test_minimal_location_required_fields_only(self):
        """Minimal location with only required fields."""
        location = TrialLocation(
            facility_name="General Hospital",
            city="Boston",
            country="United States",
            recruitment_status="NOT_YET_RECRUITING",
        )
        assert location.facility_name == "General Hospital"
        assert location.city == "Boston"
        assert location.country == "United States"
        assert location.recruitment_status == "NOT_YET_RECRUITING"

    def test_omit_if_null_pattern_state(self):
        """T047: State is omitted for non-US/Canada locations."""
        location = TrialLocation(
            facility_name="London Hospital",
            city="London",
            state=None,  # No state for UK
            country="United Kingdom",
            recruitment_status="RECRUITING",
        )
        assert location.state is None
        data = location.model_dump(exclude_none=True)
        assert "state" not in data

    def test_omit_if_null_pattern_zip(self):
        """T047: Zip code can be omitted."""
        location = TrialLocation(
            facility_name="Hospital",
            city="Paris",
            country="France",
            zip=None,
            recruitment_status="COMPLETED",
        )
        data = location.model_dump(exclude_none=True)
        assert "zip" not in data

    def test_omit_if_null_pattern_contact_name(self):
        """T047: Contact name can be omitted."""
        location = TrialLocation(
            facility_name="Hospital",
            city="Tokyo",
            country="Japan",
            contact_name=None,
            recruitment_status="RECRUITING",
        )
        data = location.model_dump(exclude_none=True)
        assert "contact_name" not in data

    def test_omit_if_null_pattern_contact_phone(self):
        """T047: Contact phone can be omitted."""
        location = TrialLocation(
            facility_name="Hospital",
            city="Toronto",
            state="Ontario",
            country="Canada",
            contact_phone=None,
            recruitment_status="RECRUITING",
        )
        data = location.model_dump(exclude_none=True)
        assert "contact_phone" not in data

    def test_omit_if_null_pattern_contact_email(self):
        """T047: Contact email can be omitted."""
        location = TrialLocation(
            facility_name="Hospital",
            city="Sydney",
            country="Australia",
            contact_email=None,
            recruitment_status="RECRUITING",
        )
        data = location.model_dump(exclude_none=True)
        assert "contact_email" not in data

    def test_us_location_with_state(self):
        """US locations include state."""
        location = TrialLocation(
            facility_name="Mayo Clinic",
            city="Rochester",
            state="Minnesota",
            country="United States",
            zip="55905",
            recruitment_status="RECRUITING",
        )
        assert location.state == "Minnesota"
        assert location.zip == "55905"

    def test_canada_location_with_province(self):
        """Canadian locations include province in state field."""
        location = TrialLocation(
            facility_name="Toronto General Hospital",
            city="Toronto",
            state="Ontario",
            country="Canada",
            zip="M5G 2C4",
            recruitment_status="RECRUITING",
        )
        assert location.state == "Ontario"

    def test_international_location_no_state(self):
        """International locations (non-US/Canada) omit state."""
        location = TrialLocation(
            facility_name="Karolinska University Hospital",
            city="Stockholm",
            country="Sweden",
            recruitment_status="RECRUITING",
        )
        assert location.state is None

    def test_multiple_recruitment_statuses(self):
        """Various recruitment statuses are supported."""
        statuses = [
            "RECRUITING",
            "NOT_YET_RECRUITING",
            "COMPLETED",
            "SUSPENDED",
            "TERMINATED",
            "ACTIVE_NOT_RECRUITING",
        ]
        for status in statuses:
            location = TrialLocation(
                facility_name="Hospital",
                city="City",
                country="Country",
                recruitment_status=status,
            )
            assert location.recruitment_status == status

    def test_complete_contact_information(self):
        """Location with complete contact information."""
        location = TrialLocation(
            facility_name="Research Center",
            city="San Francisco",
            state="California",
            country="United States",
            zip="94143",
            contact_name="Dr. Jane Smith",
            contact_phone="+1-415-555-1234",
            contact_email="jane.smith@research.ucsf.edu",
            recruitment_status="RECRUITING",
        )
        assert location.contact_name == "Dr. Jane Smith"
        assert location.contact_phone == "+1-415-555-1234"
        assert location.contact_email == "jane.smith@research.ucsf.edu"

    def test_partial_contact_information(self):
        """Location with partial contact information (only phone)."""
        location = TrialLocation(
            facility_name="Research Center",
            city="Boston",
            state="Massachusetts",
            country="United States",
            contact_phone="617-555-9999",
            contact_name=None,
            contact_email=None,
            recruitment_status="RECRUITING",
        )
        assert location.contact_phone == "617-555-9999"
        assert location.contact_name is None
        assert location.contact_email is None

    def test_serialization_round_trip(self):
        """Model can be serialized and deserialized."""
        location = TrialLocation(
            facility_name="Hospital",
            city="New York",
            state="New York",
            country="United States",
            zip="10001",
            contact_name="Contact Person",
            contact_phone="212-555-1111",
            contact_email="contact@hospital.org",
            recruitment_status="RECRUITING",
        )
        data = location.model_dump()
        restored = TrialLocation(**data)
        assert restored == location

    def test_extra_fields_allowed(self):
        """Extra fields are allowed for forward compatibility."""
        location = TrialLocation(
            facility_name="Hospital",
            city="City",
            country="Country",
            recruitment_status="RECRUITING",
            future_field="Some future data",  # Extra field
        )
        assert location.future_field == "Some future data"  # type: ignore
