"""Clinical trial data models for ClinicalTrials.gov API.

This module defines Pydantic models for clinical trial data following the
Agentic Biolink schema with flattened JSON structure and omit-if-null pattern.
"""

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrialSearchCandidate(BaseModel):
    """Lightweight trial search result for fuzzy discovery.

    Token Budget: ~100-200 tokens per candidate
    """

    id: str = Field(description="NCT CURIE (e.g., 'NCT:00461032')")
    title: str = Field(description="Official trial title")
    brief_summary: str = Field(description="Brief description of the trial")
    phase: str | None = Field(
        default=None, description="Trial phase (PHASE1, PHASE2, PHASE3, PHASE4, NA, EARLY_PHASE1)"
    )
    status: str = Field(description="Recruitment status (RECRUITING, COMPLETED, etc.)")
    conditions: list[str] = Field(default_factory=list, description="Disease/condition names")
    interventions: list[str] = Field(
        default_factory=list, description="Treatment/intervention names"
    )

    @field_validator("id")
    @classmethod
    def validate_nct_id(cls, v: str) -> str:
        """Validate NCT CURIE format."""
        if not re.match(r"^NCT:\d{8}$", v):
            raise ValueError(f"Invalid NCT CURIE format: {v}. Expected format: NCT:NNNNNNNN")
        return v


class TrialProtocol(BaseModel):
    """Protocol design details."""

    study_type: str = Field(
        description="Study type (INTERVENTIONAL, OBSERVATIONAL, EXPANDED_ACCESS)"
    )
    allocation: str | None = Field(
        default=None, description="Allocation method (RANDOMIZED, NON_RANDOMIZED, NA)"
    )
    intervention_model: str | None = Field(
        default=None, description="Intervention model (PARALLEL, CROSSOVER, SINGLE_GROUP, etc.)"
    )
    masking: str | None = Field(
        default=None, description="Masking type (NONE, SINGLE, DOUBLE, TRIPLE, QUADRUPLE)"
    )
    primary_purpose: str | None = Field(
        default=None, description="Primary purpose (TREATMENT, PREVENTION, DIAGNOSTIC, etc.)"
    )


class EligibilityCriteria(BaseModel):
    """Patient eligibility requirements."""

    criteria_text: str | None = Field(
        default=None, description="Formatted inclusion/exclusion criteria"
    )
    minimum_age: str | None = Field(default=None, description="Minimum age (e.g., '18 Years')")
    maximum_age: str | None = Field(default=None, description="Maximum age (e.g., '65 Years')")
    sex: str | None = Field(default=None, description="Eligible sex (ALL, FEMALE, MALE)")
    accepts_healthy_volunteers: bool = Field(
        default=False, description="Whether healthy volunteers are accepted"
    )


class Outcome(BaseModel):
    """Trial outcome measure."""

    measure: str = Field(description="Outcome measure description")
    time_frame: str | None = Field(default=None, description="Assessment timeframe")
    description: str | None = Field(
        default=None, description="Additional details about the outcome"
    )


class Sponsor(BaseModel):
    """Trial sponsor or collaborator."""

    name: str = Field(description="Organization name")
    role: str = Field(description="Role (LEAD_SPONSOR, COLLABORATOR)")


class Trial(BaseModel):
    """Complete clinical trial entity with full protocol details.

    Token Budget: ~5K-10K tokens (deep nested structure from API)
    """

    # Identity
    id: str = Field(description="NCT CURIE (e.g., 'NCT:00461032')")
    title: str = Field(description="Official trial title")
    brief_summary: str = Field(description="Brief description of the trial")
    detailed_description: str | None = Field(default=None, description="Full protocol description")

    # Protocol
    protocol: TrialProtocol = Field(description="Protocol design details")

    # Eligibility
    eligibility_criteria: EligibilityCriteria | None = Field(
        default=None, description="Patient eligibility requirements"
    )

    # Outcomes
    primary_outcomes: list[Outcome] = Field(default_factory=list, description="Primary endpoints")
    secondary_outcomes: list[Outcome] = Field(
        default_factory=list, description="Secondary endpoints"
    )

    # Administrative
    sponsors: list[Sponsor] = Field(
        default_factory=list, description="Lead sponsor and collaborators"
    )
    phase: str | None = Field(default=None, description="Trial phase")
    status: str = Field(description="Recruitment status")
    enrollment: int | None = Field(default=None, description="Target/actual enrollment count")

    # Dates
    start_date: str | None = Field(
        default=None, description="Study start date (YYYY-MM-DD or partial)"
    )
    completion_date: str | None = Field(default=None, description="Primary completion date")
    last_update_date: str | None = Field(default=None, description="Last registry update date")

    # Conditions and Interventions
    conditions: list[str] = Field(default_factory=list, description="Disease/condition names")
    interventions: list[str] = Field(
        default_factory=list, description="Treatment/intervention names"
    )

    # Cross-references (omit-if-null pattern)
    cross_references: dict[str, Any] = Field(
        default_factory=dict,
        description="External database identifiers (pubmed, clinicaltrials_gov, mesh_conditions, mesh_interventions)",
    )

    @field_validator("id")
    @classmethod
    def validate_nct_id(cls, v: str) -> str:
        """Validate NCT CURIE format."""
        if not re.match(r"^NCT:\d{8}$", v):
            raise ValueError(f"Invalid NCT CURIE format: {v}. Expected format: NCT:NNNNNNNN")
        return v

    # Pydantic v2 model configuration
    model_config = ConfigDict(extra="allow")
