"""Clinical trial location and facility data models.

This module defines Pydantic models for clinical trial facility/location data
following the Agentic Biolink schema with omit-if-null pattern.
"""

from pydantic import BaseModel, ConfigDict, Field


class TrialLocation(BaseModel):
    """Trial facility with contact information.

    Token Budget: ~50-100 tokens per location
    """

    facility_name: str = Field(description="Facility/hospital name")
    city: str = Field(description="City name")
    state: str | None = Field(
        default=None, description="State/province (US/Canada only, omit for other countries)"
    )
    country: str = Field(description="Country name")
    zip: str | None = Field(default=None, description="Postal code")
    contact_name: str | None = Field(default=None, description="Contact person name")
    contact_phone: str | None = Field(default=None, description="Contact phone number")
    contact_email: str | None = Field(default=None, description="Contact email address")
    recruitment_status: str = Field(
        description="Recruitment status (RECRUITING, NOT_YET_RECRUITING, COMPLETED, etc.)"
    )

    # Pydantic v2 model configuration
    model_config = ConfigDict(extra="allow")
