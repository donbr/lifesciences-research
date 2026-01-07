# API Reference

## Overview

This API reference documents all public APIs in the Life Sciences MCP (Model Context Protocol) project. The project provides a unified gateway to 13+ biological databases through a consistent Fuzzy-to-Fact protocol.

**Main Components:**
- **Client APIs**: Async HTTP clients for each biological database (HGNC, UniProt, Ensembl, ChEMBL, etc.)
- **Data Models**: Pydantic models for biological entities (genes, proteins, compounds, etc.)
- **Server APIs**: MCP servers exposing tools for LLM integration
- **Gateway Server**: Unified server composing all individual MCP servers
- **Orchestration APIs**: High-level search and aggregation utilities

**Organization:**
- All client code: `src/lifesciences_mcp/clients/`
- All models: `src/lifesciences_mcp/models/`
- All servers: `src/lifesciences_mcp/servers/`
- Orchestration: `src/lifesciences_agent/`

---

## Client APIs

All clients implement the Fuzzy-to-Fact protocol with two-phase operations:
1. **Phase 1 (Fuzzy Search)**: `search_*()` methods return ranked candidates
2. **Phase 2 (Fact Retrieval)**: `get_*()` methods return complete records with CURIEs

### LifeSciencesClient (Base Class)

**File**: `src/lifesciences_mcp/clients/base.py`

#### Description
Base async HTTP client for all life sciences APIs. Provides connection pooling, session management, and common HTTP functionality.

#### Constructor
```python
def __init__(
    self,
    base_url: str,
    timeout: float = 30.0,
    max_connections: int = 10,
) -> None
```

**Parameters:**
- `base_url` (str): Base URL for the API endpoint
- `timeout` (float): Request timeout in seconds (default: 30.0)
- `max_connections` (int): Maximum concurrent connections (default: 10)

**Example:**
```python
from lifesciences_mcp.clients.base import LifeSciencesClient

# Create a custom client
client = LifeSciencesClient(
    base_url="https://api.example.com",
    timeout=60.0,
    max_connections=20
)
```

#### Methods

##### close()
```python
async def close(self) -> None
```

Close the HTTP client and cleanup resources.

**Example:**
```python
await client.close()
```

**Best Practices:**
- Always close clients when done to avoid resource leaks
- Use clients as async context managers for automatic cleanup
- Subclasses should call `super().close()` in their cleanup methods

---

### HGNCClient

**File**: `src/lifesciences_mcp/clients/hgnc.py`

#### Description
HGNC (HUGO Gene Nomenclature Committee) REST API client implementing the Fuzzy-to-Fact protocol for gene symbol resolution. Provides authoritative gene nomenclature with cross-references to 22 external databases.

**Features:**
- Rate limiting at 10 requests/second (HGNC requirement)
- Exponential backoff with thundering herd prevention
- Alias boosting (e.g., "p53" → "TP53")
- Context manager support for automatic cleanup

#### Constructor
```python
def __init__(self) -> None
```

**Example:**
```python
from lifesciences_mcp.clients import HGNCClient

# Standard usage
client = HGNCClient()

# Context manager (recommended)
async with HGNCClient() as client:
    result = await client.search_genes("BRCA1")
```

#### Methods

##### search_genes()
```python
async def search_genes(
    self,
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope[SearchCandidate] | ErrorEnvelope
```

Fuzzy search for genes (Phase 1 of Fuzzy-to-Fact). Searches gene symbols, names, and aliases with intelligent ranking.

**Parameters:**
- `query` (str): Search term (minimum 2 characters). Can be gene symbol, name, alias, or natural language
- `slim` (bool): If True, return minimal fields (~20 tokens per entity). Default: False
- `cursor` (str | None): Opaque pagination cursor from previous response
- `page_size` (int): Results per page (1-100, default: 50)

**Returns:**
- `PaginationEnvelope[SearchCandidate]`: Paginated search results with ranked candidates
- `ErrorEnvelope`: On validation errors, rate limiting, or upstream failures

**Example:**
```python
from lifesciences_mcp.clients import HGNCClient

async with HGNCClient() as client:
    # Basic search
    result = await client.search_genes("BRCA1")

    if result.items:
        print(f"Found {len(result.items)} candidates")
        for candidate in result.items:
            print(f"  {candidate.symbol}: {candidate.name} (score: {candidate.score})")

    # Pagination
    if result.pagination.cursor:
        next_page = await client.search_genes(
            "BRCA1",
            cursor=result.pagination.cursor
        )

    # Slim mode for token efficiency
    slim_result = await client.search_genes("TP53", slim=True)
```

**Search Behavior:**
- Searches multiple HGNC fields: symbol, name, aliases, previous symbols
- Alias matches get perfect score (1.0) and appear first
- Exact symbol matches get perfect score (1.0)
- General matches use position-based scoring (0.95 - 0.05 * position)
- Minimum query length: 2 characters
- Returns AMBIGUOUS_QUERY error if >100 results and query <3 chars

**Best Practices:**
- Use specific queries (gene symbols) for best results
- Check `score` field to assess match quality
- Handle `ErrorEnvelope` responses for error recovery
- Use pagination for large result sets
- Use slim mode when processing many candidates

##### get_gene()
```python
async def get_gene(self, hgnc_id: str) -> Gene | ErrorEnvelope
```

Get complete gene record by HGNC CURIE (Phase 2 of Fuzzy-to-Fact). Returns full entity with cross-references to external databases.

**Parameters:**
- `hgnc_id` (str): HGNC CURIE in format 'HGNC:NNNNN' (e.g., 'HGNC:1100')

**Returns:**
- `Gene`: Complete gene record with all fields and cross-references
- `ErrorEnvelope`: On invalid CURIE format, not found, or upstream errors

**Example:**
```python
from lifesciences_mcp.clients import HGNCClient

async with HGNCClient() as client:
    # Get gene by CURIE
    gene = await client.get_gene("HGNC:1100")

    if isinstance(gene, Gene):
        print(f"Symbol: {gene.symbol}")
        print(f"Name: {gene.name}")
        print(f"Location: {gene.location}")

        # Access cross-references
        if gene.cross_references.ensembl_gene:
            print(f"Ensembl: {gene.cross_references.ensembl_gene}")
        if gene.cross_references.uniprot:
            print(f"UniProt: {', '.join(gene.cross_references.uniprot)}")
    else:
        # Handle error
        print(f"Error: {gene.error.message}")
        print(f"Recovery hint: {gene.error.recovery_hint}")
```

**Error Codes:**
- `UNRESOLVED_ENTITY`: Invalid CURIE format (not matching `HGNC:\d+`)
- `ENTITY_NOT_FOUND`: Valid CURIE but gene not found in HGNC
- `RATE_LIMITED`: Too many requests (429 response)
- `UPSTREAM_ERROR`: HGNC API failure (5xx errors)

**Best Practices:**
- Always validate CURIE format from search results
- Use search_genes first to resolve ambiguous identifiers
- Check cross_references for database linkage
- Handle all error codes with appropriate recovery actions

---

### UniProtClient

**File**: `src/lifesciences_mcp/clients/uniprot.py`

#### Description
UniProt REST API client for protein search and retrieval. Implements Fuzzy-to-Fact protocol with rate limiting and exponential backoff.

**Features:**
- Rate limiting at 10 requests/second
- Context manager support
- Cross-reference mapping to 22-key registry
- Slim mode for token budgeting

#### Constructor
```python
def __init__(self) -> None
```

**Example:**
```python
from lifesciences_mcp.clients import UniProtClient

async with UniProtClient() as client:
    result = await client.search_proteins("p53")
```

#### Methods

##### search_proteins()
```python
async def search_proteins(
    self,
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope[ProteinSearchCandidate] | ErrorEnvelope
```

Fuzzy search for proteins (Phase 1 of Fuzzy-to-Fact).

**Parameters:**
- `query` (str): Search term (protein name, accession, gene, organism). Minimum 2 characters
- `slim` (bool): Return minimal fields. Default: False
- `cursor` (str | None): Server-provided pagination cursor
- `page_size` (int): Results per page (1-500, default: 50)

**Returns:**
- `PaginationEnvelope[ProteinSearchCandidate]`: Paginated search results
- `ErrorEnvelope`: On errors

**Example:**
```python
async with UniProtClient() as client:
    # Search for p53 protein
    result = await client.search_proteins("p53")

    for candidate in result.items:
        print(f"{candidate.id}: {candidate.name}")
        print(f"  Organism: {candidate.organism}")
        print(f"  Genes: {', '.join(candidate.gene_names or [])}")
        print(f"  Score: {candidate.score}")

    # Search by organism
    result = await client.search_proteins("p53 AND organism_name:human")

    # Pagination using server cursor
    if result.pagination.cursor:
        next_page = await client.search_proteins(
            "p53",
            cursor=result.pagination.cursor
        )
```

**Best Practices:**
- Use specific queries (accessions, gene symbols) for best results
- UniProt search supports advanced query syntax (AND, OR, field:value)
- Check organism field to disambiguate proteins
- Server-side cursors expire after inactivity

##### get_protein()
```python
async def get_protein(
    self,
    uniprot_id: str,
    slim: bool = False
) -> Protein | ErrorEnvelope
```

Get complete protein record by UniProt CURIE (Phase 2 of Fuzzy-to-Fact).

**Parameters:**
- `uniprot_id` (str): UniProt CURIE in format 'UniProtKB:XXXXXX' (e.g., 'UniProtKB:P04637')
- `slim` (bool): Return minimal fields (id, name, organism only)

**Returns:**
- `Protein`: Complete protein record
- `ErrorEnvelope`: On errors

**Example:**
```python
async with UniProtClient() as client:
    # Get protein by CURIE
    protein = await client.get_protein("UniProtKB:P04637")

    if isinstance(protein, Protein):
        print(f"Name: {protein.name}")
        print(f"Function: {protein.function}")
        print(f"Length: {protein.sequence_length} amino acids")

        # Cross-references
        if protein.cross_references.hgnc:
            print(f"Gene: {protein.cross_references.hgnc}")
        if protein.cross_references.pdb:
            print(f"Structures: {', '.join(protein.cross_references.pdb[:5])}")

    # Slim mode
    slim_protein = await client.get_protein("UniProtKB:P04637", slim=True)
```

**CURIE Format:**
- Pattern: `^UniProtKB:[A-Z][A-Z0-9]{5,9}$`
- Examples: `UniProtKB:P04637` (Swiss-Prot), `UniProtKB:A0A123B4C5` (TrEMBL)
- Must start with uppercase letter, followed by 5-9 alphanumeric chars

**Best Practices:**
- Use search_proteins to resolve names to CURIEs
- Check cross_references for gene and structure linkage
- Slim mode reduces tokens from ~300 to ~20

---

### EnsemblClient

**File**: `src/lifesciences_mcp/clients/ensembl.py`

#### Description
Ensembl REST API client for gene and transcript data. Supports multi-species queries with intelligent species normalization.

**Features:**
- Rate limiting at 15 requests/second (Ensembl limit)
- Species aliasing ("human" → "homo_sapiens")
- Transcript expansion for gene records
- Cross-reference mapping

#### Constructor
```python
def __init__(self) -> None
```

**Example:**
```python
from lifesciences_mcp.clients import EnsemblClient

async with EnsemblClient() as client:
    result = await client.search_genes("BRCA1", species="human")
```

#### Methods

##### search_genes()
```python
async def search_genes(
    self,
    query: str,
    species: str = "homo_sapiens",
    page_size: int = 50,
    cursor: str | None = None,
    slim: bool = False,
) -> PaginationEnvelope[GeneSearchCandidate] | ErrorEnvelope
```

Fuzzy search for genes with species filtering.

**Parameters:**
- `query` (str): Gene symbol or name (minimum 2 characters)
- `species` (str): Species name or alias (default: "homo_sapiens")
- `page_size` (int): Results per page (1-100)
- `cursor` (str | None): Pagination cursor
- `slim` (bool): Minimal fields (included for API consistency)

**Returns:**
- `PaginationEnvelope[GeneSearchCandidate]`: Search results
- `ErrorEnvelope`: On errors

**Example:**
```python
async with EnsemblClient() as client:
    # Human genes
    result = await client.search_genes("TP53", species="human")

    # Mouse genes with species alias
    result = await client.search_genes("Brca1", species="mouse")

    # Full species name
    result = await client.search_genes("brca1", species="mus_musculus")

    for candidate in result.items:
        print(f"{candidate.symbol} ({candidate.id})")
        print(f"  {candidate.name}")
        print(f"  Biotype: {candidate.biotype}")
```

**Species Aliases:**
- `human` → `homo_sapiens`
- `mouse` → `mus_musculus`
- `rat` → `rattus_norvegicus`
- `zebrafish` → `danio_rerio`
- `fly` → `drosophila_melanogaster`
- `worm` → `caenorhabditis_elegans`
- `yeast` → `saccharomyces_cerevisiae`

**Best Practices:**
- Use common species aliases for convenience
- Check biotype field to filter protein-coding genes
- Symbol capitalization varies by species (TP53 for human, Tp53 for mouse)

##### get_gene()
```python
async def get_gene(
    self,
    ensembl_id: str,
    slim: bool = False
) -> EnsemblGene | ErrorEnvelope
```

Get complete gene record by Ensembl Gene ID.

**Parameters:**
- `ensembl_id` (str): Ensembl Gene ID in format 'ENSG + 11 digits' (e.g., 'ENSG00000141510')
- `slim` (bool): Omit cross_references to reduce token count

**Returns:**
- `EnsemblGene`: Complete gene record
- `ErrorEnvelope`: On errors

**Example:**
```python
async with EnsemblClient() as client:
    gene = await client.get_gene("ENSG00000141510")

    if isinstance(gene, EnsemblGene):
        print(f"Symbol: {gene.symbol}")
        print(f"Location: {gene.chromosome}:{gene.start}-{gene.end}")
        print(f"Assembly: {gene.assembly_name}")

        # Transcript list
        if gene.transcripts:
            print(f"Transcripts: {len(gene.transcripts)}")
            for transcript_id in gene.transcripts[:5]:
                print(f"  {transcript_id}")

        # Cross-references
        if gene.cross_references.hgnc:
            print(f"HGNC: {gene.cross_references.hgnc}")
```

**ID Format:**
- Pattern: `^ENSG\d{11}$`
- Example: `ENSG00000141510` (TP53)
- Version numbers (`.12`) are automatically stripped

**Best Practices:**
- Use search_genes to find valid Ensembl IDs
- Access transcripts list for alternative splicing analysis
- Check strand field for gene orientation (+1 or -1)

##### get_transcript()
```python
async def get_transcript(
    self,
    transcript_id: str,
    slim: bool = False
) -> EnsemblTranscript | ErrorEnvelope
```

Get transcript record by Ensembl Transcript ID.

**Parameters:**
- `transcript_id` (str): Ensembl Transcript ID in format 'ENST + 11 digits'
- `slim` (bool): Omit cross_references

**Returns:**
- `EnsemblTranscript`: Transcript record
- `ErrorEnvelope`: On errors

**Example:**
```python
async with EnsemblClient() as client:
    transcript = await client.get_transcript("ENST00000269305")

    if isinstance(transcript, EnsemblTranscript):
        print(f"Display name: {transcript.display_name}")
        print(f"Parent gene: {transcript.parent_gene}")
        print(f"Canonical: {transcript.is_canonical}")
        print(f"Biotype: {transcript.biotype}")
```

**Best Practices:**
- Get transcript IDs from gene.transcripts list
- Check is_canonical to identify primary isoform
- Use parent_gene to navigate back to gene record

---

### ChEMBLClient

**File**: `src/lifesciences_mcp/clients/chembl.py`

#### Description
ChEMBL API client for compound and bioactivity data. Uses synchronous SDK wrapped with async executor.

**Features:**
- Rate limiting at 10 requests/second
- Batch compound lookup (up to 100 compounds)
- Indication data (approved therapeutic uses)
- Cross-reference mapping

#### Constructor
```python
def __init__(self) -> None
```

**Example:**
```python
from lifesciences_mcp.clients import ChEMBLClient

client = ChEMBLClient()
try:
    result = await client.search_compounds("aspirin")
finally:
    await client.close()
```

#### Methods

##### search_compounds()
```python
async def search_compounds(
    self,
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope[CompoundSearchCandidate] | ErrorEnvelope
```

Fuzzy search for compounds.

**Parameters:**
- `query` (str): Search term (minimum 2 characters)
- `slim` (bool): Return minimal fields
- `cursor` (str | None): Pagination cursor
- `page_size` (int): Results per page (1-100)

**Returns:**
- `PaginationEnvelope[CompoundSearchCandidate]`: Search results
- `ErrorEnvelope`: On errors

**Example:**
```python
client = ChEMBLClient()

# Search by name
result = await client.search_compounds("aspirin")

for candidate in result.items:
    print(f"{candidate.id}: {candidate.name}")
    print(f"  Formula: {candidate.molecular_formula}")
    print(f"  Score: {candidate.score}")

# Search by molecular formula
result = await client.search_compounds("C9H8O4")

await client.close()
```

##### get_compound()
```python
async def get_compound(
    self,
    chembl_id: str,
    slim: bool = False
) -> dict[str, Any] | ErrorEnvelope
```

Get compound by ChEMBL CURIE.

**Parameters:**
- `chembl_id` (str): ChEMBL CURIE in format 'CHEMBL:NNNNN' (e.g., 'CHEMBL:25')
- `slim` (bool): Return minimal fields

**Returns:**
- `dict`: Compound record (or slim representation)
- `ErrorEnvelope`: On errors

**Example:**
```python
client = ChEMBLClient()

compound = await client.get_compound("CHEMBL:25")

if not isinstance(compound, ErrorEnvelope):
    print(f"Name: {compound['name']}")
    print(f"SMILES: {compound.get('smiles')}")
    print(f"Max Phase: {compound.get('max_phase')}")
    print(f"Indications: {', '.join(compound.get('indications', []))}")

    # Cross-references
    xrefs = compound.get('cross_references', {})
    if 'drugbank' in xrefs:
        print(f"DrugBank: {xrefs['drugbank']}")

await client.close()
```

**CURIE Format:**
- Pattern: `^CHEMBL:[0-9]+$`
- Examples: `CHEMBL:25` (aspirin), `CHEMBL:1201583`

##### get_compounds_batch()
```python
async def get_compounds_batch(
    self,
    chembl_ids: list[str],
    slim: bool = True
) -> list[dict[str, Any]] | ErrorEnvelope
```

Batch lookup for multiple compounds (maximum 100).

**Parameters:**
- `chembl_ids` (list[str]): List of ChEMBL CURIEs
- `slim` (bool): Return minimal fields (default: True for batch)

**Returns:**
- `list[dict]`: List of compound records (may include ErrorEnvelopes for individual failures)
- `ErrorEnvelope`: On batch validation errors

**Example:**
```python
client = ChEMBLClient()

# Batch lookup
chembl_ids = ["CHEMBL:25", "CHEMBL:192", "CHEMBL:621"]
results = await client.get_compounds_batch(chembl_ids)

for result in results:
    if 'error' not in result:
        print(f"{result['id']}: {result['name']}")
    else:
        print(f"Error: {result['error']['message']}")

await client.close()
```

**Best Practices:**
- Use batch lookup for efficiency when retrieving multiple compounds
- Default slim=True in batch mode to manage token usage
- Maximum 100 compounds per batch
- Individual compounds may fail while batch succeeds

---

### OpenTargetsClient

**File**: `src/lifesciences_mcp/clients/opentargets.py`

#### Description
Open Targets Platform GraphQL API client for target-disease associations and evidence.

**Features:**
- GraphQL query execution
- Rate limiting at 10 requests/second
- Target-disease association scoring
- Evidence source tracking

#### Constructor
```python
def __init__(self) -> None
```

**Example:**
```python
from lifesciences_mcp.clients import OpenTargetsClient

async with OpenTargetsClient() as client:
    result = await client.search_targets("TP53")
```

#### Methods

##### search_targets()
```python
async def search_targets(
    self,
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope[TargetSearchCandidate] | ErrorEnvelope
```

Fuzzy search for targets.

**Parameters:**
- `query` (str): Search term (minimum 2 characters)
- `slim` (bool): Return minimal fields
- `cursor` (str | None): Pagination cursor
- `page_size` (int): Results per page (1-100)

**Returns:**
- `PaginationEnvelope[TargetSearchCandidate]`: Search results
- `ErrorEnvelope`: On errors

**Example:**
```python
async with OpenTargetsClient() as client:
    result = await client.search_targets("kinase")

    for candidate in result.items:
        print(f"{candidate.approved_symbol} ({candidate.id})")
        print(f"  {candidate.approved_name}")
        print(f"  Score: {candidate.score}")
```

##### get_target()
```python
async def get_target(
    self,
    ensembl_id: str,
    slim: bool = False
) -> Target | dict | ErrorEnvelope
```

Get target by Ensembl gene ID.

**Parameters:**
- `ensembl_id` (str): Ensembl gene ID (format: ENSG[11 digits])
- `slim` (bool): Return minimal fields

**Returns:**
- `Target` or `dict`: Target record
- `ErrorEnvelope`: On errors

**Example:**
```python
async with OpenTargetsClient() as client:
    target = await client.get_target("ENSG00000141510")

    if isinstance(target, Target):
        print(f"Symbol: {target.approved_symbol}")
        print(f"Function: {target.description}")
        print(f"Biotype: {target.biotype}")

        # Cross-references
        if target.cross_references.hgnc:
            print(f"HGNC: {target.cross_references.hgnc}")
```

##### get_associations()
```python
async def get_associations(
    self,
    target_id: str,
    disease_id: str | None = None,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope[Association] | ErrorEnvelope
```

Get target-disease associations.

**Parameters:**
- `target_id` (str): Ensembl gene ID
- `disease_id` (str | None): Optional disease ID to filter (EFO/MONDO/Orphanet/HP/DOID/OTAR format)
- `cursor` (str | None): Pagination cursor
- `page_size` (int): Results per page (1-100)

**Returns:**
- `PaginationEnvelope[Association]`: Association records
- `ErrorEnvelope`: On errors

**Example:**
```python
async with OpenTargetsClient() as client:
    # Get all associations for TP53
    result = await client.get_associations("ENSG00000141510")

    for assoc in result.items:
        print(f"Disease: {assoc.disease_name}")
        print(f"  Score: {assoc.score}")
        print(f"  Evidence count: {assoc.evidence_count}")
        print(f"  Sources: {', '.join(assoc.evidence_sources)}")

    # Filter by disease
    cancer_result = await client.get_associations(
        "ENSG00000141510",
        disease_id="EFO_0000616"  # neoplasm
    )
```

**Disease ID Format:**
- Pattern: `^(EFO|MONDO|Orphanet|HP|DOID|OTAR)_\d+$`
- Examples: `EFO_0000616` (neoplasm), `MONDO_0005015` (diabetes)

---

## Data Models

All models use Pydantic for validation and serialization. Models follow the "omit-if-null" pattern: fields with no value are excluded from JSON output.

### Gene

**File**: `src/lifesciences_mcp/models/gene.py`

#### Description
Complete gene record from HGNC with Agentic Biolink cross-references.

#### Fields
- `id` (str): HGNC CURIE (format: `HGNC:\d+`, e.g., 'HGNC:1100')
- `symbol` (str): Official gene symbol (e.g., 'BRCA1')
- `name` (str): Full gene name
- `status` (str): Approval status ('Approved', 'Withdrawn', 'Entry Withdrawn')
- `locus_type` (str | None): Gene type classification
- `locus_group` (str | None): Gene group classification
- `location` (str | None): Chromosomal location (e.g., '17q21.31')
- `alias_symbols` (list[str] | None): Alternative symbols
- `alias_names` (list[str] | None): Alternative names
- `prev_symbols` (list[str] | None): Previous symbols
- `prev_names` (list[str] | None): Previous names
- `cross_references` (CrossReferences): External database identifiers

#### Example
```python
from lifesciences_mcp.models import Gene

# Create gene from API response
gene = Gene(
    id="HGNC:1100",
    symbol="BRCA1",
    name="BRCA1 DNA repair associated",
    status="Approved",
    locus_type="gene with protein product",
    location="17q21.31",
    cross_references={
        "ensembl_gene": "ENSG00000012048",
        "uniprot": ["P38398"],
        "entrez": "672"
    }
)

# Access fields
print(gene.symbol)  # BRCA1
print(gene.cross_references.ensembl_gene)  # ENSG00000012048

# JSON serialization (None values omitted)
json_data = gene.model_dump()
json_str = gene.model_dump_json()
```

#### Validation
- `id` must match pattern `HGNC:\d+`
- `status` must be one of: 'Approved', 'Withdrawn', 'Entry Withdrawn'
- Empty lists and empty strings are converted to None

---

### SearchCandidate

**File**: `src/lifesciences_mcp/models/gene.py`

#### Description
Lightweight gene representation for fuzzy search results. Token budget: ~20 tokens per entity.

#### Fields
- `id` (str): HGNC CURIE (pattern: `HGNC:\d+`)
- `symbol` (str): Official gene symbol
- `name` (str): Full gene name
- `score` (float): Relevance score (0.0-1.0, where 1.0 is perfect match)

#### Example
```python
from lifesciences_mcp.models import SearchCandidate

candidate = SearchCandidate(
    id="HGNC:1100",
    symbol="BRCA1",
    name="BRCA1 DNA repair associated",
    score=1.0
)

# Convert Gene to SearchCandidate
gene = await client.get_gene("HGNC:1100")
candidate = gene.to_search_candidate(score=0.95)
```

---

### CrossReferences

**File**: `src/lifesciences_mcp/models/gene.py`

#### Description
External database identifiers per the 22-key registry. Keys are omitted if no value exists.

#### Fields (22-key registry)

**Core identifiers:**
- `ensembl_gene` (str | None): Ensembl gene ID (e.g., ENSG00000012048)
- `ensembl_transcript` (list[str] | None): Ensembl transcript IDs
- `uniprot` (list[str] | None): UniProt accessions
- `entrez` (str | None): NCBI Entrez gene ID
- `refseq` (list[str] | None): RefSeq accessions
- `hgnc` (str | None): HGNC gene ID (e.g., HGNC:5)

**Disease/phenotype:**
- `omim` (str | None): OMIM ID
- `orphanet` (str | None): Orphanet rare disease ID (e.g., ORPHA:558)
- `mondo` (str | None): MONDO disease ontology ID
- `efo` (str | None): Experimental Factor Ontology ID

**Drug/compound:**
- `chembl` (str | None): ChEMBL target/compound ID
- `drugbank` (str | None): DrugBank ID (e.g., DB01050)
- `pubchem_compound` (str | None): PubChem compound ID
- `pubchem_substance` (str | None): PubChem substance ID

**Pathway databases:**
- `kegg` (str | None): KEGG gene ID
- `kegg_pathway` (list[str] | None): KEGG pathway IDs

**Interaction databases:**
- `string` (str | None): STRING protein ID
- `biogrid` (str | None): BioGRID gene ID
- `stitch` (str | None): STITCH chemical-protein interaction ID
- `iuphar` (str | None): IUPHAR/GtoPdb ligand or target ID

**Structural:**
- `pdb` (list[str] | None): Protein Data Bank IDs

#### Example
```python
from lifesciences_mcp.models import CrossReferences

# Create with some references
xrefs = CrossReferences(
    ensembl_gene="ENSG00000141510",
    uniprot=["P04637"],
    entrez="7157",
    pdb=["1TUP", "1TSR", "1YCR"]
)

# Access fields
print(xrefs.ensembl_gene)  # ENSG00000141510
print(xrefs.uniprot)  # ['P04637']

# JSON output omits None values
json_data = xrefs.model_dump()
# {'ensembl_gene': 'ENSG00000141510', 'uniprot': ['P04637'], 'entrez': '7157', 'pdb': ['1TUP', '1TSR', '1YCR']}
```

**Validation:**
- Empty strings and empty lists are automatically converted to None
- Fields with None values are excluded from JSON serialization
- Pattern validation for each ID type

---

### Protein

**File**: `src/lifesciences_mcp/models/protein.py`

#### Description
Complete protein record from UniProt with Agentic Biolink cross-references. Token budget: ~115-300 tokens in full mode, ~20 tokens in slim mode.

#### Fields
- `id` (str): UniProt CURIE (format: `UniProtKB:[A-Z][A-Z0-9]{5,9}`, e.g., 'UniProtKB:P04637')
- `accession` (str): Raw UniProt accession ID (e.g., 'P04637')
- `name` (str): Protein name
- `full_name` (str | None): Recommended full name
- `gene_names` (list[str] | None): Associated gene symbols
- `organism` (str): Scientific name (e.g., 'Homo sapiens')
- `organism_id` (int | None): NCBI Taxonomy ID
- `function` (str | None): Functional description
- `sequence_length` (int | None): Amino acid sequence length
- `cross_references` (CrossReferences): Cross-references to external databases

#### Example
```python
from lifesciences_mcp.models import Protein

protein = Protein(
    id="UniProtKB:P04637",
    accession="P04637",
    name="Cellular tumor antigen p53",
    full_name="Cellular tumor antigen p53",
    gene_names=["TP53", "P53"],
    organism="Homo sapiens",
    organism_id=9606,
    function="Acts as a tumor suppressor...",
    sequence_length=393,
    cross_references={
        "hgnc": "HGNC:11998",
        "ensembl_gene": "ENSG00000141510",
        "pdb": ["1TUP", "1TSR", "1YCR"]
    }
)

# Access fields
print(protein.name)
print(f"Length: {protein.sequence_length} aa")
print(f"Gene: {protein.gene_names[0]}")
```

**CURIE Validation:**
- Pattern: `^UniProtKB:[A-Z][A-Z0-9]{5,9}$`
- Must start with uppercase letter
- Followed by 5-9 uppercase alphanumeric characters
- Total accession length: 6-10 characters

---

### ProteinSearchCandidate

**File**: `src/lifesciences_mcp/models/protein.py`

#### Description
Lightweight protein match for fuzzy search results. Token budget: ~20 tokens per entity.

#### Fields
- `id` (str): UniProt CURIE
- `name` (str): Protein name
- `organism` (str): Scientific name
- `gene_names` (list[str] | None): Associated gene symbols
- `score` (float): Relevance score (0.0-1.0)

#### Example
```python
from lifesciences_mcp.models import ProteinSearchCandidate

candidate = ProteinSearchCandidate(
    id="UniProtKB:P04637",
    name="Cellular tumor antigen p53",
    organism="Homo sapiens",
    gene_names=["TP53"],
    score=1.0
)
```

---

### Compound

**File**: `src/lifesciences_mcp/models/compound.py`

#### Description
Complete ChEMBL compound record with Agentic Biolink cross-references. Token budget: ~115-300 tokens in full mode, ~20 tokens in slim mode.

#### Fields
- `id` (str): ChEMBL CURIE (format: `CHEMBL:[0-9]+`, e.g., 'CHEMBL:25')
- `name` (str | None): Preferred compound name
- `molecular_formula` (str | None): Molecular formula (e.g., 'C9H8O4')
- `molecular_weight` (float | None): Molecular weight in g/mol
- `smiles` (str | None): Simplified Molecular-Input Line-Entry System notation
- `inchi` (str | None): International Chemical Identifier
- `max_phase` (int | None): Maximum clinical phase (0-4) reached
- `indications` (list[str]): Approved indications (Mesh headings)
- `canonical_name` (str | None): Canonical IUPAC name
- `synonyms` (list[str]): Alternative names and trade names
- `cross_references` (dict[str, list[str]]): Cross-references using 22-key registry

#### Methods

##### to_slim()
```python
def to_slim(self) -> dict[str, Any]
```

Return slim representation with minimal fields (~20 tokens).

**Returns:**
- `dict`: Contains only id, name, and molecular_formula

#### Example
```python
from lifesciences_mcp.models import Compound

compound = Compound(
    id="CHEMBL:25",
    name="Aspirin",
    molecular_formula="C9H8O4",
    molecular_weight=180.16,
    smiles="CC(=O)Oc1ccccc1C(=O)O",
    max_phase=4,
    indications=["Pain", "Fever"],
    synonyms=["Acetylsalicylic acid", "ASA"],
    cross_references={
        "pubchem_compound": ["2244"],
        "drugbank": ["DB:00945"]
    }
)

# Slim mode
slim = compound.to_slim()
# {'id': 'CHEMBL:25', 'name': 'Aspirin', 'molecular_formula': 'C9H8O4'}
```

---

### Target

**File**: `src/lifesciences_mcp/models/target.py`

#### Description
Complete Open Targets target record with Agentic Biolink cross-references. Token budget: ~115-300 tokens in full mode, ~20 tokens in slim mode.

#### Fields
- `id` (str): Ensembl gene ID (pattern: `ENSG\d{11}`)
- `approved_symbol` (str | None): HGNC approved gene symbol
- `approved_name` (str | None): HGNC approved gene name
- `biotype` (str | None): Gene biotype (e.g., 'protein_coding', 'lncRNA')
- `description` (str | None): Gene function description
- `associated_diseases_count` (int | None): Total number of associated diseases
- `cross_references` (CrossReferences): Cross-references to external databases

#### Methods

##### to_slim()
```python
def to_slim(self) -> dict
```

Return slim mode representation (~20 tokens). Excludes description, associated_diseases_count, and cross_references.

#### Example
```python
from lifesciences_mcp.models import Target

target = Target(
    id="ENSG00000141510",
    approved_symbol="TP53",
    approved_name="tumor protein p53",
    biotype="protein_coding",
    description="Tumor suppressor gene...",
    associated_diseases_count=245,
    cross_references={
        "hgnc": "HGNC:11998",
        "uniprot": "UniProtKB:P04637"
    }
)

# Slim mode
slim = target.to_slim()
# {'id': 'ENSG00000141510', 'approved_symbol': 'TP53', 'approved_name': 'tumor protein p53', 'biotype': 'protein_coding'}
```

---

### Association

**File**: `src/lifesciences_mcp/models/target.py`

#### Description
Target-disease association with aggregated evidence. Token budget: ~60-80 tokens per association.

#### Fields
- `target_id` (str): Ensembl gene ID
- `disease_id` (str): Disease ID (format: `(EFO|MONDO|Orphanet|HP|DOID|OTAR)_\d+`)
- `disease_name` (str): Human-readable disease name
- `score` (float): Overall association score (0.0-1.0, higher = stronger evidence)
- `evidence_count` (int): Total number of evidence sources
- `evidence_sources` (list[str]): Data type IDs (e.g., 'genetic_association', 'somatic_mutation')

#### Example
```python
from lifesciences_mcp.models import Association

assoc = Association(
    target_id="ENSG00000141510",
    disease_id="EFO_0000616",
    disease_name="neoplasm",
    score=0.85,
    evidence_count=142,
    evidence_sources=["genetic_association", "somatic_mutation", "drugs"]
)
```

---

### EnsemblGene

**File**: `src/lifesciences_mcp/models/ensembl.py`

#### Description
Complete gene record from Ensembl with Agentic Biolink cross-references. Token budget: ~150-350 tokens.

#### Fields
- `id` (str): Ensembl Gene ID (pattern: `ENSG\d{11}`)
- `symbol` (str): Official gene symbol
- `name` (str): Gene description/name
- `biotype` (str): Gene biotype (e.g., 'protein_coding', 'lncRNA')
- `species` (str): Species name (e.g., 'homo_sapiens')
- `assembly_name` (str): Genome assembly (e.g., 'GRCh38')
- `chromosome` (str): Chromosome/seq_region_name
- `start` (int): Genomic start position
- `end` (int): Genomic end position
- `strand` (int): Strand (+1 or -1)
- `transcripts` (list[str] | None): List of Ensembl Transcript IDs
- `cross_references` (EnsemblCrossReferences): External database identifiers

#### Validation
- `id` must match pattern `ENSG\d{11}`
- `strand` must be 1 or -1
- `start` must be less than `end`

#### Example
```python
from lifesciences_mcp.models import EnsemblGene

gene = EnsemblGene(
    id="ENSG00000141510",
    symbol="TP53",
    name="tumor protein p53",
    biotype="protein_coding",
    species="homo_sapiens",
    assembly_name="GRCh38",
    chromosome="17",
    start=7661779,
    end=7687538,
    strand=-1,
    transcripts=["ENST00000269305", "ENST00000445888"],
    cross_references={
        "hgnc": "HGNC:11998",
        "uniprot": ["P04637"]
    }
)
```

---

## Envelope Models

All API responses use canonical envelope models for consistency.

### PaginationEnvelope

**File**: `src/lifesciences_mcp/models/envelopes.py`

#### Description
Canonical pagination envelope for all list/search operations per ADR-001 Section 8.

#### Fields
- `items` (list[T]): Data payload (generic type)
- `pagination` (Pagination): Pagination metadata

#### Pagination Metadata
- `cursor` (str | None): Opaque cursor for next page; null means end of results
- `total_count` (int | None): Total items if known (may be None for some APIs)
- `page_size` (int): Items per page (default: 50)

#### Class Methods

##### create()
```python
@classmethod
def create(
    cls,
    items: list[T],
    cursor: str | None = None,
    total_count: int | None = None,
    page_size: int = 50,
) -> "PaginationEnvelope[T]"
```

Create a pagination envelope with the given items and metadata.

#### Example
```python
from lifesciences_mcp.models import PaginationEnvelope, SearchCandidate

# Create envelope
candidates = [
    SearchCandidate(id="HGNC:1100", symbol="BRCA1", name="...", score=1.0),
    SearchCandidate(id="HGNC:5", symbol="A1BG", name="...", score=0.95)
]

envelope = PaginationEnvelope.create(
    items=candidates,
    cursor="eyJvZmZzZXQiOiA1MH0=",
    total_count=250,
    page_size=50
)

# Access fields
print(f"Results: {len(envelope.items)}")
print(f"Total: {envelope.pagination.total_count}")

# Check for more pages
if envelope.pagination.cursor:
    print("More results available")
```

---

### ErrorEnvelope

**File**: `src/lifesciences_mcp/models/envelopes.py`

#### Description
Canonical error envelope for all error responses. Provides actionable recovery hints for agent self-correction.

#### Fields
- `success` (bool): Always False for errors
- `error` (ErrorDetail): Error details with recovery hint

#### ErrorDetail Fields
- `code` (ErrorCode): Error code from registry (enum)
- `message` (str): Human-readable error message
- `recovery_hint` (str): Agent-actionable guidance for recovery
- `invalid_input` (str | None): The input that caused the error

#### Error Codes

```python
class ErrorCode(str, Enum):
    UNRESOLVED_ENTITY = "UNRESOLVED_ENTITY"      # Raw string passed to strict tool
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"        # Valid CURIE but no record
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"          # Too many/few results or invalid query
    RATE_LIMITED = "RATE_LIMITED"                # Too many requests
    UPSTREAM_ERROR = "UPSTREAM_ERROR"            # External API failure
    INVALID_CROSS_REFERENCE = "INVALID_CROSS_REFERENCE"  # Invalid xref format
```

#### Class Methods

##### unresolved_entity()
```python
@classmethod
def unresolved_entity(cls, invalid_input: str) -> "ErrorEnvelope"
```

Create UNRESOLVED_ENTITY error for raw string passed to strict tool.

##### entity_not_found()
```python
@classmethod
def entity_not_found(cls, hgnc_id: str) -> "ErrorEnvelope"
```

Create ENTITY_NOT_FOUND error for valid CURIE with no record.

##### ambiguous_query()
```python
@classmethod
def ambiguous_query(cls, query: str, result_count: int) -> "ErrorEnvelope"
```

Create AMBIGUOUS_QUERY error for too many or too few results.

##### rate_limited()
```python
@classmethod
def rate_limited(cls, retry_after: int | None = None) -> "ErrorEnvelope"
```

Create RATE_LIMITED error for upstream API throttling.

##### upstream_error()
```python
@classmethod
def upstream_error(cls, status_code: int, detail: str | None = None) -> "ErrorEnvelope"
```

Create UPSTREAM_ERROR for API failures.

#### Example
```python
from lifesciences_mcp.models import ErrorEnvelope, ErrorCode

# Check if response is error
result = await client.get_gene("invalid-id")

if isinstance(result, ErrorEnvelope):
    print(f"Error: {result.error.code}")
    print(f"Message: {result.error.message}")
    print(f"Recovery: {result.error.recovery_hint}")
    print(f"Input: {result.error.invalid_input}")

    # Handle specific error codes
    if result.error.code == ErrorCode.UNRESOLVED_ENTITY:
        # Try search instead
        search_result = await client.search_genes(result.error.invalid_input)
    elif result.error.code == ErrorCode.RATE_LIMITED:
        # Wait and retry
        await asyncio.sleep(60)
        retry_result = await client.get_gene("HGNC:1100")

# Create custom error
error = ErrorEnvelope.ambiguous_query("BR", 150)
```

**Error Recovery Patterns:**
- `UNRESOLVED_ENTITY`: Call search tool to resolve identifier
- `ENTITY_NOT_FOUND`: Verify ID or try alternate database
- `AMBIGUOUS_QUERY`: Refine query with more specific terms
- `RATE_LIMITED`: Wait specified time before retry
- `UPSTREAM_ERROR`: Retry after delay or try alternate source

---

## Server APIs

All servers use FastMCP framework and expose tools following the Fuzzy-to-Fact protocol.

### Gateway Server

**File**: `src/lifesciences_mcp/servers/gateway.py`

#### Description
Unified gateway server composing all 13 individual MCP servers into a single deployment. Provides access to all life sciences APIs through a consistent interface.

**Mounted Servers:**
- HGNC (gene nomenclature)
- UniProt (protein data)
- Ensembl (genomic data)
- ChEMBL (compound bioactivity)
- Open Targets (target-disease associations)
- STRING (protein interactions)
- BioGRID (genetic interactions)
- Entrez (NCBI genes)
- PubChem (chemical compounds)
- IUPHAR (pharmacology)
- WikiPathways (biological pathways)
- ClinicalTrials (clinical trials)

**Note:** DrugBank is excluded (requires commercial API key)

#### Available Tools

All tools are prefixed with database name:

**HGNC:**
- `hgnc_search_genes`: Fuzzy gene search
- `hgnc_get_gene`: Strict gene lookup

**UniProt:**
- `uniprot_search_proteins`: Fuzzy protein search
- `uniprot_get_protein`: Strict protein lookup

**ChEMBL:**
- `chembl_search_compounds`: Fuzzy compound search
- `chembl_get_compound`: Strict compound lookup
- `chembl_get_compounds_batch`: Batch compound lookup

**Open Targets:**
- `opentargets_search_targets`: Fuzzy target search
- `opentargets_get_target`: Strict target lookup
- `opentargets_get_associations`: Target-disease associations

**STRING:**
- `string_search_proteins`: Fuzzy protein search
- `string_get_interactions`: Protein-protein interactions
- `string_get_network_image_url`: Network visualization URL

**BioGRID:**
- `biogrid_search_genes`: Fuzzy gene search
- `biogrid_get_interactions`: Genetic/protein interactions

**Ensembl:**
- `ensembl_search_genes`: Fuzzy gene search
- `ensembl_get_gene`: Strict gene lookup
- `ensembl_get_transcript`: Transcript lookup

**Entrez:**
- `entrez_search_genes`: Fuzzy gene search
- `entrez_get_gene`: Strict gene lookup
- `entrez_get_pubmed_links`: PubMed literature links

**PubChem:**
- `pubchem_search_compounds`: Fuzzy compound search
- `pubchem_get_compound`: Strict compound lookup

**IUPHAR:**
- `iuphar_search_ligands`: Fuzzy ligand search
- `iuphar_get_ligand`: Strict ligand lookup
- `iuphar_search_targets`: Fuzzy target search
- `iuphar_get_target`: Strict target lookup

**WikiPathways:**
- `wikipathways_search_pathways`: Fuzzy pathway search
- `wikipathways_get_pathway`: Strict pathway lookup
- `wikipathways_get_pathways_for_gene`: Pathways containing gene
- `wikipathways_get_pathway_components`: Pathway components

**ClinicalTrials:**
- `clinicaltrials_search_trials`: Fuzzy trial search
- `clinicaltrials_get_trial`: Strict trial lookup
- `clinicaltrials_get_trial_locations`: Trial locations

#### Configuration

```python
# Run locally
uv run fastmcp run src/lifesciences_mcp/servers/gateway.py

# FastMCP Cloud deployment
# Entrypoint: src/lifesciences_mcp/servers/gateway.py:mcp
```

#### Example Usage

```python
# Connect to gateway via MCP protocol
# (Typically done by LLM client like Claude)

# Example tool call sequence:
# 1. Fuzzy search
response = await call_tool("hgnc_search_genes", {"query": "BRCA1"})

# 2. Extract CURIE from top candidate
hgnc_id = response.items[0].id  # "HGNC:1100"

# 3. Strict lookup
gene = await call_tool("hgnc_get_gene", {"hgnc_id": hgnc_id})

# 4. Cross-database navigation
ensembl_id = gene.cross_references.ensembl_gene
ensembl_gene = await call_tool("ensembl_get_gene", {"ensembl_id": ensembl_id})

# 5. Protein lookup
if gene.cross_references.uniprot:
    uniprot_id = f"UniProtKB:{gene.cross_references.uniprot[0]}"
    protein = await call_tool("uniprot_get_protein", {"uniprot_id": uniprot_id})
```

**Best Practices:**
- Use prefixed tool names to avoid conflicts
- Follow Fuzzy-to-Fact: search → get → cross-reference
- Handle ErrorEnvelopes at each step
- Use slim mode for exploratory searches
- Batch operations where available (chembl_get_compounds_batch)

---

### HGNC Server

**File**: `src/lifesciences_mcp/servers/hgnc.py`

#### Description
HGNC MCP server providing gene resolution using the Fuzzy-to-Fact protocol.

#### Tools

##### search_genes
```python
async def search_genes(
    query: str,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope[SearchCandidate] | ErrorEnvelope
```

Fuzzy search for genes by name, symbol, synonym, or description.

**Parameters:**
- `query` (str): Search term (minimum 2 characters)
- `slim` (bool): Return minimal fields (~20 tokens per entity)
- `cursor` (str | None): Opaque pagination cursor
- `page_size` (int): Results per page (1-100, default: 50)

**Example:**
```python
# Via MCP tool call
result = await call_tool("search_genes", {
    "query": "BRCA1",
    "page_size": 10
})

for candidate in result.items:
    print(f"{candidate.symbol}: {candidate.score}")
```

##### get_gene
```python
async def get_gene(hgnc_id: str) -> Gene | ErrorEnvelope
```

Get complete gene record by HGNC CURIE.

**Parameters:**
- `hgnc_id` (str): HGNC CURIE (format: 'HGNC:NNNNN')

**Example:**
```python
# Via MCP tool call
gene = await call_tool("get_gene", {"hgnc_id": "HGNC:1100"})

if not gene.error:
    print(f"Symbol: {gene.symbol}")
    print(f"Ensembl: {gene.cross_references.ensembl_gene}")
```

#### Configuration

```python
# Run standalone
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
```

---

## Orchestration APIs

High-level utilities for multi-database search and aggregation.

### UnifiedSearch

**File**: `src/lifesciences_agent/aggregator.py`

#### Description
Experimental aggregator for resolving biological entities across multiple databases. Orchestrates queries across HGNC, UniProt, and Open Targets with intelligent re-ranking.

**Features:**
- Multi-database search aggregation
- Alias-aware boosting (e.g., "p53" → "TP53")
- Exact symbol match prioritization
- Configurable result limits

#### Constructor
```python
def __init__(self)
```

Creates client instances for HGNC, UniProt, and Open Targets.

#### Methods

##### search()
```python
async def search(
    self,
    query: str,
    limit: int = 10
) -> PaginationEnvelope[SearchCandidate]
```

Search across multiple databases and re-rank results.

**Parameters:**
- `query` (str): Search term
- `limit` (int): Maximum results to return (default: 10)

**Returns:**
- `PaginationEnvelope[SearchCandidate]`: Re-ranked search results from all databases

**Example:**
```python
from lifesciences_agent.aggregator import UnifiedSearch

# Create aggregator
searcher = UnifiedSearch()

# Search across databases
result = await searcher.search("p53", limit=5)

for candidate in result.items:
    print(f"{candidate.symbol}: {candidate.score}")
    # Expected: TP53 appears first due to alias boosting

# Close clients
await searcher.hgnc.close()
await searcher.uniprot.close()
await searcher.opentargets.close()
```

**Re-ranking Logic:**
1. Collects results from HGNC (extensible to other sources)
2. Applies boosting heuristics:
   - Exact symbol match: +2.0 score boost
   - Known alias match (e.g., "p53" → "TP53"): +2.0 boost
3. Sorts by boosted score descending
4. Returns top N results

**Best Practices:**
- Use for ambiguous queries where single-database search may miss results
- Consider cross-database ID mapping for comprehensive coverage
- Experimental: may change in future versions

---

## Utility Functions and Helpers

### Cross-Reference Utilities

Cross-reference mapping is built into client classes:

**HGNCClient._build_cross_references()**
- Maps HGNC response fields to CrossReferences model
- Omits keys with no value
- Handles OMIM list format

**UniProtClient._map_cross_references()**
- Maps UniProt xrefs to 22-key registry
- Limits PDB structures to first 10
- Normalizes CURIE formats

**EnsemblClient._map_cross_references()**
- Maps Ensembl xrefs to EnsemblCrossReferences model
- Handles RefSeq, UniProt, PDB, KEGG, ChEMBL
- Applies CURIE prefixes where needed

**ChEMBLClient._build_cross_references()**
- Maps ChEMBL cross_references array to registry
- Normalizes DrugBank, UniProt, PDB formats
- Omits unmapped sources

**OpenTargetsClient._build_cross_references()**
- Maps GraphQL dbXrefs to CrossReferences
- Applies CURIE normalization per source
- Handles Open Targets specific formats

---

### Error Handling

All clients use consistent error handling patterns:

**Rate Limiting:**
- Exponential backoff on 429/403/503 errors
- Respects Retry-After header when present
- Thundering herd prevention (re-check timing after lock)
- Maximum retry attempts: 3 (configurable per client)

**Network Errors:**
- Timeout errors return UPSTREAM_ERROR
- Connection errors return UPSTREAM_ERROR with recovery hint
- All httpx exceptions wrapped in ErrorEnvelope

**Validation Errors:**
- CURIE format validation before API calls
- Returns UNRESOLVED_ENTITY for invalid format
- Query length validation (minimum 2 characters)

**Error Mapping:**
- 404 → ENTITY_NOT_FOUND
- 429/403 → RATE_LIMITED
- 400 → AMBIGUOUS_QUERY or UNRESOLVED_ENTITY
- 5xx → UPSTREAM_ERROR

**Example Error Handling:**
```python
from lifesciences_mcp.clients import HGNCClient
from lifesciences_mcp.models import ErrorEnvelope, ErrorCode

async with HGNCClient() as client:
    result = await client.get_gene("invalid-format")

    if isinstance(result, ErrorEnvelope):
        if result.error.code == ErrorCode.UNRESOLVED_ENTITY:
            # Try search instead
            print(f"Invalid CURIE: {result.error.invalid_input}")
            print(f"Recovery: {result.error.recovery_hint}")

            search_result = await client.search_genes(result.error.invalid_input)
            if search_result.items:
                # Retry with resolved CURIE
                gene = await client.get_gene(search_result.items[0].id)

        elif result.error.code == ErrorCode.RATE_LIMITED:
            # Wait and retry
            retry_after = 60  # default
            if "Wait" in result.error.recovery_hint:
                # Parse retry time from hint
                pass
            await asyncio.sleep(retry_after)
```

---

## Configuration Reference

### Environment Variables

Currently, the system does not require environment variables for most APIs. Future implementations may add:

- `HGNC_API_KEY`: Optional API key for higher rate limits
- `CHEMBL_API_KEY`: Optional API key (not currently required)
- `DRUGBANK_API_KEY`: Required for DrugBank access (not implemented)
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

### Rate Limiting Configuration

Each client has built-in rate limiting:

**HGNC:**
- Rate: 10 requests/second
- Delay: 100ms between requests
- Constant: `RATE_LIMIT_DELAY = 0.1`

**UniProt:**
- Rate: 10 requests/second (conservative)
- Delay: 100ms between requests
- Constant: `RATE_LIMIT_DELAY = 0.1`

**Ensembl:**
- Rate: 15 requests/second
- Delay: 66.67ms between requests
- Constant: `RATE_LIMIT_DELAY = 1.0 / 15`

**ChEMBL:**
- Rate: 10 requests/second
- Delay: 100ms between requests
- Constants: `RATE_LIMIT_REQUESTS = 10`, `RATE_LIMIT_PERIOD = 1.0`

**Open Targets:**
- Rate: 10 requests/second
- Delay: 100ms between requests
- Constant: `RATE_LIMIT_DELAY = 0.1`

**Customization:**
Rate limits are defined as class constants and can be modified by subclassing (not recommended - may violate API terms).

### Pagination Configuration

**Default Page Sizes:**
- HGNC: 50 (range: 1-100)
- UniProt: 50 (range: 1-500)
- Ensembl: 50 (range: 1-100)
- ChEMBL: 50 (range: 1-100)
- Open Targets: 50 (range: 1-100)

**Cursor Formats:**
- HGNC: Base64 JSON with offset (`{"offset": 50}`)
- UniProt: Server-provided opaque cursor
- Ensembl: Base64 JSON with offset
- ChEMBL: Base64 JSON with offset
- Open Targets: Base64 JSON with index and size

**Example Pagination:**
```python
async with HGNCClient() as client:
    # First page
    result = await client.search_genes("kinase", page_size=25)
    all_results = list(result.items)

    # Subsequent pages
    cursor = result.pagination.cursor
    while cursor:
        result = await client.search_genes("kinase", page_size=25, cursor=cursor)
        all_results.extend(result.items)
        cursor = result.pagination.cursor

    print(f"Total results: {len(all_results)}")
```

---

## Usage Patterns and Best Practices

### Pattern 1: Fuzzy-to-Fact Search

The canonical workflow for resolving biological entities:

```python
from lifesciences_mcp.clients import HGNCClient

async with HGNCClient() as client:
    # Phase 1: Fuzzy search
    search_result = await client.search_genes("BRCA")

    # Validate and select candidate
    if search_result.items:
        top_candidate = search_result.items[0]
        print(f"Top match: {top_candidate.symbol} (score: {top_candidate.score})")

        # Phase 2: Fact retrieval with CURIE
        gene = await client.get_gene(top_candidate.id)

        if isinstance(gene, Gene):
            print(f"Confirmed: {gene.symbol} - {gene.name}")
            print(f"Location: {gene.location}")
```

**When to Use:**
- User provides ambiguous input (gene name, partial symbol)
- Need to validate existence before detailed lookup
- Want ranked alternatives for disambiguation

**Anti-pattern:**
- Skipping search and guessing CURIE format
- Using get_* methods with user-provided strings

### Pattern 2: Cross-Database Navigation

Leverage cross-references to navigate between databases:

```python
from lifesciences_mcp.clients import HGNCClient, UniProtClient, EnsemblClient

async with HGNCClient() as hgnc, \
           UniProtClient() as uniprot, \
           EnsemblClient() as ensembl:

    # Start with gene
    gene = await hgnc.get_gene("HGNC:11998")

    # Navigate to Ensembl
    if gene.cross_references.ensembl_gene:
        ensembl_gene = await ensembl.get_gene(
            gene.cross_references.ensembl_gene
        )
        print(f"Transcripts: {len(ensembl_gene.transcripts or [])}")

    # Navigate to UniProt
    if gene.cross_references.uniprot:
        uniprot_id = f"UniProtKB:{gene.cross_references.uniprot[0]}"
        protein = await uniprot.get_protein(uniprot_id)
        print(f"Protein: {protein.name}")
        print(f"Function: {protein.function}")

        # Navigate to PDB structures
        if protein.cross_references.pdb:
            print(f"Structures: {', '.join(protein.cross_references.pdb[:5])}")
```

**When to Use:**
- Need comprehensive entity information
- Building knowledge graphs
- Validating cross-database consistency

**Best Practices:**
- Check cross_reference existence before navigation
- Handle ErrorEnvelopes at each step
- Use slim mode for intermediate lookups

### Pattern 3: Batch Operations

Efficient retrieval of multiple entities:

```python
from lifesciences_mcp.clients import ChEMBLClient

client = ChEMBLClient()

try:
    # Search to get CURIEs
    search_result = await client.search_compounds("kinase inhibitor", page_size=20)

    # Extract CURIEs
    chembl_ids = [c.id for c in search_result.items[:10]]

    # Batch lookup (max 100)
    compounds = await client.get_compounds_batch(chembl_ids, slim=True)

    # Process results
    for compound in compounds:
        if 'error' not in compound:
            print(f"{compound['name']}: Phase {compound.get('max_phase', 'N/A')}")
        else:
            print(f"Error: {compound['error']['message']}")

finally:
    await client.close()
```

**When to Use:**
- Retrieving multiple related entities
- Building comparison tables
- Bulk data extraction

**Best Practices:**
- Respect batch size limits (100 for ChEMBL)
- Use slim mode to reduce token usage
- Handle individual failures within batch
- Consider rate limiting for large batches

### Pattern 4: Error Recovery

Robust error handling with automatic recovery:

```python
from lifesciences_mcp.clients import HGNCClient
from lifesciences_mcp.models import ErrorEnvelope, ErrorCode
import asyncio

async def resilient_gene_lookup(query: str, max_retries: int = 3) -> Gene | None:
    """Lookup gene with automatic error recovery."""
    async with HGNCClient() as client:
        # Try search first
        search_result = await client.search_genes(query)

        if isinstance(search_result, ErrorEnvelope):
            if search_result.error.code == ErrorCode.AMBIGUOUS_QUERY:
                # Query too broad, refine
                print(f"Refining query: {query}")
                search_result = await client.search_genes(f"{query} homo sapiens")
            elif search_result.error.code == ErrorCode.RATE_LIMITED:
                # Wait and retry
                await asyncio.sleep(60)
                search_result = await client.search_genes(query)
            else:
                print(f"Search failed: {search_result.error.message}")
                return None

        # Get top candidate
        if not search_result.items:
            print("No results found")
            return None

        candidate = search_result.items[0]

        # Retry get_gene with backoff
        for attempt in range(max_retries):
            gene = await client.get_gene(candidate.id)

            if isinstance(gene, Gene):
                return gene

            if gene.error.code == ErrorCode.RATE_LIMITED:
                wait_time = 2 ** attempt
                print(f"Rate limited, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                print(f"Lookup failed: {gene.error.message}")
                return None

        return None

# Usage
gene = await resilient_gene_lookup("BRCA1")
if gene:
    print(f"Found: {gene.symbol}")
```

**When to Use:**
- Production systems requiring reliability
- Automated workflows
- Handling unpredictable user input

**Best Practices:**
- Always check for ErrorEnvelope
- Use error.recovery_hint for guidance
- Implement exponential backoff for rate limiting
- Log errors for debugging
- Set maximum retry limits

---

## Appendix

### Type Definitions

Common types used across the API:

```python
# Generic pagination type
T = TypeVar("T")
PaginationEnvelope[T]

# Union types for responses
SearchResult = PaginationEnvelope[SearchCandidate] | ErrorEnvelope
GeneResult = Gene | ErrorEnvelope
ProteinResult = Protein | ErrorEnvelope

# Cross-reference types
CrossRefValue = str | list[str] | None
```

### Error Codes

Complete error code reference with descriptions and recovery strategies:

| Code | Description | Recovery Strategy |
|------|-------------|-------------------|
| `UNRESOLVED_ENTITY` | Invalid CURIE format or raw string passed to strict lookup | Call search tool to resolve identifier to valid CURIE |
| `ENTITY_NOT_FOUND` | Valid CURIE but entity not found in database | Verify CURIE spelling, try alternate database, or search for synonyms |
| `AMBIGUOUS_QUERY` | Query too broad (>100 results) or too short (<2 chars) | Add more specific terms, use exact symbols, or filter by organism/type |
| `RATE_LIMITED` | Too many requests to upstream API | Wait specified time (check recovery_hint), implement exponential backoff |
| `UPSTREAM_ERROR` | External API failure (timeout, 5xx error, network issue) | Retry after delay, check API status page, try alternate data source |
| `INVALID_CROSS_REFERENCE` | Cross-reference ID format invalid | Verify ID format, check source database documentation |

**Example Error Message Formats:**

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

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "HGNC API rate limit exceeded.",
    "recovery_hint": "Retry after 60 seconds.",
    "invalid_input": null
  }
}
```

### Common CURIE Formats

Reference for valid CURIE formats across databases:

| Database | Format | Pattern | Example |
|----------|--------|---------|---------|
| HGNC | HGNC:NNNNN | `^HGNC:\d+$` | HGNC:1100 |
| UniProt | UniProtKB:XXXXXX | `^UniProtKB:[A-Z][A-Z0-9]{5,9}$` | UniProtKB:P04637 |
| Ensembl Gene | ENSGXXXXXXXXXXX | `^ENSG\d{11}$` | ENSG00000141510 |
| Ensembl Transcript | ENSTXXXXXXXXXXX | `^ENST\d{11}$` | ENST00000269305 |
| ChEMBL | CHEMBL:NNNNN | `^CHEMBL:[0-9]+$` | CHEMBL:25 |
| Entrez | Raw number | `^\d+$` | 7157 |
| OMIM | NNNNNN | `^\d{6}$` | 191170 |
| RefSeq | NM_NNNNNN | `^[NX][MR]_\d+$` | NM_000546 |
| PDB | 1ABC | `^[0-9][A-Z0-9]{3}$` | 1TUP |

### Source File Reference

Complete mapping of files to APIs:

**Client Files:**
- `src/lifesciences_mcp/clients/base.py`: LifeSciencesClient base class
- `src/lifesciences_mcp/clients/hgnc.py`: HGNCClient
- `src/lifesciences_mcp/clients/uniprot.py`: UniProtClient
- `src/lifesciences_mcp/clients/ensembl.py`: EnsemblClient
- `src/lifesciences_mcp/clients/chembl.py`: ChEMBLClient
- `src/lifesciences_mcp/clients/opentargets.py`: OpenTargetsClient

**Model Files:**
- `src/lifesciences_mcp/models/gene.py`: Gene, SearchCandidate, CrossReferences
- `src/lifesciences_mcp/models/protein.py`: Protein, ProteinSearchCandidate
- `src/lifesciences_mcp/models/compound.py`: Compound, CompoundSearchCandidate
- `src/lifesciences_mcp/models/target.py`: Target, TargetSearchCandidate, Association
- `src/lifesciences_mcp/models/ensembl.py`: EnsemblGene, EnsemblTranscript, GeneSearchCandidate
- `src/lifesciences_mcp/models/envelopes.py`: PaginationEnvelope, ErrorEnvelope, ErrorCode

**Server Files:**
- `src/lifesciences_mcp/servers/gateway.py`: Gateway server (all databases)
- `src/lifesciences_mcp/servers/hgnc.py`: HGNC MCP server

**Orchestration Files:**
- `src/lifesciences_agent/aggregator.py`: UnifiedSearch

---

**Document Version:** 1.0
**Last Updated:** 2026-01-07
**API Version:** Based on codebase commit 4308911
