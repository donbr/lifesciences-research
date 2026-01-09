# Component Inventory

## Overview

The Life Sciences MCP (Model Context Protocol) project is a comprehensive FastMCP-based system that provides unified access to 13 major life sciences databases through a standardized API. The project implements the "Fuzzy-to-Fact" protocol for entity resolution and follows the Agentic Biolink schema for cross-references.

**Project Structure:**
```
lifesciences-research/
├── src/lifesciences_mcp/          # Main package (50 Python files)
│   ├── clients/                    # API client implementations (15 files)
│   ├── models/                     # Pydantic data models (18 files)
│   └── servers/                    # FastMCP server definitions (15 files)
├── scripts/                        # Demonstration and validation scripts (5 files)
├── tests/                          # Test suite (116 files)
└── tools/                          # Compliance auditing (1 file)
```

**Architecture Pattern:**
- **3-Layer Architecture**: Clients (data access) → Models (data structures) → Servers (MCP endpoints)
- **Protocol**: JSON-RPC 2.0 over HTTP using FastMCP framework
- **Deployment**: FastMCP Cloud gateway at https://lifesciences-research.fastmcp.app/mcp

---

## Public API

### Main Package Module

#### `src/lifesciences_mcp/__init__.py` (Lines 1-99)
**Purpose**: Package entry point exposing public API surface

**Public Exports:**
- **Version**: `__version__ = "0.1.0"`
- **13 Client Classes**: ChEMBLClient, ClinicalTrialsClient, DrugBankClient, HGNCClient, IUPHARClient, etc.
- **18 Model Classes**: Compound, Gene, Protein, PubChemCompound, ErrorEnvelope, PaginationEnvelope, etc.

**Usage Documentation**: Includes command-line examples for running each server via `uv run fastmcp run`

---

### Public Client Classes

All clients inherit from `LifeSciencesClient` base class and implement the Fuzzy-to-Fact protocol with two core operations:
1. **search_X**: Fuzzy search returning ranked candidates with pagination
2. **get_X**: Strict lookup by validated CURIE identifier

#### `src/lifesciences_mcp/clients/base.py` (Lines 16-77)

**Class: `LifeSciencesClient`** (Lines 16-77)
- **Purpose**: Base async HTTP client with connection pooling and lifecycle management
- **Public Methods**:
  - `__init__(base_url, timeout=30.0, max_connections=10)` (Lines 23-39)
  - `close()` (Lines 67-71) - Cleanup HTTP client

**Key Features**:
- Async httpx client with granular timeout configuration (connect: 5s, read: 30s, write: 10s, pool: 5s)
- Connection pooling with configurable limits
- Standard Accept header for JSON responses

---

#### `src/lifesciences_mcp/clients/hgnc.py` (Lines 29-353)

**Class: `HGNCClient`** (Lines 29-353)
- **Purpose**: HGNC Gene Nomenclature Committee API client for gene symbol resolution
- **Base URL**: https://rest.genenames.org
- **Rate Limit**: 10 requests/second (100ms delay)

**Public Methods**:
  - `__init__()` (Lines 46-50)
  - `search_genes(query, slim=False, cursor=None, page_size=50)` (Lines 110-248)
    - Returns: `PaginationEnvelope[SearchCandidate] | ErrorEnvelope`
    - Features: Alias boosting, position-based scoring, ambiguity detection
  - `get_gene(hgnc_id)` (Lines 273-332)
    - Returns: `Gene | ErrorEnvelope`
    - Validates CURIE format (HGNC:NNNNN)

**Key Features**:
- Context manager support (`async with`)
- Exponential backoff on 429/403/503 errors (max 3 retries)
- Alias search with score boosting (aliases get score=1.0)
- Client-side pagination (HGNC doesn't support server-side)

---

#### `src/lifesciences_mcp/clients/chembl.py` (Lines 40-681)

**Class: `ChEMBLClient`** (Lines 40-681)
- **Purpose**: ChEMBL bioactivity database client for compound and drug data
- **Base URL**: https://www.ebi.ac.uk/chembl/api/data
- **Rate Limit**: 10 requests/second with exponential backoff
- **SDK**: Uses synchronous `chembl_webresource_client` wrapped with `run_in_executor`

**Public Methods**:
  - `__init__()` (Lines 71-86)
  - `search_compounds(query, slim=False, cursor=None, page_size=50)` (Lines 453-517)
    - Returns: `PaginationEnvelope[CompoundSearchCandidate] | ErrorEnvelope`
  - `get_compound(chembl_id, slim=False)` (Lines 519-586)
    - Returns: `dict[str, Any] | ErrorEnvelope`
    - Fetches drug indications (separate API call) unless slim=True
  - `get_compounds_batch(chembl_ids, slim=True)` (Lines 588-673)
    - Max 100 compounds per batch
    - Returns: `list[dict[str, Any]] | ErrorEnvelope`

**Key Features**:
- ThreadPoolExecutor for wrapping synchronous SDK
- Cross-reference mapping to 22-key registry (UniProt, PDB, PubChem, DrugBank)
- CURIE validation pattern: `^CHEMBL:[0-9]+$`
- Slim mode for token efficiency (~20 tokens per entity)

---

#### `src/lifesciences_mcp/clients/uniprot.py` (Lines 29-353)

**Class: `UniProtClient`** (Lines 29-353)
- **Purpose**: UniProt protein database client
- **Base URL**: https://rest.uniprot.org
- **Rate Limit**: 10 requests/second (conservative estimate)

**Public Methods**:
  - `__init__()` (Lines 49-53)
  - `search_proteins(query, organism=None, slim=False, cursor=None, page_size=50)` (Lines ~110-250)
    - Returns: `PaginationEnvelope[ProteinSearchCandidate] | ErrorEnvelope`
  - `get_protein(uniprot_id)` (Lines ~270-330)
    - Returns: `Protein | ErrorEnvelope`
    - Validates UniProt accession format

---

#### `src/lifesciences_mcp/clients/opentargets.py`

**Class: `OpenTargetsClient`**
- **Purpose**: Open Targets Platform for target-disease associations
- **Base URL**: https://api.platform.opentargets.org/api/v4

**Public Methods**:
  - `search_targets(query, ...)`
  - `get_target(target_id)`
  - `get_associations(target_id, disease_id=None, ...)`

---

#### `src/lifesciences_mcp/clients/string.py` (Lines 36-450)

**Class: `STRINGClient`** (Lines 36-450)
- **Purpose**: STRING database for protein-protein interaction networks
- **Base URL**: https://string-db.org/api
- **Rate Limit**: 1 request/second (strict)

**Public Methods**:
  - `__init__(species=9606)` (Lines 54-63) - Default: Homo sapiens
  - `search_proteins(query, limit=10, ...)` (Lines ~120-200)
    - Returns: `PaginationEnvelope[InteractionSearchCandidate] | ErrorEnvelope`
  - `get_interactions(string_id, score_threshold=400, limit=100)` (Lines ~220-320)
    - Returns: `InteractionNetwork | ErrorEnvelope`
    - Score threshold: 400 = medium confidence (0-1000 scale)
  - `get_network_image_url(string_ids, network_flavor="evidence")` (Lines ~340-400)
    - Returns: `str` (URL to network visualization)

---

#### `src/lifesciences_mcp/clients/biogrid.py`

**Class: `BioGridClient`**
- **Purpose**: BioGRID genetic and protein interaction database
- **Requires**: Free API key (BIOGRID_API_KEY environment variable)

**Public Methods**:
  - `search_genes(symbol, ...)`
  - `get_interactions(gene_symbol, max_results=100, ...)`

---

#### `src/lifesciences_mcp/clients/entrez.py`

**Class: `EntrezClient`**
- **Purpose**: NCBI Entrez/Gene database
- **Requires**: NCBI API key (optional but recommended)

**Public Methods**:
  - `search_genes(query, ...)`
  - `get_gene(ncbi_gene_id)`
  - `get_pubmed_links(ncbi_gene_id, ...)`

---

#### `src/lifesciences_mcp/clients/ensembl.py`

**Class: `EnsemblClient`**
- **Purpose**: Ensembl genomic database (genes, transcripts)

**Public Methods**:
  - `search_genes(query, species="human", ...)`
  - `get_gene(ensembl_id)`
  - `get_transcript(transcript_id)`

---

#### `src/lifesciences_mcp/clients/pubchem.py`

**Class: `PubChemClient`**
- **Purpose**: PubChem chemical compound database

**Public Methods**:
  - `search_compounds(query, ...)`
  - `get_compound(pubchem_cid)`
  - `get_compound_synonyms(pubchem_cid, ...)`

---

#### `src/lifesciences_mcp/clients/iuphar.py`

**Class: `IUPHARClient`**
- **Purpose**: IUPHAR/Guide to Pharmacology for ligands and targets

**Public Methods**:
  - `search_ligands(query, ...)`
  - `get_ligand(iuphar_id)`
  - `search_targets(query, ...)`
  - `get_target(target_id)`

---

#### `src/lifesciences_mcp/clients/wikipathways.py`

**Class: `WikiPathwaysClient`**
- **Purpose**: WikiPathways biological pathway database

**Public Methods**:
  - `search_pathways(query, organism="Homo sapiens", ...)`
  - `get_pathway(pathway_id)`
  - `get_pathways_for_gene(gene_symbol, ...)`
  - `get_pathway_components(pathway_id)`

---

#### `src/lifesciences_mcp/clients/clinicaltrials.py`

**Class: `ClinicalTrialsClient`**
- **Purpose**: ClinicalTrials.gov clinical study database

**Public Methods**:
  - `search_trials(query, condition=None, status=None, phase=None, ...)`
  - `get_trial(nct_id)`
  - `get_trial_locations(nct_id)`

---

#### `src/lifesciences_mcp/clients/drugbank.py`

**Class: `DrugBankClient`**
- **Purpose**: DrugBank drug database
- **Requires**: Commercial API key (DRUGBANK_API_KEY)
- **Note**: Excluded from gateway server due to commercial licensing

**Public Methods**:
  - `search_drugs(query, ...)`
  - `get_drug(drugbank_id)`

---

### Public Model Classes

All models are Pydantic v2 BaseModel subclasses with validation and serialization.

#### `src/lifesciences_mcp/models/envelopes.py` (Lines 1-145)

**Purpose**: Canonical response envelopes per ADR-001 Section 8

**Class: `ErrorCode`** (Lines 16-25) - Enum
- **Values**: UNRESOLVED_ENTITY, ENTITY_NOT_FOUND, AMBIGUOUS_QUERY, RATE_LIMITED, UPSTREAM_ERROR, INVALID_CROSS_REFERENCE

**Class: `ErrorDetail`** (Lines 27-34)
- **Fields**: code, message, recovery_hint, invalid_input
- **Purpose**: Structured error information with agent-actionable guidance

**Class: `ErrorEnvelope`** (Lines 36-108)
- **Fields**: success (always False), error (ErrorDetail)
- **Factory Methods**:
  - `unresolved_entity(invalid_input)` (Lines 47-56)
  - `entity_not_found(hgnc_id)` (Lines 58-68)
  - `ambiguous_query(query, result_count)` (Lines 70-80)
  - `rate_limited(retry_after=None)` (Lines 82-94)
  - `upstream_error(status_code, detail=None)` (Lines 96-108)

**Class: `Pagination`** (Lines 111-117)
- **Fields**: cursor (opaque, None = end), total_count, page_size

**Class: `PaginationEnvelope[T]`** (Lines 119-145) - Generic
- **Fields**: items (list[T]), pagination (Pagination)
- **Factory Method**: `create(items, cursor=None, total_count=None, page_size=50)` (Lines 128-144)

---

#### `src/lifesciences_mcp/models/gene.py` (Lines 1-215)

**Purpose**: Gene models for HGNC following Agentic Biolink schema

**Constants**:
- `HGNC_CURIE_PATTERN = re.compile(r"^HGNC:\d+$")` (Line 12)

**Class: `CrossReferences`** (Lines 27-143)
- **Purpose**: External database identifiers (22-key registry)
- **Fields** (all optional, omitted if None):
  - Core: ensembl_gene, ensembl_transcript, uniprot, entrez, refseq, hgnc
  - Disease: omim, orphanet, mondo, efo
  - Drug/Compound: chembl, drugbank, pubchem_compound, pubchem_substance
  - Pathway: kegg, kegg_pathway
  - Interaction: string, biogrid, stitch, iuphar
  - Structural: pdb
- **Method**: `model_dump(**kwargs)` (Lines 139-142) - Excludes None values

**Class: `SearchCandidate`** (Lines 145-164)
- **Fields**: id (HGNC CURIE), symbol, name, score (0.0-1.0)
- **Validation**: HGNC CURIE format enforced (Lines 156-163)

**Class: `Gene`** (Lines 166-215)
- **Fields**: id, symbol, name, status, locus_type, locus_group, location, alias_symbols, alias_names, prev_symbols, prev_names, cross_references
- **Validation**:
  - HGNC CURIE format (Lines 188-195)
  - Status enum (Approved, Withdrawn, Entry Withdrawn) (Lines 197-205)
- **Method**: `to_search_candidate(score=1.0)` (Lines 207-215)

---

#### `src/lifesciences_mcp/models/protein.py`

**Class: `ProteinSearchCandidate`**
- **Fields**: id (UniProt accession), name, gene_names, organism, score

**Class: `Protein`**
- **Fields**: id, accession, name, gene_names, organism, sequence_length, mass, function, subcellular_location, cross_references

---

#### `src/lifesciences_mcp/models/compound.py`

**Class: `CompoundSearchCandidate`**
- **Fields**: id (ChEMBL CURIE), name, molecular_formula, score

**Class: `Compound`**
- **Fields**: id, name, molecular_formula, molecular_weight, smiles, inchi, canonical_name, max_phase, indications, synonyms, cross_references
- **Method**: `to_slim()` - Returns minimal dict for token efficiency

---

#### `src/lifesciences_mcp/models/interaction.py`

**Constants**:
- `STRING_CURIE_PATTERN = re.compile(r"^9606\.[A-Z0-9]+$")` - Human STRING IDs

**Class: `EvidenceScores`**
- **Fields**: neighborhood, fusion, cooccurrence, coexpression, experimental, database, textmining, combined_score

**Class: `InteractionSearchCandidate`**
- **Fields**: id, preferred_name, protein_size, annotation, score

**Class: `Interaction`**
- **Fields**: protein_a, protein_b, preferred_name_a, preferred_name_b, score, evidence_scores

**Class: `InteractionCrossReferences`**
- **Fields**: string_ids, uniprot_ids, ensembl_genes

**Class: `InteractionNetwork`**
- **Fields**: query_protein_id, interactions, cross_references

---

#### `src/lifesciences_mcp/models/target.py`

**Class: `TargetSearchCandidate`**
- **Fields**: id (Ensembl), approved_symbol, approved_name, score

**Class: `Association`**
- **Fields**: disease_id, disease_name, therapeutic_area, score, datasource_count

**Class: `Target`**
- **Fields**: id, approved_symbol, approved_name, biotype, description, go_terms, tractability, associations

---

#### `src/lifesciences_mcp/models/pharmacology.py`

**Class: `LigandSearchCandidate`**
- **Fields**: id (IUPHAR:NNNN), name, type, approved, score

**Class: `Ligand`**
- **Fields**: id, ligand_id, name, approved_name, type, approved, approval_source, synonyms, cross_references

**Class: `Target`** (pharmacological)
- **Fields**: id, target_id, name, target_family, family_ids, species, gene_symbol, cross_references

**Class: `TargetSearchCandidate`**
- **Fields**: id, name, family, type, score

---

#### `src/lifesciences_mcp/models/pathway.py`

**Class: `PathwaySearchCandidate`**
- **Fields**: id (WP:NNNNN), title, organism, score

**Class: `ComponentCounts`**
- **Fields**: gene_count, metabolite_count, interaction_count, pathway_count

**Class: `RevisionMetadata`**
- **Fields**: revision, last_modified, author

**Class: `Pathway`**
- **Fields**: id, title, organism, description, url, component_counts, revision_metadata

---

#### `src/lifesciences_mcp/models/pathway_components.py`

**Class: `DataNode`**
- **Fields**: id, name, type, database, identifier

**Class: `Interaction`** (pathway)
- **Fields**: id, source_id, target_id, interaction_type

**Class: `PathwayComponents`**
- **Fields**: pathway_id, genes, metabolites, interactions

---

#### `src/lifesciences_mcp/models/trial.py`

**Class: `TrialSearchCandidate`**
- **Fields**: id (NCT number), title, status, phase, score

**Class: `Sponsor`**
- **Fields**: lead_sponsor, collaborators

**Class: `EligibilityCriteria`**
- **Fields**: min_age, max_age, sex, accepts_healthy_volunteers

**Class: `Outcome`**
- **Fields**: type, measure, time_frame, description

**Class: `TrialProtocol`**
- **Fields**: allocation, intervention_model, masking, primary_purpose

**Class: `Trial`**
- **Fields**: id, title, official_title, status, phase, enrollment, start_date, completion_date, last_update, conditions, interventions, sponsor, eligibility, outcomes, protocol, study_url

---

#### `src/lifesciences_mcp/models/trial_location.py`

**Class: `TrialLocation`**
- **Fields**: facility_name, city, state, zip_code, country, recruitment_status, contact_name, contact_phone, contact_email

---

#### Additional Model Files

**`src/lifesciences_mcp/models/drug.py`**: Drug, DrugSearchCandidate, DrugCrossReferences

**`src/lifesciences_mcp/models/entrez.py`**: EntrezGene, EntrezCrossReferences, GeneSearchCandidate, NCBI_GENE_CURIE_PATTERN

**`src/lifesciences_mcp/models/ensembl.py`**: EnsemblGene, EnsemblTranscript, EnsemblCrossReferences, GeneSearchCandidate

**`src/lifesciences_mcp/models/biogrid.py`**: GeneticInteraction, InteractionResult, BioGridCrossReferences, BioGridSearchCandidate

**`src/lifesciences_mcp/models/pubchem_compound.py`**: PubChemCompound, PubChemSearchCandidate, PUBCHEM_CURIE_PATTERN

**`src/lifesciences_mcp/models/provenance.py`**: Provenance, Source, ProvenanceMetadata

---

### Public Server Entry Points

All servers are FastMCP applications exposing MCP tools via JSON-RPC 2.0.

#### `src/lifesciences_mcp/servers/gateway.py` (Lines 1-116)

**Purpose**: Unified gateway server composing all 13 individual servers

**Entry Point**: `mcp = FastMCP("Life Sciences MCP Gateway")` (Line 49)

**Mounted Servers** (Lines 52-109):
- hgnc: hgnc_search_genes, hgnc_get_gene
- uniprot: uniprot_search_proteins, uniprot_get_protein
- chembl: chembl_search_compounds, chembl_get_compound, chembl_get_compounds_batch
- opentargets: opentargets_search_targets, opentargets_get_target, opentargets_get_associations
- string: string_search_proteins, string_get_interactions, string_get_network_image_url
- biogrid: biogrid_search_genes, biogrid_get_interactions
- ensembl: ensembl_search_genes, ensembl_get_gene, ensembl_get_transcript
- entrez: entrez_search_genes, entrez_get_gene, entrez_get_pubmed_links
- pubchem: pubchem_search_compounds, pubchem_get_compound
- iuphar: iuphar_search_targets, iuphar_get_target, iuphar_search_ligands, iuphar_get_ligand
- wikipathways: wikipathways_search_pathways, wikipathways_get_pathway, wikipathways_get_pathways_for_gene, wikipathways_get_pathway_components
- clinicaltrials: clinicaltrials_search_trials, clinicaltrials_get_trial, clinicaltrials_get_trial_locations

**Main**: `if __name__ == "__main__": mcp.run()` (Lines 114-115)

**Deployment**: FastMCP Cloud entrypoint at `src/lifesciences_mcp/servers/gateway.py:mcp`

**Note**: DrugBank excluded (requires commercial API key)

---

#### `src/lifesciences_mcp/servers/hgnc.py` (Lines 1-86)

**Entry Point**: `mcp = FastMCP("HGNC Gene Server")` (Line 22)

**Tools** (decorated with `@mcp.tool`):
1. `search_genes(query, slim=False, cursor=None, page_size=50)` (Lines 36-64)
   - Returns: `PaginationEnvelope[SearchCandidate] | ErrorEnvelope`
2. `get_gene(hgnc_id)` (Lines 67-81)
   - Returns: `Gene | ErrorEnvelope`

**Shared Client**: `_client: HGNCClient | None = None` (Line 25) with lazy initialization (Lines 28-33)

**Main**: `if __name__ == "__main__": mcp.run()` (Lines 84-85)

---

#### Individual Server Files

All follow the same pattern as HGNC server:

**`src/lifesciences_mcp/servers/uniprot.py`**: uniprot_mcp with search_proteins, get_protein

**`src/lifesciences_mcp/servers/chembl.py`**: chembl_mcp with search_compounds, get_compound, get_compounds_batch

**`src/lifesciences_mcp/servers/opentargets.py`**: opentargets_mcp with search_targets, get_target, get_associations

**`src/lifesciences_mcp/servers/string.py`**: string_mcp with search_proteins, get_interactions, get_network_image_url

**`src/lifesciences_mcp/servers/biogrid.py`**: biogrid_mcp with search_genes, get_interactions

**`src/lifesciences_mcp/servers/ensembl.py`**: ensembl_mcp with search_genes, get_gene, get_transcript

**`src/lifesciences_mcp/servers/entrez.py`**: entrez_mcp with search_genes, get_gene, get_pubmed_links

**`src/lifesciences_mcp/servers/pubchem.py`**: pubchem_mcp with search_compounds, get_compound

**`src/lifesciences_mcp/servers/iuphar.py`**: iuphar_mcp with search_ligands, get_ligand, search_targets, get_target

**`src/lifesciences_mcp/servers/wikipathways.py`**: wikipathways_mcp with search_pathways, get_pathway, get_pathways_for_gene, get_pathway_components

**`src/lifesciences_mcp/servers/clinicaltrials.py`**: clinicaltrials_mcp with search_trials, get_trial, get_trial_locations

**`src/lifesciences_mcp/servers/drugbank.py`**: drugbank_mcp with search_drugs, get_drug (excluded from gateway)

---

### Public Scripts

#### `scripts/showcase_nsclc_v2_fastmcp.py` (Lines 1-428)

**Purpose**: Demonstration script showcasing two NSCLC research scenarios using MCP protocol

**Entry Point**: `if __name__ == "__main__": asyncio.run(main())` (Lines 426-427)

**Main Function**: `main()` (Lines 401-424)

**Scenarios**:
1. `run_kras_scenario_enhanced(mcp)` (Lines 155-270) - KRAS targeting with WikiPathways
2. `run_alk_scenario_enhanced(mcp)` (Lines 272-399) - EML4-ALK fusion with ClinicalTrials

**Class: `MCPClient`** (Lines 48-121)
- **Purpose**: Simple MCP JSON-RPC 2.0 client over HTTP
- **Methods**:
  - `call_tool(tool_name, arguments)` (Lines 56-117)
  - `close()` (Lines 119-121)

**Endpoint**: Configurable via `FASTMCP_CLOUD_ENDPOINT` environment variable (default: https://lifesciences-research.fastmcp.app/mcp)

---

#### `scripts/showcase_nsclc_v2_mcp.py`

**Purpose**: Alternative MCP showcase using native MCP protocol (not FastMCP HTTP)

---

#### `scripts/showcase_graph_construction.py`

**Purpose**: Demonstrates graph construction from MCP data

---

#### `scripts/verify_chembl_v2.py`

**Purpose**: Validation script for ChEMBL client implementation

---

#### `scripts/verify_swi_snf.py`

**Purpose**: Validation script for SWI/SNF complex data retrieval

---

## Internal Implementation

### Internal Helper Modules

#### `src/lifesciences_mcp/clients/__init__.py` (Lines 1-55)

**Purpose**: Package-level imports and re-exports for clients
- Imports all 14 client classes
- Exports via `__all__` list (Lines 39-54)

---

#### `src/lifesciences_mcp/models/__init__.py` (Lines 1-140)

**Purpose**: Package-level imports and re-exports for models
- Imports all model classes and constants
- Exports via `__all__` list (Lines 83-139)
- Includes CURIE patterns: NCBI_GENE_CURIE_PATTERN, PUBCHEM_CURIE_PATTERN

---

#### `src/lifesciences_mcp/servers/__init__.py` (Lines 1-2)

**Purpose**: Empty module (servers are independent FastMCP applications)

---

#### `src/lifesciences_mcp/tools/__init__.py` (Lines 1)

**Purpose**: Empty module (tools directory reserved for future use)

---

### Internal Client Methods

All clients implement common internal patterns:

#### Rate Limiting (Pattern shared across all clients)

**`_rate_limited_get(path, **kwargs)`** - Present in all clients
- **Purpose**: Enforces rate limits with thundering herd prevention
- **Implementation**:
  - Acquires async lock
  - Checks elapsed time since last request
  - Sleeps if needed to maintain rate limit
  - Makes HTTP request
  - Updates last request timestamp

**Example**: `HGNCClient._rate_limited_get()` (Lines 62-108)

---

#### Exponential Backoff (Pattern in most clients)

**Purpose**: Retry logic for 429 (rate limited) and 5xx errors

**Example**: `ChEMBLClient._sdk_call_with_backoff()` (Lines 125-168)
- Retries up to MAX_RETRIES (typically 3)
- Delay: min(BASE_DELAY * 2^attempt, MAX_DELAY)
- Respects Retry-After header if present

---

#### Cross-Reference Mapping

**`_build_cross_references(doc)`** - Present in clients that return cross-references

**Purpose**: Map upstream API response to standardized 22-key registry

**Example**: `HGNCClient._build_cross_references()` (Lines 333-344)
- Extracts cross-reference fields from API response
- Normalizes to CURIE format where applicable
- Omits None/empty values (ADR-001 principle)

---

#### CURIE Validation

**`_validate_*_curie(id)`** - Present in clients with strict CURIE requirements

**Purpose**: Validate identifier format before API call

**Example**: `ChEMBLClient._validate_chembl_curie()` (Lines 170-189)
- Regex validation against CURIE pattern
- Returns numeric ID or ErrorEnvelope
- Prevents invalid API calls

---

#### SDK Wrapping (ChEMBL-specific)

**`_rate_limited_sdk_call(sdk_func)`** (Lines 94-123)
- **Purpose**: Wrap synchronous SDK calls with async rate limiting
- **Implementation**: Uses `loop.run_in_executor()` with ThreadPoolExecutor

**`_get_executor()`** (Lines 87-92)
- **Purpose**: Lazy initialization of thread pool
- **Implementation**: Python default thread count (min(32, CPU+4))

---

#### Cursor Encoding/Decoding (Pagination)

**`_encode_cursor(offset)` / `_decode_cursor(cursor)`**

**Purpose**: Base64 encoding of pagination state

**Example**: `ChEMBLClient._encode_cursor()` (Lines 438-441), `_decode_cursor()` (Lines 443-451)
- Encodes: `{"offset": N}` → Base64 string
- Decodes: Base64 string → offset integer

---

#### Error Mapping

**`_map_sdk_error(error, input_value=None)`**

**Purpose**: Convert API/SDK exceptions to canonical ErrorEnvelope

**Example**: `ChEMBLClient._map_sdk_error()` (Lines 191-244)
- Maps HTTP status codes (404, 429, 500, etc.) to ErrorCode enum
- Provides recovery hints for agent self-correction

---

#### Data Transformation

**`_transform_to_search_candidate(result, index)`**
**`_transform_to_<entity>(result, slim=False)`**

**Purpose**: Convert upstream API response to Pydantic models

**Example**: `ChEMBLClient._transform_to_compound()` (Lines 359-436)
- Extracts fields from SDK result
- Normalizes IDs to CURIE format
- Handles optional fields
- Supports slim mode for token efficiency

---

### Internal Test Infrastructure

#### `tests/conftest.py` (Lines 1-280)

**Purpose**: Pytest fixtures for all test modules

**Async Client Fixtures**:
- `hgnc_client()` (Lines 127-131) - Real HGNCClient for integration tests
- `entrez_client()` (Lines 198-202) - Real EntrezClient
- `iuphar_client()` (Lines 275-279) - Real IUPHARClient

**Sample Data Fixtures**:
- `sample_gene()` (Lines 29-46) - BRCA1 Gene model
- `sample_search_candidate()` (Lines 50-57) - Gene SearchCandidate
- `sample_pagination_envelope()` (Lines 61-69) - PaginationEnvelope[SearchCandidate]
- `sample_error_envelope()` (Lines 73-75) - ErrorEnvelope
- `sample_entrez_gene()` (Lines 181-194) - TP53 EntrezGene
- `sample_ligand()` (Lines 223-239) - Ibuprofen Ligand
- `sample_target()` (Lines 255-271) - D2 receptor Target

**Mock Fixtures**:
- `mock_hgnc_search_response()` (Lines 79-97) - HGNC API search mock
- `mock_hgnc_fetch_response()` (Lines 101-123) - HGNC API fetch mock
- `mock_httpx_client()` (Lines 135-139) - httpx.AsyncClient mock
- `mock_response_factory()` (Lines 143-159) - Factory for httpx.Response mocks

**Configuration**: Loads `.env` file for integration test credentials (Line 14)

---

#### Test Organization

**`tests/unit/`** - Unit tests with mocked dependencies
- test_chembl_client.py, test_chembl_models.py
- test_clinicaltrials_client.py
- test_drugbank_client.py, test_drugbank_models.py
- test_ensembl_client.py, test_ensembl_models.py
- test_entrez_client.py, test_entrez_models.py
- test_error_envelopes.py
- test_iuphar_client.py
- test_models.py, test_pharmacology_models.py
- test_provenance_models.py
- test_pubchem_client.py, test_pubchem_models.py
- test_trial_location_models.py, test_trial_models.py
- test_wikipathways_client.py, test_wikipathways_models.py

**`tests/integration/`** - Integration tests hitting real APIs
- test_biogrid_api.py, test_biogrid_performance.py
- test_chembl_api.py
- test_clinicaltrials_api.py
- test_competency_questions_client.py, test_competency_questions_mcp.py
- test_concurrency.py, test_error_recovery.py
- test_drugbank_api.py
- test_ensembl_api.py
- test_entrez_api.py, test_entrez_performance.py
- test_gateway.py
- test_hgnc_api.py
- test_iuphar_api.py
- test_opentargets_api.py
- test_performance.py
- test_pubchem_api.py
- test_string_api.py, test_string_performance.py
- test_uniprot_api.py
- test_wikipathways_api.py

**`tests/e2e/`** - End-to-end tests
- test_competency_questions_cloud.py (tests deployed gateway)

**`tests/manual/`** - Manual verification scripts
- test_ct_headers.py, test_ct_headers2.py
- test_wikipathways_xref_format.py
- verify_cloud_deployment.py

**`tests/fixtures/`** - Test data
- tier1_string_data.py (STRING interaction test data)

**`tests/gaps/`** - Gap analysis tests
- test_grounding_gap.py (tests entity grounding issues)

**`tests/contract/`** - Contract tests (empty placeholder)

---

### Internal Utility Modules

#### `tests/utils.py`

**Purpose**: Shared test utilities and helpers

---

#### `tests/integration/conftest.py`

**Purpose**: Integration test-specific fixtures (extends base conftest.py)

---

### Compliance and Auditing

#### `tools/audit_compliance.py`

**Purpose**: Automated compliance auditing for ADR-001 standards

**Likely Functions** (not read in detail):
- Validate CURIE format consistency
- Check cross-reference key usage
- Verify error envelope structure
- Audit rate limiting implementation

---

## Entry Points

### Main Entry Points

1. **Gateway Server** (Production)
   - **File**: `src/lifesciences_mcp/servers/gateway.py`
   - **Entry**: Line 49 `mcp = FastMCP("Life Sciences MCP Gateway")`
   - **Main**: Lines 114-115 `if __name__ == "__main__": mcp.run()`
   - **Deployment**: FastMCP Cloud at `src/lifesciences_mcp/servers/gateway.py:mcp`
   - **Access**: https://lifesciences-research.fastmcp.app/mcp

2. **Individual Servers** (Development/Testing)
   - **Files**: All files in `src/lifesciences_mcp/servers/` (except gateway.py and __init__.py)
   - **Pattern**: Each has `mcp = FastMCP("...")` and `if __name__ == "__main__": mcp.run()`
   - **Usage**: `uv run fastmcp run src/lifesciences_mcp/servers/<server>.py`

3. **Showcase Scripts** (Demonstration)
   - **File**: `scripts/showcase_nsclc_v2_fastmcp.py` (Lines 426-427)
   - **Main**: `asyncio.run(main())`
   - **Usage**: `python scripts/showcase_nsclc_v2_fastmcp.py`

4. **Validation Scripts** (Testing)
   - **Files**: `scripts/verify_chembl_v2.py`, `scripts/verify_swi_snf.py`
   - **Pattern**: Standard `if __name__ == "__main__"` entry points

5. **Test Suites** (Quality Assurance)
   - **Entry**: `pytest` command (no explicit main)
   - **Config**: pytest discovers tests in `tests/` directory

---

### CLI Tools

**FastMCP CLI** (not in codebase, external dependency):
```bash
# Run individual server
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py

# Run gateway server
uv run fastmcp run src/lifesciences_mcp/servers/gateway.py
```

**Pytest** (testing):
```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with markers
pytest -m "not slow"
```

---

### Package Entry Point

**File**: `src/lifesciences_mcp/__init__.py`
- **Version**: Line 39 `__version__ = "0.1.0"`
- **Public API**: Lines 42-98 (re-exports of clients and models)
- **Usage**: Import as library

```python
from lifesciences_mcp import HGNCClient, Gene, ErrorEnvelope

async with HGNCClient() as client:
    result = await client.search_genes("BRCA1")
```

---

## Dependencies Between Components

### Primary Dependency Flow

```
Servers (FastMCP tools)
    ↓ (imports and calls)
Clients (API interaction)
    ↓ (returns)
Models (Pydantic schemas)
```

### Detailed Dependency Graph

#### Servers → Clients → Models

**Example: HGNC Server**
```
src/lifesciences_mcp/servers/hgnc.py
  ↓ imports HGNCClient
src/lifesciences_mcp/clients/hgnc.py
  ↓ imports LifeSciencesClient (base class)
  ↓ imports Gene, SearchCandidate, CrossReferences
  ↓ imports ErrorEnvelope, PaginationEnvelope
src/lifesciences_mcp/models/gene.py
src/lifesciences_mcp/models/envelopes.py
```

#### Clients → Base Client

All clients inherit from `LifeSciencesClient`:

```
src/lifesciences_mcp/clients/base.py (LifeSciencesClient)
  ↑ inherited by
  ├── HGNCClient
  ├── UniProtClient
  ├── ChEMBLClient
  ├── OpenTargetsClient
  ├── STRINGClient
  ├── BioGridClient
  ├── EntrezClient
  ├── EnsemblClient
  ├── PubChemClient
  ├── IUPHARClient
  ├── WikiPathwaysClient
  ├── ClinicalTrialsClient
  └── DrugBankClient
```

#### Models → Envelopes

All data models depend on envelope models for responses:

```
src/lifesciences_mcp/models/envelopes.py (ErrorEnvelope, PaginationEnvelope)
  ↑ used by
  ├── Gene (via clients returning Gene | ErrorEnvelope)
  ├── Protein (via clients)
  ├── Compound (via clients)
  ├── Target (via clients)
  ├── Interaction (via clients)
  ├── Pathway (via clients)
  └── Trial (via clients)
```

#### Models → CrossReferences

Many models share the CrossReferences model:

```
src/lifesciences_mcp/models/gene.py (CrossReferences)
  ↑ reused by
  ├── Gene (gene.py)
  ├── Protein (protein.py) - imports from gene.py
  ├── Ligand (pharmacology.py)
  ├── Target (pharmacology.py)
  ├── EntrezGene (entrez.py)
  ├── EnsemblGene (ensembl.py)
  └── Drug (drug.py)
```

#### Gateway → Individual Servers

```
src/lifesciences_mcp/servers/gateway.py
  ↓ imports and mounts
  ├── hgnc_mcp (from servers/hgnc.py)
  ├── uniprot_mcp (from servers/uniprot.py)
  ├── chembl_mcp (from servers/chembl.py)
  ├── opentargets_mcp (from servers/opentargets.py)
  ├── string_mcp (from servers/string.py)
  ├── biogrid_mcp (from servers/biogrid.py)
  ├── ensembl_mcp (from servers/ensembl.py)
  ├── entrez_mcp (from servers/entrez.py)
  ├── pubchem_mcp (from servers/pubchem.py)
  ├── iuphar_mcp (from servers/iuphar.py)
  ├── wikipathways_mcp (from servers/wikipathways.py)
  └── clinicaltrials_mcp (from servers/clinicaltrials.py)
```

#### Tests → Application Code

```
tests/
  ├── conftest.py (fixtures)
  │   ↓ imports
  │   ├── lifesciences_mcp.clients (HGNCClient, EntrezClient, IUPHARClient)
  │   └── lifesciences_mcp.models (Gene, SearchCandidate, ErrorEnvelope, etc.)
  │
  ├── unit/ (mocked tests)
  │   ↓ imports and tests
  │   ├── clients (mocked HTTP calls)
  │   └── models (Pydantic validation)
  │
  ├── integration/ (real API tests)
  │   ↓ imports and tests
  │   ├── clients (real HTTP calls)
  │   └── servers (MCP tool invocation)
  │
  └── e2e/ (end-to-end tests)
      ↓ tests deployed gateway
      └── gateway server (via HTTP JSON-RPC)
```

---

### External Dependencies

#### Core Framework
- **fastmcp**: FastMCP framework for MCP server creation
- **pydantic**: Data validation and serialization (v2)
- **httpx**: Async HTTP client

#### Domain-Specific SDKs
- **chembl_webresource_client**: ChEMBL synchronous SDK (wrapped with asyncio)

#### Utilities
- **python-dotenv**: Environment variable loading
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support

#### Type Checking & Linting
- **mypy**: Static type checking
- **ruff**: Linting and formatting

---

### Cross-Reference Registry (22-Key Standard)

All models share a common cross-reference schema (defined in ADR-001):

**Keys**: ensembl_gene, ensembl_transcript, uniprot, entrez, refseq, hgnc, omim, orphanet, mondo, efo, chembl, drugbank, pubchem_compound, pubchem_substance, kegg, kegg_pathway, string, biogrid, stitch, iuphar, pdb

**Pattern**: Each client maps upstream API cross-references to this registry, enabling seamless data integration across databases.

**Example Flow**:
1. HGNC client returns Gene with CrossReferences (ensembl_gene, uniprot, entrez)
2. Application uses ensembl_gene to query EnsemblClient
3. EnsemblClient returns EnsemblGene with CrossReferences (reusing same schema)
4. Data can be linked across all 13 databases via consistent cross-reference keys

---

## Summary Statistics

- **Total Python Files** (main package): 50
- **Client Modules**: 15 (14 clients + 1 base class)
- **Model Modules**: 18 (17 model files + 1 __init__)
- **Server Modules**: 15 (13 individual + 1 gateway + 1 __init__)
- **Script Files**: 5 demonstration/validation scripts
- **Test Files**: 116 (unit + integration + e2e + manual + fixtures)
- **Public Classes**: 60+ (14 clients, 40+ models, envelopes)
- **Public MCP Tools**: 35+ (across 13 servers)
- **Supported Databases**: 13 life sciences APIs
- **Cross-Reference Keys**: 22 standardized identifiers

---

## Architecture Principles

1. **Fuzzy-to-Fact Protocol**: All clients implement two-phase resolution (search → get)
2. **CURIE Validation**: Strict identifier validation before API calls
3. **Rate Limiting**: All clients enforce upstream API rate limits with exponential backoff
4. **Error Recovery**: Canonical error envelopes with agent-actionable recovery hints
5. **Token Efficiency**: Slim mode support for reduced token usage
6. **Connection Pooling**: Shared HTTP clients with lifecycle management
7. **Async-First**: All I/O operations are async (with run_in_executor for sync SDKs)
8. **Pydantic V2**: Strong typing and validation throughout
9. **Omit-If-Null**: Cross-references omit keys with no value (never null/empty)
10. **Gateway Pattern**: Single unified endpoint via FastMCP mounting

---

## Notes

- **DrugBank**: Excluded from gateway server due to commercial API key requirement
- **BioGRID**: Requires free API key (BIOGRID_API_KEY environment variable)
- **NCBI Entrez**: Optional API key recommended for higher rate limits
- **FastMCP Cloud**: Production deployment at https://lifesciences-research.fastmcp.app/mcp
- **Protocol**: JSON-RPC 2.0 over HTTP (Server-Sent Events for streaming)
- **Python Version**: Requires Python 3.13+ (based on type hints)
