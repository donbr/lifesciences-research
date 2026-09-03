# Linear and Governance Inventory: biosciences-mcp and psychology-mcp

**Date:** 2026-09-02
**Question answered:** Do Linear issues exist for the work done and identified in the architecture review, and where do the two MCP repos diverge in Spec Kit approach and governance?
**Reviewed:** 2026-09-03 by the pr3-biosciences-memory session for program context; three corrections applied (citation for the ADR-authoring quote, a second ADR-007 draft, ADR-MEM-001 merge status).
**Method:** Linear searches for `biosciences-mcp`, `psychology-mcp`, `SpecKit`, `ADR-001`; issue reads for AGE-548, 552, 581, 592, 680, 681, 682; file inspection of both repos' `.specify/`, constitutions, `docs/adr/`, and `CLAUDE.md`.

---

## 1. Short answer

No. Of the ten pieces of work this review produced or surfaced, only three have Linear coverage, and one of those (AGE-681) carries a description that no longer matches what was done. The merged PR #4 in `biosciences-mcp` has no issue at all.

The two repos are on different Spec Kit generations and different governance models. psychology-mcp moved in mid-August 2026 to upstream Spec Kit v0.16.4 in the skills layout, a constitution at v1.6.0 with two new principles and a "Recorded Deviations" mechanism, and Linear sub-issues as the roadmap in place of the Spec Kit CLI rituals. biosciences-mcp is still on the January 2026 dotted-command layout with the constitution at v1.1.0. psychology-mcp also cites a platform "ADR-007" that does not exist as a file anywhere in the workspace.

---

## 2. Coverage matrix for this review's work

| Work item | Where it lives | Linear issue | Gap |
|---|---|---|---|
| Wire-level contract harness + `OmitNoneModel` fix | `biosciences-mcp` PR #4, merged | **none** | No issue; PR references nothing |
| Twelve recorded registry deviations (seven servers emit malformed cross-reference values) | `tests/contract/test_wire_contracts.py` deviation table | **none** | Need per-server or one umbrella issue |
| ADR-001 v1.5 decision (Biolink option A/B/C, registry format, serialization contract) | review doc §4 Phase 0 | **none** | AGE-66 / AGE-67 (Dec 2025) are the last ADR-001 issues; AGE-135 (22-key doc) was **Canceled** |
| Six pre-existing integration failures (WikiPathways counts, IUPHAR casing, timing threshold) | `biosciences-mcp` main | **none** | Should be filed so they stop being rediscovered |
| Spec Kit upgrade for biosciences-mcp (skills layout, `converge`, `feature.json`) | review doc §4 Phase 3 | **none** | psychology-mcp did it under AGE-552 sub-issues; nothing for biosciences-mcp |
| Constitution 1.2.0 for biosciences-mcp (enforcement columns, Recorded Deviations, partial-implementation clause, serialization rule) | review doc §4 Phase 3 | **none** | psychology-mcp's AGE-581 is the precedent |
| Governance pointers stale (program and architecture CLAUDE.md, migration tracker say ADRs live in `biosciences-program`) | Addendum 1 | AGE-153, AGE-183, AGE-184 all **Done** and also stale (say `biosciences-architecture`) | Linear history contradicts the filesystem twice over |
| ADR-MEM-001 relocation | `biosciences-memory` PR #2 (merge `3fc1161`), `biosciences-program` PR #3 (merge `f256196`), both merged 2026-09-03 | **AGE-682** (Todo) with AGE-683, AGE-684, AGE-685, all under the `graphiti-fastmcp` project | Covered; created 2026-09-03 by the pr3 session |
| DepMap server and prompt | `lifesciences-research` PR #24, #25 | **AGE-681** (In Progress), parent AGE-680 | Covered, but description prompt and kickoff status superseded; correction posted as a comment 2026-09-02 |
| Target repo for new endpoints | Addendum 2 | **none** | Decision needed before AGE-680 items 2 and 3 |

Adjacent issues that touch the same ground and should be linked rather than duplicated:

- **AGE-673** (Todo): `.env` never loaded at runtime in biosciences-temporal, biosciences-mcp, psychology-mcp. Same territory as the `.env`-in-worktree confusion during PR #4 validation.
- **AGE-226** (In Progress): biosciences-mcp-edge and plugin skill updates. Downstream consumer of the omit-null change.
- **AGE-213** (Backlog): wire gateway connectors and update CONNECTORS.md. Where the deploy-then-revalidate step for open-biosciences-plugins belongs.
- **AGE-548** (Backlog, Urgent): plugin scope boundary decision. Blocks several plugin issues and is the governing decision for what a consumer may depend on in tool output.
- **AGE-118** (Done, Jan 2026): "Run speckit.analyze on all 11 servers". The artifact-only audit the review found insufficient; a `converge` run would be its successor.

---

## 3. Spec Kit and governance divergence between the repos

| Dimension | biosciences-mcp | psychology-mcp |
|---|---|---|
| Spec Kit install | January 2026 vintage; `.claude/commands/speckit.*.md`, dotted invocation, no `feature.json`, no `converge` | Upstream v0.16.4 pinned; `.claude/skills/speckit-*/SKILL.md`, hyphen invocation, `.specify/feature.json`, `workflows/`, `integrations/`, `converge` present |
| Constitution | v1.1.0, ratified 2025-12-21, cites ADR-001 v1.2 | v1.6.0, ratified 2026-08-15; adds VII Classification Honesty, VIII Headerless Gateway Rate Resilience, Recorded Deviations, "Compliance on a partial implementation" |
| Process | Constitution says all PRs pass `/analyze`; not run since AGE-118 | Linear sub-issues are the roadmap; Implementer / PM-Auditor split; Auditor sets acceptance criteria before implementation; recorded as a deviation (AGE-581) |
| Enforcement honesty | Required Patterns table names `/analyze` validation and runtime regex validation that never run | Constitution states an enforcement mechanism is a deferral until it has actually run; each check reports checked / deferred / uncheckable |
| ADRs | Holds the accepted platform set 001 to 006 | Inherits by reference to `biosciences-mcp/docs/adr/accepted/`, records five literature adaptations locally; cites platform **ADR-007** |
| Wire-level tests | Yes, as of PR #4 (`tests/contract/`) | No; integration tests call clients, not `fastmcp.Client` |
| Serialization | `OmitNoneModel` as of PR #4 | Not checked; likely the same bypass, since it shares the model pattern |

### The phantom ADR-007

psychology-mcp's constitution v1.6.0 says Principle VIII "implements platform ADR-007 (Gateway Rate Resilience, Full-Jitter Backoff...)" and its ADR index lists 007 as a platform ADR. No file named `adr-007` exists in `biosciences-mcp`, `biosciences-program`, `biosciences-architecture`, or `psychology-mcp`. The only ADR-007 in the workspace is a **draft** in `lifesciences-research/docs/adr/draft/` on a different subject (stateless tool provider boundary); a second unrelated draft, `graphiti-org/lifesciences-mcp/docs/adr/draft/adr-007-agentic-stack.md`, also holds the number. AGE-592, which produced Principle VIII, says "Update constitution.md, ADR-001, and connector specs" and is marked Done; the ADR-001 update did not happen either. The platform-level decision exists only as a psychology-mcp constitution principle and a dangling reference.

### What psychology-mcp got right that biosciences-mcp should adopt

1. The Spec Kit layout and version, including `converge`.
2. The "Compliance on a partial implementation" clause: a named enforcement mechanism counts as deferred until it runs. This is exactly the biosciences-mcp Required Patterns problem.
3. Recorded Deviations as a first-class constitution section, so a process change is visible rather than silent.
4. Inheriting platform ADRs by reference instead of copying.

### What biosciences-mcp now has that psychology-mcp lacks

The wire-level contract tier. psychology-mcp's ADR index says the envelopes are "adopted verbatim" and `cross_references` follows a nine-key registry, but nothing tests the JSON that leaves the server. The same serialization bypass is likely present.

---

## 4. Recommended sequencing

Do the inventory-driven housekeeping first, then the decisions, then the code. Creating issues is a maintainer action; the list below is the proposal.

**A. Record what already happened (no decisions needed)** — *filed 2026-09-02: AGE-686 through AGE-695; comments added on AGE-153, 183, 184, 592*

1. **AGE-686** (Done). File a retroactive issue for PR #4 (contract harness + `OmitNoneModel`) so the merge has a home; link AGE-673 and AGE-226.
2. **AGE-687** (umbrella; children AGE-691 to AGE-695). File one umbrella issue for the twelve registry deviations, with a checklist row per server pointing at the deviation table; child issues only for the ones that are pure client bugs (Open Targets double prefixes, Ensembl double prefix, Entrez protein ID under `ensembl_gene`, IUPHAR bare-number `chembl`, IUPHAR `pattern=` short-circuit).
3. **AGE-688**. File the six pre-existing integration failures as one issue with the evidence from the PR #4 validation.
4. **AGE-689**. Reopen or annotate AGE-153 / AGE-183 / AGE-184 to state the actual ADR and Spec Kit home, and file the governance-pointer fix for `biosciences-program/CLAUDE.md`, `biosciences-architecture/CLAUDE.md`, and `migration-tracker.md`.
5. **AGE-690**. File the ADR-007 gap: either write the platform ADR that AGE-592 claimed, or amend psychology-mcp's constitution to stop citing it. (Peer check 2026-09-03: a second unrelated draft also holds the number, `graphiti-org/lifesciences-mcp/docs/adr/draft/adr-007-agentic-stack.md`; a `/home/donbr` search found "Gateway Rate Resilience" only in psychology-mcp.)

**B. Decide (each needs the maintainer)**

6. ADR-001 v1.5: Biolink option, canonical cross-reference value format, serialization contract. One issue, labeled `adr-pending` like AGE-548.
7. Target repo for new endpoints (biosciences-mcp vs lifesciences-research), and therefore what happens to PR #24 and #25.
8. Whether biosciences-mcp adopts psychology-mcp's process model (Linear sub-issues as roadmap, Auditor-set acceptance criteria) or stays on Spec Kit commands. Either is fine; the constitution must say which.

**C. Then code**

9. Spec Kit upgrade for biosciences-mcp, mirroring psychology-mcp's install, and a first `converge` pass per `specs/NNN-*/` directory.
10. Constitution 1.2.0 for biosciences-mcp carrying the serialization rule, honest enforcement columns, and whichever process model was chosen.
11. A contract tier for psychology-mcp, ported from biosciences-mcp, and the `OmitNoneModel` check there.
12. Only then resume AGE-680 items 2 and 3.

---

## Appendix: issues consulted

| Issue | Status | Relevance |
|---|---|---|
| AGE-680 | Backlog | Plugin roadmap; parent of DepMap |
| AGE-681 | In Progress | DepMap; description superseded, correction comment posted |
| AGE-682, 683, 684 | Todo | ADR-MEM-001 and its levers |
| AGE-673 | Todo | `.env` not loaded at runtime across three repos |
| AGE-666 | In Progress | Env-var discrepancies parent |
| AGE-226 | In Progress | biosciences-mcp-edge + plugin skills |
| AGE-213 | Backlog | Gateway connectors + CONNECTORS.md |
| AGE-548 | Backlog, Urgent | Plugin scope boundary decision |
| AGE-552 | Done | psychology-mcp connector surface; parent of the Tier-0 sub-issues that replaced Spec Kit rituals |
| AGE-581 | In Progress | Records the tracking deviation in psychology-mcp's constitution |
| AGE-592 | Done | Principle VIII; claims an ADR-001 update and "platform ADR-007" that do not exist |
| AGE-118 | Done | Jan 2026 `speckit.analyze` run across servers |
| AGE-153, 183, 184 | Done | Say ADRs and `.specify` moved to biosciences-architecture; they are in biosciences-mcp |
| AGE-135 | Canceled | 22-key registry documentation |
| AGE-66, 67 | Done | ADR-001 v1.1 acceptance and the extended registry amendment (Dec 2025) |
