# Feature Specification: DepMap Genotype-Selective Dependency MCP Server

**Feature Branch**: `implement/014-depmap-mcp-server` (feature `014-depmap-mcp-server`)
**Created**: 2026-09-02
**Status**: Draft
**Input**: User description: "Build the DepMap MCP Server. Genotype-selective dependency contrasts: does loss of tumour-suppressor X make cells depend on target Y? Sanger Cell Model Passports REST for model and genotype resolution; provenance-matched contrast computation over cached gene-effect matrices. Fuzzy-to-Fact, Agentic Biolink, canonical envelopes (ADR-001); client extends LifeSciencesClient (ADR-006); module-level singleton, no shutdown hooks (ADR-004)." (Linear AGE-681, child of AGE-680)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Test a genotype-selective dependency claim (Priority: P1)

A researcher asks whether a candidate target is selectively essential in cells that have lost a
given tumour suppressor. Today they must leave the agent entirely: existing connectors report
per-screen essentiality but never the wild-type-versus-mutant contrast, which is the question every
synthetic-lethality claim actually rests on. The researcher wants a single call that returns the
difference in dependency between the two cohorts, a significance value, the size of each cohort,
and which data release the numbers came from.

**Why this priority**: This is the capability gap the feature exists to close. Without it nothing
else in the server delivers value that another connector does not already provide.

**Independent Test**: Fully testable by requesting a contrast for a known genotype-selective pair
and confirming the returned direction, effect size, significance and cohort sizes match a frozen
reference result, with no other tool involved.

**Acceptance Scenarios**:

1. **Given** a target and a genotype gene with sufficient cells in both cohorts, **When** the
   researcher requests a contrast, **Then** the result reports the mean dependency of each cohort,
   their difference, a significance value, a false-discovery-rate-adjusted value, the size of each
   cohort, the direction of selectivity, and the data release the values came from.
2. **Given** a genotype whose mutant cohort is smaller than the minimum, **When** the researcher
   requests a contrast, **Then** the result is explicitly marked as not tested and carries a note
   saying why, rather than reporting an underpowered number as if it were a finding.
3. **Given** cells whose dependency value is missing, **When** a contrast is computed, **Then**
   those cells are excluded from both cohorts and the reported cohort sizes reflect the exclusion.
4. **Given** two cohorts with identical dependency distributions, **When** a contrast is computed,
   **Then** the direction is reported as neither mutant- nor wild-type-selective.

---

### User Story 2 - Resolve a cell model from the name a researcher actually types (Priority: P2)

A researcher refers to cell lines the way they appear in papers: A549, a549, MCF-7, HeLa. The
underlying catalogue stores a stable identifier plus a list of aliases, and its own filter matches
those aliases exactly and case-sensitively. The researcher wants to type any common form and get
back ranked candidates carrying the stable identifier, so a later strict call cannot be made
against a guessed identifier.

**Why this priority**: This is the Fuzzy-to-Fact entry point. Every strict tool depends on it, and
without normalisation the most common queries silently return nothing at all.

**Independent Test**: Fully testable by searching a set of names in mixed case and punctuation and
confirming each resolves to the expected stable identifier, then confirming a strict lookup with
that identifier returns the full record.

**Acceptance Scenarios**:

1. **Given** a cell-line name in any capitalisation, **When** the researcher searches for it,
   **Then** the matching model is returned with its stable identifier and its known aliases.
2. **Given** a name that differs only by punctuation from a stored alias, **When** the researcher
   searches for it, **Then** the matching model is still returned.
3. **Given** a query that matches nothing, **When** the researcher searches, **Then** an empty
   result set is returned rather than an error.
4. **Given** an unresolved free-text name, **When** it is passed to a strict lookup tool, **Then**
   the call is refused with a recovery hint naming the search tool to use first.

---

### User Story 3 - Assemble a genotype cohort (Priority: P3)

Before a contrast can be run, the researcher needs the set of cell models carrying a damaging
variant in the genotype gene. The catalogue can list models by variant class, but its default class
is so broad that it returns almost the entire catalogue and would silently destroy the contrast.
The researcher wants the cohort built from a damaging variant class, and wants the choice recorded
alongside the result.

**Why this priority**: It makes the contrast reproducible end to end inside the agent. The contrast
itself can already be run against a caller-supplied cohort, so this is an enabler rather than the
core value.

**Independent Test**: Fully testable by requesting cohorts for one gene under different variant
classes and confirming the sizes differ as expected and the chosen class is reported back.

**Acceptance Scenarios**:

1. **Given** a gene and a damaging variant class, **When** the researcher requests the cohort,
   **Then** the matching models are returned with the variant class recorded in the result.
2. **Given** a variant class the catalogue does not recognise, **When** the cohort is requested,
   **Then** the call is refused with a message naming the classes that are accepted.
3. **Given** a cohort larger than one page, **When** the researcher pages through it, **Then**
   every model is reachable and the result never silently stops partway.

### Edge Cases

- A name is stored in mixed case (HeLa) so neither the raw nor the upper-cased query matches the
  catalogue's exact filter. Both must still resolve.
- The catalogue's default variant class returns roughly 96% of all models for a common tumour
  suppressor, which is not the damaging call a genotype contrast requires.
- Dependency values are not obtainable from the catalogue's live interface at all, so a contrast
  must be computed from values the caller supplies or from a cached release, never fetched live.
- A cohort has enough cells overall but too few after missing values are dropped.
- Every dependency value in one cohort is missing.
- The catalogue is unreachable or returns an error; the failure must be attributed to this data
  source and not to an unrelated one.
- A result set is empty, which is an answer, not a failure.
- Results drawn from two different providers must never be compared without their provenance being
  visible, because they come from different screens.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute a wild-type-versus-mutant dependency contrast returning, at
  minimum, the mean of each cohort, their difference, a rank-based significance value, a
  false-discovery-rate-adjusted value, the size of each cohort, and the direction of selectivity.
- **FR-002**: System MUST exclude cells with a missing dependency value from both cohorts before
  computing, and MUST report the cohort sizes actually used.
- **FR-003**: System MUST mark a contrast as not tested, with a stated reason, whenever either
  cohort has fewer than a configurable minimum number of cells; it MUST NOT report an underpowered
  contrast as a result.
- **FR-004**: System MUST report a direction of neither-selective when the two cohorts do not
  differ, and MUST NOT default to one direction on an exact tie.
- **FR-005**: Every record the system returns MUST carry the data release it was derived from, and
  releases from different providers MUST be distinguishable.
- **FR-006**: System MUST offer a fuzzy search over cell-model names that succeeds regardless of
  the capitalisation or common punctuation of the query, and MUST return ranked candidates carrying
  the stable identifier and known aliases.
- **FR-007**: Fuzzy search MUST return an empty result set for a query that matches nothing, not an
  error.
- **FR-008**: Strict lookup tools MUST accept only a resolved identifier and MUST refuse free text
  with an UNRESOLVED_ENTITY error whose recovery hint names the search tool to use first.
- **FR-009**: System MUST allow a genotype cohort to be assembled from a caller-chosen variant
  class, MUST reject a class the upstream catalogue does not recognise with a message listing the
  accepted classes, and MUST record the chosen class on the result.
- **FR-010**: System MUST make every member of a multi-page cohort reachable, and MUST NOT return a
  truncated set that presents itself as complete.
- **FR-011**: All list-returning tools MUST use the canonical pagination envelope and all failures
  MUST use the canonical error envelope with a recovery hint.
- **FR-012**: All list-returning tools MUST support a reduced-output mode for token budgeting.
- **FR-013**: Every returned entity MUST carry a cross-reference object using the shared
  cross-reference registry, omitting keys for which no reference exists.
- **FR-014**: Errors originating from this data source MUST be attributed to it by name and MUST
  NOT be reported using another data source's wording.
- **FR-015**: System MUST limit its own request rate against the upstream catalogue and MUST back
  off rather than retry immediately on a rate-limit response.
- **FR-016**: System MUST surface the upstream catalogue's access terms, including that third-party
  application use requires prior permission and is non-commercial, where a caller will see them.
- **FR-017**: The reproducible analysis pipeline MUST remain file-based and MUST NOT gain a
  dependency on this server; the server is for interactive research only.

### Key Entities

- **Cell model**: A cancer cell line or organoid. Carries a stable catalogue identifier, a list of
  names and aliases, a tissue or lineage, flags for which data types exist for it, and cross
  references to external catalogues.
- **Dependency record**: How essential one gene is in one cell model, with the data release it came
  from.
- **Genotype cohort**: The set of cell models carrying a given variant class in a given gene, with
  the variant class recorded.
- **Genotype contrast**: The comparison of dependency between the wild-type and mutant cohorts for
  a target gene: per-cohort means and sizes, the difference, significance, adjusted significance,
  direction, whether it was tested, and the data release.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A researcher can go from a cell-line name as written in a paper to a stable
  identifier, and from a target and genotype pair to a contrast result, without supplying any
  identifier by hand.
- **SC-002**: Cell-line names resolve for at least 95% of a representative sample of common
  aliases, in any capitalisation, where exact-case matching today resolves fewer than half.
- **SC-003**: A contrast for a known genotype-selective pair reproduces the published direction and
  significance of the reference analysis, checked against a frozen fixture.
- **SC-004**: No contrast is ever reported as a finding when either cohort is below the minimum
  size; every such case is returned marked as not tested with a reason.
- **SC-005**: Every returned record states its data release, so results from two providers are
  never silently compared.
- **SC-006**: A reduced-output search result costs roughly 20 tokens per entity rather than the
  full record cost, so a multi-hop query does not exhaust the context window.
