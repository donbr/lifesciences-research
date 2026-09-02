# Data Model: DepMap Genotype-Selective Dependency MCP Server

**Feature**: 014-depmap-mcp-server
**Created**: 2026-09-02
**Input**: [spec.md](./spec.md), [research.md](./research.md)

## Overview

Pydantic v2 models following the Agentic Biolink schema: flattened JSON, omit-if-null, canonical
envelopes, and a `cross_references` object drawn from the shared registry.

**Omit-if-null is implemented with a `model_dump` override, never with `ConfigDict(exclude_none=...)`.**
That config key does not exist in Pydantic v2 and is silently ignored, which is the defect the
current code has. The working pattern in this repository is `models/drug.py`, `models/ensembl.py`
and `models/pharmacology.py`:

```python
def model_dump(self, **kwargs: Any) -> dict[str, Any]:
    kwargs.setdefault("exclude_none", True)
    return super().model_dump(**kwargs)
```

Every model below carries that override, including `GenotypeContrast`, which currently has no
configuration at all and emits six nulls.

## Shared Types

```python
DataSource = Literal["broad_24q2", "sanger_project_score"]
```

Present on every record (FR-005). Results from the two providers come from different screens and
must never be compared without it being visible.

```python
MutationType = Literal["frameshift", "snp", "insertion", "deletion", "splice_variant", "mutation"]
```

The closed set the upstream accepts, quoted from its own 404 body (research.md R2). `mutation` is
accepted but means *any variant*: for RB1 it returns 2185 of 2266 models. It is a valid value, not a
sensible default for a genotype cohort, and the tool contract says so.

```python
Direction = Literal["mutant-selective", "WT-selective", "none"]
```

`none` is returned on an exact tie (FR-004), not only when a contrast was not tested.

## Entity Models

### CellModel

**Purpose**: A cancer cell line or organoid. Returned by `search_models` (as a candidate) and
`get_model` (in full).

**Token budget**: ~20 tokens slim, ~90 full.

```python
class CellModel(BaseModel):
    id: str                          # "SIDM:00903" CURIE
    name: str                        # primary name, e.g. "A549"
    aliases: list[str] = []          # every stored alias
    lineage: str | None = None       # tissue/lineage from the linked sample
    model_type: str | None = None    # e.g. "Cell Line"
    data_available: list[str] = []   # which datasets exist, from the *_available flags
    data_source: DataSource
    cross_references: CrossReferences | None = None
```

**Validation**:

- `id` must match `^SIDM:\d{5}$`. The upstream native form is `SIDM00903`; the CURIE adds the colon
  so the identifier is self-describing, matching `NCT:########` in feature 013.
- `validate_id` is a static method on the client, and `normalize_id` accepts the bare upstream form
  and returns the CURIE.

**Cross-references** (research.md R5): `ccle` and `cosmic` are both resolvable upstream. Omit either
key entirely when the model has no such identifier; never emit null.

### DependencyRecord

**Purpose**: How essential one gene is in one cell model.

```python
class DependencyRecord(BaseModel):
    gene: str                        # HGNC symbol, upper-cased
    model_id: str                    # "SIDM:#####" CURIE
    gene_effect: float | None = None # more negative = more essential
    data_source: DataSource
```

**Note**: values never come from a live call. No provider serves gene effect over an API
(research.md R3); they come from a cached matrix. Any record whose `gene_effect` is absent is
omitted from a contrast rather than treated as zero (FR-002).

### GenotypeCohort

**Purpose**: The models carrying a given variant class in a given gene.

```python
class GenotypeCohort(BaseModel):
    gene: str
    mutation_type: MutationType      # recorded, never implicit (FR-009)
    model_ids: list[str]
    total_count: int
    data_source: DataSource
```

**Validation**: `mutation_type` outside the closed set is rejected with a message naming the
accepted values, before any request is made.

### GenotypeContrast

**Purpose**: The comparison this feature exists to provide.

```python
class GenotypeContrast(BaseModel):
    target_gene: str
    genotype_gene: str
    n_mutant: int                    # after missing values are dropped
    n_wildtype: int
    mean_dep_mutant: float | None = None
    mean_dep_wt: float | None = None
    delta_dep: float | None = None   # mutant mean minus wild-type mean
    mw_p: float | None = None        # Mann-Whitney U, normal approximation
    bh_fdr: float | None = None      # Benjamini-Hochberg adjusted
    direction: Direction
    tested: bool                     # false when either cohort is under min_lines
    note: str | None = None          # why it was not tested
    min_lines: int
    mutation_type: MutationType | None = None
    data_source: DataSource
```

**Validation and behaviour**:

- Cells with a missing dependency value are dropped from both cohorts first; `n_mutant` and
  `n_wildtype` report the sizes actually used (FR-002).
- If either cohort is below `min_lines`, `tested` is false, `note` says why, and the statistics are
  omitted rather than reported (FR-003). A caller cannot mistake an underpowered comparison for a
  finding.
- `direction` is `none` when `delta_dep` is exactly zero (FR-004). The current code's
  `"mutant-selective" if delta < 0 else "WT-selective"` reports a tie as wild-type-selective.
- `data_source` is required, so a Broad result and a Sanger result are never confused (FR-005).

## Envelopes

Unchanged from the canonical definitions in `models/envelopes.py`:

- `PaginationEnvelope` for `search_models` and `models_with_mutation`, with `page_size` carrying the
  **requested** page size, not the number of items returned, and `cursor` set whenever more results
  remain (FR-010, FR-011).
- `ErrorEnvelope` for every failure, with a `recovery_hint`. Error messages must name this data
  source; the current code routes four call sites through a helper that hardcodes another API's
  name (FR-014).

**Error codes used**: `UNRESOLVED_ENTITY` (free text passed to a strict tool), `ENTITY_NOT_FOUND`
(a well-formed identifier that does not exist), `INVALID_INPUT` (an unaccepted mutation type),
`RATE_LIMITED`, `UPSTREAM_ERROR`.

An empty result set is **not** an error. `search_models` returns an empty `PaginationEnvelope`
(FR-007), where the current code returns `ENTITY_NOT_FOUND`.

## Alias Index (internal, not a returned entity)

Fuzzy search is served from a normalised in-process index because the upstream filter is exact and
case-sensitive (research.md R4).

- Built with one request: `/models?fields[model]=names&page[size]=2500`. Measured at 2266 rows,
  250 KB, ~1.7 s.
- Normalisation: case-fold, then strip whitespace and punctuation, so `A549`, `a549`, `MCF-7`,
  `MCF7` and `HeLa` all reduce to a comparable key.
- Ranking: exact alias match first, then normalised match, then prefix match.
- Cached for the process lifetime and rebuilt lazily if absent. This is a cache, not storage; the
  server remains stateless across restarts.
