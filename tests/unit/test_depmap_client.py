"""Unit tests for the DepMap genotype-contrast core (no network).

The genotype contrast is the key capability (AGE-681): does loss of a tumor
suppressor make cells selectively dependent on a target? These tests pin the
math against synthetic fixtures.

Run with:
    uv run pytest tests/unit/test_depmap_client.py -v
"""

import math

import pytest

from lifesciences_mcp.clients.depmap import (
    bh_fdr,
    compute_genotype_contrast,
    mannwhitney_u_p,
)

pytestmark = [pytest.mark.unit, pytest.mark.depmap]


# --- fixtures: 6 mutant (call 2), 6 WT (call 0), 1 excluded (call 1) ----------
def _genotypes():
    g = {f"MUT{i}": 2 for i in range(6)}
    g.update({f"WT{i}": 0 for i in range(6)})
    g["EXCL"] = 1
    return g


def _mutant_selective_effects():
    # mutant models strongly dependent (very negative gene-effect); WT near zero
    eff = {f"MUT{i}": v for i, v in enumerate([-1.0, -0.9, -1.1, -0.95, -1.05, -1.2])}
    eff.update({f"WT{i}": v for i, v in enumerate([-0.1, 0.0, -0.05, 0.05, -0.02, 0.02])})
    eff["EXCL"] = -1.0  # excluded model must not count
    return eff


# ==============================================================================
# Mann-Whitney U (numpy-free normal approximation)
# ==============================================================================
class TestMannWhitney:
    def test_separated_groups_significant(self):
        p = mannwhitney_u_p([5, 6, 7, 8, 9], [0, 1, 2, 3, 4])
        assert p < 0.05

    def test_identical_groups_not_significant(self):
        p = mannwhitney_u_p([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        assert p == pytest.approx(1.0, abs=1e-9)

    def test_empty_is_nan(self):
        assert math.isnan(mannwhitney_u_p([], [1, 2, 3]))


# ==============================================================================
# Benjamini-Hochberg FDR
# ==============================================================================
class TestBHFDR:
    def test_monotone_and_bounded(self):
        q = bh_fdr([0.001, 0.5, 0.9])
        assert all(0 <= x <= 1 for x in q)
        assert q[0] <= q[1] <= q[2]

    def test_nan_passthrough(self):
        q = bh_fdr([0.01, float("nan"), 0.02])
        assert math.isnan(q[1])


# ==============================================================================
# Genotype contrast — the key capability
# ==============================================================================
class TestGenotypeContrast:
    def test_mutant_selective(self):
        r = compute_genotype_contrast(
            "AURKB", "RB1", _mutant_selective_effects(), _genotypes(), min_lines=5
        )
        assert r.tested is True
        assert r.n_wt == 6 and r.n_mut == 6  # excluded model dropped
        assert r.delta_dep < 0  # WT - MUT < 0 => mutant more dependent
        assert r.direction == "mutant-selective"
        assert r.mw_p < 0.05
        assert r.data_source == "broad_24q2"

    def test_wt_selective_flips_direction(self):
        # invert: WT strongly dependent, mutant near zero
        eff = _mutant_selective_effects()
        flipped = {}
        for k, v in eff.items():
            if k.startswith("MUT"):
                flipped[k] = -0.02
            elif k.startswith("WT"):
                flipped[k] = -1.0
            else:
                flipped[k] = v
        r = compute_genotype_contrast("CDK6", "RB1", flipped, _genotypes(), min_lines=5)
        assert r.tested is True
        assert r.delta_dep > 0
        assert r.direction == "WT-selective"

    def test_small_cohort_not_tested(self):
        eff = _mutant_selective_effects()
        geno = _genotypes()
        # shrink mutant cohort to 3 by excluding three mutant models
        for i in (3, 4, 5):
            geno[f"MUT{i}"] = 1
        r = compute_genotype_contrast("PARP1", "PTEN", eff, geno, min_lines=5)
        assert r.tested is False
        assert r.direction == "none"
        assert r.n_mut == 3
        assert r.note is not None and "too small" in r.note

    def test_nan_effects_skipped(self):
        eff = _mutant_selective_effects()
        eff["MUT0"] = float("nan")
        r = compute_genotype_contrast("AURKB", "RB1", eff, _genotypes(), min_lines=5)
        assert r.n_mut == 5  # the NaN mutant dropped

    def test_provenance_label_preserved(self):
        r = compute_genotype_contrast(
            "AURKB", "RB1", _mutant_selective_effects(), _genotypes(),
            min_lines=5, data_source="sanger_project_score",
        )
        assert r.data_source == "sanger_project_score"
