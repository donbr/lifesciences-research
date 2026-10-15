# **Agentic Data Strategy: Technical Implementation for @lifesciences-mcp**

## **1. Executive Summary: The Agentic Shift in Bioinformatics Data Integration**

The landscape of biomedical data integration is undergoing a fundamental transformation. For decades, the industry has relied on rigid, deterministic pipelines—Extract, Transform, Load (ETL) systems—that require exhaustive, pre-computed mapping tables to bridge the semantic gaps between disparate databases. In this traditional model, a query for "Tylenol" fails unless a hardcoded synonym table explicitly links it to "Acetaminophen" and subsequently to its chemical identifier. The fragility of these systems is well-documented; they are brittle in the face of ambiguity, prone to obsolescence as terminologies evolve, and notoriously difficult to maintain at the scale of modern biological knowledge graphs.

The @lifesciences-mcp project represents a departure from this deterministic legacy. By adopting an **Agentic Integration Strategy**, we move the complexity of data resolution from static code to dynamic, probabilistic reasoning managed by Large Language Models (LLMs). The Model Context Protocol (MCP) server serves not merely as a data fetcher, but as a "cognitive middleware" that empowers the LLM to act as a reasoning engine. In this architecture, the LLM performs Just-In-Time (JIT) resolution, navigating the "fuzzy" reality of user intent—misspellings, colloquialisms, and ambiguous gene symbols—to locate precise, canonical identifiers within our target APIs.

This report defines the technical implementation strategy for this Agentic architecture, focusing on a tiered API ecosystem. We designate **Open Targets** and **ChEMBL** as **Tier 0** sources, forming the primary knowledge graph for target-disease-drug associations. **DrugBank**, **HGNC**, and **UniProt** serve as **Tier 1** sources, providing critical verification, nomenclature normalization, and enrichment layers.

Our analysis, synthesized from a deep review of current API specifications and best practices, dictates a move away from "Strict Lookup" patterns toward a **"Search-Verify-Execute"** workflow. This workflow relies on **Context-Rich Tool Outputs**—semantic scaffolding provided by the API wrappers—to allow the LLM to verify its own assumptions before committing to a data retrieval path. Furthermore, to maintain the responsiveness required for a conversational agent, the implementation must reject blocking, synchronous client libraries in favor of a fully asynchronous Python ecosystem built on httpx and asyncio.

The following sections detail the architectural blueprints, API-specific strategies, and engineering patterns required to realize this vision. We explore how to engineer "semantic density" into JSON responses, how to triangulate facts across databases to prevent hallucination, and how to structure the underlying client ecosystem to handle the massive concurrency of agentic reasoning.

## **2. Strategic Context: The Agentic Integration Paradigm**

### **2.1 Beyond Deterministic ETL**

In the context of the @lifesciences-mcp project, the "Agentic" approach fundamentally redefines the relationship between the user, the query, and the database. Traditional bioinformatics middleware treats a user's query as a precise command to be executed. If the command does not match the database schema exactly, the execution fails. This is the "deterministic trap." For example, a user inquiring about "targets for mucoviscidosis" might receive zero results if the database index only recognizes the term "Cystic Fibrosis," despite the two being synonyms.

The Agentic Integration Strategy treats the user's query as an *intent* to be deciphered. The LLM acts as a planner and translator, converting vague natural language into precise API calls. This shifts the burden of "fuzzy mapping" and "ID resolution" from the database indexers to the LLM's reasoning core. The implications for our technical strategy are profound: our tools must be designed to be explored, not just queried. They must return enough context to allow the LLM to recognize when it has found the correct entity, even if the initial search term was imperfect.

### **2.2 The "Fuzzy-to-Fact" Operational Loop**

The core mechanism of the @lifesciences-mcp agent is the "Fuzzy-to-Fact" loop. This recursive process acknowledges that while biological reality is precise (specific sequences, specific chemical structures), human language is ambiguous. The agent must bridge this gap through a three-stage process:

1. **Broad Discovery (Fuzzy Search):** The agent casts a wide net using search endpoints that support partial matching, synonyms, and relevance ranking. The goal here is recall, not precision. We want to ensure the correct entity is somewhere in the returned list.1  
2. **Contextual Verification (Reasoning):** The agent analyzes the metadata returned with the search results—descriptions, synonyms, organism associations—to filter the list. It uses its internal world model to determine that "MDR1" in the context of cancer likely refers to *ABCB1* (P-glycoprotein) rather than a bacterial gene or a distinct unrelated protein.3  
3. **Precise Execution (Canonical Retrieval):** Once the agent has "locked" onto a canonical identifier (e.g., an Ensembl ID or ChEMBL ID), it transitions to exact-match endpoints to retrieve high-fidelity, structured data.4

This loop replaces the fragile "if-then-else" logic of legacy scripts with a robust, self-correcting cognitive workflow. The success of this strategy hinges on the quality of the "Context-Rich Tool Outputs" we design, which provide the evidence the LLM needs to make these decisions confidently.

## **3. Tier 0 Strategy: The Primary Knowledge Graph**

The Tier 0 APIs—Open Targets and ChEMBL—are the foundation of the @lifesciences-mcp system. They provide the dense connectivity between targets, diseases, and drugs that answers the majority of user queries.

### **3.1 Open Targets Platform: The Central Integration Hub**

Open Targets (OT) serves as the "semantic glue" for the project. By pre-integrating data from GWAS, somatic mutations, animal models, and drug databases, it offers a harmonized view of the target-disease landscape.1 For an Agentic system, the Open Targets GraphQL API is uniquely valuable because it allows for the precise shaping of data payloads, minimizing token usage while maximizing information density.

#### **3.1.1 GraphQL Strategy: Tailoring Context for Agents**

Unlike REST APIs, which return fixed data structures, GraphQL allows the client to specify exactly what fields are needed. This is a critical advantage for an LLM-driven system where context window space is at a premium.4 However, raw GraphQL queries are complex and prone to syntax errors if generated dynamically by an LLM.7 Therefore, the strategy dictates that we **do not** expose a generic execute_graphql tool. Instead, we must engineer specific, high-level tools that wrap optimized GraphQL query strings.

The search_entity Tool:  
The entry point for any interaction with Open Targets is the search node. This endpoint indexes all entities (targets, diseases, drugs) in the platform.4 The Agent needs a tool that wraps this node but, crucially, requests the specific metadata fields required for verification.

* **Query Structure:** The tool must request id, name, entity, description, and synonyms. For targets, it should specifically request approvedSymbol and proteinAnnotations { functions }. For diseases, it should request dbXRefs to allow cross-referencing with other ontologies.8  
* **Ranking & Scoring:** The OT search API returns an ElasticSearch score (score), which is not normalized (e.g., values like 873.0).9 The LLM must be instructed to use this score as a heuristic signal of relevance but to prioritize semantic verification (matching the description to the user's prompt) over the raw numerical score.

The get_target_associations Tool:  
Once an ID is resolved (e.g., ENSG00000141510 for TP53), the Agent needs to traverse the graph. The target node in the GraphQL schema allows for deep retrieval of associatedDiseases.

* **Data Density Strategy:** A naive query might return thousands of associations. The Agentic strategy requires us to paginate and sort these on the server side before presenting them to the LLM. The tool should fetch the top 10-20 associations sorted by score (global association score), providing a "semantic fingerprint" of the target.4 If a target is strongly associated with "Li-Fraumeni Syndrome" and "Osteosarcoma," the LLM can instantly recognize it as TP53.

#### **3.1.2 Schema Analysis & Field Selection**

The OT GraphQL schema is vast. To prevent "token bloating," we must meticulously select fields.

* **Target Object:** id, approvedSymbol, biotype, tractability (to assess druggability), and safety (to identify risks).4  
* **Disease Object:** id, name, therapeuticAreas (provides high-level categorization, e.g., "Oncology"), and clinicalSigns.  
* **Avoid:** Large lists of evidence strings or raw textMining data unless specifically requested, as these consume massive amounts of tokens with low signal-to-noise ratio for initial discovery.11

### **3.2 ChEMBL: The Chemical Reality Engine**

While Open Targets aggregates data, ChEMBL provides the ground truth for chemical structures and bioactivity.5 It is the domain of "strict chemistry," essential for queries involving molecular weight, mechanism of action, or structural similarity.

#### **3.2.1 Search Modalities: Substring vs. Similarity**

ChEMBL offers two distinct search paradigms, and the Agent must be equipped to use both appropriately.13

* **Substring/Metadata Filtering:** For text-based queries (e.g., "Find drugs similar to Aspirin"), the Agent utilizes the molecule endpoint with filter parameters. The pref_name__icontains filter allows for case-insensitive substring matching, while molecule_synonyms__synonym__icontains extends the search to the synonym table.5 This is the "Fuzzy" entry point for chemistry.  
* **Similarity Search:** For structural queries (e.g., "Find analogs of this SMILES string"), the Agent utilizes the /similarity/{smiles}/{similarity_cutoff} endpoint.13 This capability is unique to ChEMBL in this stack and allows the Agent to perform "chemical reasoning"—finding molecules that *look* like the query rather than just *sound* like it.

#### **3.2.2 Linking Targets to Chemistry**

A critical workflow involves linking a biological target (from Open Targets) to specific chemical inhibitors. The ChEMBL mechanism endpoint is the key.

* **Tool Strategy:** A get_drug_mechanism tool should accept a ChEMBL ID (either for a target or a molecule) and return the mechanism of action description and the action type (e.g., "INHIBITOR", "ANTAGONIST").4  
* **Cross-Reference:** To link an Open Targets ID (Ensembl) to ChEMBL, the Agent uses the UniProt cross-references or the internal mapping within Open Targets. However, ChEMBL's own target endpoint allows searching by target_components__accession (UniProt Accession), creating a robust bridge between the two Tier 0 systems.16

## **4. Tier 1 Strategy: Verification and Enrichment**

The Tier 1 APIs—DrugBank, HGNC, and UniProt—act as the "Referees" of the system. They are used to verify the hypotheses generated from Tier 0 data and to enrich that data with specialized attributes (e.g., pharmacokinetics, nomenclature history, protein sequences).

### **4.1 DrugBank: Clinical Context and Commercial Constraints**

DrugBank offers high-quality, curated clinical information that is often more readable and structured than ChEMBL's raw bioactivity data.2 However, it presents unique integration challenges due to its licensing model and API structure.

#### **4.1.1 The Challenge of Fuzzy Search**

DrugBank's API supports a fuzzy parameter (q=...&fuzzy=true) on the drug_names endpoint.2 However, research indicates this fuzzy matching is limited; it handles some phonetic similarity but is restrictive compared to modern ElasticSearch implementations.18

* **Strategic Mitigation:** The Agent should prioritize **Exact Match** first. If that fails, it triggers the Fuzzy Search. If that also fails, the Agent should be instructed to "lemmatize" or simplify the query (e.g., stripping "Hydrochloride" or "Tablets" from the drug name) and retry.19

#### **4.1.2 Regional Filtering and Public vs. Commercial Data**

DrugBank's API is segmented by region (US, CA, EU).2 A query for "Paracetamol" might return different results (or no results) depending on the region filter.

* **Implementation:** The tool wrapper must default to region=us (United States) to maximize the probability of finding FDA-approved drugs, which dominate the literature.2 It should also allow the Agent to override this if the user context implies a specific geography (e.g., "What is this drug called in Europe?").  
* **Error Handling:** Accessing restricted "Commercial" endpoints may result in 403 Forbidden errors.20 The wrapper must catch these and return a polite, informative message to the LLM ("Commercial data for this entity is restricted"), preventing the Agent from interpreting the error as a "Not Found" result.

### **4.2 HGNC: The Nomenclature Authority**

Biological literature is rife with outdated gene aliases (e.g., *HER2*, *p53*). HGNC is the ultimate authority for resolving these to the current approved symbols (*ERBB2*, *TP53*).21

#### **4.2.1 Symbol Normalization Workflow**

The Agent must treat HGNC as the first step in any gene-related query.

* **Tool:** normalize_gene_symbol.  
* **Logic:** The tool queries the HGNC search endpoint. If the result matches a prev_symbol or alias_symbol, the tool returns the symbol (Approved Symbol) as the primary ID.22  
* **Impact:** This normalization prevents downstream failures in Open Targets or ChEMBL, which index primarily on the approved symbol or Ensembl ID. It acts as a "sanity check" ensuring the Agent is speaking the correct biological language.23

### **4.3 UniProt: Sequence Truth and Cross-Referencing**

UniProt is the definitive source for protein sequence data and functional annotation.24 Its strategic value lies in its extensive cross-referencing capabilities.25

#### **4.3.1 The Triangulation Anchor**

UniProt entries contain explicit links to ChEMBL, DrugBank, Ensembl, and PDB.26

* **Verification Strategy:** If the Agent is unsure whether ChEMBL Target CHEMBL123 is actually *TP53*, it can query the UniProt entry for *TP53* (P04637) and check the xref_chembl list. If CHEMBL123 is present, the link is verified. This "Triangulation" capability is a powerful tool against hallucination.  
* **Data Retrieval:** The Agent should use the uniprotkb/search endpoint with specific field selection (accession, id, gene_names, xref_chembl, xref_ensembl) to retrieve these links efficiently.25

## **5. Deep Dive: The "Fuzzy-to-Fact" Entity Resolution Loop**

The "Fuzzy-to-Fact" loop is the central operational pattern of the Agent. It is the mechanism by which the Agent resolves ambiguity.

### **5.1 Step 1: Intent Decomposition**

The Agent first analyzes the user's prompt to extract potential entities.

* *User Prompt:* "What inhibitors are available for the protein involved in cystic fibrosis?"  
* *Agent Extraction:* Target Description: "protein involved in cystic fibrosis". Desired Output: "inhibitors" (Drugs).

### **5.2 Step 2: Broad Discovery (Fuzzy Search)**

The Agent executes search tools to find candidates.

* *Tool Call:* opentargets_search(query="cystic fibrosis", entity_type="target").  
* *Response:* The API returns a list of hits.  
  * Hit 1: CFTR (Score 900, Description: "Cystic fibrosis transmembrane conductance regulator...").  
  * Hit 2: TGFB1 (Score 450, Description: "Transforming growth factor beta 1...").  
  * Hit 3: SCNN1A (Score 300).

### **5.3 Step 3: Contextual Verification**

The Agent evaluates the hits against the user's intent.

* *Reasoning:* "The user asked for 'the protein' (singular) involved in the disease. CFTR is the primary causative gene. TGFB1 is a modifier. CFTR is the most logical match."  
* *Action:* The Agent selects CFTR (ENSG00000001626).

### **5.4 Step 4: Precise Execution**

The Agent uses the resolved ID to fetch specific data.

* *Tool Call:* opentargets_get_known_drugs(ensemblId="ENSG00000001626").  
* *Response:* Returns a list of drugs: Ivacaftor, Lumacaftor, Tezacaftor.

### **5.5 Step 5: Synthesis**

The Agent formulates the final answer, explicitly stating the resolved entity to ground the user.

* *Response:* "The primary protein associated with cystic fibrosis is **CFTR** (Cystic Fibrosis Transmembrane Conductance Regulator). Known inhibitors and modulators for this target include **Ivacaftor**, **Lumacaftor**, and **Tezacaftor**..."

## **6. Context-Rich Tooling: Engineering Semantic Density**

The success of the Agent depends on the quality of the information returned by the tools. A raw API response is often "semantically sparse"—filled with technical IDs and nulls but lacking the descriptive text an LLM needs to reason.28

### **6.1 The "Sanitization Layer"**

We must implement a transformation layer between the raw API and the LLM. This layer processes the JSON to maximize **Semantic Density**—the ratio of useful reasoning tokens to total tokens.

**Principles of Sanitization:**

1. **Pruning:** Recursively remove all keys with null values or empty lists. This reduces noise.  
2. **Flattening:** Collapse deeply nested structures. E.g., data.target.associatedDiseases.rows becomes associated_diseases.  
3. **Field Prioritization:** Always preserve description, synonyms, function, and mechanism_of_action. These text fields are the "native language" of the LLM.  
4. **List Truncation with Summaries:** Never return a list of 5,000 items. Return the top 10 (sorted by score) and a count of the remainder.  
   * *Example:* {"top_drugs":, "total_drug_count": 142, "note": "List truncated. Use specific filters to see more."}. This informs the Agent of the data's existence without overflowing the context window.10

### **6.2 Comparison: Raw vs. Agentic Output**

**Table 1: Transformation of API Responses**

| Feature | Raw API Response (Open Targets) | Agentic Optimized Response |
| :---- | :---- | :---- |
| **Structure** | Deeply nested GraphQL JSON (data.search.hits...) | Flat, key-value pairs (match_candidate) |
| **Content** | Includes version_hash, scores (raw), internal_ids | Includes symbol, name, description, match_score |
| **Lists** | Returns all requested rows (potentially huge) | Returns Top 5 + "Total Count" metadata |
| **Nulls** | Explicit null fields | Keys removed entirely |
| **Reasoning Value** | Low (Requires parsing logic) | High (Self-evident context) |

## **7. Verification Workflows: Triangulation and Trust**

In an Agentic system, "hallucination" is often just a retrieval error. Verification workflows are the defense mechanism.

### **7.1 The Triangulation Protocol**

Triangulation involves confirming a fact using two independent data sources.

* **Scenario:** Agent identifies Drug X as a target for Gene Y.  
* **Source A (Open Targets):** Queries target(Y) -> knownDrugs. Finds Drug X.  
* **Source B (DrugBank):** Queries drug(X) -> targets. Finds Gene Y.  
* **Logic:** If Source A and Source B agree, the confidence is High. If they disagree (e.g., DrugBank lists Gene Y as a "metabolizer" rather than a "target"), the Agent must report this nuance.

### **7.2 Metadata Consistency Checks**

When triangulation isn't possible (e.g., restricted data), the Agent uses internal consistency checks.

* **Phenotype Check:** If the Agent retrieves a target for "Diabetes," it checks the associatedDiseases list. If the list contains only "Cancer" terms and no metabolic terms, the Agent flags a potential mismatch: "I found a target with this name, but it appears to be associated with Oncology, not Diabetes. Please verify."

## **8. Client Ecosystem & Async Support**

The technical foundation of the @lifesciences-mcp server is its client ecosystem. The requirement for an "Agentic" experience—fast, conversational, multi-step reasoning—demands a non-blocking architecture.

### **8.1 The Failure of Synchronous Clients**

Official client libraries for these APIs (e.g., chembl_webresource_client 29, opentargets-py 30) are typically synchronous. They make blocking network calls using urllib or requests.

* **Impact:** In an MCP server, a blocking call pauses the entire event loop. If the Agent needs to verify 5 drugs against DrugBank, and each call takes 1 second, the user waits 5+ seconds. This latency destroys the "flow" of interaction.  
* **Decision:** We typically **reject** official synchronous clients for the runtime agent.

### **8.2 The Async Python Stack**

We recommend a custom client architecture built on **httpx** and **asyncio**.

* **httpx:** Chosen over aiohttp for its modern API, full type hinting support, and HTTP/2 capabilities.31 It allows for a unified AsyncClient that can pool connections across different tools, significantly reducing SSL handshake overhead.  
* **asyncio.gather:** This is the key enabler of "parallel reasoning." The Agent can dispatch search queries to Open Targets, ChEMBL, and HGNC *simultaneously*.  
  * *Workflow:*  
    Python  
    # Parallel Execution Pattern  
    results = await asyncio.gather(  
        opentargets.search("brca1"),  
        chembl.search("brca1"),  
        hgnc.search("brca1")  
    )  
    # LLM synthesizes all three results instantly

This reduces the total wait time to the duration of the slowest single request, rather than the sum of all requests.32

### **8.3 Rate Limiting and Resilience**

Async systems can easily overwhelm public APIs. We must implement **client-side throttling**.

* **Semaphore Pattern:** Use asyncio.Semaphore(10) to limit the Agent to 10 concurrent requests.  
* **Retry Logic:** Implement exponential backoff for 429 Too Many Requests errors using libraries like tenacity. This ensures the Agent is a "good citizen" of the API ecosystem.23

## **9. Implementation Roadmap**

The deployment of the @lifesciences-mcp agentic strategy should follow a phased approach.

### **Phase 1: Foundation (Weeks 1-2)**

* **Objective:** Establish the Async Core and Tier 0 Connectivity.  
* **Tasks:**  
  * Set up the Python project with httpx and pydantic.  
  * Implement the raw OpenTargetsClient and ChEMBLClient using httpx.  
  * Develop the GraphQL query builder for Open Targets.  
  * Create the "Sanitization Layer" to process JSON outputs.

### **Phase 2: The Logic Core (Weeks 3-4)**

* **Objective:** Enable "Fuzzy-to-Fact" Resolution.  
* **Tasks:**  
  * Implement the search tools with fuzzy parameters.  
  * Design the system prompts that guide the LLM through the "Search-Verify-Execute" loop.  
  * Deploy HGNCClient for symbol normalization.  
  * Test resolution of ambiguous terms (e.g., "Her2", "Tylenol").

### **Phase 3: Verification & Enrichment (Weeks 5-6)**

* **Objective:** Integrate Tier 1 for robustness.  
* **Tasks:**  
  * Implement DrugBankClient with region awareness and auth handling.  
  * Implement UniProtClient for sequence retrieval and cross-referencing.  
  * Build "Verification Tools" that perform multi-source checks (Triangulation).

### **Phase 4: Optimization & Scale (Weeks 7-8)**

* **Objective:** Performance tuning.  
* **Tasks:**  
  * Implement async-lru caching to store search results for 24 hours.  
  * Tune connection pooling and semaphore limits.  
  * Conduct user testing with complex, multi-hop queries ("Find me inhibitors for the pathway involved in X").

## **10. Conclusion**

The @lifesciences-mcp project defines a new standard for bioinformatics middleware. By embracing an **Agentic Integration Strategy**, we move beyond the limitations of static ETL pipelines and harness the reasoning power of LLMs to navigate the complexity of biological data. The architecture defined here—anchored by a tiered API strategy, powered by asynchronous Python tooling, and safeguarded by rigorous verification workflows—ensures that the system is not only technically robust but also semantically intelligent. It turns the "fuzzy" ambiguity of scientific inquiry into actionable, evidence-based facts.

#### **Works cited**

1. API | Open Targets Platform, accessed December 21, 2025, [https://platform.opentargets.org/api](https://platform.opentargets.org/api)  
2. API Reference | DrugBank Help Center, accessed December 21, 2025, [https://docs.drugbank.com/](https://docs.drugbank.com/)  
3. Fuzzy search algorithm (approximate string matching algorithm) - Stack Overflow, accessed December 21, 2025, [https://stackoverflow.com/questions/32337135/fuzzy-search-algorithm-approximate-string-matching-algorithm](https://stackoverflow.com/questions/32337135/fuzzy-search-algorithm-approximate-string-matching-algorithm)  
4. GraphQL API | Open Targets Platform Documentation, accessed December 21, 2025, [https://platform-docs.opentargets.org/data-access/graphql-api](https://platform-docs.opentargets.org/data-access/graphql-api)  
5. Target Questions | ChEMBL Interface Documentation - GitBook, accessed December 21, 2025, [https://chembl.gitbook.io/chembl-interface-documentation/frequently-asked-questions/target-questions](https://chembl.gitbook.io/chembl-interface-documentation/frequently-asked-questions/target-questions)  
6. Open Targets Platform, accessed December 21, 2025, [https://platform.opentargets.org/](https://platform.opentargets.org/)  
7. QuentinCody/open-targets-mcp-server - GitHub, accessed December 21, 2025, [https://github.com/QuentinCody/open-targets-mcp-server](https://github.com/QuentinCody/open-targets-mcp-server)  
8. schema - opentargets platform api, accessed December 21, 2025, [https://api.platform.opentargets.org/api/v4/graphql/schema](https://api.platform.opentargets.org/api/v4/graphql/schema)  
9. What kind of score is returned when using the "search" endpoint? - GraphQL API, accessed December 21, 2025, [https://community.opentargets.org/t/what-kind-of-score-is-returned-when-using-the-search-endpoint/348](https://community.opentargets.org/t/what-kind-of-score-is-returned-when-using-the-search-endpoint/348)  
10. Returning all associations data using the Platform API - Open Targets Community, accessed December 21, 2025, [https://community.opentargets.org/t/returning-all-associations-data-using-the-platform-api/324](https://community.opentargets.org/t/returning-all-associations-data-using-the-platform-api/324)  
11. Open Targets API Tutorial: Getting Started | by eliseo papa | opentargets - Medium, accessed December 21, 2025, [https://medium.com/opentargets/target-validation-api-tutorial-getting-started-35d5051d3188](https://medium.com/opentargets/target-validation-api-tutorial-getting-started-35d5051d3188)  
12. ChEMBL: a large-scale bioactivity database for drug discovery | Nucleic Acids Research | Oxford Academic, accessed December 21, 2025, [https://academic.oup.com/nar/article/40/D1/D1100/2903401](https://academic.oup.com/nar/article/40/D1/D1100/2903401)  
13. ChEMBL Data Web Services, accessed December 21, 2025, [https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services](https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services)  
14. ChEMBL web services: streamlining access to drug discovery data and utilities - PMC, accessed December 21, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC4489243/](https://pmc.ncbi.nlm.nih.gov/articles/PMC4489243/)  
15. Chembl Tools - ToolUniverse Documentation, accessed December 21, 2025, [https://zitniklab.hms.harvard.edu/ToolUniverse/tools/chembl_tools.html](https://zitniklab.hms.harvard.edu/ToolUniverse/tools/chembl_tools.html)  
16. ChEMBL REST API, accessed December 21, 2025, [https://www.ebi.ac.uk/training/online/courses/embl-ebi-programmatically/wp-content/uploads/sites/128/2020/08/ChEMBL-programmatically.pdf](https://www.ebi.ac.uk/training/online/courses/embl-ebi-programmatically/wp-content/uploads/sites/128/2020/08/ChEMBL-programmatically.pdf)  
17. Discovery API Reference | DrugBank Help Center, accessed December 21, 2025, [https://docs.drugbank.com/discovery/v1/](https://docs.drugbank.com/discovery/v1/)  
18. AI-Powered Drug Classification and Indication Mapping for Pharmacoepidemiologic Studies: Prompt Development and Validation - NIH, accessed December 21, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12203024/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12203024/)  
19. Developing Large Language Models for Clinical Research Using One Million Clinical Trials, accessed December 21, 2025, [https://arxiv.org/html/2505.16097v2](https://arxiv.org/html/2505.16097v2)  
20. DrugBank 6.0: the DrugBank Knowledgebase for 2024 | Nucleic Acids Research | Oxford Academic, accessed December 21, 2025, [https://academic.oup.com/nar/article/52/D1/D1265/7416367](https://academic.oup.com/nar/article/52/D1/D1265/7416367)  
21. Frequently asked questions | HUGO Gene Nomenclature Committee, accessed December 21, 2025, [https://www.genenames.org/help/faq/](https://www.genenames.org/help/faq/)  
22. Multi-symbol checker help | HUGO Gene Nomenclature Committee, accessed December 21, 2025, [https://www.genenames.org/help/multi-symbol-checker/](https://www.genenames.org/help/multi-symbol-checker/)  
23. REST web-service help | HUGO Gene Nomenclature Committee, accessed December 21, 2025, [https://www.genenames.org/help/rest/](https://www.genenames.org/help/rest/)  
24. UniProtKB query fields | UniProt help, accessed December 21, 2025, [https://www.uniprot.org/help/query-fields](https://www.uniprot.org/help/query-fields)  
25. UniProtKB return fields | UniProt help, accessed December 21, 2025, [https://www.uniprot.org/help/return_fields](https://www.uniprot.org/help/return_fields)  
26. cross references in UniProt help search, accessed December 21, 2025, [https://www.uniprot.org/help/cross_references](https://www.uniprot.org/help/cross_references)  
27. Programmatic access - Retrieving entries via queries | UniProt help, accessed December 21, 2025, [https://www.uniprot.org/help/api_queries](https://www.uniprot.org/help/api_queries)  
28. Latency optimization | OpenAI API, accessed December 21, 2025, [https://platform.openai.com/docs/guides/latency-optimization](https://platform.openai.com/docs/guides/latency-optimization)  
29. Official Python client for accessing ChEMBL API - GitHub, accessed December 21, 2025, [https://github.com/chembl/chembl_webresource_client](https://github.com/chembl/chembl_webresource_client)  
30. opentargets-archive/opentargets-py: Python client for the Open Targets REST API at targetvalidation.org - GitHub, accessed December 21, 2025, [https://github.com/opentargets-archive/opentargets-py](https://github.com/opentargets-archive/opentargets-py)  
31. Build an Async Python function for API - Stack Overflow, accessed December 21, 2025, [https://stackoverflow.com/questions/62324811/build-an-async-python-function-for-api](https://stackoverflow.com/questions/62324811/build-an-async-python-function-for-api)  
32. Python Tutorial: AsyncIO - Complete Guide to Asynchronous Programming with Animations, accessed December 21, 2025, [https://www.youtube.com/watch?v=oAkLSJNr5zY](https://www.youtube.com/watch?v=oAkLSJNr5zY)  
33. Async vs Sync in Python - Calling External APIs - YouTube, accessed December 21, 2025, [https://www.youtube.com/watch?v=xjNPG31j2yk](https://www.youtube.com/watch?v=xjNPG31j2yk)