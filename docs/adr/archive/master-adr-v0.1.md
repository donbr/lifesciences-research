Here is the updated **Master Architectural Decision Record (ADR-001)**.

It now explicitly incorporates the **"Cognitive Hooks"** (redundant metadata) and **"Batch Resolution"** patterns from the Agentic Data Strategy, while maintaining the robust **Hybrid Client** architecture from the Technical Standard.

---

# ADR-001: The "Agentic-First" Architecture for Life Sciences Integration

**Status:** Draft
**Date:** 2025-12-21
**Context:** The `@lifesciences-research` project aims to create a Model Context Protocol (MCP) server that enables LLM agents to reason across heterogeneous biological datasets (Open Targets, ChEMBL, DrugBank, HGNC, UniProt).
**Sources:** Synthesized from "Technical Standards & Implementation Guide" (Hardware/OS) and "Agentic Data Strategy" (Cognitive/UX).

## 1. Context and Problem Statement

Traditional bioinformatics middleware relies on synchronous, deterministic scripts that fail when confronted with the high concurrency and ambiguity of autonomous agent interactions. Current clients are often blocking (incompatible with FastMCP), and raw API outputs are either too sparse (IDs only) or too verbose (deeply nested JSON) for LLM context windows.

We must define a unified architecture that balances **high-throughput performance** with **cognitive reasoning capabilities**.

## 2. Decision: The Hybrid Client Architecture

To resolve the tension between modern performance requirements and the value of legacy domain logic, we adopt a **Hybrid Client Strategy**.

* **Strict Async (Greenfield):** For modern APIs (Open Targets, HGNC, UniProt), we **reject** official synchronous SDKs. We will implement lightweight, custom `httpx` clients that support connection pooling and native `asyncio`.
* **Executor Pattern (Brownfield):** For the ChEMBL API, we **retain** the official `chembl_webresource_client` to leverage its complex Django-style query logic. However, it must be strictly encapsulated within a `run_in_executor` thread pool to prevent blocking the main event loop.
* *Constraint:* All legacy client wrappers must force "Eager Evaluation" (converting lazy iterators to lists) *inside* the thread to prevent blocking during serialization.



## 3. Decision: The "Fuzzy-to-Fact" Resolution Protocol

To prevent "hallucinated mappings" where agents guess identifiers, we enforce a strict, bi-modal workflow for all entity interactions.

* **Phase 1: Fuzzy Discovery (The "Search" Tools):**
* **Input:** Natural language (e.g., "Tylenol", "Breast Cancer").
* **Mechanism:** Uses broad string matching, synonym tables, and Open Targets' Word2Vec similarity.
* **Pattern:** **Batch Resolution** is mandated. Tools must accept lists of queries (e.g., `resolve_genes(["BRCA1", "TP53"])`) to prevent HTTP request avalanches during complex reasoning tasks.


* **Phase 2: Strict Execution (The "Get" Tools):**
* **Input:** **MUST** be a resolved CURIE (e.g., `CHEMBL:CHEMBL112`, `HGNC:1101`).
* **Mechanism:** Direct ID lookup with zero ambiguity.
* **Constraint:** No downstream tool (e.g., `get_mechanism`) is permitted to accept a raw string. It must throw an error instructing the agent to "Resolve the entity first".



## 4. Decision: The "Agentic Biolink" Schema

We resolve the tension between **Interoperability** (Biolink/TRAPI) and **Context Efficiency** (Semantic Density) by adopting the **"Agentic Biolink"** schema.

* **Vocabulary:** We strictly use **Biolink Model** terms for keys and values (e.g., `biolink:treats`, `biolink:Gene`) to ensure the agent understands the semantics.
* **Structure:** We **reject** the verbose, deeply nested TRAPI structure in favor of a flattened, sparse JSON format.
* **Mandate - Cognitive Hooks:** Every tool response must include **Redundant Metadata** to aid triangulation. This includes Aliases (`synonyms`), Previous Symbols, and Verification Anchors (`chromosomal_location`, `molecular_weight`).

**Example: Agentic Biolink JSON**

```json
// APPROVED
{
  "subject_id": "HGNC:1101",
  "subject_name": "BRCA1",
  "subject_aliases": ["RNF53", "PPP1R53"],  // Cognitive Hook: Enables LLM to match synonyms
  "subject_location": "17q21.31",           // Verification Anchor: "Ground Truth" for triangulation
  "relation": "biolink:associated_with",    // Biolink Vocabulary
  "object_id": "MONDO:0000001",
  "object_name": "Breast Cancer",
  "evidence_score": 0.85                    // Flattened from nested attributes
}

```

## 5. Decision: The Tool/Resource Bifurcation

To protect the LLM's context window, we enforce a strict separation based on data utility.

* **Tools (Reasoning):** Return JSON. Used for metadata, summaries, and decision-making. Capped at <50 items per page (Cursor-based pagination required).
* **Resources (Reading):** Return raw text/binary. Used for high-volume data needed for specific analytical tasks.
* **URI Standard:** Resources must use custom schemes to abstract the source:
* `uniprot://sequence/{accession}`
* `pdb://structure/{id}`
* `drugbank://xml/{id}`



## 6. Decision: Triangulation and Verification

We mandate that high-stakes assertions (e.g., "Drug X targets Gene Y") must be verified via **Triangulation** whenever possible.

* **Protocol:** The agent must check **Verification Anchors** across sources.
* *Example:* If ChEMBL links a drug to a protein, the agent verifies if the ChEMBL Target ID appears in the UniProt entry's `cross_references` list.


* **Reporting:** The agent must report "High Confidence" (multi-source agreement) or "Nuanced" (sources disagree on mechanism) in its final answer.

## 7. Consequences

**Positive:**

* **Resilience:** The "Resolve-First" protocol eliminates the most common cause of agent failure (ID mismatch).
* **Cognitive Efficiency:** "Cognitive Hooks" allow the LLM to verify identity without extra API calls, reducing latency.
* **Performance:** The hybrid async architecture ensures high throughput, while Batch Resolution prevents network bottlenecks.

**Negative:**

* **Maintenance:** Maintaining the "Agentic Biolink" transformers requires custom mapping logic for every new API endpoint.
* **Complexity:** The "Fuzzy-to-Fact" loop adds a required step to every user interaction, increasing the "time-to-first-token" for simple queries.