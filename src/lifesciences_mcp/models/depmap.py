"""DepMap data models for cancer cell-line dependencies and genotype contrasts.

Implements Pydantic models for the DepMap MCP following ADR-001 Agentic Biolink
schema and Constitution Principle III (Schema Determinism).

Two data provenances are supported and always labeled:
- ``broad_24q2``          — Broad DepMap 24Q2 CRISPR (Chronos) / DEMETER2 RNAi (local matrices).
- ``sanger_project_score`` — Sanger Cell Model Passports REST API (live).

Dependency convention (matches sprime-lung-repro/demeter_validation.py):
    dependency = -gene_effect   (higher value = MORE dependent)
    delta_dep  = mean(dep_WT) - mean(dep_MUT)
    delta_dep < 0  =>  mutant cohort more dependent  =>  "mutant-selective"
"""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

GENE_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9\-_@.]{0,29}$")

DataSource = Literal["broad_24q2", "sanger_project_score"]
Direction = Literal["mutant-selective", "WT-selective", "none"]


class DepMapModelCandidate(BaseModel):
    """A cancer cell-line ("model") search result (Fuzzy Phase 1)."""

    model_config = ConfigDict(exclude_none=True)

    model_id: str = Field(..., description="Model identifier (Broad ACH-###### or Sanger SIDM#####)")
    model_name: str | None = Field(None, description="Human-readable cell-line name")
    lineage: str | None = Field(None, description="Tissue lineage (e.g., lung)")
    data_source: DataSource = Field(..., description="Provenance of this record")


class DependencyRecord(BaseModel):
    """A single gene-effect dependency value for one gene in one model."""

    model_config = ConfigDict(exclude_none=True)

    gene: str = Field(..., description="HGNC gene symbol")
    model_id: str = Field(..., description="Model identifier")
    gene_effect: float = Field(..., description="Chronos/gene-effect score (negative = dependent)")
    dependency: float = Field(..., description="-gene_effect (higher = more dependent)")
    dependent: bool = Field(..., description="True if scored as a dependency in the source")
    data_source: DataSource = Field(..., description="Provenance of this record")

    @field_validator("gene")
    @classmethod
    def _validate_gene(cls, v: str) -> str:
        if not GENE_SYMBOL_PATTERN.match(v.upper()):
            raise ValueError(f"Invalid gene symbol format: {v}")
        return v.upper()


class GenotypeContrast(BaseModel):
    """WT-vs-mutant dependency contrast for a target gene under a genotype.

    This is the key capability the S′ paper needed: does loss of ``genotype_gene``
    make cells selectively dependent on ``target_gene``?
    """

    target_gene: str = Field(..., description="Gene whose dependency is contrasted")
    genotype_gene: str = Field(..., description="Tumor-suppressor genotype defining the cohorts")
    n_wt: int = Field(..., description="Wild-type models with a dependency value", ge=0)
    n_mut: int = Field(..., description="Mutant models with a dependency value", ge=0)
    mean_dep_wt: float | None = Field(None, description="Mean dependency in WT cohort")
    mean_dep_mut: float | None = Field(None, description="Mean dependency in mutant cohort")
    delta_dep: float | None = Field(
        None, description="mean(dep_WT) - mean(dep_MUT); <0 => mutant-selective"
    )
    direction: Direction = Field(..., description="mutant-selective | WT-selective | none")
    mw_p: float | None = Field(None, description="Mann-Whitney U p-value (two-sided)")
    bh_fdr: float | None = Field(None, description="Benjamini-Hochberg FDR if a gene set was tested")
    min_lines: int = Field(..., description="Minimum per-cohort n required to report", ge=1)
    tested: bool = Field(..., description="False if a cohort was too small (n < min_lines)")
    data_source: DataSource = Field(..., description="Provenance of the underlying matrix")
    note: str | None = Field(None, description="Human-readable caveat (e.g., cohort too small)")

    @field_validator("target_gene", "genotype_gene")
    @classmethod
    def _validate_symbols(cls, v: str) -> str:
        if not GENE_SYMBOL_PATTERN.match(v.upper()):
            raise ValueError(f"Invalid gene symbol format: {v}")
        return v.upper()
