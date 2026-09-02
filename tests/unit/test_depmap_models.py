"""Unit tests for DepMap Pydantic models (no network)."""

import pytest
from pydantic import ValidationError

from lifesciences_mcp.models.depmap import (
    DepMapModelCandidate,
    DependencyRecord,
    GenotypeContrast,
)

pytestmark = [pytest.mark.unit, pytest.mark.depmap]


class TestDependencyRecord:
    def test_gene_uppercased(self):
        r = DependencyRecord(
            gene="rb1", model_id="ACH-000001", gene_effect=-1.0,
            dependency=1.0, dependent=True, data_source="broad_24q2",
        )
        assert r.gene == "RB1"

    def test_invalid_gene_rejected(self):
        with pytest.raises(ValidationError):
            DependencyRecord(
                gene="!!bad", model_id="ACH-1", gene_effect=0.0,
                dependency=0.0, dependent=False, data_source="broad_24q2",
            )

    def test_invalid_data_source_rejected(self):
        with pytest.raises(ValidationError):
            DependencyRecord(
                gene="RB1", model_id="ACH-1", gene_effect=0.0,
                dependency=0.0, dependent=False, data_source="made_up",
            )


class TestGenotypeContrast:
    def test_minimal_valid(self):
        c = GenotypeContrast(
            target_gene="AURKB", genotype_gene="RB1", n_wt=6, n_mut=6,
            direction="mutant-selective", min_lines=5, tested=True, data_source="broad_24q2",
        )
        assert c.target_gene == "AURKB" and c.genotype_gene == "RB1"

    def test_symbols_uppercased(self):
        c = GenotypeContrast(
            target_gene="aurkb", genotype_gene="rb1", n_wt=0, n_mut=0,
            direction="none", min_lines=5, tested=False, data_source="broad_24q2",
        )
        assert c.target_gene == "AURKB" and c.genotype_gene == "RB1"

    def test_bad_direction_rejected(self):
        with pytest.raises(ValidationError):
            GenotypeContrast(
                target_gene="AURKB", genotype_gene="RB1", n_wt=6, n_mut=6,
                direction="sideways", min_lines=5, tested=True, data_source="broad_24q2",
            )


class TestModelCandidate:
    def test_omits_none(self):
        c = DepMapModelCandidate(model_id="SIDM00001", data_source="sanger_project_score")
        dumped = c.model_dump()
        assert "model_name" not in dumped  # exclude_none
