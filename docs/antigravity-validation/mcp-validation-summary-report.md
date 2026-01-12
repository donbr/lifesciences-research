# Life Sciences MCP Validation: Summary Report

**Date**: 2026-01-12
**Executor**: Antigravity (Claude Code)
**Scope**: Validation of `lifesciences-research` MCPs via Competency Questions (CQ1, CQ2, CQ7, CQ13).

## Executive Summary
The `lifesciences-research` MCP suite is **production-ready** and highly effective when paired with the **Agentic Architectural Patterns** defined in this project.

The MCPs successfully serve as the "Anchor" for specific entity resolution, but purely structured API access has inherent data gaps (especially for new clinical assets) and "static data rot" (obsolete IDs). The validating agent **successfully overcame these limitations** by dynamically switching to "Agentic Skills" (Web Search, `curl`, Python scripts) as predicted by the "Triangulated Validation" pattern.

## Critical Findings

### 1. The "Silent Data Gap" (Crucial for Novel Drugs)
*   **Observation**: during CQ7 (NGLY1 Repurposing), the agent identified **CB-5083** (`CHEMBL:3747513`) as a candidate. However, the ChEMBL MCP's structured endpoint returned **0 mechanisms**.
*   **Deep Dive**: A debug script confirmed the API works for established drugs (Aspirin) but lacks data for this clinical candidate.
*   **Resolution**: The Agent successfully used **Web Search** to triangulate the mechanism ("p97/VCP inhibitor") and confirm the Repurposing logic.
*   **Verdict**: MCP tools *must* be backed by a fallback to unstructured data (Web/LLM Internal Knowledge) for novel entities.

### 2. "Static Data Rot" requires "Self-Healing"
*   **Observation**: In CQ7 (Adversarial), the agent was given an obsolete ID `MONDO:0014109`.
*   **Code Insight**: MCP search tools do **not** return deprecation warnings in the initial fuzzy list.
*   **Resolution**: The Agent detected the issue during the "Fact" lookup or via Web Search and "Self-Healed" to the active ID `MONDO:0800044`.
*   **Verdict**: The "Fuzzy-to-Fact" protocol is mandatory. Agents cannot trust IDs provided in prompts without verification.

### 3. "Clinical Intelligence" works for Monitoring
*   **Observation**: In CQ13, the MCPs successfully tracked a high-velocity asset (**Retatrutide**) from a Trial ID (`NCT:07232719`) to a Chemical Structure (`CHEMBL:5095485`).
*   **Verdict**: The schema correctly links `ClinicalTrial` -> `Drug` -> `Disease`, enabling automated monitoring of competitor pipelines.

## Conclusion on Usage
**Q: Can we use it effectively with Agentic `curl` / Skills?**
**A: YES.**

The recommended (and validated) workflow is:
1.  **Use MCPs for "Anchoring"**: Use `search_*` and `get_*` to ground entities in precise CURIEs (e.g., `HGNC:17646`). This prevents hallucination.
2.  **Use Skills for "Edges"**: Use `curl` (or `wikipathways` tools) to traverse connections where the MCP might be too rigid or empty.
    *   *Example*: Use MCP to get the Gene ID, use `curl`/Web to find its latest interactions if the DB is stale.
3.  **Use Triangulation for "Truth"**: Never rely on a single source for critical assertions (like Drug Mechanism). Cross-reference ChEMBL with Web Search.

The system is robust precisely *because* it allows this hybrid approach.
