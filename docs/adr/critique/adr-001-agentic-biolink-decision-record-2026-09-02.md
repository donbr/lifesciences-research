# Agentic Biolink: What Was Decided, What Was Built, and What ADR-001 v1.5 Must Reconcile

**Date:** 2026-09-02
**Status:** Decision record (synthesis). Not an ADR; input to ADR-001 v1.5.
**Supersedes in part:** `docs/evaluation/architecture-review-recommendations-2026-09-02.md` §2.3 verdict and §4 Phase 0, which framed the Biolink question as an open decision. It is not open. See §1.
**Sources:** every file under `docs/adr/` (accepted, archive, critique, draft, amendments, plus v1.2 and v1.3 recovered from git blobs `4308911` and `501c816`), `docs/prior-art-api-patterns.md`, `docs/platform-engineering-rationale.md`, both `speckit-standard-prompt*.md`, all of `docs/research/`, all ten papers under `docs/prior-art-research/`, `docs/competency-questions/competency-questions-catalog.md`, and the models under `src/lifesciences_mcp/models/`.

---

## 1. Verdict

The Agentic Biolink schema **was decided on 2025-12-21 and has been implemented consistently since**. The earlier review's "partially adopted" verdict measured the code against one sentence of ADR-001 §4 that does not describe the decision the rest of the corpus records and the code follows. The sentence is the outlier, not the implementation.

Three things were decided, in this order of importance:

1. **Structure.** Flat, sparse JSON entity records; TRAPI nesting rejected. Implemented in all 13 servers.
2. **Identity and cross-references.** Every entity carries a canonical CURIE and a `cross_references` object keyed by a normative registry, so an agent can triangulate across sources. Implemented in all 13 servers, with the value-format inconsistencies now tracked in AGE-687.
3. **Cognitive Hooks.** Redundant, identity-confirming metadata on every record: aliases and synonyms, previous symbols, and verification anchors such as chromosomal location. Implemented where the upstream supplies them (HGNC `alias_symbols`, `prev_symbols`, `location`; Entrez `aliases`, `map_location`; ChEMBL and IUPHAR `synonyms`), and stripped by `slim=True` exactly as the v1.0 red-team review specified.

The Biolink Model enters the decision in two ways, both honored:

- **Categories** are carried by the registry: each key maps to a Biolink category (Gene, Protein, ChemicalEntity, Disease, Pathway), which is how the January 2026 standards review scored Biolink alignment.
- **Predicates and node types as `biolink:` CURIEs** live in the edge layer, not the MCP tool payloads. The competency-question graphs type nodes as `biolink:Gene` and edges as `biolink:agonist_of` or `biolink:gene_associated_with_condition`. This follows the architecture's explicit split, recorded in `docs/prior-art-api-patterns.md` §7.5: MCP tools return verified nodes; skills and the graph builder produce edges.

The one sentence that does not fit is ADR-001 §4's "**Vocabulary:** Keys must use Biolink Model terms (e.g., `biolink:treats`)". Its example is a predicate, and predicates are not keys of an entity record. §2 traces where that sentence came from.

---

## 2. How the vocabulary sentence became an orphan

| Version | Vocabulary clause | What the worked example showed | Where the mandate makes sense |
|---|---|---|---|
| master ADR v0.1 (2025-12-21) | "strictly use Biolink Model terms for **keys and values** (e.g., `biolink:treats`, `biolink:Gene`)" | An **association record**: `subject_id`, `subject_aliases`, `subject_location`, `relation: "biolink:associated_with"`, `object_id` | On an edge record, `relation` takes a Biolink predicate and node types take Biolink classes. Coherent. |
| master ADR v1.0 | narrowed silently to "terms for **keys**" | Same association record, now with `cross_references`, `previous_symbols`, `gene_groups` | Still an edge record. Still coherent. |
| ADR-001 v1.1 through v1.4 | "Keys must use Biolink Model terms (e.g., `biolink:treats`)" | **Example deleted.** §4 compressed to four lines; Cognitive Hooks enumeration deleted at the same time | The record type changed underneath the sentence. From v1.1 the "Mandate" line says "every **entity** response", the registry is entity-keyed, and every server returns entity records. No entity key is a predicate. |

Between v1.0 and v1.1 the red-team review moved all normativity into Appendix A (the Key Registry), §7 (slim mode), and §8 (envelopes). The association-record example that gave the vocabulary clause its meaning was dropped, the clause survived by inertia, and §4 has been byte-identical from v1.1 to v1.4 (diff-verified across the git blobs). Three critiques and two sign-offs later, nobody re-read the sentence against an entity record.

Meanwhile the predicate vocabulary went where edges went. `docs/prior-art-api-patterns.md` §7.5 names the split as a deliberate contribution; the competency-question catalog and the graph-builder skill use `biolink:` terms for exactly the association records v0.1 drew. So the original intent, "Biolink terms so the agent understands the semantics", was carried out at the layer where those terms have referents.

---

## 3. What the corpus says, file by file

| Claim | Where | Status in code |
|---|---|---|
| Flat JSON, reject TRAPI nesting | v0.1:52, v1.0:53, v1.4:44; `industry-standards-alignment.md` §1.2 ("~60% token reduction") | Implemented everywhere |
| `cross_references` object per Key Registry, omit absent keys | v1.0:55 (forced by `adr-001-agentic-experience-critique.md`); v1.1 Appendix A (from red-team Blocker 1); null policy at v1.2 | Implemented everywhere; omit-null fixed on the wire in biosciences-mcp PR #4; value-format deviations in AGE-687 |
| Cognitive Hooks = aliases/synonyms, previous symbols, verification anchors (`chromosomal_location`, `molecular_weight`) | v0.1:53 (only enumeration), v1.0:54, 64-65; `adr-001-v1.0-red-team-review.md:182` ("slim = no cognitive hooks") | Implemented per upstream availability; definition absent from v1.1 onward; standard prompts cite the undefined term |
| Biolink categories covered by the registry | `industry-standards-alignment.md:23, 37, 97-112, 238` (10 of 15 categories, "Strong") | Implemented as key-to-category mapping |
| Biolink predicates on associations | v0.1:64, v1.0:73 examples; `competency-questions-catalog.md:59-67`; graph-builder skill | Implemented in the edge layer |
| Full Biolink/TRAPI serialization | `industry-standards-alignment.md:201`, `validation-strategy-recommendations.md:119-120` (FC-1, FC-2, low priority) | Explicitly deferred, never rescinded |
| Monarch and OLS (would force `biolink:*Association` typing) | `ontology-api-assessment.md:32, 58, 285` | Explicitly deferred to Q2 2026 |
| "Document TRAPI deviation in ADR-001 §10" | `validation-strategy-recommendations.md:92` (QW-3) | Never done; no §10 exists |
| `biolink:` terms as keys of entity records | v1.1 through v1.4 §4 only | Not implemented, and not implementable as written |

Two sources the ADR cites, "Technical Standards & Implementation Guide" and "Agentic Data Strategy", exist nowhere in the repository. Any intent older than master ADR v0.1 is lost. The research directory post-dates the schema by about five weeks, so the prior-art work justified the decision rather than producing it. That is fine; the decision is well justified. But it means v0.1 is the earliest surviving statement of intent and should be treated as such.

---

## 4. What ADR-001 v1.5 must do

This is a reconciliation, not a new decision. Four edits and one open question.

1. **Rewrite §4 as three mandates plus one alignment statement.**
   - Structure: flat JSON, no TRAPI nesting (unchanged).
   - Identity and cross-references: canonical CURIE `id` plus `cross_references` per Appendix A, keys omitted when absent, **enforced on the wire** (cite the contract tier in `biosciences-mcp/tests/contract/`).
   - Cognitive Hooks: restore the v0.1 enumeration as a named field family: `synonyms` or `alias_symbols`, `prev_symbols`, and verification anchors (`location`, `molecular_weight`, `molecular_formula`), populated when the upstream supplies them, stripped by `slim=True`.
   - Biolink alignment: registry keys map to Biolink categories (cite the standards-alignment table); `biolink:` node classes and predicates are the vocabulary of the **edge layer** (skills, graph builder, Graphiti), per `prior-art-api-patterns.md` §7.5. Delete the "keys must use Biolink Model terms" sentence.
2. **Add a serialization contract** (§4 or §8): omit-null applies to tool output; name the mechanism (`OmitNoneModel`) and the test that proves it.
3. **Fix the counts and the amendment.** Appendix A has 23 keys, not 22; fold Amendment 001 into Appendix A or mark it Rejected (its `opentargets` key never landed and is redundant with `ensembl_gene`).
4. **Add the §10 the research plan asked for**: a short "Standards alignment and deferred items" section recording FC-1, FC-2, and the Monarch/OLS deferral, so the next reviewer does not rediscover them.

**Open question, the only real one:** canonical cross-reference **value format**. The registry says bare local IDs (`CHEMBL25`, `672`); tool `id` fields and the competency graphs use CURIEs (`CHEMBL:25`, `HGNC:1100`); ChEMBL and PubChem outputs already emit CURIEs in `cross_references`. Bioregistry-canonical CURIEs everywhere is the agent-friendlier choice and matches the standards review's CURIE section; it changes the regexes and four servers' outputs. Bare IDs match the registry as written and change two servers. Either is defensible; AGE-687's five ADR-blocked cases wait on it.

**Optional enhancement, not a reconciliation item:** a `category` field (`biolink:Gene` etc.) on entity records would let a consumer type a record without knowing which tool produced it, and would make the DrugMechDB and `reasoner-validator` benchmarks in `benchmark-datasets-analysis.md` directly joinable. Cheap, additive, and the first step toward FC-2 if it is ever wanted. Decide separately.

---

## 5. Documents worth preserving, ranked

The canonical record of this decision is these seven files. Nothing here should be archived or deleted, and the two git-only versions should be restored to disk under `docs/adr/archive/`.

| # | File | Why it matters |
|---|---|---|
| 1 | `docs/adr/archive/master-adr-v0.1.md` | Only surviving statement of original intent; only enumeration of Cognitive Hooks; the association-record example that explains the vocabulary clause. |
| 2 | `docs/adr/critique/adr-001-agentic-experience-critique.md` | Proved §4 and §6 contradicted each other and forced `cross_references` into the schema; this is why Agentic Biolink means what it means in practice. |
| 3 | `docs/adr/critique/adr-001-v1.0-red-team-review.md` | Blocker 1 created the Key Registry, Blocker 4 created `slim=True`, and its "three developers, three implementations" test is the standard any v1.5 sentence must pass. |
| 4 | `docs/adr/accepted/adr-001-v1.4.md` | Binding text. |
| 5 | `docs/adr/archive/adr-001-v1.1.md`, plus v1.2 (`git show 4308911:docs/adr/accepted/adr-001-v1.2.md`) and v1.3 (`git show 501c816:docs/adr/accepted/adr-001-v1.3.md`) | Where §4 froze and the example was deleted; v1.2 and v1.3 exist only in git and should be restored to `docs/adr/archive/`. |
| 6 | `docs/research/industry-standards-alignment.md` | The only systematic Biolink, TRAPI, and CURIE audit; the category-level reading of Biolink alignment; the deferral of full serialization. |
| 7 | `docs/prior-art-api-patterns.md` | §7.4 (registry as contribution), §7.5 (node tools vs edge skills, the split that locates the predicate vocabulary), glossary definition of Agentic Biolink. |

Supporting: `docs/prior-art-research/markdown/Jackson_Callaghan_NoDate_BioThings_Explorer_a_query_engine_for.md` (closest external analogue; its line 64 is the published warrant for substituting a lighter model than full Biolink), `docs/research/validation-strategy-recommendations.md` (FC-1, FC-2, QW-3), `docs/research/ontology-api-assessment.md` (Monarch/OLS deferral), `docs/competency-questions/competency-questions-catalog.md` (where `biolink:` vocabulary is actually used).

Two housekeeping facts: `docs/evaluation/architecture-review-recommendations-2026-09-02.md` and `docs/evaluation/linear-and-governance-inventory-2026-09-02.md` are untracked in git as of this writing; and this repository is the reference copy, so whatever is preserved here should also be mirrored or linked from `biosciences-mcp/docs/adr/`, which holds the binding ADR set.

---

## 6. Correction to the 2026-09-02 architecture review

§2.3 of that review said "the project adopted a flat, cross-referenced JSON convention, not a Biolink-aligned schema". That is wrong as a description of the decision and half-right as a description of the ADR text. The corrected statement: the project adopted the schema it decided on, with Biolink alignment at the category level in entity records and at the predicate level in the edge layer; ADR-001 §4 carries one sentence from a superseded association-record example that should be removed. §4 Phase 0 of the review ("decide A, B, or C") should read: apply the reconciliation in §4 above, then decide the value-format question.
