# Component Inventory

## Overview

The Life Sciences MCP (Model Context Protocol) codebase is a comprehensive biological data integration platform that provides unified access to 13+ life sciences databases through a standardized API. The architecture follows a client-server pattern with three main layers:

1. **Client Layer** (`lifesciences_mcp.clients`): Async HTTP clients for biological databases
2. **Model Layer** (`lifesciences_mcp.models`): Pydantic data models with cross-reference support
3. **Server Layer** (`lifesciences_mcp.servers`): FastMCP servers exposing tools via MCP protocol

The codebase implements a "Fuzzy-to-Fact" protocol where fuzzy searches return ranked candidates, followed by strict CURIE-based lookups for detailed information. All components use async/await patterns, connection pooling, rate limiting, and comprehensive error handling.

**Code Statistics:**
- Client modules: ~8,162 lines of code
- Model modules: ~3,403 lines of code
- 14 API clients (13 in gateway, 1 requires commercial key)
- 18 Pydantic model files
- 15 MCP server implementations

## Public API

### Primary Entry Points

#### Gateway Server
**File:** `src/lifesciences_mcp/servers/gateway.py`
**Lines:** 1-116

The unified gateway server that composes all 13 individual MCP servers into a single deployment endpoint. This is the primary public interface for the entire platform.

**Entry Point:**
```python
# Line 49: Main gateway server instance
mcp = FastMCP("Life Sciences MCP Gateway")

# Line 114-115: Command-line entry
if __name__ == "__main__":
    mcp.run()
```

**Mounted Services:**
- HGNC (Gene Nomenclature)
- UniProt (Protein Data)
- ChEMBL (Compounds)
- Open Targets (Target-Disease Associations)
- STRING (Protein Interactions)
- BioGRID (Genetic Interactions)
- Ensembl (Genomic Data)
- Entrez (NCBI Gene Database)
- PubChem (Chemical Compounds)
- IUPHAR/GtoPdb (Pharmacology)
- WikiPathways (Biological Pathways)
- ClinicalTrials (Clinical Trial Data)

### Public Client Classes

All clients inherit from `LifeSciencesClient` base class and implement async context manager protocol.

#### Base Client
**File:** `src/lifesciences_mcp/clients/base.py`
**Lines:** 1-66

```python
class LifeSciencesClient:
    """Base async HTTP client for life sciences APIs."""

    # Line 23-39: Initialization with connection pooling
    def __init__(self, base_url: str, timeout: float = 30.0, max_connections: int = 10)

    # Line 41-54: Get or create async HTTP client
    async def _get_client(self) -> httpx.AsyncClient

    # Line 56-60: Close HTTP client
    async def close(self) -> None

    # Line 62-65: Make GET request
    async def _get(self, path: str, **kwargs: Any) -> httpx.Response
```

#### HGNCClient - Gene Nomenclature
**File:** `src/lifesciences_mcp/clients/hgnc.py`
**Lines:** 1-353

Primary interface for gene symbol resolution and gene information retrieval.

**Key Public Methods:**
```python
class HGNCClient(LifeSciencesClient):
    # Line 110-248: Fuzzy search for genes (Phase 1)
    async def search_genes(
        query: str,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50
    ) -> PaginationEnvelope[SearchCandidate] | ErrorEnvelope

    # Line 273-331: Strict lookup by HGNC CURIE (Phase 2)
    async def get_gene(hgnc_id: str) -> Gene | ErrorEnvelope
```

**Constants:**
- Line 40: `HGNC_BASE_URL = "https://rest.genenames.org"`
- Line 41: `RATE_LIMIT_DELAY = 0.1` (10 req/s)
- Line 42: `AMBIGUOUS_THRESHOLD = 100`

#### UniProtClient - Protein Data
**File:** `src/lifesciences_mcp/clients/uniprot.py`
**Lines:** 1-461

Interface for protein sequence and annotation data from UniProt.

**Key Public Methods:**
```python
class UniProtClient(LifeSciencesClient):
    # Line 170-312: Fuzzy protein search
    async def search_proteins(
        query: str,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50
    ) -> PaginationEnvelope[ProteinSearchCandidate] | ErrorEnvelope

    # Line 314-460: Strict protein lookup by UniProt CURIE
    async def get_protein(
        uniprot_id: str,
        slim: bool = False
    ) -> Protein | ErrorEnvelope
```

**Constants:**
- Line 41: `UNIPROT_BASE_URL = "https://rest.uniprot.org"`
- Line 42: `RATE_LIMIT_DELAY = 0.1` (10 req/s)
- Line 46: `MAX_PAGE_SIZE = 500`

#### ChEMBLClient - Compound Data
**File:** `src/lifesciences_mcp/clients/chembl.py`
**Lines:** 1-681

Interface for bioactivity data and compound information. Uses synchronous SDK wrapped with `run_in_executor`.

**Key Public Methods:**
```python
class ChEMBLClient(LifeSciencesClient):
    # Line 453-517: Fuzzy compound search
    async def search_compounds(
        query: str,
        slim: bool = False,
        cursor: str | None = None,
        page_size: int = 50
    ) -> PaginationEnvelope[CompoundSearchCandidate] | ErrorEnvelope

    # Line 519-586: Strict compound lookup
    async def get_compound(
        chembl_id: str,
        slim: bool = False
    ) -> dict[str, Any] | ErrorEnvelope

    # Line 588-673: Batch compound lookup
    async def get_compounds_batch(
        chembl_ids: list[str],
        slim: bool = True
    ) -> list[dict[str, Any]] | ErrorEnvelope
```

**Constants:**
- Line 52: `CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"`
- Line 55-56: `RATE_LIMIT_REQUESTS = 10` (10 req/s)
- Line 59-61: Exponential backoff configuration

#### OpenTargetsClient - Target-Disease Associations
**File:** `src/lifesciences_mcp/clients/opentargets.py`

GraphQL-based client for disease-target association data.

**Key Public Methods:**
```python
class OpenTargetsClient(LifeSciencesClient):
    async def search_targets(query: str, ...) -> PaginationEnvelope[TargetSearchCandidate] | ErrorEnvelope
    async def get_target(ensembl_id: str, ...) -> Target | ErrorEnvelope
    async def get_associations(ensembl_id: str, ...) -> PaginationEnvelope[Association] | ErrorEnvelope
```

#### STRINGClient - Protein Interactions
**File:** `src/lifesciences_mcp/clients/string.py`

Interface for protein-protein interaction networks.

**Key Public Methods:**
```python
class STRINGClient(LifeSciencesClient):
    async def search_proteins(query: str, ...) -> PaginationEnvelope[InteractionSearchCandidate] | ErrorEnvelope
    async def get_interactions(identifiers: list[str], ...) -> InteractionNetwork | ErrorEnvelope
    async def get_network_image_url(identifiers: list[str], ...) -> dict[str, str] | ErrorEnvelope
```

**Constants:**
- `RATE_LIMIT_DELAY = 1.0` (1 req/s)
- `DEFAULT_SPECIES = 9606` (Homo sapiens)
- `DEFAULT_SCORE_THRESHOLD = 400` (medium confidence)

#### BioGridClient - Genetic Interactions
**File:** `src/lifesciences_mcp/clients/biogrid.py`

Interface for genetic and protein interaction data.

**Key Public Methods:**
```python
class BioGridClient(LifeSciencesClient):
    async def search_genes(query: str, ...) -> PaginationEnvelope[BioGridSearchCandidate] | ErrorEnvelope
    async def get_interactions(gene_symbol: str, ...) -> InteractionResult | ErrorEnvelope
```

**Constants:**
- `BASE_URL = "https://webservice.thebiogrid.org"`
- `RATE_LIMIT = 0.5` (2 req/s)

#### EnsemblClient - Genomic Data
**File:** `src/lifesciences_mcp/clients/ensembl.py`

Interface for gene and transcript information from Ensembl.

**Key Public Methods:**
```python
class EnsemblClient(LifeSciencesClient):
    async def search_genes(query: str, ...) -> PaginationEnvelope[EnsemblGeneSearchCandidate] | ErrorEnvelope
    async def get_gene(ensembl_id: str, ...) -> EnsemblGene | ErrorEnvelope
    async def get_transcript(transcript_id: str, ...) -> EnsemblTranscript | ErrorEnvelope
```

#### EntrezClient - NCBI Gene Database
**File:** `src/lifesciences_mcp/clients/entrez.py`

Interface for NCBI Gene database using E-utilities.

**Key Public Methods:**
```python
class EntrezClient(LifeSciencesClient):
    async def search_genes(query: str, ...) -> PaginationEnvelope[EntrezGeneSearchCandidate] | ErrorEnvelope
    async def get_gene(gene_id: str, ...) -> EntrezGene | ErrorEnvelope
    async def get_pubmed_links(gene_id: str, ...) -> PaginationEnvelope[dict] | ErrorEnvelope
```

#### PubChemClient - Chemical Compounds
**File:** `src/lifesciences_mcp/clients/pubchem.py`

Interface for chemical compound data from PubChem.

**Key Public Methods:**
```python
class PubChemClient(LifeSciencesClient):
    async def search_compounds(query: str, ...) -> PaginationEnvelope[PubChemSearchCandidate] | ErrorEnvelope
    async def get_compound(cid: str, ...) -> PubChemCompound | ErrorEnvelope
```

#### IUPHARClient - Pharmacological Data
**File:** `src/lifesciences_mcp/clients/iuphar.py`

Interface for pharmacological ligand and target data.

**Key Public Methods:**
```python
class IUPHARClient(LifeSciencesClient):
    async def search_ligands(query: str, ...) -> PaginationEnvelope[LigandSearchCandidate] | ErrorEnvelope
    async def get_ligand(ligand_id: str, ...) -> Ligand | ErrorEnvelope
    async def search_targets(query: str, ...) -> PaginationEnvelope[PharmacologicalTargetSearchCandidate] | ErrorEnvelope
    async def get_target(target_id: str, ...) -> PharmacologicalTarget | ErrorEnvelope
```

#### WikiPathwaysClient - Biological Pathways
**File:** `src/lifesciences_mcp/clients/wikipathways.py`

Interface for biological pathway data.

**Key Public Methods:**
```python
class WikiPathwaysClient(LifeSciencesClient):
    async def search_pathways(query: str, ...) -> PaginationEnvelope[PathwaySearchCandidate] | ErrorEnvelope
    async def get_pathway(pathway_id: str, ...) -> Pathway | ErrorEnvelope
    async def get_pathways_for_gene(gene_symbol: str, ...) -> PaginationEnvelope[PathwaySearchCandidate] | ErrorEnvelope
    async def get_pathway_components(pathway_id: str, ...) -> PathwayComponents | ErrorEnvelope
```

#### ClinicalTrialsClient - Clinical Trial Data
**File:** `src/lifesciences_mcp/clients/clinicaltrials.py`

Interface for clinical trial information from ClinicalTrials.gov.

**Key Public Methods:**
```python
class ClinicalTrialsClient(LifeSciencesClient):
    async def search_trials(query: str, ...) -> PaginationEnvelope[TrialSearchCandidate] | ErrorEnvelope
    async def get_trial(nct_id: str, ...) -> Trial | ErrorEnvelope
    async def get_trial_locations(nct_id: str, ...) -> list[TrialLocation] | ErrorEnvelope
```

#### DrugBankClient - Drug Data (Requires API Key)
**File:** `src/lifesciences_mcp/clients/drugbank.py`

Interface for comprehensive drug and drug target information (not included in gateway).

**Key Public Methods:**
```python
class DrugBankClient(LifeSciencesClient):
    async def search_drugs(query: str, ...) -> PaginationEnvelope[DrugSearchCandidate] | ErrorEnvelope
    async def get_drug(drugbank_id: str, ...) -> Drug | ErrorEnvelope
```

### Public Data Models

All models are Pydantic BaseModel subclasses with validation and serialization support.

#### Core Envelope Models
**File:** `src/lifesciences_mcp/models/envelopes.py`
**Lines:** 1-145

```python
# Line 16-25: Standard error codes
class ErrorCode(str, Enum):
    UNRESOLVED_ENTITY = "UNRESOLVED_ENTITY"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    INVALID_CROSS_REFERENCE = "INVALID_CROSS_REFERENCE"

# Line 27-34: Error detail structure
class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    recovery_hint: str
    invalid_input: str | None = None

# Line 36-108: Standard error envelope
class ErrorEnvelope(BaseModel):
    success: bool = False
    error: ErrorDetail

# Line 111-117: Pagination metadata
class Pagination(BaseModel):
    cursor: str | None = None
    total_count: int | None = None
    page_size: int = 50

# Line 119-144: Generic pagination envelope
class PaginationEnvelope(BaseModel, Generic[T]):
    items: list[T]
    pagination: Pagination
```

#### Gene Models
**File:** `src/lifesciences_mcp/models/gene.py`
**Lines:** 1-215

```python
# Line 27-142: Cross-reference model (22-key registry)
class CrossReferences(BaseModel):
    ensembl_gene: str | None = None
    ensembl_transcript: list[str] | None = None
    uniprot: list[str] | None = None
    entrez: str | None = None
    refseq: list[str] | None = None
    hgnc: str | None = None
    omim: str | None = None
    orphanet: str | None = None
    mondo: str | None = None
    efo: str | None = None
    chembl: str | None = None
    drugbank: str | None = None
    pubchem_compound: str | None = None
    pubchem_substance: str | None = None
    kegg: str | None = None
    kegg_pathway: list[str] | None = None
    string: str | None = None
    biogrid: str | None = None
    stitch: str | None = None
    iuphar: str | None = None
    pdb: list[str] | None = None

# Line 145-163: Search candidate (lightweight)
class SearchCandidate(BaseModel):
    id: str  # HGNC CURIE
    symbol: str
    name: str
    score: float  # 0.0-1.0

# Line 166-214: Full gene record
class Gene(BaseModel):
    id: str  # HGNC CURIE
    symbol: str
    name: str
    status: str
    locus_type: str | None = None
    locus_group: str | None = None
    location: str | None = None
    alias_symbols: list[str] | None = None
    alias_names: list[str] | None = None
    prev_symbols: list[str] | None = None
    prev_names: list[str] | None = None
    cross_references: CrossReferences = Field(default_factory=CrossReferences)
```

#### Protein Models
**File:** `src/lifesciences_mcp/models/protein.py`

```python
class ProteinSearchCandidate(BaseModel):
    id: str  # UniProtKB CURIE
    name: str
    organism: str
    gene_names: list[str] | None = None
    score: float

class Protein(BaseModel):
    id: str  # UniProtKB CURIE
    accession: str
    name: str
    organism: str
    full_name: str | None = None
    gene_names: list[str] | None = None
    organism_id: int | None = None
    function: str | None = None
    sequence_length: int | None = None
    cross_references: CrossReferences | None = None
```

#### Compound Models
**File:** `src/lifesciences_mcp/models/compound.py`

```python
class CompoundSearchCandidate(BaseModel):
    id: str  # ChEMBL CURIE
    name: str
    molecular_formula: str | None = None
    score: float

class Compound(BaseModel):
    id: str  # ChEMBL CURIE
    name: str | None = None
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    smiles: str | None = None
    inchi: str | None = None
    canonical_name: str | None = None
    max_phase: int | None = None
    indications: list[str] = []
    synonyms: list[str] = []
    cross_references: dict[str, list[str]] = {}
```

#### Interaction Models
**File:** `src/lifesciences_mcp/models/interaction.py`

```python
class EvidenceScores(BaseModel):
    combined_score: int
    experimental: int | None = None
    database: int | None = None
    textmining: int | None = None
    coexpression: int | None = None

class Interaction(BaseModel):
    protein_a: str
    protein_b: str
    symbol_a: str | None = None
    symbol_b: str | None = None
    scores: EvidenceScores
    cross_references: InteractionCrossReferences | None = None

class InteractionNetwork(BaseModel):
    query_proteins: list[str]
    interactions: list[Interaction]
    network_stats: dict[str, int] | None = None
```

#### Target Models
**File:** `src/lifesciences_mcp/models/target.py`

```python
class TargetSearchCandidate(BaseModel):
    id: str  # Ensembl gene ID
    symbol: str
    name: str
    score: float

class Association(BaseModel):
    disease_id: str
    disease_name: str
    score: float
    evidence_count: int | None = None

class Target(BaseModel):
    id: str  # Ensembl gene ID
    symbol: str
    name: str
    biotype: str | None = None
    description: str | None = None
    associations: list[Association] = []
    cross_references: CrossReferences | None = None
```

#### Pathway Models
**File:** `src/lifesciences_mcp/models/pathway.py`

```python
class PathwaySearchCandidate(BaseModel):
    id: str  # WikiPathways ID
    name: str
    organism: str
    score: float

class ComponentCounts(BaseModel):
    genes: int = 0
    metabolites: int = 0
    pathways: int = 0
    interactions: int = 0

class Pathway(BaseModel):
    id: str
    name: str
    organism: str
    description: str | None = None
    url: str | None = None
    component_counts: ComponentCounts | None = None
    revision: RevisionMetadata | None = None
```

#### Trial Models
**File:** `src/lifesciences_mcp/models/trial.py`

```python
class TrialSearchCandidate(BaseModel):
    nct_id: str
    title: str
    status: str
    score: float

class Trial(BaseModel):
    nct_id: str
    title: str
    status: str
    phase: str | None = None
    sponsor: Sponsor | None = None
    protocol: TrialProtocol | None = None
    eligibility: EligibilityCriteria | None = None
    outcomes: list[Outcome] = []
```

### Public Aggregator

#### UnifiedSearch - Multi-Database Search
**File:** `src/lifesciences_agent/aggregator.py`
**Lines:** 1-74

Experimental aggregator that orchestrates queries across multiple databases for improved entity resolution.

```python
# Line 18-73: Unified search orchestrator
class UnifiedSearch:
    """
    Experimental Aggregator for resolving biological entities.
    Orchestrates queries across HGNC, UniProt, and Open Targets.
    """

    # Line 25-28: Initialize clients
    def __init__(self)

    # Line 30-73: Multi-database search with re-ranking
    async def search(self, query: str, limit: int = 10) -> PaginationEnvelope[SearchCandidate]
```

## Internal Implementation

### Internal Modules

#### Client Utilities and Helpers

**Rate Limiting Implementation**
- Located in each client's `_rate_limited_get()` method
- Uses `asyncio.Lock` for thread-safe request serialization
- Implements exponential backoff with thundering herd prevention
- Pattern: Re-check timing after acquiring lock to prevent race conditions

**Cross-Reference Mapping**
- Each client has `_build_cross_references()` or `_map_cross_references()` methods
- Maps API-specific identifiers to 22-key registry
- Implements "omit-if-null" pattern (never stores empty strings or empty lists)

**Error Handling**
- `_map_sdk_error()` methods in SDK-based clients (ChEMBL)
- Canonical error codes: UNRESOLVED_ENTITY, ENTITY_NOT_FOUND, AMBIGUOUS_QUERY, RATE_LIMITED, UPSTREAM_ERROR
- All errors include actionable recovery hints for agent self-correction

#### Model Validators

**CURIE Pattern Validation**
All models validate identifier formats using compiled regex patterns:
- HGNC: `^HGNC:\d+$`
- UniProt: `^UniProtKB:[A-Z][A-Z0-9]{5,9}$`
- ChEMBL: `^CHEMBL:[0-9]+$`
- Ensembl Gene: `^ENSG\d{11}$`
- NCBI Gene: `^NCBI_Gene:\d+$`
- PubChem: `^CID:\d+$`

**Cross-Reference Validation**
- `CrossReferences.omit_empty_values()` model validator (Line 130-137 in gene.py)
- Ensures no empty strings or empty lists
- Automatically excludes None values on serialization

### Internal Classes

#### SDK Wrappers

**ChEMBL SDK Wrapper**
**File:** `src/lifesciences_mcp/clients/chembl.py`

```python
# Line 87-92: Thread pool executor for synchronous SDK
def _get_executor(self) -> ThreadPoolExecutor

# Line 94-123: Rate-limited SDK call wrapper
async def _rate_limited_sdk_call(self, sdk_func: Any) -> Any

# Line 125-168: SDK call with exponential backoff
async def _sdk_call_with_backoff(self, sdk_func: Any) -> Any
```

#### Pagination Cursor Encoding

Multiple clients implement cursor-based pagination:

```python
# Base64-encoded JSON pattern used by HGNC, ChEMBL, PubChem, etc.
def _encode_cursor(self, offset: int) -> str:
    data = json.dumps({"offset": offset})
    return base64.b64encode(data.encode()).decode()

def _decode_cursor(self, cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        data = json.loads(base64.b64decode(cursor).decode())
        return data.get("offset", 0)
    except Exception:
        return 0
```

#### XML Parsing (Entrez)

**File:** `src/lifesciences_mcp/clients/entrez.py`

Uses `defusedxml` for secure XML parsing to prevent XXE attacks:
- Parses E-utilities XML responses
- Extracts gene data from Entrezgene_xref elements
- Builds cross-references from XML structure

### Internal Functions

#### Search Result Transformers

Each client implements transformation functions:

**ChEMBL:**
```python
# Line 246-284: Transform SDK result to search candidate
def _transform_to_search_candidate(self, sdk_result: dict[str, Any], index: int) -> CompoundSearchCandidate

# Line 359-436: Transform SDK result to full compound
def _transform_to_compound(self, sdk_result: dict[str, Any], slim: bool = False, ...) -> Compound
```

**UniProt:**
```python
# Line 114-168: Map UniProt cross-references to 22-key registry
def _map_cross_references(self, uniprot_refs: list[dict[str, Any]]) -> CrossReferences
```

**HGNC:**
```python
# Line 255-271: Search by alias_symbol field
async def _search_by_alias(self, query: str) -> list[dict[str, Any]]

# Line 333-353: Build cross-references from HGNC response
def _build_cross_references(self, doc: dict[str, Any]) -> CrossReferences
```

#### Score Calculation

Fuzzy search results use position-based scoring with decay:

```python
# Common pattern across clients
score = max(0.1, 1.0 - (index * SCORE_DECAY))  # SCORE_DECAY typically 0.05
```

Special boosting for exact matches:
```python
# HGNC exact symbol match
if symbol.upper() == query_upper:
    score = 1.0
else:
    score = max(0.1, 0.95 - (position * self.SCORE_DECAY))
```

## Entry Points

### MCP Server Entry Points

All server modules follow the same pattern:

**Individual Server Pattern:**
```python
# Example: src/lifesciences_mcp/servers/hgnc.py
from fastmcp import FastMCP

mcp = FastMCP("HGNC Gene Server")  # Line 22

@mcp.tool
async def search_genes(...):  # Line 36
    ...

@mcp.tool
async def get_gene(...):  # Line 67
    ...

if __name__ == "__main__":
    mcp.run()  # Line 84-85
```

**Command-line execution:**
```bash
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
```

**FastMCP Cloud Entry Point:**
```python
# Gateway server: src/lifesciences_mcp/servers/gateway.py:mcp
```

### Script Entry Points

#### Showcase Scripts

**NSCLC Research Scenario**
**File:** `scripts/showcase_nsclc.py`
**Lines:** 1-100+

Demonstrates KRAS targeting and EML4-ALK fusion scenarios:
```python
# Line 32-58: Gene resolution helper
async def resolve_gene(symbol: str)

# Line 61-100+: KRAS scenario orchestration
async def run_kras_scenario()
```

Entry: `if __name__ == "__main__":`

**Graph Construction Showcase**
**File:** `scripts/showcase_graph_construction.py`

Demonstrates building knowledge graphs from API data.

**Validation and Verification Scripts**

1. **Competency Validation**
   - File: `scripts/validate_competency.py`
   - Purpose: Validate API responses against expected competency questions

2. **ChEMBL Verification**
   - File: `scripts/verify_chembl_v2.py`
   - Purpose: Verify ChEMBL API integration

3. **SWI/SNF Verification**
   - File: `scripts/verify_swi_snf.py`
   - Purpose: Verify SWI/SNF complex data retrieval

#### Benchmark Scripts

**Value Benchmark**
**File:** `scripts/benchmark_value.py`

Performance and value benchmarking for API operations.

## Module Dependencies

### Dependency Graph

```
lifesciences_mcp/
├── models/                  (No internal dependencies)
│   ├── envelopes.py        → Core envelope types (ErrorEnvelope, PaginationEnvelope)
│   ├── gene.py             → Uses envelopes
│   ├── protein.py          → Uses gene.CrossReferences, envelopes
│   ├── compound.py         → Uses envelopes
│   ├── target.py           → Uses gene.CrossReferences, envelopes
│   ├── interaction.py      → Uses envelopes
│   ├── pathway.py          → Uses envelopes
│   ├── trial.py            → Uses envelopes
│   └── ...                 → Other specialized models
│
├── clients/                 (Depends on models, base)
│   ├── base.py             → Uses httpx (external)
│   ├── hgnc.py             → Uses base, models.gene, models.envelopes
│   ├── uniprot.py          → Uses base, models.protein, models.gene, models.envelopes
│   ├── chembl.py           → Uses base, models.compound, models.envelopes
│   ├── opentargets.py      → Uses base, models.target, models.gene, models.envelopes
│   ├── string.py           → Uses base, models.interaction, models.envelopes
│   ├── biogrid.py          → Uses base, models.biogrid, models.envelopes
│   └── ...                 → Other API clients
│
├── servers/                 (Depends on clients)
│   ├── hgnc.py             → Uses clients.HGNCClient, models
│   ├── uniprot.py          → Uses clients.UniProtClient, models
│   ├── chembl.py           → Uses clients.ChEMBLClient, models
│   ├── gateway.py          → Composes ALL servers
│   └── ...                 → Other MCP servers
│
└── lifesciences_agent/      (Depends on clients)
    └── aggregator.py        → Uses clients.{HGNC,UniProt,OpenTargets}Client

scripts/                     (Depends on clients and agent)
├── showcase_nsclc.py        → Uses clients.*, lifesciences_agent.aggregator
├── validate_competency.py   → Uses clients.*
└── ...                      → Other scripts
```

### External Dependencies

**Core Runtime:**
- `httpx` - Async HTTP client with connection pooling
- `pydantic` - Data validation and serialization
- `fastmcp` - MCP server framework
- `asyncio` - Async/await runtime

**API SDKs:**
- `chembl_webresource_client` - ChEMBL SDK (synchronous)

**Security:**
- `defusedxml` - Secure XML parsing for Entrez

**Development/Testing:**
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `python-dotenv` - Environment variable loading

### Cross-Module Patterns

1. **Fuzzy-to-Fact Protocol**
   - Phase 1: `search_*()` returns `PaginationEnvelope[*SearchCandidate]`
   - Phase 2: `get_*()` requires CURIE, returns full entity

2. **Error Handling**
   - All methods return `Result | ErrorEnvelope` union types
   - Errors include actionable recovery hints

3. **Rate Limiting**
   - All clients implement `_rate_limited_get()` with asyncio.Lock
   - Exponential backoff with thundering herd prevention

4. **Cross-References**
   - 22-key registry defined in `models.gene.CrossReferences`
   - Omit-if-null pattern (never store empty values)
   - Each client maps API-specific IDs to registry

5. **Pagination**
   - Cursor-based (opaque base64-encoded JSON)
   - Clients with server-side pagination use API cursors
   - Clients without use client-side slicing with offset cursors

6. **Slim Mode**
   - Optional `slim: bool` parameter reduces token usage
   - Excludes cross_references, synonyms, detailed fields
   - Search candidates always lightweight (~20 tokens)

## Architecture Patterns

### Async-First Design
All I/O operations use async/await with connection pooling and proper resource cleanup.

### Repository Pattern
Each API client acts as a repository with standardized search/get operations.

### Gateway Pattern
The gateway server composes multiple services into a unified interface using FastMCP mounting.

### Factory Pattern
`PaginationEnvelope.create()` and `ErrorEnvelope.*()` class methods provide factory constructors.

### Strategy Pattern
Rate limiting strategies vary by client based on API requirements (1-15 req/s).

### Builder Pattern
Cross-reference builders construct complex reference objects from API responses.

## File Organization Summary

**Total Python Files:** 121 (excluding framework directories)

**Source Code Structure:**
- `/src/lifesciences_mcp/clients/` - 14 files, ~8,162 lines
- `/src/lifesciences_mcp/models/` - 18 files, ~3,403 lines
- `/src/lifesciences_mcp/servers/` - 15 files
- `/src/lifesciences_agent/` - 2 files

**Scripts:** 8 showcase/validation scripts
**Tests:** 40+ test files across unit/integration/e2e

**Configuration:**
- `pyproject.toml` - Project dependencies and metadata
- `.env` - Environment variables (API keys)

This component inventory provides a comprehensive map of the codebase architecture, public APIs, and internal implementation details for understanding and maintaining the Life Sciences MCP platform.
