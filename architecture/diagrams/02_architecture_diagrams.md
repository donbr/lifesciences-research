# Architecture Diagrams

## System Architecture

```mermaid
graph TB
    %% Color Palette - Semantic Layer Styling
    classDef clientLayer fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#000
    classDef modelLayer fill:#E8F5E9,stroke:#388E3C,stroke-width:2px,color:#000
    classDef serverLayer fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000
    classDef orchestrationLayer fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#000
    classDef apiLayer fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#000

    subgraph CL["CLIENT LAYER"]
        BC[LifeSciencesClient<br/>Base Class]:::clientLayer

        subgraph Gene["Gene/Protein"]
            HGNC[HGNC]:::clientLayer
            UniProt[UniProt]:::clientLayer
            Ensembl[Ensembl]:::clientLayer
            Entrez[Entrez]:::clientLayer
        end

        subgraph Compound["Compound/Drug"]
            ChEMBL[ChEMBL]:::clientLayer
            PubChem[PubChem]:::clientLayer
            DrugBank[DrugBank]:::clientLayer
        end

        subgraph Interaction["Interactions"]
            STRING[STRING]:::clientLayer
            BioGRID[BioGRID]:::clientLayer
        end

        subgraph Target["Target/Pathway"]
            OpenTargets[OpenTargets]:::clientLayer
            IUPHAR[IUPHAR]:::clientLayer
            WikiPathways[WikiPathways]:::clientLayer
        end

        Clinical[ClinicalTrials]:::clientLayer
    end

    subgraph ML["DATA MODEL LAYER"]
        Core["Core Models<br/>(Gene, Protein, Compound)"]:::modelLayer
        Rel["Relationships<br/>(Interaction, Target, Pathway)"]:::modelLayer
        Support["Support<br/>(Envelopes, Provenance, XRefs)"]:::modelLayer
    end

    subgraph SL["SERVER LAYER"]
        GW[Gateway Server<br/>Unified Entry Point]:::serverLayer
        Servers["13 FastMCP Servers<br/>(hgnc.py, uniprot.py, etc.)"]:::serverLayer
    end

    subgraph OL["ORCHESTRATION LAYER"]
        Agg[UnifiedSearch Aggregator<br/>Multi-DB Query + Re-ranking]:::orchestrationLayer
    end

    subgraph AL["EXTERNAL APIs"]
        APIs[HGNC, UniProt, ChEMBL<br/>STRING, Open Targets, etc.]:::apiLayer
    end

    %% Flow connections
    BC -.inherits.-> Gene
    BC -.inherits.-> Compound
    BC -.inherits.-> Interaction
    BC -.inherits.-> Target
    BC -.inherits.-> Clinical

    Gene & Compound & Interaction & Target & Clinical --> Core
    Core & Rel --> Support

    Gene & Compound & Interaction & Target & Clinical --> Servers
    Servers --> GW

    GW --> Agg

    Gene & Compound & Interaction & Target & Clinical -->|HTTP/JSON| APIs
```

### System Architecture Explanation

The Life Sciences Research codebase follows a **4-layer architecture** implementing the Model Context Protocol (MCP):

1. **Client Layer** - 13 specialized API clients that inherit from `LifeSciencesClient` base class
   - All clients provide async HTTP operations with connection pooling
   - Implement rate limiting (10 req/s) with exponential backoff
   - Follow the "Fuzzy-to-Fact" protocol (search → get pattern)

2. **Data Model Layer** - Pydantic models organized by domain
   - Core entity models (Gene, Protein, Compound, Drug, etc.)
   - Relationship models (Interaction, Target, Pathway, Trial)
   - Support models (PaginationEnvelope, ErrorEnvelope, Provenance, CrossReferences)
   - All models enforce CURIE validation and the 22-key cross-reference registry

3. **Server Layer** - FastMCP servers exposing tools for each API
   - Each server provides 2-4 MCP tools (search, get, batch operations)
   - Gateway server composes all 13 servers into a unified endpoint
   - Tools return either PaginationEnvelope<T> or ErrorEnvelope

4. **Orchestration Layer** - Experimental aggregator for multi-database queries
   - UnifiedSearch aggregator coordinates HGNC, UniProt, and Open Targets
   - Implements result re-ranking and entity resolution

---

## Component Relationships

```mermaid
graph LR
    %% Color Palette
    classDef protocol fill:#E3F2FD,stroke:#1976D2,stroke-width:2px
    classDef client fill:#E8F5E9,stroke:#388E3C,stroke-width:2px
    classDef error fill:#FFEBEE,stroke:#C62828,stroke-width:2px
    classDef validation fill:#FFF3E0,stroke:#F57C00,stroke-width:2px
    classDef provenance fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px

    subgraph Protocol["FUZZY-TO-FACT PROTOCOL"]
        Search[1. search_* Tools<br/>Fuzzy Phase]:::protocol
        Get[2. get_* Tools<br/>Fact Phase]:::protocol
        Search -->|Returns| SC[SearchCandidate<br/>CURIE + score]:::protocol
        SC -->|Agent selects| Get
        Get -->|Returns| Entity[Full Entity<br/>+ cross_references]:::protocol
    end

    subgraph Client["CLIENT ARCHITECTURE"]
        Base[LifeSciencesClient]:::client
        Base -->|Provides| Pool[Connection Pool<br/>httpx.AsyncClient]:::client
        Base -->|Provides| RL[Rate Limiting<br/>10 req/s]:::client
        Base -->|Provides| EB[Exponential Backoff<br/>429/503 handling]:::client
    end

    subgraph Error["ERROR HANDLING"]
        ErrEnv[ErrorEnvelope]:::error
        ErrEnv --> Codes["5 Error Codes<br/>UNRESOLVED_ENTITY<br/>ENTITY_NOT_FOUND<br/>AMBIGUOUS_QUERY"]:::error
        ErrEnv --> Hints[Recovery Hints<br/>Agent-actionable]:::error
    end

    subgraph Validation["DATA VALIDATION"]
        Pyd[Pydantic BaseModel]:::validation
        Pyd --> CURIE[CURIE Patterns<br/>HGNC:12345<br/>CHEMBL:25]:::validation
        Pyd --> XRefKeys[22-Key Registry<br/>ensembl_gene<br/>uniprot, chembl]:::validation
    end

    subgraph Prov["PROVENANCE TRACKING"]
        ProvModel[Provenance Model]:::provenance
        ProvModel --> Metadata[Source, Timestamp<br/>CURIE, Version<br/>Confidence]:::provenance
    end
```

### Component Relationships Explanation

**Fuzzy-to-Fact Protocol**:
- All APIs implement a two-phase discovery pattern
- Phase 1: `search_*` tools return lightweight `SearchCandidate` objects with CURIEs and relevance scores
- Phase 2: Agent selects best candidate, calls `get_*` with validated CURIE to retrieve full entity
- This prevents hallucination by forcing CURIE resolution before fact retrieval

**Client Architecture**:
- Base class `LifeSciencesClient` provides shared infrastructure:
  - Async HTTP client with connection pooling (httpx.AsyncClient)
  - Rate limiting with lock-based throttling (10 requests/second)
  - Exponential backoff for 429/503 errors with thundering herd prevention
- 13 specialized clients inherit base functionality and add:
  - API-specific response transformation
  - CURIE format validation (regex patterns)
  - Cross-reference mapping to 22-key registry

**Error Handling**:
- Canonical `ErrorEnvelope` with 5 standard error codes
- Each error includes agent-actionable recovery hints
- Enables self-correcting agent behavior

**Data Validation**:
- All models use Pydantic for runtime validation
- CURIE patterns enforce identifier format consistency
- 22-key cross-reference registry enables cross-database linking
- Omit-if-null pattern (exclude_none=True) reduces token usage

**Provenance Tracking**:
- Optional provenance metadata for data lineage
- Tracks source tool, timestamp, CURIE, API version, and confidence
- Enables reproducibility and citation generation

---

## Class Hierarchies

### Data Model Class Hierarchy

```mermaid
classDiagram
    class BaseModel {
        <<pydantic>>
        +model_dump()
        +model_validate()
    }

    class SearchCandidate {
        +str id
        +str symbol
        +str name
        +float score
    }

    class Gene {
        +str id
        +str symbol
        +str name
        +str status
        +str locus_type
        +str location
        +list~str~ alias_symbols
        +CrossReferences cross_references
        +to_search_candidate()
    }

    class CompoundSearchCandidate {
        +str id
        +str name
        +str molecular_formula
        +float score
    }

    class Compound {
        +str id
        +str name
        +str molecular_formula
        +float molecular_weight
        +str smiles
        +str inchi
        +int max_phase
        +list~str~ indications
        +dict cross_references
        +to_slim()
    }

    class ProteinSearchCandidate {
        +str id
        +str name
        +str organism
        +list~str~ gene_names
        +float score
    }

    class Protein {
        +str id
        +str accession
        +str name
        +str full_name
        +list~str~ gene_names
        +str organism
        +int organism_id
        +str function
        +int sequence_length
        +CrossReferences cross_references
    }

    class CrossReferences {
        +str ensembl_gene
        +list~str~ ensembl_transcript
        +list~str~ uniprot
        +str entrez
        +list~str~ refseq
        +str hgnc
        +str omim
        +str chembl
        +str drugbank
        +str string
        +str biogrid
        +model_dump()
        +omit_empty_values()
    }

    class PaginationEnvelope~T~ {
        +list~T~ items
        +Pagination pagination
        +create()
    }

    class Pagination {
        +str cursor
        +int total_count
        +int page_size
    }

    class ErrorEnvelope {
        +bool success
        +ErrorDetail error
        +unresolved_entity()
        +entity_not_found()
        +ambiguous_query()
        +rate_limited()
        +upstream_error()
    }

    class ErrorDetail {
        +ErrorCode code
        +str message
        +str recovery_hint
        +str invalid_input
    }

    class Provenance {
        +str source
        +datetime timestamp
        +str curie
        +str api_version
        +float confidence_score
        +to_citation_string()
    }

    class MCPClaim {
        +str claim
        +Any value
        +Provenance provenance
        +to_citation_format()
    }

    BaseModel <|-- SearchCandidate
    BaseModel <|-- Gene
    BaseModel <|-- CompoundSearchCandidate
    BaseModel <|-- Compound
    BaseModel <|-- ProteinSearchCandidate
    BaseModel <|-- Protein
    BaseModel <|-- CrossReferences
    BaseModel <|-- PaginationEnvelope
    BaseModel <|-- Pagination
    BaseModel <|-- ErrorEnvelope
    BaseModel <|-- ErrorDetail
    BaseModel <|-- Provenance
    BaseModel <|-- MCPClaim

    Gene --> CrossReferences
    Protein --> CrossReferences
    PaginationEnvelope --> Pagination
    ErrorEnvelope --> ErrorDetail
    MCPClaim --> Provenance
```

### Data Model Class Hierarchy Explanation

The data model layer uses **Pydantic BaseModel** for all entities, providing:
- Runtime type validation
- JSON serialization/deserialization
- Field constraints and validators

**Entity Model Pattern** (Gene, Protein, Compound, Drug, etc.):
- Full entity models contain complete data with cross-references
- SearchCandidate variants provide lightweight representations (~20 tokens)
- All entities have a `id` field containing a validated CURIE
- Cross-references use the shared `CrossReferences` model with 22-key registry

**Envelope Pattern**:
- `PaginationEnvelope<T>` wraps all list/search results with cursor-based pagination
- `ErrorEnvelope` provides canonical error responses with recovery hints
- Generic typing enables type-safe results (e.g., `PaginationEnvelope[SearchCandidate]`)

**Provenance Models**:
- Optional metadata for data lineage tracking
- `Provenance` records source, timestamp, CURIE, API version, and confidence
- `MCPClaim` combines claims with provenance for citation-ready outputs

---

### Client Class Hierarchy

```mermaid
classDiagram
    class LifeSciencesClient {
        <<abstract>>
        +str base_url
        +AsyncClient _client
        +float _timeout
        +int _max_connections
        +_get_client() AsyncClient
        +close() None
        +_get(path, **kwargs) Response
    }

    class HGNCClient {
        +str HGNC_BASE_URL
        +float RATE_LIMIT_DELAY
        +int AMBIGUOUS_THRESHOLD
        +Lock _lock
        +float _last_request_time
        +_rate_limited_get(path) Response
        +search_genes(query, slim, cursor, page_size) PaginationEnvelope|ErrorEnvelope
        +get_gene(hgnc_id) Gene|ErrorEnvelope
        +_search_by_alias(query) list
        +_build_cross_references(doc) CrossReferences
        +__aenter__()
        +__aexit__()
    }

    class ChEMBLClient {
        +str CHEMBL_BASE_URL
        +int RATE_LIMIT_REQUESTS
        +ThreadPoolExecutor _executor
        +Lock _rate_lock
        +_molecule SDK
        +_drug_indication SDK
        +_rate_limited_sdk_call(func) Any
        +_sdk_call_with_backoff(func) Any
        +search_compounds(query, slim, cursor, page_size) PaginationEnvelope|ErrorEnvelope
        +get_compound(chembl_id, slim) dict|ErrorEnvelope
        +get_compounds_batch(chembl_ids, slim) list|ErrorEnvelope
        +_validate_chembl_curie(id) str|ErrorEnvelope
        +_transform_to_compound(result, slim) Compound
        +_build_cross_references(result) dict
    }

    class UniProtClient {
        +str UNIPROT_BASE_URL
        +float RATE_LIMIT_DELAY
        +int MAX_PAGE_SIZE
        +Lock _lock
        +float _last_request_time
        +_rate_limited_get(path, **kwargs) Response
        +search_proteins(query, organism, slim, cursor, page_size) PaginationEnvelope|ErrorEnvelope
        +get_protein(uniprot_id, slim) Protein|ErrorEnvelope
        +_build_cross_references(entry) CrossReferences
        +__aenter__()
        +__aexit__()
    }

    class STRINGClient {
        +str STRING_BASE_URL
        +float RATE_LIMIT_DELAY
        +int DEFAULT_TAXON_ID
        +Lock _lock
        +_rate_limited_get(path, **kwargs) Response
        +search_proteins(query, taxon_id, cursor, page_size) PaginationEnvelope|ErrorEnvelope
        +get_interactions(protein_id, min_score, limit) InteractionNetwork|ErrorEnvelope
        +get_network_image_url(protein_ids, network_type) str|ErrorEnvelope
    }

    class OpenTargetsClient {
        +str OPENTARGETS_BASE_URL
        +Lock _lock
        +search_targets(query, cursor, page_size) PaginationEnvelope|ErrorEnvelope
        +get_target(target_id, slim) Target|ErrorEnvelope
        +get_associations(target_id, disease_id, page_size) list|ErrorEnvelope
    }

    class BioGRIDClient {
        +str BIOGRID_BASE_URL
        +str api_key
        +Lock _lock
        +search_genes(query, organism, cursor, page_size) PaginationEnvelope|ErrorEnvelope
        +get_interactions(gene_id, organism, interaction_type) InteractionResult|ErrorEnvelope
    }

    LifeSciencesClient <|-- HGNCClient
    LifeSciencesClient <|-- ChEMBLClient
    LifeSciencesClient <|-- UniProtClient
    LifeSciencesClient <|-- STRINGClient
    LifeSciencesClient <|-- OpenTargetsClient
    LifeSciencesClient <|-- BioGRIDClient

    note for LifeSciencesClient "Provides:\n- Async HTTP client pool\n- Connection lifecycle\n- Base URL management\n- Common error handling"

    note for HGNCClient "HGNC-specific:\n- Alias boosting\n- CURIE validation\n- Cross-ref mapping\n- Context manager"

    note for ChEMBLClient "ChEMBL-specific:\n- SDK wrapper with run_in_executor\n- Batch operations\n- Thread pool management\n- Indication fetching"

    note for UniProtClient "UniProt-specific:\n- Organism filtering\n- Field selection\n- Pagination via cursor\n- Function extraction"
```

### Client Class Hierarchy Explanation

**Base Class (`LifeSciencesClient`)**:
- Provides shared infrastructure for all API clients
- Manages httpx.AsyncClient lifecycle with connection pooling
- Configurable timeout and max connections
- Base `_get()` method for HTTP GET requests

**Specialized Clients** (13 total):
Each client inherits from `LifeSciencesClient` and adds:

1. **Rate Limiting**: Lock-based throttling (typically 10 req/s)
   - `_rate_limited_get()` enforces minimum delay between requests
   - Exponential backoff for 429/503 errors
   - Thundering herd prevention (re-check timing after acquiring lock)

2. **API-Specific Methods**:
   - `search_*()` - Fuzzy search returning PaginationEnvelope[SearchCandidate]
   - `get_*()` - Strict lookup by CURIE returning full entity or ErrorEnvelope
   - Batch operations (ChEMBL, PubChem)

3. **Response Transformation**:
   - `_transform_to_*()` - Convert API responses to Pydantic models
   - `_build_cross_references()` - Map API xrefs to 22-key registry
   - CURIE validation and normalization

4. **Special Cases**:
   - **ChEMBLClient**: Wraps synchronous SDK with `run_in_executor` and ThreadPoolExecutor
   - **HGNCClient**: Implements alias boosting for common gene symbols (e.g., "p53" → "TP53")
   - **UniProtClient**: Supports organism filtering and field selection
   - **STRINGClient**: Provides network image URL generation

---

## Module Dependencies

```mermaid
graph TB
    %% Color Palette
    classDef models fill:#E8F5E9,stroke:#388E3C,stroke-width:2px
    classDef clients fill:#E3F2FD,stroke:#1976D2,stroke-width:2px
    classDef servers fill:#FFF3E0,stroke:#F57C00,stroke-width:2px
    classDef gateway fill:#FFEBEE,stroke:#C62828,stroke-width:3px
    classDef agent fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px
    classDef external fill:#ECEFF1,stroke:#455A64,stroke-width:2px

    subgraph Models["MODELS LAYER (Foundation)"]
        M_Core["Core Models<br/>(gene.py, protein.py, compound.py)"]:::models
        M_Support["Support Models<br/>(envelopes.py, provenance.py)"]:::models
    end

    subgraph Clients["CLIENTS LAYER"]
        C_Base[base.py<br/>LifeSciencesClient]:::clients
        C_Gene["Gene Clients<br/>(hgnc, uniprot, ensembl, entrez)"]:::clients
        C_Compound["Compound Clients<br/>(chembl, pubchem, drugbank)"]:::clients
        C_Interaction["Interaction Clients<br/>(string, biogrid)"]:::clients
        C_Target["Target Clients<br/>(opentargets, iuphar, wikipathways)"]:::clients
        C_Clinical[clinicaltrials.py]:::clients
    end

    subgraph Servers["SERVERS LAYER"]
        S_Servers["13 FastMCP Servers<br/>(hgnc.py, uniprot.py, etc.)"]:::servers
        S_GW[gateway.py<br/>Unified Composition]:::gateway
    end

    subgraph Agent["ORCHESTRATION LAYER"]
        A_Agg[aggregator.py<br/>Multi-DB Coordinator]:::agent
    end

    subgraph External["EXTERNAL DEPENDENCIES"]
        Pydantic[pydantic]:::external
        HTTPX[httpx]:::external
        FastMCP[fastmcp]:::external
        ChEMBL_SDK[chembl_webresource_client]:::external
    end

    %% Dependencies
    M_Core --> Pydantic
    M_Support --> Pydantic

    C_Base --> HTTPX
    C_Gene & C_Compound & C_Interaction & C_Target & C_Clinical --> C_Base
    C_Gene & C_Compound & C_Interaction & C_Target & C_Clinical --> M_Core
    C_Gene & C_Compound & C_Interaction & C_Target & C_Clinical --> M_Support
    C_Compound --> ChEMBL_SDK

    S_Servers --> C_Gene
    S_Servers --> C_Compound
    S_Servers --> C_Interaction
    S_Servers --> C_Target
    S_Servers --> C_Clinical
    S_Servers --> FastMCP
    S_GW --> S_Servers

    A_Agg --> C_Gene
    A_Agg --> C_Compound
    A_Agg --> C_Target
```

### Module Dependencies Explanation

The codebase is organized into **3 main packages** with clear dependency layers:

**1. models Package** (Foundation Layer):
- **No external package dependencies** (only Pydantic)
- Defines all data structures used throughout the system
- `envelopes.py` provides canonical response formats (PaginationEnvelope, ErrorEnvelope)
- `provenance.py` enables data lineage tracking
- Domain-specific models (gene.py, protein.py, compound.py, etc.)
- `__init__.py` exports all models for easy importing

**2. clients Package** (API Access Layer):
- **Depends on**: models, httpx, external SDKs (chembl_webresource_client)
- `base.py` provides LifeSciencesClient base class (httpx wrapper)
- 13 specialized clients inherit from base and use models for validation
- Each client transforms API responses into Pydantic models
- Clients handle rate limiting, retries, and error mapping
- `__init__.py` exports common clients

**3. servers Package** (MCP Tool Layer):
- **Depends on**: clients, models, fastmcp
- Each server wraps a client with MCP tool decorators
- Thin translation layer: receives MCP calls → delegates to client → returns Pydantic models
- `gateway.py` composes all 13 servers into a unified endpoint using FastMCP mount()
- No business logic (just routing and client delegation)

**4. lifesciences_agent Package** (Orchestration Layer):
- **Depends on**: clients, models
- `aggregator.py` provides UnifiedSearch for multi-database queries
- Coordinates multiple clients (HGNC, UniProt, Open Targets)
- Implements result re-ranking and entity resolution

**Dependency Flow**:
```
External APIs → Clients → Models ← Servers → Gateway
                    ↓
                  Agent (Aggregator)
```

**Key Design Principles**:
1. **Models are independent** - No circular dependencies
2. **Clients depend on models** - For type safety and validation
3. **Servers depend on clients** - Thin wrapper, no duplication
4. **Gateway depends on all servers** - Single composition point
5. **Agent depends on clients** - Direct access for orchestration

---

## Data Flow

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant Gateway as Gateway Server
    participant Server as HGNC Server
    participant Client as HGNCClient
    participant API as HGNC REST API

    Note over Agent,API: Phase 1: Fuzzy Search

    Agent->>Gateway: hgnc_search_genes("p53")
    Gateway->>Server: search_genes("p53")
    Server->>Client: search_genes("p53")

    Client->>Client: Rate limit check<br/>(100ms delay)
    Client->>API: GET /search/alias_symbol/p53
    API-->>Client: 200 OK [{"hgnc_id": "11998", "symbol": "TP53"}]

    Client->>API: GET /search/p53
    API-->>Client: 200 OK [multiple results]

    Client->>Client: Merge & rank results<br/>Alias matches get score=1.0
    Client->>Client: Build SearchCandidates<br/>with CURIEs

    Client-->>Server: PaginationEnvelope[SearchCandidate]<br/>[{id:"HGNC:11998", symbol:"TP53", score:1.0}]
    Server-->>Gateway: PaginationEnvelope[SearchCandidate]
    Gateway-->>Agent: PaginationEnvelope[SearchCandidate]

    Note over Agent: Agent selects best candidate<br/>based on score and context

    Note over Agent,API: Phase 2: Fact Retrieval

    Agent->>Gateway: hgnc_get_gene("HGNC:11998")
    Gateway->>Server: get_gene("HGNC:11998")
    Server->>Client: get_gene("HGNC:11998")

    Client->>Client: Validate CURIE format<br/>HGNC:\d+ pattern
    Client->>Client: Extract numeric ID: 11998

    Client->>Client: Rate limit check
    Client->>API: GET /fetch/hgnc_id/11998
    API-->>Client: 200 OK {gene data with xrefs}

    Client->>Client: Transform to Gene model<br/>Map cross-references<br/>to 22-key registry

    Client-->>Server: Gene{<br/>id:"HGNC:11998",<br/>symbol:"TP53",<br/>cross_references:{<br/>  ensembl_gene:"ENSG00000141510",<br/>  uniprot:["P04637"],<br/>  entrez:"7157"<br/>}<br/>}
    Server-->>Gateway: Gene model
    Gateway-->>Agent: Gene model

    Note over Agent: Agent uses cross-references<br/>to query other databases

    Agent->>Gateway: uniprot_get_protein("UniProtKB:P04637")
    Gateway->>Server: (UniProt flow similar)

    Note over Agent,API: Error Handling Flow

    Agent->>Gateway: hgnc_get_gene("invalid")
    Gateway->>Server: get_gene("invalid")
    Server->>Client: get_gene("invalid")

    Client->>Client: CURIE validation fails
    Client-->>Server: ErrorEnvelope{<br/>code:"UNRESOLVED_ENTITY",<br/>message:"Invalid HGNC CURIE",<br/>recovery_hint:"Call search_genes first"<br/>}
    Server-->>Gateway: ErrorEnvelope
    Gateway-->>Agent: ErrorEnvelope

    Note over Agent: Agent self-corrects:<br/>calls search_genes instead
```

### Data Flow Explanation

The system implements a **two-phase Fuzzy-to-Fact protocol** that prevents hallucination:

**Phase 1: Fuzzy Search** (`search_*` tools)
1. Agent submits natural language query (e.g., "p53")
2. Request flows: Gateway → Server → Client → External API
3. Client performs rate-limited API call (100ms minimum delay)
4. For HGNC: alias search is performed first for boosting common symbols
5. Results are merged and ranked by relevance (alias matches get perfect score)
6. Client transforms API responses to `SearchCandidate` objects with:
   - Validated CURIE (e.g., "HGNC:11998")
   - Display name and metadata
   - Relevance score (0.0-1.0)
7. Response wrapped in `PaginationEnvelope` with cursor for pagination
8. Agent receives ranked candidates and selects best match

**Phase 2: Fact Retrieval** (`get_*` tools)
1. Agent calls `get_*` with validated CURIE from search results
2. Client validates CURIE format using regex pattern
3. Rate-limited API call fetches complete entity
4. Client transforms response to full Pydantic model:
   - Validates all fields
   - Maps cross-references to 22-key registry
   - Omits null/empty values
5. Agent receives complete entity with cross-references
6. Cross-references enable multi-database traversal

**Error Handling Flow**:
1. If agent calls `get_*` with invalid input (raw string instead of CURIE)
2. Client validation fails immediately (no API call)
3. Returns `ErrorEnvelope` with:
   - Error code: `UNRESOLVED_ENTITY`
   - Human-readable message
   - Recovery hint: "Call search_genes to resolve the identifier first"
4. Agent self-corrects by calling search tool

**Cross-Database Navigation**:
1. Agent retrieves Gene from HGNC with cross-references
2. Uses `cross_references.uniprot` to query UniProt for protein data
3. Uses `cross_references.ensembl_gene` to query Ensembl for genomic data
4. Builds complete knowledge graph across 13 databases

**Rate Limiting & Resilience**:
- All clients enforce 10 req/s limit with lock-based throttling
- Exponential backoff for 429/503 errors (1s, 2s, 4s delays)
- Thundering herd prevention: re-check timing after acquiring lock
- Connection pooling reduces overhead for repeated requests

---

## Additional Diagrams

### Cross-Reference Mapping

```mermaid
graph LR
    %% Color Palette
    classDef entity fill:#E3F2FD,stroke:#1976D2,stroke-width:2px
    classDef xref fill:#E8F5E9,stroke:#388E3C,stroke-width:2px
    classDef registry fill:#FFF3E0,stroke:#F57C00,stroke-width:2px

    subgraph Entities["ENTITY MODELS"]
        G[Gene<br/>HGNC:11998]:::entity
        P[Protein<br/>UniProtKB:P04637]:::entity
        C[Compound<br/>CHEMBL:25]:::entity
    end

    subgraph XRefs["CROSS REFERENCES"]
        GX[Gene.cross_references]:::xref
        PX[Protein.cross_references]:::xref
        CX[Compound.cross_references]:::xref
    end

    subgraph Registry["22-KEY REGISTRY"]
        K1[ensembl_gene]:::registry
        K2[uniprot]:::registry
        K3[entrez]:::registry
        K4[hgnc]:::registry
        K5[chembl]:::registry
        K6[drugbank]:::registry
        K7[string]:::registry
        K8[pubchem_compound]:::registry
        K9[pdb]:::registry
        K10[omim]:::registry
        K11[kegg]:::registry
    end

    G --> GX
    P --> PX
    C --> CX

    GX -->|maps to| K2
    GX -->|maps to| K1
    GX -->|maps to| K3
    GX -->|maps to| K10

    PX -->|maps to| K4
    PX -->|maps to| K1
    PX -->|maps to| K9
    PX -->|maps to| K7

    CX -->|maps to| K2
    CX -->|maps to| K5
    CX -->|maps to| K6
    CX -->|maps to| K8
```

### Server-to-Client Mapping

```mermaid
graph LR
    %% Color Palette
    classDef server fill:#FFF3E0,stroke:#F57C00,stroke-width:2px
    classDef client fill:#E3F2FD,stroke:#1976D2,stroke-width:2px

    subgraph Servers["13 MCP SERVERS"]
        S1[hgnc.py]:::server
        S2[uniprot.py]:::server
        S3[chembl.py]:::server
        S4[opentargets.py]:::server
        S5[string.py]:::server
        S6[biogrid.py]:::server
        S7[ensembl.py]:::server
        S8[entrez.py]:::server
        S9[pubchem.py]:::server
        S10[drugbank.py]:::server
        S11[iuphar.py]:::server
        S12[wikipathways.py]:::server
        S13[clinicaltrials.py]:::server
    end

    subgraph Clients["13 API CLIENTS"]
        C1[HGNCClient]:::client
        C2[UniProtClient]:::client
        C3[ChEMBLClient]:::client
        C4[OpenTargetsClient]:::client
        C5[STRINGClient]:::client
        C6[BioGRIDClient]:::client
        C7[EnsemblClient]:::client
        C8[EntrezClient]:::client
        C9[PubChemClient]:::client
        C10[DrugBankClient]:::client
        C11[IUPHARClient]:::client
        C12[WikiPathwaysClient]:::client
        C13[ClinicalTrialsClient]:::client
    end

    S1 -->|1:1| C1
    S2 -->|1:1| C2
    S3 -->|1:1| C3
    S4 -->|1:1| C4
    S5 -->|1:1| C5
    S6 -->|1:1| C6
    S7 -->|1:1| C7
    S8 -->|1:1| C8
    S9 -->|1:1| C9
    S10 -->|1:1| C10
    S11 -->|1:1| C11
    S12 -->|1:1| C12
    S13 -->|1:1| C13
```

---

## Summary

This Life Sciences Research codebase implements a **comprehensive MCP-based architecture** for querying 13 biological databases:

**Key Architectural Features**:
1. **4-Layer Architecture**: Models → Clients → Servers → Gateway
2. **Fuzzy-to-Fact Protocol**: Two-phase search-then-get pattern prevents hallucination
3. **Unified Gateway**: Single entry point composing 13 specialized servers
4. **22-Key Cross-Reference Registry**: Enables cross-database navigation
5. **Canonical Error Handling**: ErrorEnvelope with agent-actionable recovery hints
6. **Rate Limiting & Resilience**: 10 req/s throttling, exponential backoff, connection pooling
7. **Type Safety**: Pydantic models with CURIE validation and field constraints
8. **Provenance Tracking**: Optional metadata for data lineage and citation

**Entity Coverage**:
- Genes (HGNC, Ensembl, Entrez)
- Proteins (UniProt)
- Compounds (ChEMBL, PubChem)
- Drugs (DrugBank)
- Interactions (STRING, BioGRID)
- Targets (Open Targets, IUPHAR)
- Pathways (WikiPathways)
- Clinical Trials (ClinicalTrials.gov)

**Files by Layer**:
- **Models**: 18 files (gene.py, protein.py, compound.py, envelopes.py, etc.)
- **Clients**: 14 files (base.py + 13 specialized clients)
- **Servers**: 14 files (13 servers + gateway.py)
- **Agent**: 1 file (aggregator.py for multi-database orchestration)

The architecture emphasizes **modularity, type safety, and agent-friendly error handling** to enable robust biological entity resolution and knowledge graph construction.
