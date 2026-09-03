# Architecture Review Recommendations: Method, Tooling, and the Agentic Biolink Question

**Date:** 2026-09-02
**Scope:** Recommend *how* to review the 13 MCP server implementations against the architecture documentation (ADR-001 v1.4, Constitution v1.1.0, `docs/speckit-standard-prompt-v2.md`) and how to bring the documentation back in line with the code. This document stops short of implementation.
**Inputs:** Official Claude Code docs (code.claude.com/docs), GitHub Spec Kit v1.0.4 docs and command templates (repo HEAD a369c5c), local code inspection, and in-process wire-level tool calls against the checked-out code.

---

## 1. Executive Summary

1. **The "Agentic Biolink" schema was only partially adopted.** ADR-001 §4 has three mandates. One (flattened JSON) is met everywhere. One (`cross_references` per the Key Registry) is met by 4 of 13 servers and violated in shape, key set, or null handling by the rest. One (Biolink Model vocabulary, e.g. `biolink:treats`) was never implemented in any model, server, or test. "Agentic Biolink" in practice means "flat JSON plus a `cross_references` object". The name over-claims.
2. **The omit-null guarantee does not hold on the wire.** `CrossReferences.model_dump()` is overridden with `exclude_none=True`, but FastMCP serializes return values through pydantic-core and bypasses that override. Calling `get_gene("HGNC:1100")` through `fastmcp.Client` against local code returns 15 `null` keys. Unit tests pass because they call `model_dump()` directly. The February 2026 compliance report marked HGNC Principle III as PASS because it read model definitions rather than tool output.
3. **The existing review method audits definitions, not behavior.** The February playbook and its six reports are code-reading exercises. The Constitution's "Required Patterns" table promises `/analyze` validation and runtime regex validation, but Spec Kit's `analyze` never reads code and the regex table `CROSS_REF_PATTERNS` is defined and never used.
4. **The Spec Kit install is two generations behind the official tooling.** Spec Kit now ships `/speckit.converge`, the official "audit code against spec, plan, tasks, and constitution" command, and installs Claude Code commands as skills under `.claude/skills/speckit-*/`. This repo has neither.
5. **Recommended approach:** make compliance executable before re-auditing. Build a wire-level conformance test harness that encodes ADR-001 §4, §8, and Appendix A as pytest contract tests. Then run a three-layer review: contract tests (deterministic), `/speckit.converge` per feature directory (artifact-to-code), and a custom `architecture-reviewer` subagent run headless in CI (judgment). Feed the results into ADR-001 v1.5 and Constitution v1.2.0. Details in §4.

---

## 2. Validation: Did We Adopt the Agentic Biolink Schema?

### 2.1 What ADR-001 §4 actually mandates

| Mandate | Text in ADR-001 v1.4 | Status |
|---|---|---|
| Vocabulary | "Keys must use Biolink Model terms (e.g., `biolink:treats`)" | **Not adopted.** Zero occurrences of `biolink:` in `src/` or `tests/`. No `category` or `predicate` fields on any model. The only `biolink:` usage is in competency-question validation write-ups under `docs/`. |
| Structure | "Flattened JSON (no deep TRAPI nesting)" | **Adopted.** All entity models are flat pydantic models; nesting is limited to `cross_references`, `pagination`, and small sub-objects (`revision`, `component_counts`, `protocol`). |
| Cross-references | "Every entity response MUST include a `cross_references` object adhering to the Key Registry (Appendix A)" | **Partially adopted.** See 2.2. |
| Cognitive Hooks | "enriched with Cognitive Hooks to aid triangulation" | **Undefined.** The term appears in the standard prompt and ADR but is never defined in v1.4. The red-team critique reads it as aliases and location. HGNC, Entrez, and UniProt models carry aliases and locations ad hoc; nothing is normative. |

### 2.2 `cross_references` implementation by server

| Server | Type used for `cross_references` | Registry conformance | Wire evidence |
|---|---|---|---|
| HGNC | shared `CrossReferences` | Keys conform. Nulls serialized for all absent keys. | 15 `null` keys for BRCA1 (local, in-process). |
| UniProt | shared `CrossReferences` | Conforms. Server calls `model_dump(exclude_none=True)` explicitly. | One of two servers that omit nulls correctly. |
| Open Targets | shared `CrossReferences` | Conforms at definition level; wire not verified. | Not tested. |
| IUPHAR | shared `CrossReferences` + own `model_dump` override | Same bypass risk as HGNC. | Not tested. |
| Ensembl | custom `EnsemblCrossReferences` (12 keys) | Subset of registry. Own `model_dump` override, same bypass risk. | Not tested. |
| Entrez | custom `EntrezCrossReferences` (10 keys) | Subset of registry. | Not tested. |
| DrugBank | custom `DrugCrossReferences` (7 keys) | Subset of registry. | Blocked (API key). |
| BioGRID | custom `BioGridCrossReferences` (1 key: `entrez`) | Minimal. | Not tested. |
| STRING | custom `InteractionCrossReferences` (3 keys) | Minimal. | Not tested. |
| ChEMBL | raw `dict[str, list[str]]` | Only self-reference. Value is `["CHEMBL:25"]`: list where registry says String, CURIE-prefixed where regex `^CHEMBL\d+$` forbids a prefix. | `{"chembl": ["CHEMBL:25"]}` (cloud). Top-level `molecular_formula: null`, `canonical_name: null`. |
| PubChem | raw `dict[str, list[str]]` | Only self-reference `{"pubchem_compound": ["2244"]}`. Server docstring promises `chembl` and `drugbank` keys that the output does not contain. | Cloud output confirmed. |
| WikiPathways | raw `dict[str, str \| list[str]]` | `hgnc` key holds gene **symbols** (`"MDH2"`), registry regex requires `^HGNC:\d+$`. `entrez` and `ensembl_gene` are lists where registry says String. Uses `reactome` and `gene_ontology` keys that are not in the registry. | Cloud output confirmed. |
| ClinicalTrials | raw `dict[str, Any]` | `pubmed` is a comma-joined string, registry says `List[String]` with `PMID:` prefix. `clinicaltrials_gov`, `mesh_conditions`, `mesh_interventions` are not registry keys. | Code inspection. |

Two further inconsistencies affect ADR-001 §6 (Triangulation), which assumes an agent can compare `cross_references` values across servers mechanically:

- **Value format varies by server for the same key.** `entrez` is `"672"` from HGNC and `["4191", ...]` from WikiPathways. `chembl` is bare in the registry, `CHEMBL:25` in ChEMBL and PubChem output.
- **Registry drift.** ADR v1.4 Appendix A lists 23 keys. Docstrings, the Constitution, and the standard prompt all say "22-key". Amendment 001 (still "Proposed") adds an `opentargets` key that neither the ADR nor the model has. `CROSS_REF_PATTERNS` covers 8 of 23 keys and is never invoked, so `INVALID_CROSS_REFERENCE` can never be raised.

### 2.3 Verdict

> **Corrected 2026-09-02, see `docs/adr/critique/adr-001-agentic-biolink-decision-record-2026-09-02.md`.** The decision was made and consistently implemented: Biolink alignment is at the category level in entity records (registry keys) and at the predicate level in the edge layer (competency graphs, graph-builder skill), per `prior-art-api-patterns.md` §7.5. The §4 "keys must use Biolink Model terms" sentence is a residue of the v0.1 association-record example and should be deleted, not implemented. The paragraph below is retained as originally written.

The project adopted a **flat, cross-referenced JSON convention**, not a Biolink-aligned schema. That convention is internally inconsistent across servers and the one runtime guarantee it does promise (omit nulls) is broken on the wire for most servers. This is a documentation problem as much as a code problem: the ADR should either define the Biolink commitment precisely enough to test, or drop the Biolink claim and name what was actually built.

### 2.4 Caveat on evidence

Cloud evidence came from `biosciences-mcp.fastmcp.app`, which is a separate deployment from this repo's `lifesciences-research.fastmcp.app`. The HGNC null-serialization finding was reproduced in-process against the checked-out code, so it is not a deployment artifact. ChEMBL, PubChem, and WikiPathways findings were confirmed against the cloud output and the local client code that builds those dicts.

---

## 3. What the Official Documentation Recommends

### 3.1 Claude Code (code.claude.com/docs)

| Need | Recommended mechanism | Notes |
|---|---|---|
| Review code against a spec | Custom subagent in `.claude/agents/<name>.md` with restricted tools (`Read, Grep, Glob`) and `memory: project` so findings persist across runs; `/code-review` for diff-scoped bug hunting | Fresh context avoids inheriting the implementer's assumptions. `/code-review` is diff-oriented, not whole-repo. |
| Make compliance verifiable | "Give Claude a way to verify its work": tests, linters, or scripts the agent must run and show output from | Evidence over assertions. This is the single most important pattern for this repo: today there is no executable ADR-001 check. |
| Repeatable audits in CI | `claude --bare -p "<prompt>" --output-format json --json-schema '<schema>' --allowedTools "Read,Grep,Glob"` | `--bare` skips local config for reproducibility. Structured output lets CI gate on a field rather than string-matching prose. Prompt size is not the constraint; context is. Pipe ADRs via `--append-system-prompt` or by file reference. |
| Enforce deterministic gates | Hooks (`Stop`, `PreToolUse`, `PostToolUse`) that run shell scripts | Use only for deterministic checks such as "contract tests pass" or "ADR references resolve". Not for judgment calls. |
| Keep CLAUDE.md useful | Under ~200 lines. Reference ADRs with `@path` imports rather than restating them. Move path-specific guidance into `.claude/rules/*.md` with `paths:` frontmatter. Run `/doctor` for trim suggestions. | The current CLAUDE.md is ~330 lines and carries a full directory listing, per-server status, and curl transcripts that the code and tests already record. |
| Large migrations | Checklist or scratchpad file the agent updates as it works; subagents as adversarial reviewers | Matches the existing audit-playbook pattern. |

Sources: `best-practices.md`, `sub-agents.md`, `memory.md`, `headless.md`, `hooks-guide.md`, `permission-modes.md` under https://code.claude.com/docs/en/.

### 3.2 GitHub Spec Kit (v1.0.4, 2026-09-02)

| Topic | Official guidance | Relevance here |
|---|---|---|
| Brownfield review | `/speckit.converge` (added 0.11.2): reads spec, plan, tasks, and constitution, compares against the code named in plan and tasks, grades contradictions of constitution MUST principles as CRITICAL, and **appends** a `## Phase N: Convergence` section to tasks.md. Never edits spec or plan. | This is the sanctioned "audit existing implementation against spec" command. It is missing from this repo. |
| `/speckit.analyze` | Read-only, artifact-only: duplication, ambiguity, underspecification, constitution alignment, coverage, inconsistency. Does not read code. | The Constitution's "All PRs MUST pass `/analyze`" gate therefore cannot catch code drift. |
| `/speckit.checklist` | "Unit tests for English": requirement-quality questions, not behavior tests. `/speckit.implement` blocks while any checklist item is unchecked. | Useful for the ADR-001 rewrite (§4, Phase 3), not for code audit. |
| Constitution for existing projects | Derive from README, ADRs, contribution guide, CI. "Do not invent standards merely to fill the template." Start with one bounded feature, not a whole-system retrospective spec. | Supports amending the Constitution to match what is actually enforced rather than promising `/analyze` and runtime checks that do not exist. |
| Spec persistence models | Flow-Forward (feature dirs immutable), Living Spec (spec.md is the contract), Flow-Back (edit anywhere, reconcile, then run analyze). Team must pick one. | Current practice (compliance-analysis files, amendments) is Flow-Back without the reconcile step. |
| Constitution versioning | MAJOR for principle removal or redefinition, MINOR for new principle or materially expanded guidance, PATCH for wording. `/speckit.constitution` no longer rewrites templates; templates read the constitution at runtime. | Constitution is at 1.1.0 and still cites ADR-001 v1.2. |
| ADRs | No official guidance. Constitution "Guidance Documents" section is the sanctioned place to cite them, which this repo already does. | Keep ADRs; do not try to fold them into Spec Kit artifacts. |
| Claude Code layout | Commands now install as `.claude/skills/speckit-<name>/SKILL.md` and are invoked as `/speckit-<name>`. `--ai` flag removed in 0.10.0; use `specify init --here --force --integration claude`. Upgrade preserves `specs/` and the constitution (SHA-256 manifest). | This repo has the pre-0.4.5 `.claude/commands/speckit.*.md` layout and no `.specify/feature.json`. |
| Context cost | Issue #1401 measured ~18.6k tokens of Spec Kit command text loaded per Claude Code session. Skills layout loads progressively. | Another reason to upgrade and remove the legacy commands. |

Sources listed in Appendix B.

---

## 4. Recommended Approach

The ordering principle: **make the architecture testable first, then audit, then rewrite the docs from the audit.** Auditing by reading, as in February, produced reports that were 94% accurate about definitions and wrong about behavior.

### Phase 0: Decide what "Agentic Biolink" means (human decision, one ADR)

> **Superseded 2026-09-02.** The decision record cited above shows this was already decided; Phase 0 reduces to the reconciliation edits in that record's §4 plus the single open question of cross-reference value format (bare vs CURIE). Options A/B/C below are retained for the record; option B's `category` field survives as an optional enhancement.

Three options for ADR-001 v1.5. Recommendation is option B.

| Option | What changes | Cost | Consequence |
|---|---|---|---|
| A. Fully adopt Biolink | Add `category` (e.g. `biolink:Gene`) to every entity, `predicate` to every edge model (STRING, BioGRID, Open Targets associations, pathway components). Keep `cross_references`. | Medium: 13 models, all contracts, all specs. | Interop with Biolink and TRAPI-aware tooling. Honors the name. |
| **B. Minimal Biolink: category only, registry tightened** | Add `category` to entities only. Rewrite Appendix A so every key has one canonical format (bare vs CURIE), one cardinality, one regex, and a validator that runs. Define Cognitive Hooks as a named field set (`synonyms`, `location`, `description`). | Low-medium. | Most of the value with the least churn. Makes §6 Triangulation mechanically possible. |
| C. Drop the Biolink claim | Rename to "Agentic Flat Schema". Keep `cross_references`, tighten the registry as in B. | Lowest. | Honest, but loses the interop story used in the competency-question docs. |

Whichever option is chosen, ADR-001 v1.5 must resolve: the 22 vs 23 key count; the fate of Amendment 001 (`opentargets` key); the single-type rule in §9 versus the five custom `*CrossReferences` classes and four raw dicts; and the serialization contract (servers must emit omit-null JSON, not just models).

### Phase 1: Build the executable conformance harness (before any re-audit)

This is the "verification target" the Claude Code docs call for and the gap that let the February audit pass HGNC.

- **Wire-level contract tests.** One parametrized pytest module that opens each server with `fastmcp.Client(mcp)` in-process, calls every tool with a canonical fixture ID, parses the returned JSON text, and asserts: no `null` values anywhere; `cross_references` keys are a subset of the registry; every value matches its registry regex and cardinality; list tools return the Pagination Envelope; error paths return the Error Envelope with a registered code. Mark them `integration` since they hit upstream APIs, and add a recorded-response variant marked `unit` if flakiness matters.
- **Turn on the regex table.** `CROSS_REF_PATTERNS` becomes a pydantic validator on the shared `CrossReferences` model so `INVALID_CROSS_REFERENCE` can actually be raised. Extend it to all registry keys.
- **Schema snapshot.** Export each tool's output JSON schema (`mcp.get_tools()` or the pydantic `model_json_schema()`) into `specs/NNN-*/contracts/` and diff in CI. Contracts already exist as YAML for several features; this makes them derived rather than hand-written.
- **A deterministic gate.** A `Stop` or pre-commit hook that runs `uv run pytest -m "unit and contract"` is appropriate here because it is deterministic. Do not put judgment checks in hooks.

### Phase 2: Run the review with three complementary layers

| Layer | Tool | Answers | Output |
|---|---|---|---|
| 1. Deterministic | Contract tests from Phase 1 | "Does the wire output obey ADR-001 §4, §8, Appendix A?" | pytest results; the compliance matrix's Principle III column becomes a test run, not a reading. |
| 2. Artifact-to-code | `/speckit.converge` per `specs/NNN-*/` after upgrading Spec Kit | "Does the code still match what spec, plan, and tasks say, and does it violate any constitution MUST?" | Appended `Convergence` phase in each tasks.md. Run `/speckit.analyze` afterward to catch artifact inconsistency introduced by the reconcile. |
| 3. Judgment | Custom `.claude/agents/architecture-reviewer.md` (tools: Read, Grep, Glob; `memory: project`), driven by an updated audit playbook | "Where do the implementation and the ADRs disagree in ways tests cannot express?" (naming, Cognitive Hooks, tier semantics, docstrings that promise fields the output lacks) | Per-server reports in `docs/evaluation/compliance-reports/`, then an aggregator report. |

Method notes for layer 3:

- Extend the February playbook with a **CHECK 7: Wire-level Schema Determinism** that requires the agent to run the Phase 1 tests and quote the output, and a **CHECK 8: Agentic Biolink** that checks vocabulary, cross-reference type, registry key membership, and docstring-to-output consistency.
- Run it headless for repeatability: `claude --bare -p` with `--json-schema` so each report yields a structured `{server, principle, status, evidence[]}` object that the aggregator can merge without parsing prose. Keep the interactive multi-agent fan-out for the first pass if the team prefers watching it.
- Reuse the February validation step (a second agent verifying each report's claims). It caught two critical errors in the UniProt report last time.
- Do not use `/code-review` for this. It is diff-scoped and bug-oriented; the question here is whole-repo conformance.

### Phase 3: Update the architecture documentation from the audit

- **ADR-001 v1.5** per Phase 0, plus a new normative section "Serialization Contract" stating that omit-null applies to tool output and naming the mechanism (explicit `model_dump(exclude_none=True)` in every server tool, or a shared FastMCP serializer).
- **Constitution 1.2.0 (MINOR).** Update the ADR citation from v1.2 to v1.5. Replace the "Enforcement" column promises that do not exist (`/analyze` validation for envelopes; "Runtime validation" for regex) with the Phase 1 test names and `/speckit.converge`. Add Principle III sub-clause for Biolink per the Phase 0 decision. Record the chosen spec persistence model (recommend Flow-Back with mandatory analyze after reconcile, since that is current practice).
- **Standard prompt v2.** Replace the undefined "Cognitive Hooks" with the named field set. Change "22-key" to the corrected count. Add a line requiring the Phase 1 contract test to pass as part of the "Junior Dev" test plan. Keep the Constraint Injection design; it worked for everything it named.
- **CLAUDE.md.** Cut to under 200 lines: remove the directory tree and per-server status table (derivable, and already stale in places), move the ClinicalTrials curl transcript into `docs/tests/` and reference it, replace ADR summaries with `@docs/adr/accepted/adr-001-v1.5.md` imports. Add `.claude/rules/adr-compliance.md` scoped to `src/lifesciences_mcp/**` carrying the short list of MUSTs that apply when editing models or servers.
- **Spec Kit upgrade.** `specify init --here --force --integration claude` after backing up `.specify/memory/constitution.md` and customized templates; then delete `.claude/commands/speckit.*.md` to avoid loading both command sets. Verify the new skills invoke as `/speckit-<name>` and update the SpecKit Workflow section of CLAUDE.md accordingly.
- **Amendment 001.** Either fold into v1.5 or mark Rejected. Leaving it "Proposed" since 2025-12-21 is the kind of drift the review is meant to remove.

### Estimated effort and order

| Step | Depends on | Size |
|---|---|---|
| Phase 0 decision | none | one review meeting or an async decision on this document |
| Spec Kit upgrade | none | small; can run today |
| Phase 1 harness | Phase 0 (which regexes and cardinalities to assert) | one feature branch via the normal `/speckit.specify` flow, since it touches all 13 servers |
| Phase 2 review | Phase 1 | one multi-agent pass, then one validation pass |
| Phase 3 docs | Phase 2 | one docs branch; Constitution and ADR changes go through the ADR amendment process |

---

## 5. Decisions Needed

1. **Phase 0 option A, B, or C** for the Biolink commitment. Recommendation: B.
2. **Canonical cross-reference value format**: bare IDs per the current registry regexes, or CURIEs everywhere. CURIE-everywhere is the more agent-friendly choice and matches what ChEMBL and PubChem already emit, but it changes the registry regexes and the HGNC/UniProt/Ensembl/Entrez outputs.
3. **Spec persistence model**: confirm Flow-Back.
4. **Whether to run the Phase 2 review headless in CI** or as an interactive multi-agent session first.

---

## Appendix A: Evidence Commands

```bash
# Biolink vocabulary never used in code
grep -rn "biolink:" src/ tests/          # no matches

# Six different cross_references shapes
grep -rn "class .*CrossReferences" src/
grep -rn "cross_references: dict" src/lifesciences_mcp/models/

# Regex table defined, never applied
grep -rn "CROSS_REF_PATTERNS" src/       # one definition, zero uses

# Wire-level null check against local code (network required)
uv run python - <<'EOF'
import asyncio, json
from fastmcp import Client
from lifesciences_mcp.servers.hgnc import mcp
async def main():
    async with Client(mcp) as c:
        r = await c.call_tool("get_gene", {"hgnc_id": "HGNC:1100"})
        xr = json.loads(r.content[0].text)["cross_references"]
        print("null keys:", sum(v is None for v in xr.values()))   # 15
asyncio.run(main())
EOF
```

## Appendix B: Sources

Claude Code
- https://code.claude.com/docs/en/best-practices.md
- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/memory.md
- https://code.claude.com/docs/en/headless.md
- https://code.claude.com/docs/en/hooks-guide.md
- https://code.claude.com/docs/en/permission-modes.md

GitHub Spec Kit
- https://github.com/github/spec-kit/blob/main/README.md
- https://github.com/github/spec-kit/blob/main/spec-driven.md
- https://github.com/github/spec-kit/blob/main/docs/guides/existing-projects.md
- https://github.com/github/spec-kit/blob/main/docs/guides/evolving-specs.md
- https://github.com/github/spec-kit/blob/main/docs/concepts/spec-persistence.md
- https://github.com/github/spec-kit/blob/main/docs/reference/agentic-sdd.md
- https://github.com/github/spec-kit/blob/main/docs/upgrade.md
- https://github.com/github/spec-kit/tree/main/templates/commands (analyze, checklist, constitution, converge, implement)
- https://github.com/github/spec-kit/blob/main/src/specify_cli/integrations/claude/__init__.py
- https://github.com/github/spec-kit/issues/1401 (per-session context cost)

Local
- `docs/adr/accepted/adr-001-v1.4.md`, `docs/adr/amendments/adr-001-amendment-001-extended-key-registry.md`
- `docs/adr/critique/adr-001-agentic-experience-critique.md` (Cognitive Hooks interpretation)
- `.specify/memory/constitution.md` (v1.1.0)
- `docs/evaluation/constitution-compliance-audit-playbook.md`, `docs/evaluation/validation-summary.md`
- `src/lifesciences_mcp/models/cross_references.py`

---

## Addendum (2026-09-02): Applicability to `open-biosciences/biosciences-mcp`

`biosciences-mcp` is the migrated successor of this repo's `src/lifesciences_mcp` (Wave 2, commit e2c2737). Every finding in §2 reproduces there:

| Check | lifesciences-research | biosciences-mcp |
|---|---|---|
| `biolink:` terms in src or tests | 0 | 0 |
| Cross-reference shapes (shared / custom classes / raw dicts) | 1 / 5 / 5 | 1 / 5 / 5 (identical files) |
| `CROSS_REF_PATTERNS` applied | never | never |
| Servers that emit omit-null JSON | UniProt, WikiPathways only | UniProt, WikiPathways only |
| HGNC `get_gene("HGNC:1100")` null cross-reference keys on the wire (in-process) | 15 of 23 | 15 of 23 |
| Spec Kit layout | legacy `.claude/commands/speckit.*.md`, no converge | same |
| Constitution | v1.1.0, cites ADR-001 v1.2 | same file |

Source divergence between the two trees, after normalizing the package rename, is ~1,100 lines: the WikiPathways client moved to static JSON bulk files (PR #2), the gateway was reformatted and gained tool-name mapping changes, ChEMBL and HGNC picked up small fixes, and `ErrorCode` became a `StrEnum`. None of that touches the schema questions. `lifesciences-research` additionally has `data/` and `tools/` packages that were not migrated.

**Governance location is inconsistent across the program.** The program-level docs say ADRs, `specs/`, `.specify/`, and the Spec Kit commands live in `biosciences-program`; they were moved to `biosciences-mcp` on 2026-03-03 (`biosciences-program` 83d6c67, `biosciences-mcp` 5278c4e), and `biosciences-program/CLAUDE.md`, `biosciences-architecture/CLAUDE.md`, and `migration-tracker.md` were not updated. `biosciences-program` briefly held a new, unrelated `docs/adr/proposed/adr-001-v1.0.md` (edge invalidation in Graphiti) that collided with the ID of the accepted Agentic-First ADR-001 in `biosciences-mcp`. **Resolved 2026-09-02 (local branches, not yet pushed):** the pr3-biosciences-memory session relocated it to `biosciences-memory/docs/adr/proposed/adr-mem-001-v1.0.md` as ADR-MEM-001 under a project-scoped MEM- series (commit 761fc1f, branch `docs/adr-mem-001-edge-invalidation`), and replaced the program copy with a pointer-only `docs/adr/README.md` (branch `docs/adr-001-edge-invalidation-ontology`, PR #3). ADR-MEM-001 §5 now carries an alignment note stating its type names are not derived from Biolink output. Phase 3 still begins by deciding the canonical home for the platform ADRs and Spec Kit config and correcting the three stale documents.

**A sibling repo already has the target pattern.** `psychology-mcp` runs the current Spec Kit layout (`.claude/skills/speckit-converge` present, `.specify/feature.json`), a constitution at v1.6.0 that carries the same Principles I-VI plus a "Compliance on a partial implementation" clause stating that an enforcement mechanism named in Required Patterns is a deferral until it has actually run. That clause is exactly the fix §4 Phase 3 recommends for the biosciences constitution, and its Spec Kit setup is the upgrade template.

**Where the Phase 1-3 work should land:** `biosciences-mcp`, not this repo. This repo is a migration source and should be treated as frozen once the review lands there.

---

## Addendum 2 (2026-09-02): Implications for new endpoints (PR #24 DepMap, PR #25 standard prompt, AGE-680 roadmap)

PR #24 (`implement/014-depmap-mcp-server`) and PR #25 (DepMap entry in `docs/speckit-standard-prompt-v2.md`) are the first new server built since the February audit, and they are the concrete test of whether the process catches the gaps in §2. Checked against the PR #24 branch in a scratch worktree, in-process through `fastmcp.Client`:

| Check | Result on PR #24 |
|---|---|
| `get_model("SIDM:00903")` wire output | `lineage: null` and `cross_references: null` present. The `_OmitNoneModel.model_dump` override is bypassed by FastMCP exactly as in §1 finding 2. The PR body states the override "fixed" the null Forbidden Pattern; it fixed it for `model_dump()` callers only. |
| `search_models(slim=True)` item keys | `id`, `name`, `data_source`. No `score`, which PR #25's prompt requires "like every other SearchCandidate". Acknowledged in PR #25 as tracked on AGE-681. |
| Cross-reference model | Sixth feature-local `*CrossReferences` class (`ccle`, `cosmic`), following the `DrugCrossReferences` precedent because the registry has no cell-line key and the Constitution requires an ADR amendment to extend it. Correct per the rules as written; it also means the §9 single-protocol-type rule is now violated six ways instead of five. |
| Spec artifacts | Full set present (spec, plan with honest Constitution Check, research, data-model, contracts, tasks, quickstart, checklist). Process worked as documented. |
| Target repo | `donbr/lifesciences-research`, not `open-biosciences/biosciences-mcp`. DepMap does not exist in the canonical successor. |

**What this shows.** The Spec Kit process produced a well-documented server and a prompt whose constraints were measured against the live API. What it could not do is catch the serialization defect, because no artifact in the pipeline runs a tool and inspects the JSON. The same defect now exists in 14 servers. PR #25 also propagates the wrong remedy: it instructs future implementers to "use the `model_dump` override pattern", which is the pattern that does not work on the wire.

**Recommended order before adding further endpoints from AGE-680** (items 2 and 3 there are new tools on BioGRID, ChEMBL, and IUPHAR, so they will inherit whatever the shared models do):

1. Land the Phase 1 wire-level contract harness first, in the repo that will carry new servers. Add a `contract` marker and make PR #24 the first branch that has to pass it. This turns the DepMap null finding into a failing test rather than a review comment.
2. Fix the serialization mechanism once, centrally: a shared base model or a server-side `model_dump(exclude_none=True)` in every tool, then remove the per-model overrides. Update PR #25's null-handling sentence to name the real mechanism.
3. Decide the target repo for new endpoints now. Building DepMap in `lifesciences-research` while `biosciences-mcp` is the migration target means either a second migration or a fork. The program docs already designate `biosciences-mcp` as the MCP Platform Engineer's repo.
4. Add a registry amendment path to the standard prompt for entities outside the 23 keys (cell lines now, compounds-by-target and mechanism-of-action next per AGE-680 item 3), so the next server does not need a seventh local cross-reference class.
5. Then resume the roadmap. Items 2 (slim/aggregation modes on heavy endpoints) and 3 (target-to-compound resolver) touch existing shared models and are the right place to also apply the Phase 0 Biolink decision.

---

## Addendum 3 (2026-09-02): Phase 1 delivered in `biosciences-mcp`

Branch `feature/contract-harness` in `open-biosciences/biosciences-mcp` (worktree `.worktrees/contract-harness`), two commits, not pushed:

| Commit | Content | Result |
|---|---|---|
| `d647776` test(contract) | `tests/contract/`: Appendix A registry as data, server catalogue with canonical CURIEs and raw-string counterexamples, a network-free module that pushes every entity model through FastMCP's two real serialisation paths, and a wire module that calls every server through `fastmcp.Client`. `contract` pytest marker registered. | RED as intended: 76 of 106 unit cases and 9 wire cases failed on null serialisation. |
| `88088e0` fix(models) | `models/base.py` adds `OmitNoneModel` (wrap-mode `model_serializer`); all entity models inherit it; five `model_dump` overrides and the invalid `ConfigDict(exclude_none=True)` removed; envelopes untouched per §8. | GREEN: 106/106 unit, 52 passed / 12 xfailed / 5 skipped wire, full unit suite 510 passed, ruff clean, pyright unchanged (one pre-existing error in `drug.py`). |

**Deviation table.** Twelve wire cases xfail with recorded evidence and fail loudly if they stop reproducing. Ten are cross-reference registry violations that need either a client data fix or the ADR-001 v1.5 decision (Phase 0): UniProt comma-joined OMIM and Orphanet values, Open Targets `CHEMBL:CHEMBL4096` and `DB:DB08363`, Ensembl `HGNC:HGNC:11998`, Entrez putting an ENSP protein ID under `ensembl_gene`, IUPHAR bare-number `chembl`, ChEMBL and PubChem list-valued self-references, WikiPathways gene symbols under `hgnc`, ClinicalTrials non-registry keys. Two are IUPHAR strict tools whose `pattern=` parameter constraint makes FastMCP return a pydantic validation string instead of the §3 ErrorEnvelope.

**Downstream validation, open-biosciences-plugins.** The plugin has no Python consumer of tool output; its only documented read is the biosciences-crispr skill's Phase 1 (`hgnc_search_genes` → `hgnc_get_gene` → `cross_references.entrez`). Replayed against the modified local gateway for DHODH it resolves `HGNC:2867` and `entrez == "1723"`, with no nulls in text or structured content. No other workspace repo indexes `cross_references` from Python. Two caveats: the plugin's `.mcp.json` points at the cloud deployment, so the change reaches it only after a deploy; and top-level optional fields are now also absent when empty (for DHODH: `alias_symbols`, `alias_names`, `prev_symbols`), so any consumer that reads such a field without a default must be checked at deploy time.

**Validation before push (2026-09-02).** Full pre-existing integration suite on the branch: 254 passed, 33 skipped, 6 failed. All six reproduce with identical values on unmodified `main` (three WikiPathways pathway-count assertions now returning 20 and 85 against a >100 threshold, two IUPHAR tests asserting `GPCR` where upstream returns `gpcr`, one concurrency timing test at 5.0–5.3 s against a 5 s limit on `main` too). Serialiser cost measured at 3.8 µs per entity. No regressions attributable to the change. Docs updated in a third commit (`tests/README.md` Act IV, `README.md`, `CLAUDE.md`).

**Merged.** PR #4 in `open-biosciences/biosciences-mcp` merged 2026-09-02; `main` now carries the contract tier, `OmitNoneModel`, and the docs. Remaining from Addendum 2: deploy so `open-biosciences-plugins` sees the change; PR #24 (DepMap) to adopt `OmitNoneModel` and drop its `_OmitNoneModel` override; PR #25's null-handling sentence to be corrected; the six pre-existing integration failures (WikiPathways counts, IUPHAR casing, timing threshold) to be fixed separately.
