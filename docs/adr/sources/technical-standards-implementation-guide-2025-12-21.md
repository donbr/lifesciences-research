# **Technical Standards & Implementation Guide: @lifesciences-mcp**

## **1. Executive Summary and Architectural Principles**

The implementation of the @lifesciences-mcp project represents a pivotal architectural shift in how autonomous agents interact with biological data. We are moving away from monolithic, human-centric web portals toward a distributed, semantic layer where Large Language Models (LLMs) must navigate the immense complexity of life science databases—specifically Open Targets, ChEMBL, DrugBank, HGNC, and UniProt. The core objective of this technical standard is to define a robust implementation strategy that abstracts these heterogeneous data sources into a unified, high-performance interface compliant with the Model Context Protocol (MCP).

This initiative faces three distinct categories of technical challenges. First, the **Client Ecosystem** for bioinformatics is historically synchronous, relying on blocking I/O operations that are fundamentally incompatible with the high-concurrency event loops required by modern agentic frameworks like FastMCP. Second, the **Data Volume** inherent in genomics and proteomics—ranging from simple gene symbols to multi-gigabyte structure files—necessitates a strict bifurcation between "Tools" (for reasoning) and "Resources" (for retrieval) to preserve the agent's finite context window. Third, the **Semantic Interoperability** challenge requires that a "target" in ChEMBL and a "target" in Open Targets be recognized as the same entity, despite divergent upstream schemas, necessitating the adoption of the Biolink Model as a unifying ontology.

The findings detailed in this report prescribe a hybrid client architecture. For modern APIs like Open Targets and HGNC, we mandate the development of lightweight, native asynchronous clients using aiohttp or httpx to maximize throughput and minimize overhead.1 For legacy systems like ChEMBL, where query logic is deeply embedded in synchronous libraries, we define a containment strategy using run_in_executor patterns to bridge the blocking/non-blocking divide without compromising server stability.3 Furthermore, to prevent the "hallucinated mapping" phenomenon—where agents conflate distinct biological entities due to identifier ambiguity—we enforce a strict "Resolve-First" protocol using Compact Uniform Resource Identifiers (CURIEs) and asynchronous interaction with the UniProt ID Mapping service.5

This document serves as the definitive implementation guide for the @lifesciences-mcp project, synthesizing technical research into actionable standards for Tier 0 and Tier 1 API integration.

## ---

**2. Architectural Foundations: Concurrency in Bioinformatics**

The foundational constraint of the @lifesciences-mcp server is the requirement for high concurrency. In a typical agentic workflow, a single user query—such as "Identify druggable targets for glioblastoma and retrieve their small molecule inhibitors"—does not translate to a single API call. Instead, it triggers a "fan-out" pattern of execution. The agent must first query a disease database, retrieve a list of gene IDs, resolve those IDs to protein accessions, query a chemistry database for each protein, and finally aggregate the results. This can easily result in dozens or hundreds of simultaneous HTTP requests.

### **2.1 The Asynchronous Imperative**

Python, the language of choice for both bioinformatics and MCP, operates under the Global Interpreter Lock (GIL), which allows only one thread to execute Python bytecode at a time. In traditional bioinformatics scripts, this is managed by purely synchronous execution: the script requests data, waits for the server to respond, and then proceeds. This "blocking" behavior is catastrophic for an MCP server.1 If the server blocks the main thread waiting for a 5-second response from ChEMBL, it cannot process "heartbeat" signals from the MCP client, potentially causing the connection to time out or the agent to become unresponsive.

The FastMCP framework is built on top of asyncio, Python’s library for writing concurrent code using the async/await syntax.1 This architecture relies on an event loop that manages tasks cooperatively. When an operation initiates a network request, it yields control back to the loop, allowing other tasks (like handling a user interrupt or processing a parallel request) to run. Therefore, the implementation strategy for @lifesciences-mcp must be rigorously asynchronous. We cannot simply "import and use" existing libraries; we must audit their internal I/O patterns.

### **2.2 The "Academic Abandonware" Risk**

A recurring theme in the analysis of the Python bioinformatics ecosystem is the prevalence of "academic abandonware"—libraries developed for a specific publication or project that are subsequently unmaintained.7 Many of these wrappers, such as opentargets-py, were designed in an era of monolithic scripts and rely on synchronous requests calls. They often lack support for modern features like connection pooling, keep-alive, or HTTP/2, which are critical for performance in a microservices environment. Relying on these legacy wrappers introduces technical debt and security vulnerabilities. Consequently, our architectural preference shifts away from heavy, unmaintained SDKs toward lightweight, custom-built API clients that leverage modern HTTP standards and the specific endpoints required by the agent.

## ---

**3. Tier 0 API Implementation Strategy**

Tier 0 APIs are the critical path for the @lifesciences-mcp project. They provide the core graph connectivity: linking diseases to targets (Open Targets) and targets to chemical modulators (ChEMBL). Failures or latency in these APIs directly degrade the agent's reasoning capabilities.

### **3.1 Open Targets Platform: The GraphQL Pivot**

The Open Targets Platform acts as the centralized knowledge graph for target identification. The discovery phase highlighted a critical divergence between the available legacy client and the platform's current capabilities.

#### **3.1.1 Ecosystem Analysis: The Obsolescence of REST**

The existing Python client, opentargets-py, targets the platform's older REST API.7 Our audit reveals this library is effectively deprecated, with its last significant update occurring in 2019. It does not support asyncio and relies on synchronous iteration over paginated results. Using this library in a FastMCP environment would require wrapping every call in a thread pool, adding significant memory overhead for the separate thread stacks and context switching.8

Furthermore, the REST paradigm itself is inefficient for the specific needs of an LLM agent. REST endpoints typically return fixed data structures ("over-fetching"). For example, querying a target might return its full sequence, GO terms, and cross-references, when the agent only requested its association score with a specific disease. This bloats the token count in the LLM's context window, increasing costs and reducing reasoning performance.

#### **3.1.2 The GraphQL Advantage**

The Open Targets Platform has migrated its primary programmatic access to a **GraphQL API** (v4+).9 GraphQL is uniquely suited for MCP agents because it allows "precise fetching." The agent can request exactly the fields it needs—e.g., just the approvedSymbol and geneticConstraint—minimizing the payload size.

However, there is no official asynchronous Python client for the Open Targets GraphQL API. Community discussions suggest users struggle with constructing complex queries manually.10 This necessitates the creation of a custom integration layer.

#### **3.1.3 Implementation Standard: OpenTargetsAsyncClient**

We define the standard implementation as a custom aiohttp-based client class. This client must manage a persistent ClientSession to enable connection pooling (reusing TCP connections for multiple queries), which is vital for the "fan-out" query patterns typical of agents.9

**Architectural Requirements:**

1. **Transport Layer**: Use aiohttp or httpx (configured for async).  
2. **Query Management**: GraphQL queries should not be constructed via string concatenation, which is prone to syntax errors. Instead, they should be stored as constant templates or .graphql files, with variables injected safely at runtime.9  
3. **Error Handling**: The client must implement exponential backoff for HTTP 429 (Too Many Requests) and 502 (Bad Gateway) errors, which are common in public APIs under load.  
4. **Biolink Transformation**: The client must include a parsing layer that transforms the nested GraphQL JSON response into a flat, Biolink-compliant structure before returning it to the Tool (see Section 7).

Reference Implementation Pattern:  
The following table contrasts the legacy approach with the mandated standard.

| Feature | Legacy opentargets-py | Mandated OpenTargetsAsyncClient |
| :---- | :---- | :---- |
| **I/O Model** | Blocking (Synchronous) | Non-blocking (Asynchronous) |
| **Data Fetching** | Fixed REST Endpoints | Dynamic GraphQL Queries |
| **Payload Control** | None (Full Objects) | Precise (Field Selection) |
| **Maintainability** | Low (Archived) | High (Custom/Minimal) |
| **MCP Integration** | Requires run_in_executor | Native await support |

**Operational Insight**: To prevent timeouts during complex queries, the GraphQL client should default to fetching only the "top k" associations and provide a cursor for pagination (see Section 6). Deeply nested queries (e.g., Target -> Disease -> Evidence -> Publication) should be avoided in favor of sequential calls to prevent server-side timeouts at Open Targets.10

### **3.2 ChEMBL: Bridging the Legacy Gap**

ChEMBL is the definitive resource for bioactive molecules. Its integration presents a different challenge: the complexity of its domain logic versus the age of its tooling.

#### **3.2.1 Ecosystem Analysis: The Complexity of chembl_webresource_client**

The official chembl_webresource_client is a sophisticated library.11 It implements a Django-like QuerySet API (e.g., new_client.activity.filter(...).order_by(...)), which abstracts away the immense complexity of SQL-like filtering over chemical properties. Replicating this query logic in a raw HTTP client would be error-prone and require effectively reverse-engineering the ChEMBL backend logic.

However, the library is fundamentally synchronous.12 It relies on requests and implements its own caching mechanisms that are not thread-safe or async-aware. It utilizes "lazy evaluation," meaning network requests are triggered only when data is iterated over. In an async function, iterating over a synchronous lazy object will block the loop.8

#### **3.2.2 Implementation Strategy: The Executor Pattern**

Given the high value of the client's query logic, rewriting it is not feasible for Phase 1. The implementation strategy is to encapsulate the legacy client within a run_in_executor block. This allows the synchronous I/O to occur in a separate thread, while the main MCP event loop remains unblocked.8

**Technical Specification:**

1. **Thread Pool Isolation**: A dedicated ThreadPoolExecutor must be defined for ChEMBL tasks. This prevents ChEMBL queries from starving other thread-based tasks (like file I/O). A pool size of 4-8 workers is recommended to respect ChEMBL's rate limits.  
2. **Eager Evaluation**: The wrapper function must force the evaluation of the lazy QuerySet *inside* the thread. Returning the lazy object to the main async loop would cause blocking when the MCP framework attempts to serialize it to JSON.  
   * *Incorrect*: return await loop.run_in_executor(pool, lambda: query) (Returns a lazy object).  
   * *Correct*: return await loop.run_in_executor(pool, lambda: list(query)) (Returns data).

Caching Considerations:  
The chembl_webresource_client uses requests_cache (sqlite backend) by default.11 This is disk I/O blocking. While acceptable in a thread, high-concurrency usage might lead to SQLite lock contention. For the @lifesciences-mcp, we recommend configuring the client to use a memory-based backend or disabling the client's internal cache in favor of an async-aware caching layer (like aiocache) at the Tool level.

## ---

**4. Tier 1 API Implementation Strategy**

Tier 1 APIs—UniProt, HGNC, and DrugBank—provide essential context: sequences, canonical names, and pharmaceutical details. These services require varied integration approaches due to their disparate technical architectures.

### **4.1 UniProt: High-Throughput Sequences and ID Mapping**

UniProt is unique because it serves both metadata (JSON) and massive sequence data (FASTA), and it offers a specialized asynchronous job queue for ID mapping.

#### **4.1.1 Ecosystem Analysis: Unipressed vs. uniprotparser**

* **Unipressed**: This library offers excellent type safety and schema validation.14 However, it is strictly synchronous. Its iterators block on network I/O, making it unsuitable for a high-performance MCP server without heavy threading.  
* **uniprotparser**: Recent updates (v1.0.5+) have introduced explicit aiohttp support.15 It allows for asynchronous iteration: async for record in parser.parse_async(...). This aligns perfectly with the FastMCP architecture.  
* **Official REST API**: The UniProt REST API is robust, supporting streamable formats and batch retrieval.16

#### **4.1.2 The ID Mapping Challenge**

One of the most critical functions of the @lifesciences-mcp is resolving IDs (e.g., mapping an Ensembl Gene ID to a UniProt Accession). UniProt's ID Mapping service is **asynchronous by design**.5 You submit a job, receive a Job ID, and must poll the service until the status is FINISHED.

* A synchronous client would sleep/block during polling.  
* An MCP-compliant async client must implement a non-blocking polling loop using asyncio.sleep(). This allows the server to handle other requests while waiting for the UniProt compute cluster to process the mapping job.

Implementation Standard:  
We mandate the use of uniprotparser's async capabilities for general search.15 For the ID Mapping service, a custom aiohttp wrapper is required to handle the specific Submit-Poll-Retrieve lifecycle efficiently, as general-purpose wrappers often mishandle the polling intervals or error states of this specific API.

### **4.2 HGNC: The Naming Authority**

HGNC (HUGO Gene Nomenclature Committee) is the "source of truth" for human gene symbols.

#### **4.2.1 Ecosystem Analysis: Avoiding Local Databases**

The library PyHGNC interacts with local databases (MySQL/SQLite) constructed from HGNC dumps.17 While powerful for bulk analytics, this architecture is antithetical to the microservices model of MCP. It requires stateful volume mounts, regular database updates, and significant local storage.  
The HGNC REST API (rest.genenames.org) is a highly performant, read-only service that returns JSON.18 It requires no authentication and supports searching by almost any field (alias, previous symbol, ID).

#### **4.2.2 Implementation Standard: Direct Async REST**

The implementation will use a direct aiohttp client. The API is simple enough that no external wrapper library is necessary.

* **Endpoint**: /fetch/symbol/{symbol} is the primary endpoint.18  
* **Header**: Accept: application/json must be set to ensure machine-readable output.18  
* **Ambiguity Handling**: The client must check the status field in the response. If a symbol is "Entry Withdrawn" or "Symbol Moved," the client must follow the new_symbol link to prevent returning obsolete data.19

### **4.3 DrugBank: The Access Barrier**

DrugBank provides high-quality pharmaceutical data but operates under a restrictive license and technical model.

#### **4.3.1 Ecosystem Analysis**

There is no official open-source Python client for the DrugBank API. The "wrappers" available on GitHub are mostly parsers for the XML database dump, which users must download manually.20 The API itself requires an API key and uses token-based authentication.22

#### **4.3.2 Implementation Standard: Commercial vs. Open**

The implementation must support two modes:

1. **API Mode (Commercial/Key Holders)**: A custom httpx async wrapper around api.drugbank.com. This is the preferred mode for real-time Tools. It must handle 403 Forbidden errors gracefully if the key is invalid.4  
2. **Resource Mode (Open/Academic)**: For users without API access who have the XML dump, the MCP server should expose this file as a **Resource** (see Section 6). Parsing a 1GB+ XML file to answer a Tool query ("What is the mechanism of Aspirin?") is too slow for real-time interaction. Therefore, DrugBank Tools should be disabled in "XML Mode," and the data should only be accessible via direct Resource reading.

## ---

**5. Identifier Resolution and Hallucination Prevention**

A pervasive failure mode in biomedical AI agents is "hallucinated mapping." This occurs when an agent assumes that an identifier in one context (e.g., the string "AKT1") refers to the same entity in another context without verification. For instance, "AKT1" could refer to the human gene, the mouse gene, or a completely unrelated chemical acronym. Furthermore, databases act as silos: ChEMBL expects UniProt IDs, while Open Targets expects Ensembl IDs. If an agent passes an Ensembl ID to ChEMBL, it will receive zero results, potentially leading it to conclude "No known drugs exist," which is a factual error caused by a technical mismatch.

### **5.1 The Resolution Imperative**

We define a strict **"Resolve-First" Protocol** for the @lifesciences-mcp server. No Tool is permitted to accept a raw user string (like "insulin") and immediately query a downstream database.

1. **Resolution Step**: The input must first be resolved to a canonical, unambiguous identifier.  
2. **Normalization Step**: That identifier must be formatted as a Compact URI (CURIE).  
3. **Expansion Step**: If the downstream API requires a different namespace, an explicit mapping must occur.

### **5.2 The CURIE Standard**

To ensure internal consistency, all internal data structures must use CURIEs.23 A CURIE combines a namespace prefix with a local identifier.

| Entity Type | Canonical Namespace | CURIE Format | Example |
| :---- | :---- | :---- | :---- |
| **Gene** | HGNC | HGNC:{id} | HGNC:1101 |
| **Protein** | UniProtKB | UniProtKB:{accession} | UniProtKB:P31749 |
| **Chemical** | ChEMBL | CHEMBL:{id} | CHEMBL:CHEMBL25 |
| **Disease** | MONDO / EFO | MONDO:{id} / EFO:{id} | MONDO:0005011 |

### **5.3 The "Resolver" Tool Implementation**

The project must include a dedicated meta-tool, resolve_entity(query: str, type: str), which acts as the entry point for agent reasoning.

**Logic Flow:**

1. **Gene/Protein Resolution**: Query the HGNC REST API (/search/{query}).  
   * If multiple hits are returned (e.g., searching "AKT" returns AKT1, AKT2, AKT3), the Tool *must* return a disambiguation prompt, not a guess.24  
   * *Agent Output*: "Ambiguous query. Did you mean AKT1 (HGNC:391) or AKT2 (HGNC:392)?"  
2. **Cross-Reference (The Cross-Walk)**:  
   * Once a CURIE is established (e.g., HGNC:1101), the agent may need to query Open Targets (needs ENSEMBL:ENSG...).  
   * The UniProt ID Mapping API is the designated "Rosetta Stone".5 The @lifesciences-mcp server must implement a background helper function map_identifier(from_ns, to_ns, id) that transparently handles this conversion.  
   * *Implementation Detail*: To prevent slow-downs, frequently used mappings (like HGNC <-> Ensembl) should be cached aggressively using an LRU (Least Recently Used) cache within the server process.

**Hallucination Check**: The implementation must explicitly validate the **Taxonomy ID**. A common error is mapping a human gene symbol to a mouse protein. All queries should default to NCBITaxon:9606 (Human) unless the user explicitly requests another organism.26

## ---

**6. Data Volume Patterns: The Tool/Resource Dichotomy**

Bioinformatics APIs present a unique data volume challenge. A single "entity" can be represented by a 200-byte summary or a 200-megabyte structure file. Current LLMs have finite context windows (e.g., 128k - 200k tokens). Injecting massive datasets directly into the conversation history ("Context Flooding") flushes out instructions and degrades reasoning performance.

The Model Context Protocol (MCP) distinguishes between **Tools** (executable functions) and **Resources** (readable data items).1 The @lifesciences-mcp project will enforce a strict dichotomy based on data utility.

### **6.1 Tools: Summarized Knowledge for Reasoning**

Tools are for asking questions. Their output must be concise, structured, and semantically rich.

* **Truncation Policy**: No Tool is permitted to return unbounded lists. If a user asks "Get all targets associated with Cancer," the API might return 5,000 hits. The Tool implementation must truncate this to the top 20-50 most relevant results (sorted by score) and provide metadata indicating the total count.28  
* **Pagination Pattern**: We will implement **Cursor-Based Pagination**.28  
  * The Tool response must include an opaque next_cursor string (derived from the upstream API).  
  * The Tool output should include "Prompt Engineering in JSON"—a text field instructing the agent on how to proceed.  
  * *Example Output*:  
    JSON  
    {  
      "data": [... 50 items...],  
      "pagination": {  
        "next_cursor": "YXJyYXljb25uZWN0aW9uOjQ5",  
        "instruction": "50 of 4,300 results shown. To retrieve the next batch, call this tool again with cursor='YXJyYXljb25uZWN0aW9uOjQ5'."  
      }  
    }

  * This empowers the agent to iterate autonomously if it deems necessary, without flooding the context initially.

### **6.2 Resources: Raw Data for Analysis**

Resources are for "reading." When the data is too large for a chat message but necessary for a task (e.g., "Analyze the binding pocket of this protein"), it must be exposed as a Resource.27 The LLM can then read this resource into its working memory *only when needed*, or pass the Resource URI to a code-interpreter tool.

Standardized URI Schemes:  
We define specific custom URI schemes to abstract the underlying data sources.

| Data Type | URI Scheme | MIME Type | Description |
| :---- | :---- | :---- | :---- |
| **Sequence** | uniprot://sequence/{accession} | text/x-fasta | Full amino acid sequence 31 |
| **Structure** | pdb://structure/{id} | chemical/x-mmcif | 3D structure data |
| **Evidence** | opentargets://evidence/{id} | application/json | Full list of evidence strings |
| **Drug Data** | drugbank://xml/{id} | application/xml | Specific XML node for a drug |

**Implementation Detail**: The MCP server's read_resource handler will intercept these URIs. For uniprot://sequence/P53_HUMAN, it will asynchronously fetch the FASTA from rest.uniprot.org and return it as a binary blob or text stream. This decoupling allows the underlying API endpoints to change without breaking the agent's "mental model" of the data.

## ---

**7. Interoperability Standards: The Biolink Model**

The "Tower of Babel" problem is the primary obstacle to multi-database integration. ChEMBL calls a connection a "mechanism of action"; Open Targets calls it an "association"; UniProt calls it an "interaction." If the MCP server simply passes raw API JSON back to the agent, the LLM must expend significant inference cycles trying to align these schemas, often failing to notice that "Target X" in one JSON is "Gene Y" in another.

### **7.1 The Biolink Standard**

The **Biolink Model** is the mandated interoperability standard for the @lifesciences-mcp project.32 Developed by the NCATS Translator consortium, Biolink is a high-level ontology specifically designed to standardize types and relationships in biological knowledge graphs.34 It provides a neutral schema that sits above the specific implementations of ChEMBL or Open Targets.

**Comparison with Alternatives:**

* **Bioschemas**: Designed for SEO and finding datasets on the web (Schema.org extension). It lacks the granular relationship types needed for scientific reasoning.34  
* **GA4GH (Beacon)**: Excellent for genomics and variant sharing but too narrow for general drug discovery (chemistry/phenotypes).35  
* **Biolink**: Offers a comprehensive hierarchy for Entities (biolink:SmallMolecule, biolink:Gene) and Associations (biolink:treats, biolink:causes), making it the ideal choice for constructing reasoning chains.36

### **7.2 Transformation Logic**

Every Tool in the @lifesciences-mcp project must include a "Transformer" layer. This layer intercepts the raw JSON from the API client and re-maps it to the Biolink schema before returning it to the LLM.

Standardized Output Structure (TRAPI-Compliant):  
We will adopt the Translator Reasoner API (TRAPI) Message structure for Tool outputs.37 This structure separates the graph topology from the node attributes.  
Example: Normalized ChEMBL Output  
Raw ChEMBL JSON:

JSON

{  
  "molecule_chembl_id": "CHEMBL25",  
  "target_chembl_id": "CHEMBL203",  
  "standard_type": "IC50",  
  "standard_value": "10.5"  
}

*Transformed Biolink/TRAPI Output:*

JSON

{  
  "subject": {  
    "id": "CHEMBL:CHEMBL25",  
    "name": "Aspirin",  
    "category":  
  },  
  "predicate": "biolink:inhibits",  
  "object": {  
    "id": "CHEMBL:CHEMBL203",  
    "category": ["biolink:Protein"]  
  },  
  "attributes": [  
    {  
      "attribute_type_id": "biolink:affinity_parameter",  
      "value": 10.5,  
      "unit": "nM"  
    }  
  ]  
}

**Mapping Rules:**

1. **Predicate Inference**: The transformer must infer the predicate based on data values. For example, if ChEMBL reports an "Activator" mechanism, the predicate becomes biolink:activates. If Open Targets reports a genetic association, the predicate becomes biolink:genetically_associated_with.  
2. **Category Assignment**: Hardcode the mapping of sources to categories.  
   * ChEMBL Targets -> biolink:Protein or biolink:Gene.  
   * Open Targets Diseases -> biolink:Disease or biolink:PhenotypicFeature.

This standardization ensures that the output of *any* Tool looks identical to the agent. Whether it queried ChEMBL or Open Targets, it sees "Subjects," "Objects," and "Predicates." This significantly improves the agent's ability to join data across tools (e.g., taking the object.id from a ChEMBL result and using it as the subject.id for an Open Targets query).

## ---

**8. Conclusion and Operational Roadmap**

The @lifesciences-mcp project is not merely an API wrapper; it is a semantic integration engine. The research dictates a clear path forward, characterized by rigorous adherence to asynchronous patterns, data volume management, and semantic standardization.

**Implementation Roadmap:**

1. **Foundation (Phase 1)**: Establish the FastMCP server skeleton. Implement the **Async Resolver Tool** (HGNC/UniProt) to serve as the gateway for all entity interactions. This prevents the "garbage in, garbage out" problem of bad identifiers.  
2. **Integration (Phase 2)**: Build the **Tier 0 Clients**. Develop the OpenTargetsAsyncClient (GraphQL) and the ChEMBLExecutorWrapper. Implement the Biolink transformers for these two key sources to enable basic Target-Disease-Drug reasoning.  
3. **Expansion (Phase 3)**: Integrate Tier 1 sources. Deploy the uniprotparser async client for sequence data and the DrugBank httpx client (or Resource loader).  
4. **Optimization (Phase 4)**: Implement the **Resource Handlers** for FASTA/PDB data and refine the pagination cursors. Add aggressive caching for ID mapping to improve response times.

By following this guide, the @lifesciences-mcp project will result in a robust, high-performance agentic interface that empowers LLMs to reason deeply and accurately across the complex domain of life sciences.

#### **Works cited**

1. jlowin/fastmcp: The fast, Pythonic way to build MCP servers and clients - GitHub, accessed December 21, 2025, [https://github.com/jlowin/fastmcp](https://github.com/jlowin/fastmcp)  
2. Creating a RESTful API with Python and aiohttp | TutorialEdge.net, accessed December 21, 2025, [https://tutorialedge.net/python/create-rest-api-python-aiohttp/](https://tutorialedge.net/python/create-rest-api-python-aiohttp/)  
3. ChEMBL Database API MCP Server for Chemical Research | MCP, accessed December 21, 2025, [https://www.mcpnow.io/en/server/chembl-jackkuo666-chembl-mcp-server](https://www.mcpnow.io/en/server/chembl-jackkuo666-chembl-mcp-server)  
4. drugbank_mcp.py - kidzik/other-public-mcps - GitHub, accessed December 21, 2025, [https://github.com/kidzik/other-public-mcps/blob/main/drugbank_mcp.py](https://github.com/kidzik/other-public-mcps/blob/main/drugbank_mcp.py)  
5. ID Mapping | UniProt help, accessed December 21, 2025, [https://www.uniprot.org/help/id_mapping](https://www.uniprot.org/help/id_mapping)  
6. Creating Your First MCP Server: A Hello World Guide | by Gianpiero Andrenacci | AI Bistrot | Dec, 2025, accessed December 21, 2025, [https://medium.com/data-bistrot/creating-your-first-mcp-server-a-hello-world-guide-96ac93db363e](https://medium.com/data-bistrot/creating-your-first-mcp-server-a-hello-world-guide-96ac93db363e)  
7. opentargets-archive/opentargets-py: Python client for the ... - GitHub, accessed December 21, 2025, [https://github.com/opentargets-archive/opentargets-py](https://github.com/opentargets-archive/opentargets-py)  
8. How to wrap an async method in python as a normal method? - Stack Overflow, accessed December 21, 2025, [https://stackoverflow.com/questions/76529168/how-to-wrap-an-async-method-in-python-as-a-normal-method](https://stackoverflow.com/questions/76529168/how-to-wrap-an-async-method-in-python-as-a-normal-method)  
9. GraphQL API | Open Targets Platform Documentation, accessed December 21, 2025, [https://platform-docs.opentargets.org/data-access/graphql-api](https://platform-docs.opentargets.org/data-access/graphql-api)  
10. Issue getting data with the GraphQL API using Python - Open Targets Community, accessed December 21, 2025, [https://community.opentargets.org/t/issue-getting-data-with-the-graphql-api-using-python/459](https://community.opentargets.org/t/issue-getting-data-with-the-graphql-api-using-python/459)  
11. chembl/chembl_webresource_client: Official Python client ... - GitHub, accessed December 21, 2025, [https://github.com/chembl/chembl_webresource_client](https://github.com/chembl/chembl_webresource_client)  
12. Asyncio support - python-can 4.6.1 documentation, accessed December 21, 2025, [https://python-can.readthedocs.io/en/stable/asyncio.html](https://python-can.readthedocs.io/en/stable/asyncio.html)  
13. Compare Versions | rcsb-db | PyPI | Open Source Insights, accessed December 21, 2025, [https://deps.dev/pypi/rcsb-db/0.71.0/compare](https://deps.dev/pypi/rcsb-db/0.71.0/compare)  
14. multimeric/Unipressed: Comprehensive Python client for ... - GitHub, accessed December 21, 2025, [https://github.com/multimeric/Unipressed](https://github.com/multimeric/Unipressed)  
15. uniprotparser - PyPI, accessed December 21, 2025, [https://pypi.org/project/uniprotparser/](https://pypi.org/project/uniprotparser/)  
16. Programmatic access | UniProt help, accessed December 21, 2025, [https://www.uniprot.org/help/programmatic_access](https://www.uniprot.org/help/programmatic_access)  
17. PyHGNC · PyPI, accessed December 21, 2025, [https://pypi.org/project/PyHGNC/](https://pypi.org/project/PyHGNC/)  
18. REST web-service help | HUGO Gene Nomenclature Committee, accessed December 21, 2025, [https://www.genenames.org/help/rest/](https://www.genenames.org/help/rest/)  
19. HGNC data archive help | HUGO Gene Nomenclature Committee, accessed December 21, 2025, [https://www.genenames.org/download/archive/](https://www.genenames.org/download/archive/)  
20. Don't worry about DrugBank licensing - write code that knows how to download it automatically, accessed December 21, 2025, [https://github.com/cthoyt/drugbank_downloader](https://github.com/cthoyt/drugbank_downloader)  
21. parsing a drugbank.xml file - python - Stack Overflow, accessed December 21, 2025, [https://stackoverflow.com/questions/30534968/parsing-a-drugbank-xml-file](https://stackoverflow.com/questions/30534968/parsing-a-drugbank-xml-file)  
22. API Reference | DrugBank Help Center, accessed December 21, 2025, [https://docs.drugbank.com/](https://docs.drugbank.com/)  
23. Biolink Model - Bioregistry, accessed December 21, 2025, [https://bioregistry.io/biolink](https://bioregistry.io/biolink)  
24. Symbol report help | HUGO Gene Nomenclature Committee, accessed December 21, 2025, [https://www.genenames.org/help/symbol-report/](https://www.genenames.org/help/symbol-report/)  
25. Batch retrieval & ID mapping | UniProt - EMBL-EBI, accessed December 21, 2025, [https://www.ebi.ac.uk/training/online/courses/uniprot-exploring-protein-sequence-and-functional-info/how-to-use-uniprot-tools-clone/batch-retrieval-id-mapping/](https://www.ebi.ac.uk/training/online/courses/uniprot-exploring-protein-sequence-and-functional-info/how-to-use-uniprot-tools-clone/batch-retrieval-id-mapping/)  
26. cokelaer/bioservices: Access to Biological Web Services from Python. - GitHub, accessed December 21, 2025, [https://github.com/cokelaer/bioservices](https://github.com/cokelaer/bioservices)  
27. MCP Architecture Deep Dive: Tools, Resources, and Prompts Explained - Knit API, accessed December 21, 2025, [https://www.getknit.dev/blog/mcp-architecture-deep-dive-tools-resources-and-prompts-explained](https://www.getknit.dev/blog/mcp-architecture-deep-dive-tools-resources-and-prompts-explained)  
28. Handling Large Datasets with Pagination - GraphAcademy - Neo4j, accessed December 21, 2025, [https://graphacademy.neo4j.com/courses/genai-mcp-build-custom-tools-python/2-database-features/9-pagination/](https://graphacademy.neo4j.com/courses/genai-mcp-build-custom-tools-python/2-database-features/9-pagination/)  
29. Pagination - Model Context Protocol, accessed December 21, 2025, [https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/pagination](https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/pagination)  
30. Extending ResourceLink: Patterns for Large Dataset Processing in MCP Applications - arXiv, accessed December 21, 2025, [https://arxiv.org/html/2510.05968v1](https://arxiv.org/html/2510.05968v1)  
31. Is there a standard reference for bioinformatics MIME types? - Reddit, accessed December 21, 2025, [https://www.reddit.com/r/bioinformatics/comments/8uopwu/is_there_a_standard_reference_for_bioinformatics/](https://www.reddit.com/r/bioinformatics/comments/8uopwu/is_there_a_standard_reference_for_bioinformatics/)  
32. Biolink Model Documentation - GitHub Pages, accessed December 21, 2025, [https://biolink.github.io/biolink-model/](https://biolink.github.io/biolink-model/)  
33. [2203.13906] Biolink Model: A Universal Schema for Knowledge Graphs in Clinical, Biomedical, and Translational Science - arXiv, accessed December 21, 2025, [https://arxiv.org/abs/2203.13906](https://arxiv.org/abs/2203.13906)  
34. Biolink Model: A universal schema for knowledge graphs in clinical, biomedical, and translational science - PubMed Central, accessed December 21, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC9372416/](https://pmc.ncbi.nlm.nih.gov/articles/PMC9372416/)  
35. BioThings Explorer: a query engine for a federated knowledge graph of biomedical APIs | Bioinformatics | Oxford Academic, accessed December 21, 2025, [https://academic.oup.com/bioinformatics/article/39/9/btad570/7273783](https://academic.oup.com/bioinformatics/article/39/9/btad570/7273783)  
36. Frequently Asked Questions - Biolink Model Documentation, accessed December 21, 2025, [https://biolink.github.io/biolink-model/faq/](https://biolink.github.io/biolink-model/faq/)  
37. NCATSTranslator/ReasonerAPI: NCATS Biomedical Translator Reasoners Standard API - GitHub, accessed December 21, 2025, [https://github.com/NCATSTranslator/ReasonerAPI](https://github.com/NCATSTranslator/ReasonerAPI)  
38. ReasonerAPI/docs/reference.md at master - GitHub, accessed December 21, 2025, [https://github.com/NCATSTranslator/ReasonerAPI/blob/master/docs/reference.md](https://github.com/NCATSTranslator/ReasonerAPI/blob/master/docs/reference.md)