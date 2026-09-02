# Phase 0 Research: DepMap Genotype-Selective Dependency MCP Server

**Feature**: 014-depmap-mcp-server | **Date**: 2026-09-02
**Method**: every finding below was confirmed against the live Sanger Cell Model Passports API on
2026-09-02, not inferred from documentation. Reproduction commands are given so a reviewer can
re-check any claim.

---

## R1: Which DepMap can actually be queried?

**Decision**: Use the Sanger Cell Model Passports REST API for cell-model and genotype resolution.
Compute dependency contrasts from a cached gene-effect matrix, never from a live call.

**Rationale**: Broad DepMap 24Q2, which is the release the reference analysis used, has no stable
public query API. Its canonical distribution is figshare matrices plus the `depmap` and `taigapy`
packages, and Taiga is token-gated. The reproducible pipeline in the companion repository pins
those files by checksum, and a live API would break the byte-reproducibility that repository
deliberately maintains.

Sanger Cell Model Passports does have a documented JSON:API v1.0 REST interface at
`https://api.cellmodelpassports.sanger.ac.uk` with a browsable schema at `/swagger`. It covers
model annotation, mutations, copy number, expression and drug sensitivity.

**Alternatives considered**:

- *ToolUniverse DepMap 24Q2 MCP* (Zitnik Lab). Wraps Broad 24Q2 correlations. Evaluated for reuse;
  it exposes correlations rather than the wild-type-versus-mutant contrast this feature exists to
  provide, so it does not close the gap.
- *A live dependency API.* None exists for either provider. See R3.

**Constraint carried into the design**: Sanger data is Project Score, not Broad 24Q2. They are
different screens with different provenance and must never be silently compared. Sanger also
requires prior permission for third-party application use (depmap@sanger.ac.uk) and is
non-commercial only. This drives FR-005 and FR-016.

---

## R2: The default variant class is unusable for a genotype cohort

**Finding**: `/models/by_mutation/RB1` returns 2185 models out of a catalogue of 2266, roughly 96%
of everything. That endpoint's `mutation` class means any variant at all, not the damaging or
homozygous call a genotype contrast requires. Building a mutant cohort from it would put nearly the
whole catalogue in the mutant arm and destroy the contrast.

**The accepted classes are a closed set.** The API states them in its own 404 body:

```
mutation type needs to be one of frameshift, snp, insertion, deletion, splice_variant or mutation
```

Measured cohort sizes for RB1:

| class | models | usable as a damaging cohort |
|---|---|---|
| mutation | 2185 | no, this is any variant |
| deletion | 501 | yes |
| splice_variant | 60 | yes |
| frameshift | 27 | yes |
| snp, insertion | not measured | class-dependent |
| nonsense, missense | HTTP 404 | not accepted by the API |

**Decision**: The variant class is a required, validated, caller-visible choice. Reject anything
outside the accepted set with a message naming the accepted values, and record the chosen class on
every cohort and contrast result. Do not default silently to `mutation`.

**Reproduce**:

```bash
curl -s 'https://api.cellmodelpassports.sanger.ac.uk/models/by_mutation/RB1?page%5Bsize%5D=1' | head -c 200
curl -s 'https://api.cellmodelpassports.sanger.ac.uk/models/by_nonsense/RB1'
```

---

## R3: CRISPR gene-effect is not a queryable endpoint

**Finding**: `crispr_ko_available` appears on a model record as a boolean flag only. Probes to
`/datasets/crispr` and `/datasets/crispr_ko` return empty. The dependency matrix is distributed as a
Project Score / Data Miner file, not served per gene or per model.

**Decision**: Dependency contrasts are matrix-based for **both** providers. The REST API supplies
model resolution and genotype cohorts; it does not supply dependency values. The contrast tool
therefore consumes values that are supplied by the caller or loaded from a cached, checksum-pinned
release.

**Consequence for the tool surface**: a contrast tool whose parameters are the full per-model
dependency and genotype vectors is not usable by an agent, because roughly 2000 entries would have
to be serialised through the tool boundary for every call. The plan resolves this by keeping the
computation as an internal, unit-tested function and exposing a matrix-backed tool that takes a
target gene and a genotype gene. See plan.md, Complexity Tracking.

---

## R4: The name filter is exact and case-sensitive, so "fuzzy" search must be built, not delegated

**Finding**: `/models` accepts `?filter=[{"name":"names","op":"any","val":"..."}]`. The `any`
operator is the **only** one the API accepts; `contains`, `eq`, `in` and `like` all return HTTP 500.
That confirms the operator the scaffold guessed, and it also means the filter does exact,
case-sensitive matching against the stored alias list.

Measured behaviour:

| query | as typed | upper-cased |
|---|---|---|
| A549 | 1 hit | 1 hit |
| a549 | 0 hits | 1 hit |
| A54 | 0 hits | 0 hits |
| MCF-7 | 0 hits | 0 hits |
| HeLa | 1 hit | 0 hits |
| hela | 0 hits | 0 hits |

Upper-casing rescues `a549` and `mcf7` but breaks `HeLa`, which is stored in mixed case. No single
server-side transformation works, so delegating fuzzy matching to the API cannot satisfy FR-006.

**Decision**: Build a local alias index. Fetch the full catalogue once with a sparse fieldset,
normalise every alias (case-fold, strip punctuation and whitespace), and match locally. Cache it on
the client for the process lifetime.

**Cost, measured**: the whole catalogue with `fields[model]=names` and `page[size]=2500` is one
request, 2266 rows, 250 KB, 1.7 seconds. A single request for the entire index is cheaper than the
per-query round trips a server-side approach would need, and it is the only approach that satisfies
the mixed-case cases.

**Alternatives considered**:

- *Upper-case the query.* Rejected: breaks `HeLa`, and still fails on punctuation variants.
- *Try several transformations per query.* Rejected: several round trips per search, still fails
  `MCF-7`, and each miss costs a full request.
- *Server-side substring matching.* Rejected: not offered; every operator other than `any` is a 500.

**Reproduce**:

```bash
curl -sG 'https://api.cellmodelpassports.sanger.ac.uk/models' \
  --data-urlencode 'filter=[{"name":"names","op":"any","val":"hela"}]' \
  --data-urlencode 'page[size]=2'
curl -sG 'https://api.cellmodelpassports.sanger.ac.uk/models' \
  --data-urlencode 'fields[model]=names' --data-urlencode 'page[size]=2500' | wc -c
```

---

## R5: Which external identifiers resolve a model

**Finding**: `/models/<source>/<source_id>` resolves by external identifier. `CCLE_ID` and
`cosmic_id` both resolve A549 to `SIDM00903`. `model_name` is **not** a valid source and returns
404, so the scaffold's assumption that a plain name resolves this way is wrong; plain names go
through the alias index from R4.

**Decision**: Strict resolution accepts the native `SIDM#####` identifier and the confirmed external
sources. Everything else is a fuzzy query and must go through search first, returning
`UNRESOLVED_ENTITY` if passed to a strict tool (FR-008).

**Cross-references available for the Agentic Biolink object** (FR-013): the CCLE identifier and the
COSMIC identifier are both resolvable, so both belong in `cross_references`; omit either when the
model has none rather than emitting a null.

---

## R6: Statistics without a new dependency

**Decision**: Keep the hand-rolled rank-sum and Benjamini-Hochberg implementation. Do not add numpy
or scipy.

**Rationale**: The contrast core is a Mann-Whitney U with a normal approximation and a
Benjamini-Hochberg adjustment, both short and fully unit-testable. The repository currently has no
numpy or scipy dependency anywhere in `src/` or `tests/`, and the existing implementation is
verified by unit tests that cover separated, identical and empty distributions plus NaN handling.
Adding a scientific stack for two functions would be the larger change.

**Correction to the scaffold's own notes**: the scaffold's spec described the core as "numpy-only"
in one place and "numpy-free" in another. It is numpy-free; that is the intended state.

**Alternatives considered**: `scipy.stats.mannwhitneyu` gives an exact test for small samples, which
matters most exactly where the minimum-cohort rule already refuses to report a result. Not worth a
new dependency; revisit if exact small-sample p-values are ever required below the minimum.

---

## R7: Rate limiting

**Decision**: One request per second with an `asyncio.Lock` and exponential backoff on 429 and 5xx,
matching `clients/clinicaltrials.py`.

**Rationale**: The Constitution's Required Patterns table makes client-side rate limiting mandatory
for all API clients, and lists unbounded concurrency as a Forbidden Pattern. Sanger publishes no
documented rate limit, and third-party use is permission-gated, so the conservative rate the
repository already uses for other unspecified APIs is the right default. Cohort pagination is the
real exposure: a cohort of 501 models is several sequential pages.

---

## R8: Reference result to regress against

**Decision**: The acceptance fixture is the AURKB-against-RB1 contrast, which the companion
analysis found mutant-selective, consistent with the RB-E2F dependency result.

**Status**: The fixture requires a slice of the Broad 24Q2 gene-effect and damaging-mutation
matrices, which are gated and not present in this repository. Recorded as a task with its blocker
stated rather than as a passing test, so the acceptance criterion is not quietly dropped. SC-003
stays in the spec and the task stays open until the fixture lands.
