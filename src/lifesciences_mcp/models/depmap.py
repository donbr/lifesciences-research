"""DepMap data models for cancer cell-line dependencies and genotype contrasts.

Implements Pydantic models for the DepMap MCP following ADR-001 Agentic Biolink
schema and Constitution Principle III (Schema Determinism).

Two data provenances are supported and always labeled:
- ``broad_24q2``           - Broad DepMap 24Q2 CRISPR (Chronos) / DEMETER2 RNAi (local matrices).
- ``sanger_project_score`` - Sanger Cell Model Passports REST API (live model resolution).

Dependency convention (matches sprime-lung-repro/demeter_validation.py, preserved so the
contrast stays byte-comparable with the reference analysis):
    dependency = -gene_effect   (higher value = MORE dependent)
    delta_dep  = mean(dep_WT) - mean(dep_MUT)
    delta_dep < 0  =>  mutant cohort more dependent  =>  "mutant-selective"

Null handling (ADR-001 section 4): keys with no value are OMITTED, never emitted as null.
This is done with a ``model_dump`` override, the pattern used by ``models/drug.py``,
``models/ensembl.py`` and ``models/pharmacology.py``. It is deliberately NOT done with
``ConfigDict(exclude_none=True)``, which is not a valid Pydantic v2 configuration key and is
silently ignored.
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

GENE_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9\-_@.]{0,29}$")

# Sanger Cell Model Passports native identifier, expressed as a CURIE (ADR-001 section 3).
# Upstream serves the bare form "SIDM00903"; the colon makes it self-describing, matching
# NCT:######## in feature 013.
SIDM_CURIE_PATTERN = re.compile(r"^SIDM:\d{5}$")
SIDM_BARE_PATTERN = re.compile(r"^SIDM\d{5}$")

DataSource = Literal["broad_24q2", "sanger_project_score"]
Direction = Literal["mutant-selective", "WT-selective", "none"]

# Mutation classes the upstream accepts, quoted from its own 404 body:
#   "mutation type needs to be one of frameshift, snp, insertion, deletion,
#    splice_variant or mutation"
# WARNING: "mutation" means ANY variant. Measured 2026-09-02: /models/by_mutation/RB1
# returns 2185 of 2266 models, against 501 for deletion, 60 for splice_variant and 27 for
# frameshift. It is not the damaging call a genotype contrast needs, which is why the
# cohort tool requires this value explicitly rather than defaulting to it.
MutationType = Literal["frameshift", "snp", "insertion", "deletion", "splice_variant", "mutation"]
MUTATION_TYPES: tuple[str, ...] = (
    "frameshift",
    "snp",
    "insertion",
    "deletion",
    "splice_variant",
    "mutation",
)


class _OmitNoneModel(BaseModel):
    """Base that omits keys with no value on serialisation (ADR-001 section 4)."""

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to exclude None values (ADR-001: omit keys with no value)."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class DepMapCrossReferences(_OmitNoneModel):
    """Cross-references for a cell model.

    The shared 22-key registry in ``models/cross_references.py`` covers genes, proteins,
    compounds and pathways; it has no key for a cell-line identifier. This feature-specific
    model follows the precedent of ``DrugCrossReferences`` and the trial cross-references
    rather than unilaterally extending the shared registry, which the Constitution requires
    to happen through an ADR amendment.

    Both identifiers below were confirmed resolvable upstream on 2026-09-02 via
    ``/models/CCLE_ID/<id>`` and ``/models/cosmic_id/<id>``.
    """

    ccle: str | None = Field(default=None, description="Broad CCLE identifier, e.g. A549_LUNG")
    cosmic: str | None = Field(default=None, description="COSMIC sample identifier, e.g. 905949")

    @model_validator(mode="after")
    def omit_empty_values(self) -> "DepMapCrossReferences":
        """Treat empty strings as absent, so they are omitted rather than serialised."""
        for field_name in type(self).model_fields:
            if getattr(self, field_name) == "":
                setattr(self, field_name, None)
        return self


class CellModel(_OmitNoneModel):
    """A cancer cell line or organoid.

    Returned as a ranked candidate by ``search_models`` (Fuzzy Phase 1) and in full by
    ``get_model`` (Strict Phase 2).
    """

    id: str = Field(..., description="Model CURIE, e.g. SIDM:00903")
    name: str = Field(..., description="Primary cell-line name, e.g. A549")
    aliases: list[str] = Field(default_factory=list, description="All known names for this model")
    lineage: str | None = Field(default=None, description="Tissue or lineage")
    model_type: str | None = Field(default=None, description="e.g. Cell Line, Organoid")
    data_available: list[str] = Field(
        default_factory=list, description="Datasets that exist for this model"
    )
    data_source: DataSource = Field(..., description="Provenance of this record")
    cross_references: DepMapCrossReferences | None = Field(
        default=None, description="External identifiers; keys with no value are omitted"
    )

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        if not SIDM_CURIE_PATTERN.match(v):
            raise ValueError(f"Invalid model CURIE, expected SIDM:NNNNN: {v}")
        return v

    def slim(self) -> dict[str, Any]:
        """Reduced representation for token budgeting (Constitution Principle IV)."""
        return {"id": self.id, "name": self.name, "data_source": self.data_source}


class DependencyRecord(_OmitNoneModel):
    """A single gene-effect dependency value for one gene in one model.

    Values are read from a cached, checksum-pinned release. No provider serves gene effect
    over a query API, so this is never populated from a live call.
    """

    gene: str = Field(..., description="HGNC gene symbol")
    model_id: str = Field(..., description="Model CURIE, e.g. SIDM:00903")
    gene_effect: float | None = Field(
        default=None, description="Chronos/gene-effect score (negative = dependent)"
    )
    dependency: float | None = Field(
        default=None, description="-gene_effect (higher = more dependent)"
    )
    dependent: bool | None = Field(
        default=None, description="True if scored as a dependency in the source"
    )
    data_source: DataSource = Field(..., description="Provenance of this record")

    @field_validator("gene")
    @classmethod
    def _validate_gene(cls, v: str) -> str:
        if not GENE_SYMBOL_PATTERN.match(v.upper()):
            raise ValueError(f"Invalid gene symbol format: {v}")
        return v.upper()


class GenotypeCohort(_OmitNoneModel):
    """The models carrying a given class of variant in a given gene."""

    gene: str = Field(..., description="HGNC gene symbol defining the cohort")
    mutation_type: MutationType = Field(
        ..., description="Variant class the cohort was built from; never implicit"
    )
    model_ids: list[str] = Field(default_factory=list, description="Model CURIEs in the cohort")
    total_count: int | None = Field(default=None, description="Upstream total for this cohort")
    data_source: DataSource = Field(..., description="Provenance of this cohort")

    @field_validator("gene")
    @classmethod
    def _validate_gene(cls, v: str) -> str:
        if not GENE_SYMBOL_PATTERN.match(v.upper()):
            raise ValueError(f"Invalid gene symbol format: {v}")
        return v.upper()


class GenotypeContrast(_OmitNoneModel):
    """WT-vs-mutant dependency contrast for a target gene under a genotype.

    This is the capability the S-prime paper needed: does loss of ``genotype_gene`` make
    cells selectively dependent on ``target_gene``?

    When a cohort is below ``min_lines`` the statistics are omitted entirely and ``tested``
    is False, so an underpowered comparison can never be mistaken for a finding.
    """

    target_gene: str = Field(..., description="Gene whose dependency is contrasted")
    genotype_gene: str = Field(..., description="Tumor-suppressor genotype defining the cohorts")
    n_wt: int = Field(..., description="Wild-type models with a dependency value", ge=0)
    n_mut: int = Field(..., description="Mutant models with a dependency value", ge=0)
    mean_dep_wt: float | None = Field(default=None, description="Mean dependency in WT cohort")
    mean_dep_mut: float | None = Field(default=None, description="Mean dependency in mutant cohort")
    delta_dep: float | None = Field(
        default=None, description="mean(dep_WT) - mean(dep_MUT); <0 => mutant-selective"
    )
    direction: Direction = Field(..., description="mutant-selective | WT-selective | none")
    mw_p: float | None = Field(default=None, description="Mann-Whitney U p-value (two-sided)")
    bh_fdr: float | None = Field(
        default=None, description="Benjamini-Hochberg FDR if a gene set was tested"
    )
    min_lines: int = Field(..., description="Minimum per-cohort n required to report", ge=1)
    tested: bool = Field(..., description="False if a cohort was too small (n < min_lines)")
    mutation_type: MutationType | None = Field(
        default=None, description="Variant class the mutant cohort was built from"
    )
    data_source: DataSource = Field(..., description="Provenance of the underlying matrix")
    note: str | None = Field(
        default=None, description="Human-readable caveat, e.g. cohort too small"
    )

    @field_validator("target_gene", "genotype_gene")
    @classmethod
    def _validate_symbols(cls, v: str) -> str:
        if not GENE_SYMBOL_PATTERN.match(v.upper()):
            raise ValueError(f"Invalid gene symbol format: {v}")
        return v.upper()
