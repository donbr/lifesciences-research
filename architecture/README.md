# Life Sciences MCP - Repository Architecture Documentation

## Overview

The **Life Sciences MCP (Model Context Protocol)** is a comprehensive biological data integration platform that provides unified access to 13+ life sciences databases through a standardized, agent-friendly API. Built on the FastMCP framework, it implements a sophisticated "Fuzzy-to-Fact" protocol that prevents hallucination by enforcing two-phase entity resolution: fuzzy search returns ranked candidates, followed by strict CURIE-based lookups for complete records.

### What It Is

A production-ready MCP server platform that:
- Integrates 13 major biological databases (HGNC, UniProt, ChEMBL, Ensembl, Open Targets, STRING, BioGRID, Entrez, PubChem, IUPHAR, WikiPathways, ClinicalTrials.gov)
- Exposes 34+ MCP tools through a unified gateway server
- Provides type-safe Pydantic models with comprehensive cross-reference linking
- Implements robust error handling with agent-actionable recovery hints
- Features intelligent rate limiting, connection pooling, and exponential backoff

### Key Features

- **Fuzzy-to-Fact Protocol**: Two-phase workflow prevents agents from using ambiguous identifiers
- **22-Key Cross-Reference Registry**: Navigate seamlessly across databases using standardized identifiers
- **Unified Gateway**: Single deployment endpoint composing all 13 servers without proxy overhead
- **Rate Limiting & Resilience**: 10 req/s throttling, exponential backoff, thundering herd prevention
- **Token Efficiency**: Slim mode reduces responses from ~300 to ~20 tokens per entity
- **Batch Operations**: Single API calls for multiple entities (up to 100 compounds)
- **Comprehensive Error Recovery**: Structured errors with recovery hints for autonomous correction

### Code Statistics

- **13 API clients** (~8,162 lines of code)
- **18 Pydantic model files** (~3,403 lines of code)
- **14 MCP server implementations** (13 operational + 1 gateway)
- **34+ MCP tools** across 13 databases
- **500+ integration tests** with comprehensive coverage
- **22-key cross-reference registry** enabling cross-database navigation

---

## Quick Start

### How to Use This Documentation

This documentation set is organized as a comprehensive reference for understanding and working with the Life Sciences MCP architecture:

1. **Start here (README)** for high-level overview and navigation guide
2. **[Component Inventory](docs/01_component_inventory.md)** for detailed API surface and implementation details
3. **[Architecture Diagrams](diagrams/02_architecture_diagrams.md)** for visual representations of system structure
4. **[Data Flow Analysis](docs/03_data_flows.md)** for understanding request/response patterns
5. **[API Reference](docs/04_api_reference.md)** for complete API documentation with examples

### For Different Audiences

#### Developers
**Start with:**
1. [Component Inventory](docs/01_component_inventory.md) - Understand the codebase structure
2. [API Reference](docs/04_api_reference.md) - Learn the client APIs and data models
3. [Data Flow Analysis](docs/03_data_flows.md#1-fuzzy-to-fact-protocol-flow) - Master the Fuzzy-to-Fact pattern

**Key concepts:**
- Async/await patterns with connection pooling
- Pydantic model validation and serialization
- Error handling with ErrorEnvelope
- Rate limiting with asyncio.Lock

#### Architects
**Start with:**
1. [Architecture Diagrams](diagrams/02_architecture_diagrams.md#system-architecture) - System overview
2. This README's [Architecture at a Glance](#architecture-at-a-glance) section
3. [Data Flow Analysis](docs/03_data_flows.md) - Understanding workflow patterns

**Key concepts:**
- 4-layer architecture (Models → Clients → Servers → Gateway)
- Gateway composition pattern (as_proxy=False)
- Module-level singleton lifecycle
- Cross-reference mapping strategies

#### Contributors
**Start with:**
1. [Component Inventory](docs/01_component_inventory.md#public-api) - Public API surface
2. [API Reference](docs/04_api_reference.md) - Usage patterns and best practices
3. [Data Flow Analysis](docs/03_data_flows.md#2-rate-limited-api-client-flow) - Rate limiting implementation

**Key concepts:**
- Client inheritance from LifeSciencesClient
- Cross-reference building patterns
- CURIE validation with regex patterns
- Batch operation implementation

#### Users
**Start with:**
1. [API Reference](docs/04_api_reference.md#overview) - Getting started with clients
2. [Data Flow Analysis](docs/03_data_flows.md#1-fuzzy-to-fact-protocol-flow) - Understanding the workflow
3. [API Reference](docs/04_api_reference.md#usage-patterns-and-best-practices) - Common use cases

**Key concepts:**
- Fuzzy-to-Fact protocol (search → get)
- Cross-database navigation with cross_references
- Error recovery using recovery hints
- Context manager usage for cleanup

---

## Architecture at a Glance

### System Architecture

The Life Sciences MCP follows a **4-layer architecture** implementing the Model Context Protocol:

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                      │
│  UnifiedSearch Aggregator (Multi-DB queries, re-ranking)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       SERVER LAYER                           │
│  Gateway Server (Unified Entry Point)                       │
│  ├── HGNC Server        ├── STRING Server                   │
│  ├── UniProt Server     ├── BioGRID Server                  │
│  ├── ChEMBL Server      ├── Ensembl Server                  │
│  ├── OpenTargets Server ├── Entrez Server                   │
│  ├── PubChem Server     ├── IUPHAR Server                   │
│  ├── WikiPathways Server└── ClinicalTrials Server           │
│  (34+ MCP Tools)                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                           │
│  13 Specialized API Clients (Inherit from LifeSciencesClient)│
│  - Async HTTP with connection pooling                       │
│  - Rate limiting (10 req/s) + exponential backoff           │
│  - Fuzzy-to-Fact protocol implementation                    │
│  - Cross-reference mapping to 22-key registry               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA MODEL LAYER                        │
│  18 Pydantic Model Files                                    │
│  - Gene, Protein, Compound, Target, Pathway, Trial          │
│  - CrossReferences (22-key registry)                        │
│  - PaginationEnvelope, ErrorEnvelope                        │
│  - Provenance, MCPClaim                                     │
│  (CURIE validation, omit-if-null pattern)                   │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow:**
```
External APIs → Clients → Models ← Servers → Gateway
                    ↓
              Aggregator (Orchestration)
```

### Layer Purposes

1. **Data Model Layer** (Foundation)
   - Pure Pydantic models with no external dependencies
   - CURIE format validation using regex patterns
   - 22-key cross-reference registry for database linking
   - Omit-if-null pattern reduces token usage

2. **Client Layer** (API Access)
   - Async HTTP clients inheriting from `LifeSciencesClient`
   - Rate limiting with lock-based throttling (10 req/s)
   - Exponential backoff for 429/503 errors
   - Response transformation to Pydantic models

3. **Server Layer** (MCP Interface)
   - FastMCP servers exposing tools for each database
   - Thin wrapper: receives MCP calls → delegates to client
   - Gateway composes all 13 servers using direct mounting
   - No business logic (just routing)

4. **Orchestration Layer** (Experimental)
   - UnifiedSearch aggregator for multi-database queries
   - Result re-ranking with heuristics
   - Entity resolution across databases

---

## Key Design Principles

The architecture is built on several foundational patterns that enable robust, scalable biological data integration:

### 1. Fuzzy-to-Fact Protocol

**The Core Pattern:** Two-phase entity resolution prevents agents from hallucinating identifiers.

**Phase 1: Fuzzy Search** (`search_*` tools)
- Input: Natural language query (e.g., "p53", "breast cancer gene")
- Output: Ranked `SearchCandidate` list with validated CURIEs and scores
- Features: Alias boosting, position-based scoring, pagination

**Phase 2: Fact Retrieval** (`get_*` tools)
- Input: Validated CURIE from Phase 1 (e.g., "HGNC:11998")
- Output: Complete entity with all fields and cross-references
- Validation: Strict CURIE format checking before API calls

**Why it matters:** Agents cannot use ambiguous identifiers. They must resolve to a CURIE before accessing facts.

**Example:**
```python
# Phase 1: Fuzzy search
results = await client.search_genes("p53")
# Returns: [{"id": "HGNC:11998", "symbol": "TP53", "score": 1.0}, ...]

# Agent selects best match based on score
top_match = results.items[0].id  # "HGNC:11998"

# Phase 2: Fact retrieval with validated CURIE
gene = await client.get_gene("HGNC:11998")
# Returns: Full Gene object with cross_references
```

**Error Prevention:**
```python
# Agent tries: get_gene("BRCA1") - NO CURIE!
# Result: UNRESOLVED_ENTITY error
# Recovery hint: "Call search_genes to resolve the identifier first."
```

### 2. Rate Limiting Strategies

**Implementation:** Lock-based rate limiting with thundering herd prevention

**Pattern:**
1. Acquire `asyncio.Lock()` for request serialization
2. Check elapsed time since last request
3. If elapsed < RATE_LIMIT_DELAY, sleep remaining time
4. Execute HTTP request
5. Update `_last_request_time`
6. Release lock

**Thundering Herd Prevention:**
```python
async with self._lock:  # Multiple requests queued
    # Re-check timing AFTER acquiring lock
    elapsed = time.time() - self._last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
    # Now safe to proceed
```

**Exponential Backoff:**
- On 429/503 errors: wait = retry_after or 2^attempt seconds
- Sleep OUTSIDE lock to allow other requests to proceed
- Maximum 3 retry attempts (configurable)

**Rate Limits by Database:**
- HGNC, UniProt, ChEMBL, Open Targets: 10 req/s (100ms delay)
- Ensembl: 15 req/s (67ms delay)
- STRING, ClinicalTrials: 1 req/s (1000ms delay)

### 3. Error Recovery Patterns

**Canonical Error Codes:** 5 standardized codes with actionable recovery hints

| Code | Scenario | Recovery Hint |
|------|----------|---------------|
| `UNRESOLVED_ENTITY` | Raw string to get_* | "Call search_genes to resolve identifier first." |
| `ENTITY_NOT_FOUND` | Valid CURIE, no record | "Verify CURIE spelling or try alternate database." |
| `AMBIGUOUS_QUERY` | Query too broad/short | "Refine query with more specific terms." |
| `RATE_LIMITED` | Too many requests | "Retry after 60 seconds." |
| `UPSTREAM_ERROR` | API failure | "HGNC API may be temporarily unavailable. Retry later." |

**Error Envelope Structure:**
```json
{
  "success": false,
  "error": {
    "code": "UNRESOLVED_ENTITY",
    "message": "The input 'brca1' is not a valid HGNC CURIE.",
    "recovery_hint": "Call search_genes to resolve the identifier first.",
    "invalid_input": "brca1"
  }
}
```

**Agent Self-Correction Workflow:**
1. Receive ErrorEnvelope instead of expected data
2. Read `error.recovery_hint` field
3. Parse hint and determine corrective action
4. Call suggested tool with corrected input
5. Succeed with valid data

### 4. Cross-Reference System

**22-Key Registry:** Standardized cross-reference identifiers across all databases

**Core Categories:**

**Gene/Protein:**
- `ensembl_gene`, `ensembl_transcript` (genomic data)
- `uniprot` (protein data)
- `entrez` (NCBI gene database)
- `refseq` (reference sequences)
- `hgnc` (gene nomenclature)

**Disease/Phenotype:**
- `omim` (genetic disorders)
- `orphanet` (rare diseases)
- `mondo` (disease ontology)
- `efo` (experimental factors)

**Drug/Compound:**
- `chembl` (bioactivity)
- `drugbank` (drug data)
- `pubchem_compound`, `pubchem_substance` (chemical data)

**Pathway/Interaction:**
- `kegg`, `kegg_pathway` (metabolic pathways)
- `string` (protein interactions)
- `biogrid` (genetic interactions)
- `iuphar` (pharmacology)

**Structural:**
- `pdb` (3D structures)

**Omit-if-Null Pattern:**
```python
# Keys with no value are excluded from JSON
gene.cross_references.model_dump()
# {"ensembl_gene": "ENSG00000141510", "uniprot": ["P04637"]}
# NOT: {"ensembl_gene": "...", "uniprot": [...], "omim": null, ...}
```

**Cross-Database Navigation:**
```python
# Start with HGNC gene
gene = await hgnc.get_gene("HGNC:11998")

# Navigate to UniProt protein
uniprot_id = f"UniProtKB:{gene.cross_references.uniprot[0]}"
protein = await uniprot.get_protein(uniprot_id)

# Navigate to Ensembl genomics
ensembl_id = gene.cross_references.ensembl_gene
ensembl_gene = await ensembl.get_gene(ensembl_id)

# Navigate to PDB structures
pdb_ids = protein.cross_references.pdb  # ["1TUP", "1TSR", ...]
```

### 5. Slim Mode for Token Efficiency

**Problem:** Full entities can consume 300+ tokens each

**Solution:** Optional `slim=True` parameter reduces to ~20 tokens

**Example:**
```python
# Full mode: ~300 tokens
gene = await client.get_gene("HGNC:11998")
# {id, symbol, name, status, locus_type, location, aliases,
#  prev_symbols, cross_references{22 keys}}

# Slim mode: ~20 tokens
gene = await client.get_gene("HGNC:11998", slim=True)
# {id, symbol, name}
```

**Use Cases:**
- Batch operations (default slim=True)
- Exploratory searches with many candidates
- Building candidate lists for ranking
- Token budget management

### 6. Gateway Composition Pattern

**Direct Mounting (as_proxy=False):** No proxy overhead, direct function calls

**Pattern:**
```python
# Import all server instances
from lifesciences_mcp.servers.hgnc import mcp as hgnc_mcp
from lifesciences_mcp.servers.uniprot import mcp as uniprot_mcp
# ... 11 more

# Create gateway
gateway_mcp = FastMCP("Life Sciences MCP Gateway")

# Mount with direct composition
gateway_mcp.mount(hgnc_mcp, prefix="hgnc", as_proxy=False,
                 tool_names={"search_genes": "hgnc_search_genes",
                            "get_gene": "hgnc_get_gene"})
```

**Benefits:**
- Single deployment artifact
- Shared connection pools per client type
- No serialization overhead between servers
- Unified error handling
- Automatic tool discovery

**Tool Naming:** All tools prefixed with database name to avoid collisions
- `hgnc_search_genes`, `hgnc_get_gene`
- `uniprot_search_proteins`, `uniprot_get_protein`
- `chembl_search_compounds`, `chembl_get_compound`, `chembl_get_compounds_batch`

---

## Component Overview

### Client Layer

**13 Specialized API Clients** inheriting from `LifeSciencesClient` base class

**Base Class Features:**
- Async HTTP client with connection pooling (httpx.AsyncClient)
- Configurable timeout (default: 30s) and max connections (default: 10)
- Lazy initialization: HTTP client created on first request
- Context manager support for automatic cleanup

**Client Implementations:**

1. **HGNCClient** - Gene Nomenclature
   - Alias boosting ("p53" → "TP53")
   - 10 req/s rate limiting
   - 353 lines of code

2. **UniProtClient** - Protein Data
   - Field selection for slim mode
   - Server-side pagination cursors
   - 461 lines of code

3. **ChEMBLClient** - Compound Bioactivity
   - Synchronous SDK wrapped with ThreadPoolExecutor
   - Batch operations (up to 100 compounds)
   - Indication fetching
   - 681 lines of code

4. **OpenTargetsClient** - Target-Disease Associations
   - GraphQL query execution
   - Evidence aggregation
   - Association scoring

5. **STRINGClient** - Protein Interactions
   - Network image URL generation
   - Confidence score filtering
   - 1 req/s rate limiting

6. **BioGRIDClient** - Genetic Interactions
   - Interaction type filtering
   - Organism-specific queries

7. **EnsemblClient** - Genomic Data
   - Species aliasing ("human" → "homo_sapiens")
   - Transcript expansion
   - 15 req/s rate limiting

8. **EntrezClient** - NCBI Gene Database
   - XML parsing with defusedxml
   - PubMed literature links

9. **PubChemClient** - Chemical Compounds
   - Molecular formula search
   - Structure data (SMILES, InChI)

10. **IUPHARClient** - Pharmacology
    - Ligand and target search
    - Receptor/ion channel data

11. **WikiPathwaysClient** - Biological Pathways
    - Pathway component extraction
    - Gene-to-pathway mapping

12. **ClinicalTrialsClient** - Clinical Trials
    - Trial location data
    - Eligibility criteria

13. **DrugBankClient** - Drug Data (Not in Gateway)
    - Requires commercial API key
    - Drug-target interactions

**Common Client Pattern:**
```python
async with ClientClass() as client:
    # Phase 1: Fuzzy search
    results = await client.search_*(query, slim=False, cursor=None, page_size=50)

    # Phase 2: Fact retrieval
    entity = await client.get_*(curie, slim=False)
```

### Data Model Layer

**18 Pydantic Model Files** (~3,403 lines of code)

**Core Entity Models:**

1. **Gene** (gene.py)
   - Fields: id, symbol, name, status, locus_type, location, aliases
   - CrossReferences with 22-key registry
   - CURIE pattern: `HGNC:\d+`

2. **Protein** (protein.py)
   - Fields: id, accession, name, organism, function, sequence_length
   - Gene name mapping
   - CURIE pattern: `UniProtKB:[A-Z][A-Z0-9]{5,9}`

3. **Compound** (compound.py)
   - Fields: id, name, molecular_formula, smiles, inchi, max_phase
   - Indication list (approved uses)
   - CURIE pattern: `CHEMBL:[0-9]+`

4. **Target** (target.py)
   - Fields: id, approved_symbol, biotype, description
   - Association list with scores
   - CURIE pattern: `ENSG\d{11}`

5. **EnsemblGene** (ensembl.py)
   - Fields: id, symbol, chromosome, start, end, strand
   - Transcript list
   - Assembly information

6. **Pathway** (pathway.py)
   - Fields: id, name, organism, description
   - Component counts (genes, metabolites, pathways)

7. **Trial** (trial.py)
   - Fields: nct_id, title, status, phase, sponsor
   - Eligibility criteria
   - Outcome measures

**Search Candidate Models:**
- Lightweight representations (~20 tokens)
- Fields: id, name/symbol, score
- Used in Phase 1 (Fuzzy Search) responses

**Support Models:**

1. **CrossReferences** (gene.py)
   - 22-key registry for database linking
   - Omit-if-null pattern
   - Per-field validation

2. **PaginationEnvelope** (envelopes.py)
   - Generic type: `PaginationEnvelope[T]`
   - Fields: items (list[T]), pagination metadata
   - Cursor-based pagination

3. **ErrorEnvelope** (envelopes.py)
   - Fields: success=False, error (ErrorDetail)
   - Factory methods for each error code
   - Recovery hints for agents

4. **Provenance** (provenance.py)
   - Fields: source, timestamp, curie, api_version, confidence
   - Citation generation
   - Data lineage tracking

### Server Layer

**14 MCP Server Implementations** (13 operational + 1 gateway)

**Server Pattern:**
```python
from fastmcp import FastMCP

mcp = FastMCP("Database Name Server")

# Module-level singleton
_client: ClientClass | None = None

async def get_client() -> ClientClass:
    global _client
    if _client is None:
        _client = ClientClass()
    return _client

@mcp.tool
async def search_*(query: str, ...) -> PaginationEnvelope[SearchCandidate] | ErrorEnvelope:
    client = await get_client()
    return await client.search_*(...)

@mcp.tool
async def get_*(id: str, ...) -> Entity | ErrorEnvelope:
    client = await get_client()
    return await client.get_*(...)
```

**Gateway Server:**
- Composes all 13 servers using `mcp.mount()`
- Direct composition (as_proxy=False)
- Prefixed tool names (e.g., `hgnc_search_genes`)
- Single deployment endpoint
- 112 lines of code

**Individual Servers:**
- 2-4 tools per server
- Thin wrapper over client
- No business logic (just delegation)
- 80-200 lines of code each

**Entry Points:**
```bash
# Individual server
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py

# Gateway server
uv run fastmcp run src/lifesciences_mcp/servers/gateway.py

# FastMCP Cloud deployment
# Entrypoint: src/lifesciences_mcp/servers/gateway.py:mcp
```

### Orchestration Layer

**UnifiedSearch Aggregator** (74 lines of code)

**Purpose:** Experimental multi-database entity resolution

**Features:**
- Coordinates queries across HGNC, UniProt, Open Targets
- Re-ranks results with heuristics:
  - Exact symbol match: +2.0 score
  - Known alias (e.g., "p53" → "TP53"): +2.0 score
- Configurable result limits

**Usage:**
```python
from lifesciences_agent.aggregator import UnifiedSearch

searcher = UnifiedSearch()
results = await searcher.search("p53", limit=10)
# Returns: TP53 first due to alias boosting
```

**Status:** Prototype demonstrating cross-database orchestration patterns

---

## Data Flow Patterns

### Core Workflows

#### 1. Fuzzy-to-Fact Search

**The canonical workflow for entity resolution:**

```
User Query → Agent → MCP Server → Client → External API
                ↓
        SearchCandidate[]
                ↓
Agent selects best match (by score)
                ↓
        Validated CURIE
                ↓
Agent → MCP Server → Client → External API
                ↓
        Complete Entity + CrossReferences
```

**Example:**
```python
# Step 1: Fuzzy search
results = await hgnc.search_genes("BRCA")
# Returns: [
#   {"id": "HGNC:1100", "symbol": "BRCA1", "score": 1.0},
#   {"id": "HGNC:1101", "symbol": "BRCA2", "score": 0.95}
# ]

# Step 2: Agent selects top candidate
curie = results.items[0].id  # "HGNC:1100"

# Step 3: Strict lookup with validated CURIE
gene = await hgnc.get_gene(curie)
# Returns: Full Gene object with all fields and cross_references
```

**Error Handling:**
```python
# Agent tries: get_gene("BRCA1") without CURIE
# → UNRESOLVED_ENTITY error
# → recovery_hint: "Call search_genes to resolve identifier first."
# → Agent corrects by calling search_genes first
```

#### 2. Cross-Database Navigation

**Workflow:**
```
Gene (HGNC)
  → cross_references.uniprot
    → Protein (UniProt)
      → cross_references.pdb
        → 3D Structures (PDB)
      → cross_references.ensembl_gene
        → Genomic Data (Ensembl)
```

**Example:**
```python
# Start with gene
gene = await hgnc.get_gene("HGNC:11998")  # TP53

# Navigate to protein
uniprot_id = f"UniProtKB:{gene.cross_references.uniprot[0]}"
protein = await uniprot.get_protein(uniprot_id)  # P04637

# Navigate to structures
pdb_ids = protein.cross_references.pdb  # ["1TUP", "1TSR", ...]

# Navigate to genomic data
ensembl_id = gene.cross_references.ensembl_gene
ensembl_gene = await ensembl.get_gene(ensembl_id)  # ENSG00000141510

# Navigate to interactions
string_id = protein.cross_references.string
interactions = await string_client.get_interactions(string_id)
```

#### 3. Batch Operations

**Workflow:**
```
Search → Extract CURIEs → Batch Lookup
  ↓           ↓              ↓
  50 results  10 CURIEs     1 API call (vs 10)
```

**Example:**
```python
# Step 1: Search to get candidates
results = await chembl.search_compounds("kinase inhibitor", page_size=20)

# Step 2: Extract CURIEs
chembl_ids = [c.id for c in results.items[:10]]

# Step 3: Batch lookup (single API call)
compounds = await chembl.get_compounds_batch(chembl_ids, slim=True)
# Returns: 10 compounds in ~1s (vs 10s for individual lookups)
```

**Benefits:**
- Reduces API calls by 10-100x
- Prevents thread pool exhaustion
- Token efficiency with slim mode
- Handles individual failures gracefully

#### 4. Error Recovery

**Workflow:**
```
Request → ErrorEnvelope
            ↓
  error.recovery_hint
            ↓
Agent corrects action
            ↓
  Retry with fix → Success
```

**Example:**
```python
# Attempt 1: Invalid input
result = await hgnc.get_gene("brca1")  # No CURIE prefix!
# → ErrorEnvelope: UNRESOLVED_ENTITY
# → recovery_hint: "Call search_genes to resolve identifier first."

# Agent corrects
search_result = await hgnc.search_genes("brca1")
curie = search_result.items[0].id  # "HGNC:1100"

# Attempt 2: Correct input
gene = await hgnc.get_gene(curie)  # SUCCESS
```

### Integration Patterns

**Pattern 1: Gene-to-Drug Discovery**
```
Disease (Open Targets)
  → Associated Genes
    → Gene Details (HGNC)
      → Protein (UniProt)
        → Interactions (STRING)
          → Compounds (ChEMBL)
            → Clinical Trials (ClinicalTrials.gov)
```

**Pattern 2: Structure-Function Analysis**
```
Gene Symbol
  → Gene (HGNC)
    → Protein (UniProt)
      → Structures (PDB via cross_references)
        → Function Analysis
          → Pathway Membership (WikiPathways)
```

**Pattern 3: Pharmacology Research**
```
Compound (ChEMBL)
  → Target Proteins
    → Genes (via cross_references)
      → Disease Associations (Open Targets)
        → Clinical Evidence (ClinicalTrials)
```

---

## Key Features and Capabilities

### Database Coverage

**13 Integrated Databases:**

1. **HGNC** - HUGO Gene Nomenclature Committee
   - Authoritative gene symbols and names
   - Cross-references to 22 external databases
   - ~42,000 approved human genes

2. **UniProt** - Universal Protein Resource
   - Protein sequences and annotations
   - Functional descriptions
   - ~560,000 reviewed proteins (Swiss-Prot)

3. **ChEMBL** - Bioactivity Database
   - Compound structures and bioactivity
   - Drug development phases
   - Therapeutic indications
   - ~2.3M compounds

4. **Open Targets** - Target-Disease Associations
   - Evidence-based associations
   - Genetic, literature, and clinical evidence
   - ~60,000 targets × ~20,000 diseases

5. **STRING** - Protein-Protein Interactions
   - Known and predicted interactions
   - Evidence scores (experimental, database, text mining)
   - Network visualization

6. **BioGRID** - Biological General Repository
   - Genetic and protein interactions
   - Manually curated data
   - ~2.5M interactions

7. **Ensembl** - Genome Databases
   - Gene and transcript annotations
   - Cross-species genomic data
   - Genome assemblies and variants

8. **Entrez** - NCBI Gene Database
   - Gene summaries and literature
   - PubMed links
   - Model organism data

9. **PubChem** - Chemical Information
   - Compound and substance records
   - Molecular structures
   - Bioassay data
   - ~110M compounds

10. **IUPHAR/GtoPdb** - Pharmacology
    - Receptor and ion channel data
    - Ligand-target interactions
    - Quantitative pharmacology

11. **WikiPathways** - Biological Pathways
    - Curated pathway models
    - Gene-pathway associations
    - Pathway components

12. **ClinicalTrials.gov** - Clinical Trials
    - Trial protocols and status
    - Eligibility criteria
    - Outcome measures
    - ~450,000 trials

13. **DrugBank** - Drug Data (Requires API Key)
    - Comprehensive drug information
    - Drug-target interactions
    - Pharmacokinetics

### API Capabilities

**Search Operations:**
- Fuzzy matching with ranking
- Pagination with cursors
- Organism filtering (Ensembl, BioGRID)
- Field-specific search (UniProt, ChEMBL)

**Lookup Operations:**
- CURIE-based retrieval
- Slim mode for token efficiency
- Batch operations (ChEMBL: up to 100)
- Cross-reference expansion

**Specialized Operations:**
- Target-disease associations (Open Targets)
- Protein-protein interactions (STRING)
- Network visualization URLs (STRING)
- Pathway components (WikiPathways)
- Trial locations (ClinicalTrials)
- PubMed literature links (Entrez)

**Data Formats:**
- JSON (primary)
- GraphQL (Open Targets)
- XML (Entrez with defusedxml)

### Performance Optimizations

**Rate Limiting:**
- Lock-based throttling (10 req/s typical)
- Exponential backoff on 429/503 errors
- Thundering herd prevention
- Configurable retry limits

**Batch Operations:**
- Single API call for 100 compounds
- Reduces latency by 10-100x
- Token efficiency with slim mode
- Individual failure handling

**Slim Mode:**
- Reduces tokens from ~300 to ~20
- Optional per request
- Default for batch operations
- Excludes cross_references, synonyms, detailed fields

**Connection Pooling:**
- Shared httpx.AsyncClient per client
- Max 10 concurrent connections (configurable)
- Keep-alive connection reuse
- Lazy initialization

**Cursor-Based Pagination:**
- Opaque cursors (no offset math)
- Server-side pagination (UniProt)
- Client-side slicing (HGNC, ChEMBL)
- Configurable page sizes (1-500)

### Reliability Features

**Error Handling:**
- 5 canonical error codes
- Actionable recovery hints
- Error type detection (4xx vs 5xx)
- Invalid input tracking

**Validation:**
- CURIE format validation (regex patterns)
- Query length checks (min 2 chars)
- Batch size limits (max 100)
- Field constraints (Pydantic)

**Retry Logic:**
- Exponential backoff (1s, 2s, 4s)
- Retry-After header respect
- Maximum 3 attempts
- Per-client configuration

**Cleanup:**
- Async context manager support
- Automatic connection closing
- Thread pool shutdown (ChEMBL)
- Module-level singleton lifecycle

---

## Technical Highlights

### Technology Stack

**Core Dependencies:**
- **Python 3.10+** - Async/await, type hints
- **Pydantic 2.x** - Data validation and serialization
- **httpx** - Async HTTP client with connection pooling
- **FastMCP** - MCP server framework
- **asyncio** - Async runtime and concurrency primitives

**API SDKs:**
- **chembl_webresource_client** - ChEMBL SDK (wrapped with ThreadPoolExecutor)

**Security:**
- **defusedxml** - Secure XML parsing (Entrez)

**Development/Testing:**
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **python-dotenv** - Environment variable loading

### Design Patterns

**Singleton Pattern:**
- Module-level client instances
- Lazy initialization on first request
- Shared across all tool invocations
- No cleanup hooks needed (FastMCP managed)

**Repository Pattern:**
- Each client acts as repository for a database
- Standardized search/get operations
- Consistent error handling
- Transaction-like semantics (async context managers)

**Factory Pattern:**
- `PaginationEnvelope.create()` factory method
- `ErrorEnvelope.*()` class methods for each error code
- Consistent envelope construction

**Strategy Pattern:**
- Rate limiting strategies vary by client (1-15 req/s)
- Pagination strategies (server-side vs client-side)
- Error mapping strategies per API

**Builder Pattern:**
- `_build_cross_references()` methods in each client
- Complex object construction from API responses
- Field mapping and normalization

**Adapter Pattern:**
- ChEMBLClient adapts synchronous SDK to async interface
- ThreadPoolExecutor wrapper for SDK calls
- Consistent API despite underlying differences

**Gateway Pattern:**
- Gateway server composes multiple services
- Direct mounting (as_proxy=False)
- Unified interface, no proxy overhead

### Code Quality

**Lines of Code:**
- Clients: ~8,162 lines
- Models: ~3,403 lines
- Servers: ~1,800 lines
- Total source: ~13,365 lines

**Type Safety:**
- 100% type hints in public APIs
- Pydantic runtime validation
- MyPy-compatible type annotations
- Generic types (PaginationEnvelope[T])

**Validation:**
- CURIE format validation (regex patterns)
- Field constraints (min/max, patterns)
- Model validators (omit-if-null)
- Enum-based error codes

**Test Coverage:**
- 500+ integration tests
- 100+ unit tests
- End-to-end workflow tests
- Error recovery test suite

**Documentation:**
- Comprehensive docstrings
- Type hints for IDE support
- Architectural Decision Records (ADRs)
- This architecture documentation set

---

## Documentation Index

### Component Documentation

**[Component Inventory](docs/01_component_inventory.md)** (912 lines)

Comprehensive catalog of all modules, classes, and functions:

- **Public API Surface:**
  - 13 client classes with method signatures
  - 18 data model files with field definitions
  - 14 server implementations with tool lists
  - Entry points and deployment configurations

- **Internal Implementation:**
  - Rate limiting patterns
  - Cross-reference mapping functions
  - Error handling utilities
  - Pagination cursor encoding
  - XML parsing (Entrez)

- **Module Dependencies:**
  - Dependency graph visualization
  - External dependencies (httpx, pydantic, fastmcp)
  - Cross-module patterns

- **Architecture Patterns:**
  - Async-first design
  - Repository pattern
  - Gateway pattern
  - Factory pattern
  - Strategy pattern

**Key Sections:**
- Lines 20-553: Public Client Classes
- Lines 307-525: Public Data Models
- Lines 547-567: Public Aggregator
- Lines 570-683: Internal Implementation
- Lines 703-872: Entry Points

### Architecture Documentation

**[Architecture Diagrams](diagrams/02_architecture_diagrams.md)** (1,091 lines)

Visual representations of system structure:

- **System Architecture** (Lines 1-178):
  - 4-layer architecture diagram
  - Client/model/server/gateway relationships
  - Inheritance hierarchies
  - External API connections

- **Component Relationships** (Lines 207-294):
  - Fuzzy-to-Fact protocol flow
  - Client architecture patterns
  - Error handling flow
  - Data validation flow
  - Provenance tracking

- **Class Hierarchies** (Lines 296-612):
  - Data model class diagram (Gene, Protein, Compound, etc.)
  - Client class diagram (LifeSciencesClient + 13 specialized)
  - Envelope pattern (PaginationEnvelope, ErrorEnvelope)

- **Module Dependencies** (Lines 614-816):
  - Package dependency graph
  - External dependencies
  - Dependency flow (External APIs → Clients → Models ← Servers → Gateway)

- **Data Flow Diagram** (Lines 818-936):
  - Phase 1: Fuzzy search sequence
  - Phase 2: Fact retrieval sequence
  - Error handling sequence
  - Cross-database navigation

- **Additional Diagrams** (Lines 939-1057):
  - Cross-reference mapping (22-key registry)
  - Server-to-client 1:1 mapping

**Key Diagrams:**
- System Architecture (mermaid graph TB)
- Component Relationships (mermaid graph LR)
- Class Hierarchies (mermaid classDiagram)
- Data Flow (mermaid sequenceDiagram)

### Data Flow Documentation

**[Data Flow Analysis](docs/03_data_flows.md)** (1,740 lines)

Detailed sequence diagrams showing request/response patterns:

- **Fuzzy-to-Fact Protocol** (Lines 20-122):
  - Phase 1: Fuzzy search with alias boosting
  - Phase 2: Strict CURIE-based lookup
  - Score calculation (1.0 for exact, 0.95-0.1 for position)
  - CURIE validation and error handling

- **Rate-Limited API Client** (Lines 124-265):
  - Lock acquisition and timing checks
  - Thundering herd prevention
  - Exponential backoff on 429/503
  - SDK wrapping pattern (ChEMBL)
  - Request 1 vs Request 2 concurrency

- **Error Recovery Flow** (Lines 267-460):
  - UNRESOLVED_ENTITY scenario (raw string → search → get)
  - AMBIGUOUS_QUERY scenario (query too short → refine)
  - RATE_LIMITED scenario (429 → backoff → retry)
  - Agent self-correction workflow

- **Gateway Composition** (Lines 462-646):
  - Server import and mounting
  - Direct composition (as_proxy=False)
  - Tool naming convention (prefix with database)
  - Lifecycle: cold start → lazy init → reuse

- **Batch Operations** (Lines 648-841):
  - 10 compounds in 1 API call vs 10 calls
  - CURIE validation and mapping
  - Result ordering preservation
  - Slim mode for token efficiency

- **Cross-Database Navigation** (Lines 843-1075):
  - Gene → Protein → Compound → Target workflow
  - 22-key registry usage
  - Cross-reference building examples
  - Navigation patterns (5 examples)

- **Aggregated Search** (Lines 1077-1298):
  - UnifiedSearch multi-database query
  - Re-ranking with heuristics
  - Alias boosting ("p53" → TP53)
  - Experimental aggregator patterns

- **Session Lifecycle** (Lines 1300-1607):
  - Module-level singleton pattern
  - Lazy HTTP client initialization
  - Connection pool benefits
  - Shutdown handling (FastMCP internal)

**Key Flows:**
- Lines 20-122: Fuzzy-to-Fact complete flow
- Lines 124-212: Rate limiting with concurrency
- Lines 267-378: Error recovery (3 scenarios)
- Lines 462-544: Gateway request routing
- Lines 650-739: Batch vs individual comparison

### API Documentation

**[API Reference](docs/04_api_reference.md)** (2,186 lines)

Complete API documentation with usage examples:

- **Client APIs** (Lines 22-835):
  - LifeSciencesClient base class
  - HGNCClient (search_genes, get_gene)
  - UniProtClient (search_proteins, get_protein)
  - EnsemblClient (search_genes, get_gene, get_transcript)
  - ChEMBLClient (search_compounds, get_compound, get_compounds_batch)
  - OpenTargetsClient (search_targets, get_target, get_associations)
  - 7 more specialized clients

- **Data Models** (Lines 837-1267):
  - Gene, SearchCandidate, CrossReferences
  - Protein, ProteinSearchCandidate
  - Compound, CompoundSearchCandidate
  - Target, Association
  - EnsemblGene, EnsemblTranscript
  - PaginationEnvelope, ErrorEnvelope
  - Field definitions, validation rules, examples

- **Server APIs** (Lines 1440-1640):
  - Gateway server (34+ tools)
  - HGNC server (search_genes, get_gene)
  - Individual server patterns
  - Configuration and deployment

- **Orchestration APIs** (Lines 1642-1718):
  - UnifiedSearch aggregator
  - Multi-database search with re-ranking

- **Utility Functions** (Lines 1720-1806):
  - Cross-reference mapping utilities
  - Error handling patterns
  - Rate limiting strategies

- **Configuration Reference** (Lines 1808-1884):
  - Environment variables
  - Rate limiting configuration
  - Pagination configuration

- **Usage Patterns** (Lines 1886-2076):
  - Pattern 1: Fuzzy-to-Fact search
  - Pattern 2: Cross-database navigation
  - Pattern 3: Batch operations
  - Pattern 4: Error recovery

- **Appendix** (Lines 2078-2186):
  - Type definitions
  - Error codes table
  - CURIE formats table
  - Source file reference

**Key Sections:**
- Lines 113-226: HGNCClient complete reference
- Lines 1270-1437: Envelope models (PaginationEnvelope, ErrorEnvelope)
- Lines 1444-1571: Gateway server (all 34+ tools)
- Lines 1890-2076: Usage patterns with examples

---

## Getting Started with the Codebase

### Understanding the Architecture

**Step-by-step guide for new developers:**

**Step 1: High-Level Overview**
1. Read this README's [Architecture at a Glance](#architecture-at-a-glance) section
2. Review [Architecture Diagrams](diagrams/02_architecture_diagrams.md#system-architecture) for visual structure
3. Understand the 4 layers: Models → Clients → Servers → Gateway

**Step 2: Core Concepts**
1. Study [Fuzzy-to-Fact Protocol](#1-fuzzy-to-fact-protocol) in this README
2. Read [Data Flow Analysis](docs/03_data_flows.md#1-fuzzy-to-fact-protocol-flow) for detailed sequence
3. Practice with example: search_genes → get_gene

**Step 3: API Exploration**
1. Review [API Reference](docs/04_api_reference.md) for client documentation
2. Study [Component Inventory](docs/01_component_inventory.md#public-api) for complete API surface
3. Examine [Data Models](docs/04_api_reference.md#data-models) for entity structures

**Step 4: Implementation Details**
1. Read [Rate Limiting Strategy](#2-rate-limiting-strategies) in this README
2. Review [Error Recovery Patterns](#3-error-recovery-patterns)
3. Examine [Cross-Reference System](#4-cross-reference-system)

**Step 5: Hands-On Practice**
1. Clone repository and install dependencies
2. Run individual server: `uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py`
3. Test Fuzzy-to-Fact workflow with HGNC client
4. Explore cross-database navigation

### Common Use Cases

**Use Case 1: Gene Resolution**
```python
from lifesciences_mcp.clients import HGNCClient

async with HGNCClient() as client:
    # Fuzzy search
    results = await client.search_genes("BRCA1")

    # Get full record
    gene = await client.get_gene(results.items[0].id)
    print(f"{gene.symbol}: {gene.name}")
    print(f"Location: {gene.location}")
```

**Documentation:**
- [HGNCClient API Reference](docs/04_api_reference.md#hgncclient)
- [Fuzzy-to-Fact Flow](docs/03_data_flows.md#1-fuzzy-to-fact-protocol-flow)
- [Gene Model](docs/04_api_reference.md#gene)

**Use Case 2: Cross-Database Navigation**
```python
from lifesciences_mcp.clients import HGNCClient, UniProtClient

async with HGNCClient() as hgnc, UniProtClient() as uniprot:
    # Get gene
    gene = await hgnc.get_gene("HGNC:11998")

    # Navigate to protein
    uniprot_id = f"UniProtKB:{gene.cross_references.uniprot[0]}"
    protein = await uniprot.get_protein(uniprot_id)
    print(f"Function: {protein.function}")
```

**Documentation:**
- [Cross-Database Navigation](docs/03_data_flows.md#6-cross-database-navigation-flow)
- [CrossReferences Model](docs/04_api_reference.md#crossreferences)
- [Pattern 2: Cross-Database Navigation](docs/04_api_reference.md#pattern-2-cross-database-navigation)

**Use Case 3: Batch Compound Lookup**
```python
from lifesciences_mcp.clients import ChEMBLClient

client = ChEMBLClient()
try:
    # Search to get CURIEs
    results = await client.search_compounds("kinase inhibitor")
    ids = [c.id for c in results.items[:10]]

    # Batch lookup
    compounds = await client.get_compounds_batch(ids, slim=True)
    for compound in compounds:
        print(f"{compound['name']}: Phase {compound.get('max_phase')}")
finally:
    await client.close()
```

**Documentation:**
- [Batch Operations Flow](docs/03_data_flows.md#5-batch-operations-flow)
- [ChEMBLClient.get_compounds_batch()](docs/04_api_reference.md#get_compounds_batch)
- [Pattern 3: Batch Operations](docs/04_api_reference.md#pattern-3-batch-operations)

**Use Case 4: Error Recovery**
```python
from lifesciences_mcp.clients import HGNCClient
from lifesciences_mcp.models import ErrorEnvelope, ErrorCode

async with HGNCClient() as client:
    result = await client.get_gene("brca1")  # Invalid format

    if isinstance(result, ErrorEnvelope):
        if result.error.code == ErrorCode.UNRESOLVED_ENTITY:
            # Recover by calling search
            search_result = await client.search_genes("brca1")
            gene = await client.get_gene(search_result.items[0].id)
```

**Documentation:**
- [Error Recovery Flow](docs/03_data_flows.md#3-error-recovery-flow)
- [ErrorEnvelope API](docs/04_api_reference.md#errorenvelope)
- [Pattern 4: Error Recovery](docs/04_api_reference.md#pattern-4-error-recovery)

### Contributing

**How to use these docs when contributing:**

**Adding a New Client:**
1. Review [LifeSciencesClient](docs/04_api_reference.md#lifesciencesclient-base-class) base class
2. Study existing client (e.g., [HGNCClient](docs/01_component_inventory.md#hgncclient---gene-nomenclature))
3. Implement:
   - `search_*()` method (Phase 1)
   - `get_*()` method (Phase 2)
   - `_build_cross_references()` mapping
   - Rate limiting (10 req/s default)
4. Add tests following [test patterns](docs/04_api_reference.md#error-handling)

**Adding a New Data Model:**
1. Review [Data Model Layer](docs/01_component_inventory.md#public-data-models)
2. Inherit from Pydantic BaseModel
3. Add CURIE validation pattern
4. Implement omit-if-null pattern
5. Add to `models/__init__.py` exports
6. Document in [API Reference](docs/04_api_reference.md#data-models)

**Adding a New Server:**
1. Review [Server Pattern](docs/01_component_inventory.md#mcp-server-entry-points)
2. Create FastMCP instance
3. Implement module-level singleton
4. Add @mcp.tool decorators
5. Mount in [Gateway](docs/04_api_reference.md#gateway-server)
6. Test individually before gateway integration

**Updating Documentation:**
1. Update [Component Inventory](docs/01_component_inventory.md) for new components
2. Add diagrams to [Architecture Diagrams](diagrams/02_architecture_diagrams.md) if needed
3. Document data flows in [Data Flow Analysis](docs/03_data_flows.md)
4. Add API docs to [API Reference](docs/04_api_reference.md)
5. Update this README if architectural patterns change

---

## Architecture Metrics

### Component Counts

- **Databases:** 13 integrated (12 operational + 1 requires API key)
- **API Clients:** 13 specialized clients
- **Data Models:** 18 Pydantic model files
- **MCP Servers:** 14 implementations (13 individual + 1 gateway)
- **MCP Tools:** 34+ tools across all databases
- **Cross-Reference Keys:** 22-key standardized registry

### Code Volume

- **Client Layer:** ~8,162 lines of code
- **Model Layer:** ~3,403 lines of code
- **Server Layer:** ~1,800 lines of code
- **Total Source Code:** ~13,365 lines (excluding tests)
- **Test Code:** 600+ test cases

### Database Coverage

**Biological Entities:**
- Genes: ~42,000 (HGNC) + millions (Ensembl, Entrez)
- Proteins: ~560,000 reviewed (UniProt)
- Compounds: ~2.3M (ChEMBL) + ~110M (PubChem)
- Trials: ~450,000 (ClinicalTrials.gov)
- Interactions: ~2.5M (BioGRID) + billions (STRING)
- Pathways: ~3,000 (WikiPathways)
- Targets: ~60,000 (Open Targets)

**Cross-References:**
- 22-key registry per entity
- Average 3-8 cross-references per gene
- Average 5-12 cross-references per protein
- Enables navigation across all 13 databases

### Performance Characteristics

**Rate Limits:**
- 10 requests/second: HGNC, UniProt, ChEMBL, Open Targets
- 15 requests/second: Ensembl
- 1 request/second: STRING, ClinicalTrials

**Response Times (typical):**
- Search operations: 100-500ms
- Get operations: 50-200ms
- Batch operations: 500-1500ms (100 entities)

**Token Budgets:**
- Full mode: 115-300 tokens per entity
- Slim mode: ~20 tokens per entity
- SearchCandidate: ~20 tokens
- ErrorEnvelope: ~40 tokens

**Batch Efficiency:**
- Single compound: ~1s (10 rate limit)
- 10 compounds (individual): ~10s
- 10 compounds (batch): ~1s (10x faster)
- 100 compounds (batch): ~2s (50x faster)

---

## Next Steps

### For New Developers

**Recommended Reading Order:**

1. **Week 1: Foundations**
   - Day 1-2: This README (overview and key concepts)
   - Day 3-4: [Architecture Diagrams](diagrams/02_architecture_diagrams.md) (visual understanding)
   - Day 5: Hands-on: Run HGNC server and test Fuzzy-to-Fact

2. **Week 2: Deep Dive**
   - Day 1-2: [Component Inventory](docs/01_component_inventory.md) (public APIs)
   - Day 3-4: [API Reference](docs/04_api_reference.md) (clients and models)
   - Day 5: Hands-on: Implement cross-database navigation

3. **Week 3: Advanced Topics**
   - Day 1-2: [Data Flow Analysis](docs/03_data_flows.md) (all 8 flows)
   - Day 3-4: Study rate limiting and error recovery implementations
   - Day 5: Hands-on: Build batch operation workflow

4. **Week 4: Mastery**
   - Day 1-2: Review all ADRs (Architectural Decision Records)
   - Day 3-4: Study test suite patterns
   - Day 5: Contribute first feature or fix

### For System Integration

**Key Documentation for Integration:**

1. **Gateway Deployment:**
   - [Gateway Server](docs/04_api_reference.md#gateway-server)
   - [Gateway Composition Flow](docs/03_data_flows.md#4-gateway-server-composition-flow)
   - Entry point: `src/lifesciences_mcp/servers/gateway.py:mcp`

2. **MCP Protocol:**
   - [Server Layer Overview](docs/01_component_inventory.md#primary-entry-points)
   - [Tool Naming Conventions](docs/04_api_reference.md#available-tools)
   - FastMCP documentation: https://github.com/jlowin/fastmcp

3. **Error Handling:**
   - [ErrorEnvelope API](docs/04_api_reference.md#errorenvelope)
   - [Error Recovery Flow](docs/03_data_flows.md#3-error-recovery-flow)
   - [Error Codes Reference](docs/04_api_reference.md#error-codes)

4. **Data Models:**
   - [All Models](docs/04_api_reference.md#data-models)
   - [CrossReferences](docs/04_api_reference.md#crossreferences)
   - [PaginationEnvelope](docs/04_api_reference.md#paginationenvelope)

### For Performance Optimization

**Relevant Performance Documentation:**

1. **Rate Limiting:**
   - [Rate Limiting Strategy](#2-rate-limiting-strategies)
   - [Rate-Limited Client Flow](docs/03_data_flows.md#2-rate-limited-api-client-flow)
   - [Configuration Reference](docs/04_api_reference.md#rate-limiting-configuration)

2. **Batch Operations:**
   - [Batch Operations Flow](docs/03_data_flows.md#5-batch-operations-flow)
   - [ChEMBLClient.get_compounds_batch()](docs/04_api_reference.md#get_compounds_batch)
   - [Pattern 3: Batch Operations](docs/04_api_reference.md#pattern-3-batch-operations)

3. **Token Efficiency:**
   - [Slim Mode](#5-slim-mode-for-token-efficiency)
   - [Slim Mode Usage](docs/04_api_reference.md#pattern-1-fuzzy-to-fact-search)

4. **Connection Pooling:**
   - [Session Lifecycle](docs/03_data_flows.md#8-session-lifecycle-and-connection-management)
   - [LifeSciencesClient](docs/04_api_reference.md#lifesciencesclient-base-class)

---

## Additional Resources

### Source Code Files

**Entry Points:**
- Gateway: `src/lifesciences_mcp/servers/gateway.py`
- Individual servers: `src/lifesciences_mcp/servers/*.py`

**Client Implementations:**
- Base: `src/lifesciences_mcp/clients/base.py`
- HGNC: `src/lifesciences_mcp/clients/hgnc.py`
- UniProt: `src/lifesciences_mcp/clients/uniprot.py`
- ChEMBL: `src/lifesciences_mcp/clients/chembl.py`
- [See full list](docs/04_api_reference.md#source-file-reference)

**Data Models:**
- Gene: `src/lifesciences_mcp/models/gene.py`
- Protein: `src/lifesciences_mcp/models/protein.py`
- Envelopes: `src/lifesciences_mcp/models/envelopes.py`
- [See full list](docs/04_api_reference.md#model-files)

**Orchestration:**
- Aggregator: `src/lifesciences_agent/aggregator.py`

**Tests:**
- Integration: `tests/integration/`
- Unit: `tests/unit/`
- E2E: `tests/e2e/`

### External Documentation

**Database APIs:**
- HGNC: https://www.genenames.org/help/rest/
- UniProt: https://www.uniprot.org/help/api
- ChEMBL: https://chembl.gitbook.io/chembl-interface-documentation/web-services
- Ensembl: https://rest.ensembl.org/
- Open Targets: https://platform-docs.opentargets.org/data-access/graphql-api

**Frameworks:**
- FastMCP: https://github.com/jlowin/fastmcp
- Pydantic: https://docs.pydantic.dev/
- httpx: https://www.python-httpx.org/

**Standards:**
- CURIE Format: https://www.w3.org/TR/curie/
- Model Context Protocol: https://modelcontextprotocol.io/

---

## Summary

The **Life Sciences MCP** is a production-ready biological data integration platform that provides:

- **Unified Access:** 13 databases through a single gateway with 34+ MCP tools
- **Agent-Friendly:** Fuzzy-to-Fact protocol prevents hallucination
- **Type-Safe:** Pydantic models with comprehensive validation
- **Robust:** Error recovery with actionable hints for autonomous agents
- **Performant:** Rate limiting, batch operations, connection pooling, slim mode
- **Navigable:** 22-key cross-reference registry for seamless database traversal

**Architecture Highlights:**
- 4-layer design (Models → Clients → Servers → Gateway)
- ~13,365 lines of production code
- 600+ test cases with comprehensive coverage
- Async-first with connection pooling and rate limiting
- Gateway composition without proxy overhead

**Use This Documentation:**
- **Start here** for architecture overview
- **[Component Inventory](docs/01_component_inventory.md)** for detailed API surface
- **[Architecture Diagrams](diagrams/02_architecture_diagrams.md)** for visual understanding
- **[Data Flow Analysis](docs/03_data_flows.md)** for workflow patterns
- **[API Reference](docs/04_api_reference.md)** for complete API documentation

**Get Started:**
```bash
# Run gateway server
uv run fastmcp run src/lifesciences_mcp/servers/gateway.py

# Or individual server
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
```

**Questions or Issues:**
- Review the appropriate documentation section
- Check [API Reference](docs/04_api_reference.md#usage-patterns-and-best-practices) for usage patterns
- Examine test suite for examples

---

**Document Version:** 1.0
**Last Updated:** 2026-01-07
**Repository:** lifesciences-research
**Commit:** 4308911 (initial commit)
