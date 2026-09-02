"""Unit tests for DepMap Pydantic models (no network)."""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.depmap import (
    CellModel,
    DependencyRecord,
    DepMapCrossReferences,
    GenotypeCohort,
    GenotypeContrast,
)

pytestmark = [pytest.mark.unit, pytest.mark.depmap]


class TestDependencyRecord:
    def test_gene_uppercased(self):
        r = DependencyRecord(
            gene="rb1",
            model_id="SIDM:00903",
            gene_effect=-1.0,
            dependency=1.0,
            dependent=True,
            data_source="broad_24q2",
        )
        assert r.gene == "RB1"

    def test_invalid_gene_rejected(self):
        with pytest.raises(ValidationError):
            DependencyRecord(gene="!!bad", model_id="SIDM:00903", data_source="broad_24q2")

    def test_invalid_data_source_rejected(self):
        with pytest.raises(ValidationError):
            DependencyRecord(gene="RB1", model_id="SIDM:00903", data_source="made_up")  # type: ignore[arg-type]

    def test_absent_measurement_is_omitted_not_zero(self):
        """A model with no measurement must omit the key, never report 0.0."""
        r = DependencyRecord(gene="RB1", model_id="SIDM:00903", data_source="broad_24q2")
        dumped = r.model_dump()
        assert "gene_effect" not in dumped
        assert "dependency" not in dumped


class TestCellModel:
    def test_requires_curie(self):
        with pytest.raises(ValidationError):
            CellModel(id="SIDM00903", name="A549", data_source="sanger_project_score")
        with pytest.raises(ValidationError):
            CellModel(id="A549", name="A549", data_source="sanger_project_score")

    def test_omits_none(self):
        """Optional fields with no value must be absent from the dump, not null.

        Guards the defect this model previously had: ConfigDict(exclude_none=True) is not a
        valid Pydantic v2 key and is silently ignored, so every optional field serialised as
        null, which ADR-001 lists as a forbidden pattern.
        """
        c = CellModel(id="SIDM:00001", name="X", data_source="sanger_project_score")
        dumped = c.model_dump()
        assert "lineage" not in dumped
        assert "model_type" not in dumped
        assert "cross_references" not in dumped
        assert dumped["id"] == "SIDM:00001"

    def test_slim_is_three_keys(self):
        c = CellModel(
            id="SIDM:00903",
            name="A549",
            aliases=["A549", "NCI-A549"],
            lineage="Lung",
            data_source="sanger_project_score",
        )
        assert c.slim() == {
            "id": "SIDM:00903",
            "name": "A549",
            "data_source": "sanger_project_score",
        }

    def test_cross_references_omit_absent_keys(self):
        c = CellModel(
            id="SIDM:00903",
            name="A549",
            data_source="sanger_project_score",
            cross_references=DepMapCrossReferences(ccle="A549_LUNG"),
        )
        xrefs = c.model_dump()["cross_references"]
        assert xrefs == {"ccle": "A549_LUNG"}
        assert "cosmic" not in xrefs

    def test_cross_references_treat_empty_string_as_absent(self):
        x = DepMapCrossReferences(ccle="", cosmic="905949")
        assert x.model_dump() == {"cosmic": "905949"}


class TestGenotypeCohort:
    def test_records_its_mutation_type(self):
        cohort = GenotypeCohort(
            gene="rb1",
            mutation_type="deletion",
            model_ids=["SIDM:00903"],
            total_count=501,
            data_source="sanger_project_score",
        )
        assert cohort.gene == "RB1"
        assert cohort.mutation_type == "deletion"

    def test_rejects_unaccepted_mutation_type(self):
        with pytest.raises(ValidationError):
            GenotypeCohort(
                gene="RB1",
                mutation_type="nonsense",  # type: ignore[arg-type]
                data_source="sanger_project_score",
            )


class TestGenotypeContrast:
    def test_minimal_valid(self):
        c = GenotypeContrast(
            target_gene="AURKB",
            genotype_gene="RB1",
            n_wt=6,
            n_mut=6,
            direction="mutant-selective",
            min_lines=5,
            tested=True,
            data_source="broad_24q2",
        )
        assert c.target_gene == "AURKB" and c.genotype_gene == "RB1"

    def test_symbols_uppercased(self):
        c = GenotypeContrast(
            target_gene="aurkb",
            genotype_gene="rb1",
            n_wt=0,
            n_mut=0,
            direction="none",
            min_lines=5,
            tested=False,
            data_source="broad_24q2",
        )
        assert c.target_gene == "AURKB" and c.genotype_gene == "RB1"

    def test_bad_direction_rejected(self):
        with pytest.raises(ValidationError):
            GenotypeContrast(
                target_gene="AURKB",
                genotype_gene="RB1",
                n_wt=6,
                n_mut=6,
                direction="sideways",  # type: ignore[arg-type]
                min_lines=5,
                tested=True,
                data_source="broad_24q2",
            )

    def test_untested_contrast_omits_statistics(self):
        """An untested contrast must not carry null statistics that could be read as values."""
        c = GenotypeContrast(
            target_gene="AURKB",
            genotype_gene="PTEN",
            n_wt=840,
            n_mut=3,
            direction="none",
            min_lines=5,
            tested=False,
            data_source="broad_24q2",
            note="mutant cohort has 3 cell lines, below the minimum of 5",
        )
        dumped = c.model_dump()
        for key in ("mean_dep_wt", "mean_dep_mut", "delta_dep", "mw_p", "bh_fdr"):
            assert key not in dumped, f"{key} must be omitted, not null, when tested is False"
        assert dumped["tested"] is False
        assert dumped["note"]
