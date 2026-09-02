# Tool Contract: models_with_mutation

**Type**: Strict Lookup (cohort assembly)
**Protocol Phase**: Phase 2
**Returns**: PaginationEnvelope[CellModel] | ErrorEnvelope
**Satisfies**: FR-009, FR-010, FR-011, FR-012

## Purpose

Assemble the genotype cohort: the cell models carrying a given class of variant in a given gene.

## Parameters

```python
{
    "gene": str,                          # HGNC symbol, upper-cased
    "mutation_type": MutationType,        # REQUIRED, no default
    "slim": bool = False,
    "cursor": str | None = None,
    "page_size": int = 50,
}
```

### mutation_type (required, no default)

Accepted values, quoted from the upstream's own error body: `frameshift`, `snp`, `insertion`,
`deletion`, `splice_variant`, `mutation`. Anything else is rejected with `INVALID_INPUT` listing the
accepted values, before any request is made.

**The value `mutation` means any variant, not a damaging call.** Measured for RB1 (research.md R2):

| mutation_type | models returned |
|---|---|
| mutation | 2185 of 2266 |
| deletion | 501 |
| splice_variant | 60 |
| frameshift | 27 |

A cohort built from `mutation` puts roughly 96% of the catalogue in the mutant arm and destroys the
contrast. The parameter has no default precisely so this choice is always made deliberately, and the
chosen value is echoed on the result.

## Behaviour

The returned `page_size` is the **requested** size, not the number of items in the page. A cursor is
set whenever the upstream reports more results, so a 501-model cohort is fully reachable (FR-010).
The current code returns a null cursor while truncating at a `max_models` cap, which presents a
partial cohort as complete.

Pagination is rate-limited like every other call (FR-015); a large cohort is several sequential
requests.

## Acceptance

| Given | Then |
|---|---|
| `gene="RB1", mutation_type="deletion"` | 501 models, mutation type echoed on the result |
| `gene="RB1", mutation_type="nonsense"` | `INVALID_INPUT` listing the six accepted values |
| a cohort larger than one page | every model reachable by following the cursor |
