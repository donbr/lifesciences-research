Here is the **Final v1.0 Master Architectural Decision Record (ADR)** for the `@lifesciences-research` project.

This document serves as the binding technical contract for the project. It synthesizes the high-performance "Hardware" specifications (Async/FastMCP) with the "Cognitive" user experience requirements, incorporating the critical fixes for schema fidelity and batch processing identified during the review process.

---

# ADR-001: The "Agentic-First" Architecture for Life Sciences Integration

**Status:** Accepted
**Date:** 2025-12-21
**Context:** The `@lifesciences-research` project aims to create a Model Context Protocol (MCP) server that enables LLM agents to reason across heterogeneous biological datasets (Open Targets, ChEMBL, DrugBank, HGNC, UniProt).
**Sources:** Synthesized from "Technical Standards & Implementation Guide," "Agentic Data Strategy," and the "Agentic Experience Critique."

## 1. Context and Problem Statement

Traditional bioinformatics middleware relies on synchronous, deterministic scripts that fail when confronted with the high concurrency and ambiguity of autonomous agent interactions. Current clients are often blocking (incompatible with FastMCP), and raw API outputs are either too sparse (IDs only) or too verbose (deeply nested JSON) for LLM context windows.

We must define a unified architecture that balances **high-throughput performance** with **cognitive reasoning capabilities**, ensuring the agent can verify its own hallucinations without incurring massive latency penalties.

## 2. Decision: The Hybrid Client Architecture

To resolve the tension between modern performance requirements and the value of legacy domain logic, we adopt a **Hybrid Client Strategy**.

* **Strict Async (Greenfield):** For modern APIs (Open Targets, HGNC, UniProt), we **reject** official synchronous SDKs. We will implement lightweight, custom `httpx` clients that support connection pooling and native `asyncio`.
* **Executor Pattern (Brownfield):** For the ChEMBL API, we **retain** the official `chembl_webresource_client` to leverage its complex Django-style query logic. However, it must be strictly encapsulated within a `run_in_executor` thread pool.
* **Constraint 1 (Eager Evaluation):** Wrappers must force list materialization *inside* the thread to prevent blocking during serialization.
* **Constraint 2 (Mandatory Batching):** To prevent thread pool exhaustion during multi-hop reasoning (the "N+1 Problem"), legacy wrappers **MUST** expose batch tools (e.g., `chembl_get_drugs_batch(target_ids: List[str])`). Single-item lookups inside a loop are prohibited.



## 3. Decision: The "Fuzzy-to-Fact" Resolution Protocol

To prevent "hallucinated mappings" where agents guess identifiers, we enforce a strict, bi-modal workflow for all entity interactions.

* **Phase 1: Fuzzy Discovery (The "Search" Tools):**
* **Input:** Natural language (e.g., "Tylenol", "Breast Cancer").
* **Mechanism:** Uses broad string matching, synonym tables, and Open Targets' Word2Vec similarity.
* **Semantic Expansion:** If a query cannot be resolved to a single entity (e.g., "HER2 Pathway"), the tool must not fail. It must returns a **List of Candidates** or a **Functional Group** (e.g., the members of the signaling complex) to allow the agent to refine its intent.


* **Phase 2: Strict Execution (The "Get" Tools):**
* **Input:** **MUST** be a resolved CURIE (e.g., `CHEMBL:CHEMBL112`, `HGNC:1101`).
* **Mechanism:** Direct ID lookup with zero ambiguity.
* **Constraint:** No downstream tool (e.g., `get_mechanism`) is permitted to accept a raw string. It must throw an error instructing the agent to "Resolve the entity first".



## 4. Decision: The "Agentic Biolink" Schema

We resolve the tension between **Interoperability** (Biolink/TRAPI) and **Context Efficiency** (Semantic Density) by adopting the **"Agentic Biolink"** schema.

* **Vocabulary:** We strictly use **Biolink Model** terms for keys (e.g., `biolink:treats`, `biolink:Gene`) to ensure semantic clarity.
* **Structure:** We **reject** the verbose TRAPI structure in favor of a flattened, sparse JSON format.
* **Mandate - Cognitive Hooks:** Every tool response must include **Redundant Metadata** to aid triangulation. This includes Aliases, Previous Symbols, and Verification Anchors.
* **Mandate - Cross-References:** To enable the Triangulation Protocol (Section 6), the schema **MUST** include a `cross_references` object containing mapped IDs for Tier 0/1 sources.

**Example: Agentic Biolink JSON**

```json
// APPROVED SCHEMA
{
  "subject_id": "HGNC:1101",
  "subject_name": "BRCA1",
  "subject_aliases": ["RNF53", "PPP1R53", "IRIS"], // Cognitive Hook: Synonyms
  "previous_symbols": ["RNF53"],                    // Cognitive Hook: Literature compatibility
  "subject_location": "17q21.31",                   // Verification Anchor
  "gene_groups": ["BRCA1-A complex"],               // Semantic Context
  "cross_references": {                             // CRITICAL: Enables Triangulation
    "ensembl": "ENSG00000012048",
    "uniprot": "P38398",
    "chembl": "CHEMBL3712877"
  },
  "relation": "biolink:associated_with",
  "object_id": "MONDO:0000001",
  "evidence_score": 0.85
}

```

## 5. Decision: The Tool/Resource Bifurcation

To protect the LLM's context window, we enforce a strict separation based on data utility.

* **Tools (Reasoning):** Return JSON. Used for decision-making. Capped at <50 items per page (Cursor-based pagination required).
* **Resources (Reading):** Return raw text/binary. Used for high-volume data needed for specific analytical tasks (e.g., sequence analysis, docking).
* **URI Standard:** Resources must use custom schemes to abstract the source:
* `uniprot://sequence/{accession}`
* `pdb://structure/{id}`
* `drugbank://xml/{id}`



## 6. Decision: Triangulation and Verification

We mandate that high-stakes assertions (e.g., "Drug X targets Gene Y") must be verified via **Triangulation** whenever possible.

* **Protocol:** The agent must check **Verification Anchors** across sources using the `cross_references` object.
* *Example:* If ChEMBL links a drug to a protein, the agent verifies if the ChEMBL Target ID appears in the UniProt entry's `cross_references` list.


* **Reporting:** The agent must report "High Confidence" (multi-source agreement) or "Nuanced" (sources disagree on mechanism) in its final answer.

## 7. Consequences

**Positive:**

* **Resilience:** The "Resolve-First" protocol eliminates ID mismatch failures.
* **Zero-Latency Verification:** The inclusion of `cross_references` allows the agent to verify facts without making secondary API calls.
* **Scalability:** Mandated batching for ChEMBL prevents thread pool exhaustion during complex reasoning chains.

**Negative:**

* **Maintenance:** Maintaining the "Agentic Biolink" transformers requires custom mapping logic for every new API endpoint.
* **Complexity:** The "Fuzzy-to-Fact" loop adds a required step to every user interaction, increasing the "time-to-first-token" for simple queries.