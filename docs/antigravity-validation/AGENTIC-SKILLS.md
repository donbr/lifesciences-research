# Antigravity Agentic Skills (The "Cognitive Ontology")

## Purpose
Unlike static scripts (classic `.claude/skills`), this document defines **Cognitive Patterns**—dynamic problem-solving schemas that I (the Agent) apply adaptively.

As you noted, the `antigravity-competency-questions-catalog.md` acts as my **SHACL (Shapes Constraint Language)**—it defines the *shape* of a valid answer. This document defines the *skills* required to construct those shapes.

---

## 1. Meta-Skill: The "Fuzzy-to-Fact" Cognitive Loop

**Trigger**: Any request involving biomedical entity resolution.
**Schema**: `Ambiguous Input -> Candidate Set -> Canonical Reality`

| Step | Pattern | Instruction |
|------|---------|-------------|
| **1. Anchor** | `Strict Resolution` | Use `*_search_*` tools to map text strings ("Retatrutide") to CURIEs (`CHEMBL:4594260`). **Reject** results with low confidence scores (<0.8) without user confirmation. |
| **2. Heal** | `Self-Healing` | **IF** an ID is "Obsolete" (e.g., `MONDO:0014109`), **THEN** immediately trigger a search for its replacement (`MONDO:0800044`). Do not ask; just fix. |
| **3. Verify** | `Triangulation` | **IF** a structured fact (e.g., Mechanism) is missing, **THEN** verify its existence via a second modality (Web Search). |

---

## 2. The "Validation" Skills (My Internal SHACL)

These are the patterns I verify against during **Verification Mode**.

### Skill: `validate_synthetic_lethality`
*   **Shape constraint**: A valid Synthetic Lethality graph MUST contain:
    *   `Node A` (Gene, Deficient)
    *   `Node B` (Gene, Target)
    *   `Edge`: "Synthetic Lethality" (Provenance: Literature/Web)
    *   `Node C` (Drug, Inhibitor of B)
*   **Anti-Pattern**: Using a drug that inhibits Node A (the lost gene). *I must catch this logic error.*

### Skill: `validate_drug_repurposing`
*   **Shape constraint**:
    *   `Node A` (Disease)
    *   `Node B` (Gene, Causal/Risk)
    *   `Node C` (Drug)
    *   `Edge`: Drug -> Inhibits -> Gene (if Gain-of-Function) OR Drug -> Activates -> Gene (if Loss-of-Function).
*   **Constraint**: The Drug MUST NOT be already indicated for the Disease (unless finding "Standard of Care").

---

## 3. The "Silent Data Gap" Heuristic (Pattern A)

**Principle**: **MCP First.** You MUST attempt to retrieve data via the structured MCP tools (`chembl_get_mechanism`) before considering any other source.

**Cognitive Rule**:
> "Absence of evidence in structured APIs is NOT evidence of absence in reality."

**Logic (Strict Fallback)**:
```python
def retrieve_mechanism(drug_id):
    # 1. ALWAYS try the Structured MCP first
    facts = chembl.get_mechanism(drug_id)
    
    # 2. ONLY if MCP returns empty AND we expect data (High Phase)
    if not facts and drug.max_phase >= 2:
        # GAP DETECTED: Structured DBs lag behind clinical reality.
        # ACTION: Fallback to Web Search (Triangulation).
        facts = search_web(f"{drug.name} mechanism of action")
        
    return facts
```
**Constraint**: Never default to Web Search for mechanism retrieval. It is slow, unstructured, and lacks provenance compared to ChEMBL.
---

## 4. The "Hybrid Tooling" Heuristic (SDK vs. API)

**Trigger**: When to use `mcp_` tools vs. `curl`?

**Insight**:
- **MCP Tools (`mcp_lifesciences_*`)**: Built on **SDKs** (e.g., `chembl_webresource_client`). Great for **Entity Resolution** (Nodes) because they handle pagination, normalization, and stable IDs.
- **Raw Skills (`curl`, `python`)**: Built on **Raw APIs** (REST/GraphQL). Essential for **Edge Discovery** (Traversing) because SDKs often hide the complex relationships or new endpoints needed for deep linking.

| Modality | Tool Type | Use Case | Example |
|----------|-----------|----------|---------|
| **Nodes** | MCP (SDK) | Finding the "Thing" | `chembl_search_compounds` (Stable, Normalized) |
| **Edges** | Raw API | Finding the "Link" | `curl /mechanism` (Flexible, Detailed) |

**Rule**: Use MCP to *find* the node, use Raw Skills to *interrogate* it.

---

## 5. The "Agentic Memory" Architecture

This replaces static `memory.md`. My memory is active:

1.  **Catalog**: The "Test Suite" (What I must be able to answer).
2.  **Patterns**: The "Strategies" (How I answer them).
3.  **Validation**: The "Proof" (That the strategies work).

---

## 6. Evolution
I update this document when I encounter a new failure mode (e.g., a new "Trap" like Janex-1). This is my **Gradient Descent**—learning from every error to refine my weights (instructions).
