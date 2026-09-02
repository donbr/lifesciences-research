# Tool Contract: genotype_contrast_by_gene

**Type**: Strict Lookup (the key capability)
**Protocol Phase**: Phase 2
**Returns**: GenotypeContrast | ErrorEnvelope
**Satisfies**: FR-001, FR-002, FR-003, FR-004, FR-005

## Purpose

Answer the question the whole feature exists for: is the target gene selectively essential in cells
that have lost the genotype gene?

## Parameters

```python
{
    "target_gene": str,                       # e.g. "AURKB"
    "genotype_gene": str,                     # e.g. "RB1"
    "mutation_type": MutationType = "deletion",
    "min_lines": int = 5,
    "data_source": DataSource = "broad_24q2",
}
```

## Why this shape, and not the vector form

The scaffold exposed a tool taking the full per-model dependency and genotype vectors as arguments.
An agent would have to serialise roughly 2000 entries through the tool boundary on every call, so
the tool could not be used at all, and its own acceptance criterion could never be exercised.

The computation is unchanged and stays a unit-tested internal function,
`compute_genotype_contrast`, which is where its existing tests already point. The tool loads the
vectors from the cached release and calls it.

## Behaviour

1. Cells with a missing dependency value are dropped from both cohorts (FR-002).
2. If either cohort is then below `min_lines`, return with `tested` false and a note giving the
   reason, and omit the statistics (FR-003). An underpowered comparison is never dressed as a
   finding.
3. Otherwise compute per-cohort means, their difference, a Mann-Whitney U p-value by normal
   approximation, and a Benjamini-Hochberg adjusted value.
4. Direction is `mutant-selective` when the mutant cohort is more dependent, `WT-selective` when it
   is less, and `none` on an exact tie (FR-004). The current code reports a tie as WT-selective.
5. Every result carries its data source and the mutation type the cohort was built from (FR-005).

## Responses

Tested:

```json
{
  "target_gene": "AURKB",
  "genotype_gene": "RB1",
  "n_mutant": 34,
  "n_wildtype": 812,
  "mean_dep_mutant": -0.71,
  "mean_dep_wt": -0.44,
  "delta_dep": -0.27,
  "mw_p": 0.0008,
  "bh_fdr": 0.004,
  "direction": "mutant-selective",
  "tested": true,
  "min_lines": 5,
  "mutation_type": "deletion",
  "data_source": "broad_24q2"
}
```

Not tested:

```json
{
  "target_gene": "AURKB",
  "genotype_gene": "PTEN",
  "n_mutant": 3,
  "n_wildtype": 840,
  "direction": "none",
  "tested": false,
  "note": "mutant cohort has 3 cell lines, below the minimum of 5",
  "min_lines": 5,
  "mutation_type": "deletion",
  "data_source": "broad_24q2"
}
```

Statistics keys are omitted, not null.

## Acceptance

| Given | Then |
|---|---|
| `AURKB` against `RB1` on Broad 24Q2 | mutant-selective, reproducing the reference analysis (SC-003, blocked on the gated fixture) |
| a mutant cohort below `min_lines` | `tested` false with a reason, no statistics |
| identical distributions | direction `none` |
| all values missing in one cohort | `tested` false, cohort size reported as zero |
