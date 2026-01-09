# API Reference

## Overview

The Life Sciences MCP provides unified access to 13 major life sciences databases through a standardized FastMCP-based API. This reference documents all public client classes, model classes, MCP server tools, and configuration options.

**Key Features:**
- **Fuzzy-to-Fact Protocol**: Two-phase resolution (search → get) for all entity types
- **Cross-Database Navigation**: 22-key registry enables seamless data integration
- **Rate Limiting**: Client-side enforcement prevents upstream API throttling
- **Connection Pooling**: Persistent HTTP connections for performance
- **Token Efficiency**: Slim mode reduces token usage by ~80%
- **Error Recovery**: Canonical error envelopes with agent-actionable hints

**Deployment:**
- **Gateway Endpoint**: `https://lifesciences-research.fastmcp.app/mcp`
- **Protocol**: JSON-RPC 2.0 over HTTP/SSE
- **Python Package**: `lifesciences_mcp` (version 0.1.0)

---

## Table of Contents

- [Quick Start](#quick-start)
- [Client Classes](#client-classes)
- [Model Classes](#model-classes)
- [MCP Server Tools](#mcp-server-tools)
- [Configuration](#configuration)
- [Usage Patterns](#usage-patterns)
- [Best Practices](#best-practices)
- [Appendices](#appendices)

---

## Quick Start

### Installation

```bash
pip install lifesciences-mcp
```

### Basic Usage (Python Client)

```python
from lifesciences_mcp import HGNCClient, ErrorEnvelope

# Context manager handles connection lifecycle
async with HGNCClient() as client:
    # Phase 1: Fuzzy search
    result = await client.search_genes("BRCA1", page_size=10)

    if isinstance(result, ErrorEnvelope):
        print(f"Error: {result.error.message}")
        return

    # Get top candidate
    top_gene = result.items[0]
    print(f"Found: {top_gene.symbol} (score: {top_gene.score})")

    # Phase 2: Strict lookup
    gene = await client.get_gene(top_gene.id)
    if not isinstance(gene, ErrorEnvelope):
        print(f"Location: {gene.location}")
        print(f"UniProt IDs: {gene.cross_references.uniprot}")
```

### MCP Tool Usage (JSON-RPC)

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "hgnc_search_genes",
    "arguments": {
      "query": "BRCA1",
      "page_size": 10
    }
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"items\": [...], \"pagination\": {...}}"
    }]
  }
}
```

---

## Client Classes

All clients inherit from `LifeSciencesClient` base class and implement the Fuzzy-to-Fact protocol with two core operations:
1. **`search_*(query, ...)`**: Fuzzy search returning ranked candidates with pagination
2. **`get_*(id)`**: Strict lookup by validated CURIE identifier

### Base Client

#### `LifeSciencesClient`

**Location**: `src/lifesciences_mcp/clients/base.py`

Base async HTTP client providing shared functionality for all API clients.

**Key Features:**
- Async httpx client with connection pooling (max 10 connections)
- Granular timeout configuration (connect: 5s, read: 30s, write: 10s, pool: 5s)
- Standard Accept header for JSON responses
- Context manager support for lifecycle management

**Constructor:**
```python
__init__(base_url: str, timeout: float = 30.0, max_connections: int = 10)
```

**Methods:**
- `async _get_client() -> httpx.AsyncClient` - Get or create HTTP client
- `async close() -> None` - Close HTTP client and release connections
- `async _get(path: str, **kwargs) -> httpx.Response` - Make GET request

---

### HGNC Client

#### `HGNCClient`

**Location**: `src/lifesciences_mcp/clients/hgnc.py`

HGNC Gene Nomenclature Committee API client for gene symbol resolution.

**Base URL**: `https://rest.genenames.org`
**Rate Limit**: 10 requests/second (100ms delay)
**Inherits From**: `LifeSciencesClient`

**Methods:**

##### `search_genes(query, slim=False, cursor=None, page_size=50)`

Fuzzy search for human genes (Phase 1 of Fuzzy-to-Fact).

**Parameters:**
- `query` (str): Gene symbol, name, alias, or natural language query (min 2 chars)
- `slim` (bool): Return minimal fields for token efficiency (default: False)
- `cursor` (str | None): Opaque cursor for pagination
- `page_size` (int): Results per page (1-100, default: 50)

**Returns**: `PaginationEnvelope[SearchCandidate] | ErrorEnvelope`

**Search Strategy:**
1. Searches alias_symbol field for exact alias matches (boosted to score=1.0)
2. Searches general endpoint for symbol/name matches
3. Merges results with exact symbol matches prioritized

**Scoring:**
- Exact symbol match: 1.0
- Alias match: 1.0
- Position-based decay: 0.95 - (position * 0.05)

##### `get_gene(hgnc_id)`

Get complete gene record by HGNC CURIE (Phase 2 of Fuzzy-to-Fact).

**Parameters:**
- `hgnc_id` (str): HGNC CURIE in format `HGNC:NNNNN` (e.g., `HGNC:1100`)

**Returns**: `Gene | ErrorEnvelope`

**Validation**: Enforces CURIE format before API call

**Example:**

```python
from lifesciences_mcp import HGNCClient

async with HGNCClient() as client:
    # Fuzzy search
    results = await client.search_genes("breast cancer 1", page_size=5)

    if not isinstance(results, ErrorEnvelope):
        top_hit = results.items[0]  # Highest score
        print(f"Top match: {top_hit.symbol} (score: {top_hit.score})")

        # Strict lookup
        gene = await client.get_gene(top_hit.id)
        if not isinstance(gene, ErrorEnvelope):
            print(f"Official name: {gene.name}")
            print(f"Location: {gene.location}")
            print(f"Ensembl ID: {gene.cross_references.ensembl_gene}")
```

**See Also**: [Gene model](#gene-models), [hgnc_search_genes tool](#hgnc-tools)

---

### UniProt Client

#### `UniProtClient`

**Location**: `src/lifesciences_mcp/clients/uniprot.py`

UniProt protein database client for protein sequences and annotations.

**Base URL**: `https://rest.uniprot.org`
**Rate Limit**: 10 requests/second
**Inherits From**: `LifeSciencesClient`

**Methods:**

##### `search_proteins(query, organism=None, slim=False, cursor=None, page_size=50)`

Fuzzy search for proteins with optional organism filtering.

**Parameters:**
- `query` (str): Protein name, gene symbol, or accession
- `organism` (str | None): Scientific name (e.g., "Homo sapiens")
- `slim` (bool): Return minimal fields
- `cursor` (str | None): Pagination cursor
- `page_size` (int): Results per page (1-500)

**Returns**: `PaginationEnvelope[ProteinSearchCandidate] | ErrorEnvelope`

##### `get_protein(uniprot_id, slim=False)`

Get complete protein record by UniProt accession.

**Parameters:**
- `uniprot_id` (str): UniProt accession (e.g., `P04637`) or CURIE (`UniProtKB:P04637`)
- `slim` (bool): Exclude large text fields

**Returns**: `Protein | ErrorEnvelope`

**Example:**

```python
from lifesciences_mcp import UniProtClient

async with UniProtClient() as client:
    # Search for human TP53 protein
    results = await client.search_proteins("TP53", organism="Homo sapiens")

    if not isinstance(results, ErrorEnvelope):
        protein = await client.get_protein(results.items[0].id)
        if not isinstance(protein, ErrorEnvelope):
            print(f"Function: {protein.function}")
            print(f"Length: {protein.sequence_length} amino acids")
```

**See Also**: [Protein model](#protein-models), [uniprot_search_proteins tool](#uniprot-tools)

---

### ChEMBL Client

#### `ChEMBLClient`

**Location**: `src/lifesciences_mcp/clients/chembl.py`

ChEMBL bioactivity database client for compounds and drug data.

**Base URL**: `https://www.ebi.ac.uk/chembl/api/data`
**Rate Limit**: 10 requests/second with exponential backoff
**Inherits From**: `LifeSciencesClient`
**Note**: Uses synchronous `chembl_webresource_client` SDK wrapped with `asyncio.run_in_executor()`

**Methods:**

##### `search_compounds(query, slim=False, cursor=None, page_size=50)`

Fuzzy search for chemical compounds.

**Parameters:**
- `query` (str): Compound name, synonym, or identifier
- `slim` (bool): Return minimal fields (~20 tokens vs ~100+)
- `cursor` (str | None): Pagination cursor (Base64-encoded offset)
- `page_size` (int): Results per page (1-100)

**Returns**: `PaginationEnvelope[CompoundSearchCandidate] | ErrorEnvelope`

##### `get_compound(chembl_id, slim=False)`

Get complete compound record by ChEMBL CURIE.

**Parameters:**
- `chembl_id` (str): ChEMBL CURIE (e.g., `CHEMBL:25`)
- `slim` (bool): Exclude drug indications (separate API call)

**Returns**: `dict[str, Any] | ErrorEnvelope`

##### `get_compounds_batch(chembl_ids, slim=True)`

Batch retrieve multiple compounds (max 100).

**Parameters:**
- `chembl_ids` (list[str]): List of ChEMBL CURIEs
- `slim` (bool): Exclude indications for performance

**Returns**: `list[dict[str, Any]] | ErrorEnvelope`

**Example:**

```python
from lifesciences_mcp import ChEMBLClient

async with ChEMBLClient() as client:
    # Search for aspirin
    results = await client.search_compounds("aspirin", page_size=5)

    if not isinstance(results, ErrorEnvelope):
        # Get full record
        compound = await client.get_compound(results.items[0].id)
        if not isinstance(compound, ErrorEnvelope):
            print(f"SMILES: {compound.get('smiles')}")
            print(f"Max phase: {compound.get('max_phase')}")
```

**See Also**: [Compound model](#compound-models), [chembl_search_compounds tool](#chembl-tools)

---

### Open Targets Client

#### `OpenTargetsClient`

**Location**: `src/lifesciences_mcp/clients/opentargets.py`

Open Targets Platform client for target-disease associations.

**Base URL**: `https://api.platform.opentargets.org/api/v4`
**API Type**: GraphQL
**Rate Limit**: 10 requests/second

**Methods:**

##### `search_targets(query, cursor=None, page_size=50)`

Search for therapeutic targets.

**Returns**: `PaginationEnvelope[TargetSearchCandidate] | ErrorEnvelope`

##### `get_target(target_id)`

Get target details by Ensembl gene ID.

**Returns**: `Target | ErrorEnvelope`

##### `get_associations(target_id, disease_id=None, cursor=None, page_size=50)`

Get target-disease associations with evidence scores.

**Returns**: `PaginationEnvelope[Association] | ErrorEnvelope`

**See Also**: [Target model](#target-models), [opentargets_search_targets tool](#opentargets-tools)

---

### STRING Client

#### `STRINGClient`

**Location**: `src/lifesciences_mcp/clients/string.py`

STRING database client for protein-protein interaction networks.

**Base URL**: `https://string-db.org/api`
**Rate Limit**: 1 request/second (strict)
**Default Species**: 9606 (Homo sapiens)

**Methods:**

##### `search_proteins(query, limit=10)`

Search for proteins to get STRING IDs.

**Returns**: `PaginationEnvelope[InteractionSearchCandidate] | ErrorEnvelope`

##### `get_interactions(string_id, score_threshold=400, limit=100)`

Get protein interaction network.

**Parameters:**
- `string_id` (str): STRING protein ID (e.g., `9606.ENSP00000269305`)
- `score_threshold` (int): Minimum confidence score (0-1000, default: 400 = medium)
- `limit` (int): Max interactions to return

**Returns**: `InteractionNetwork | ErrorEnvelope`

**Example:**

```python
from lifesciences_mcp import STRINGClient

async with STRINGClient(species=9606) as client:
    # Search for TP53
    results = await client.search_proteins("TP53")

    if not isinstance(results, ErrorEnvelope):
        # Get interaction network
        network = await client.get_interactions(
            results.items[0].id,
            score_threshold=700  # High confidence
        )
        if not isinstance(network, ErrorEnvelope):
            print(f"Found {len(network.interactions)} interactions")
            for interaction in network.interactions[:5]:
                print(f"  {interaction.preferred_name_b}: {interaction.score}")
```

**See Also**: [Interaction model](#interaction-models), [string_get_interactions tool](#string-tools)

---

### Other Client Classes

#### `EnsemblClient`
**Purpose**: Ensembl genomic database (genes, transcripts)
**Base URL**: `https://rest.ensembl.org`
**Methods**: `search_genes()`, `get_gene()`, `get_transcript()`

#### `EntrezClient`
**Purpose**: NCBI Entrez/Gene database
**Base URL**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
**Methods**: `search_genes()`, `get_gene()`, `get_pubmed_links()`
**Note**: Optional API key via `NCBI_API_KEY` environment variable

#### `BioGridClient`
**Purpose**: BioGRID genetic and protein interactions
**Base URL**: `https://webservice.thebiogrid.org`
**Methods**: `search_genes()`, `get_interactions()`
**Note**: Requires free API key via `BIOGRID_API_KEY`

#### `PubChemClient`
**Purpose**: PubChem chemical compound database
**Base URL**: `https://pubchem.ncbi.nlm.nih.gov/rest/pug`
**Methods**: `search_compounds()`, `get_compound()`

#### `IUPHARClient`
**Purpose**: IUPHAR/Guide to Pharmacology (ligands and targets)
**Base URL**: `https://www.guidetopharmacology.org/services`
**Methods**: `search_ligands()`, `get_ligand()`, `search_targets()`, `get_target()`

#### `WikiPathwaysClient`
**Purpose**: WikiPathways biological pathway database
**Base URL**: `https://webservice.wikipathways.org`
**Methods**: `search_pathways()`, `get_pathway()`, `get_pathways_for_gene()`, `get_pathway_components()`

#### `ClinicalTrialsClient`
**Purpose**: ClinicalTrials.gov clinical study database
**Base URL**: `https://clinicaltrials.gov/api/v2`
**Methods**: `search_trials()`, `get_trial()`, `get_trial_locations()`

#### `DrugBankClient`
**Purpose**: DrugBank drug database
**Base URL**: `https://api.drugbank.com`
**Methods**: `search_drugs()`, `get_drug()`
**Note**: Requires commercial API key; excluded from gateway

---

## Model Classes

All models are Pydantic v2 BaseModel subclasses with validation and serialization.

### Envelope Models

#### `ErrorEnvelope`

**Location**: `src/lifesciences_mcp/models/envelopes.py`

Canonical error response format for all tools.

**Fields:**
- `success` (bool): Always `False`
- `error` (ErrorDetail): Error details with recovery hint

**ErrorDetail Fields:**
- `code` (ErrorCode): Standard error code enum
- `message` (str): Human-readable error message
- `recovery_hint` (str): Agent-actionable guidance for self-correction
- `invalid_input` (str | None): The input that caused the error

**Error Codes:**
- `UNRESOLVED_ENTITY`: Raw string passed to strict tool (need fuzzy search first)
- `ENTITY_NOT_FOUND`: Valid CURIE but no record in database
- `AMBIGUOUS_QUERY`: Too many results or too generic query
- `RATE_LIMITED`: Upstream API throttling
- `UPSTREAM_ERROR`: API failure or network error
- `INVALID_CROSS_REFERENCE`: Cross-reference format validation failed

**Factory Methods:**
```python
ErrorEnvelope.unresolved_entity(invalid_input)
ErrorEnvelope.entity_not_found(hgnc_id)
ErrorEnvelope.ambiguous_query(query, result_count)
ErrorEnvelope.rate_limited(retry_after=None)
ErrorEnvelope.upstream_error(status_code, detail=None)
```

#### `PaginationEnvelope[T]`

**Location**: `src/lifesciences_mcp/models/envelopes.py`

Generic pagination wrapper for list operations.

**Fields:**
- `items` (list[T]): Data payload
- `pagination` (Pagination): Pagination metadata

**Pagination Fields:**
- `cursor` (str | None): Opaque cursor for next page (null = end)
- `total_count` (int | None): Total items if known
- `page_size` (int): Items per page

**Factory Method:**
```python
PaginationEnvelope.create(items, cursor=None, total_count=None, page_size=50)
```

---

### Gene Models

#### `Gene`

**Location**: `src/lifesciences_mcp/models/gene.py`

Complete gene record from HGNC with cross-references.

**Key Fields:**
- `id` (str): HGNC CURIE (e.g., `HGNC:1100`)
- `symbol` (str): Official gene symbol (e.g., `BRCA1`)
- `name` (str): Full gene name
- `status` (str): Approval status (Approved, Withdrawn, Entry Withdrawn)
- `location` (str | None): Chromosomal location (e.g., `17q21.31`)
- `alias_symbols` (list[str] | None): Alternative symbols
- `prev_symbols` (list[str] | None): Previous symbols
- `cross_references` (CrossReferences): External database IDs

**Token Count**: ~115-300 tokens depending on cross-references

#### `SearchCandidate`

Lightweight gene representation for fuzzy search (~20 tokens).

**Key Fields:**
- `id` (str): HGNC CURIE
- `symbol` (str): Gene symbol
- `name` (str): Gene name
- `score` (float): Relevance score (0.0-1.0)

#### `CrossReferences`

**Location**: `src/lifesciences_mcp/models/gene.py`

External database identifiers per 22-key registry. Keys omitted if no value (never null).

**Core Identifiers:**
- `ensembl_gene` (str | None): Ensembl gene ID (e.g., `ENSG00000012048`)
- `ensembl_transcript` (list[str] | None): Ensembl transcript IDs
- `uniprot` (list[str] | None): UniProt accessions
- `entrez` (str | None): NCBI Entrez gene ID
- `refseq` (list[str] | None): RefSeq accessions
- `hgnc` (str | None): HGNC gene ID

**Disease/Phenotype:**
- `omim` (str | None): OMIM ID
- `orphanet` (str | None): Orphanet rare disease ID
- `mondo` (str | None): MONDO disease ontology ID
- `efo` (str | None): Experimental Factor Ontology ID

**Drug/Compound:**
- `chembl` (str | None): ChEMBL target/compound ID
- `drugbank` (str | None): DrugBank ID
- `pubchem_compound` (str | None): PubChem compound ID
- `pubchem_substance` (str | None): PubChem substance ID

**Pathway:**
- `kegg` (str | None): KEGG gene ID
- `kegg_pathway` (list[str] | None): KEGG pathway IDs

**Interaction:**
- `string` (str | None): STRING protein ID
- `biogrid` (str | None): BioGRID gene ID
- `stitch` (str | None): STITCH chemical-protein ID
- `iuphar` (str | None): IUPHAR/GtoPdb ligand or target ID

**Structural:**
- `pdb` (list[str] | None): Protein Data Bank IDs

**Method:**
- `model_dump(**kwargs)`: Excludes None values (ADR-001 principle)

---

### Protein Models

#### `Protein`

**Location**: `src/lifesciences_mcp/models/protein.py`

Complete protein record from UniProt.

**Key Fields:**
- `id` (str): UniProt CURIE (e.g., `UniProtKB:P04637`)
- `accession` (str): Raw accession (e.g., `P04637`)
- `name` (str): Protein name
- `gene_names` (list[str] | None): Associated gene symbols
- `organism` (str): Scientific name
- `function` (str | None): Functional description
- `sequence_length` (int | None): Amino acid count
- `cross_references` (CrossReferences): External database IDs

#### `ProteinSearchCandidate`

Lightweight protein for search results.

**Key Fields:**
- `id`, `name`, `organism`, `gene_names`, `score`

---

### Compound Models

#### `Compound`

**Location**: `src/lifesciences_mcp/models/compound.py`

Chemical compound from ChEMBL.

**Key Fields:**
- `id` (str): ChEMBL CURIE (e.g., `CHEMBL:25`)
- `name` (str): Compound name
- `molecular_formula` (str | None): Chemical formula
- `molecular_weight` (float | None): Molecular weight
- `smiles` (str | None): SMILES notation
- `inchi` (str | None): InChI identifier
- `max_phase` (int | None): Clinical development phase (0-4)
- `indications` (list[dict] | None): Drug indications
- `synonyms` (list[str] | None): Alternative names
- `cross_references` (dict): Cross-references to other databases

**Method:**
- `to_slim()`: Returns minimal dict for token efficiency

#### `CompoundSearchCandidate`

Lightweight compound for search results.

---

### Interaction Models

#### `InteractionNetwork`

**Location**: `src/lifesciences_mcp/models/interaction.py`

Protein-protein interaction network from STRING.

**Key Fields:**
- `query_protein_id` (str): STRING ID of query protein
- `interactions` (list[Interaction]): List of interactions
- `cross_references` (InteractionCrossReferences): Cross-references for network

#### `Interaction`

Single protein-protein interaction.

**Key Fields:**
- `protein_a` (str): STRING ID of first protein
- `protein_b` (str): STRING ID of second protein
- `preferred_name_a` (str): Gene symbol for protein A
- `preferred_name_b` (str): Gene symbol for protein B
- `score` (int): Combined confidence score (0-1000)
- `evidence_scores` (EvidenceScores): Breakdown by evidence type

#### `EvidenceScores`

Evidence type breakdown for STRING interactions.

**Fields:**
- `neighborhood` (int): Genomic neighborhood
- `fusion` (int): Gene fusion
- `cooccurrence` (int): Phylogenetic co-occurrence
- `coexpression` (int): Co-expression
- `experimental` (int): Experimental data
- `database` (int): Curated databases
- `textmining` (int): Text mining
- `combined_score` (int): Combined confidence (0-1000)

---

### Target Models

#### `Target`

**Location**: `src/lifesciences_mcp/models/target.py`

Therapeutic target from Open Targets.

**Key Fields:**
- `id` (str): Ensembl gene ID
- `approved_symbol` (str): Gene symbol
- `approved_name` (str): Gene name
- `biotype` (str): Gene biotype
- `associations` (list[Association]): Target-disease associations

#### `Association`

Target-disease association from Open Targets.

**Key Fields:**
- `disease_id` (str): Disease ID
- `disease_name` (str): Disease name
- `score` (float): Association score (0.0-1.0)
- `datasource_count` (int): Number of supporting data sources

---

### Pathway Models

#### `Pathway`

**Location**: `src/lifesciences_mcp/models/pathway.py`

Biological pathway from WikiPathways.

**Key Fields:**
- `id` (str): WikiPathways CURIE (e.g., `WP:254`)
- `title` (str): Pathway title
- `organism` (str): Organism name
- `description` (str | None): Pathway description
- `url` (str): WikiPathways URL
- `component_counts` (ComponentCounts): Gene/metabolite counts

#### `PathwayComponents`

**Location**: `src/lifesciences_mcp/models/pathway_components.py`

Detailed pathway components.

**Key Fields:**
- `pathway_id` (str): WikiPathways ID
- `genes` (list[DataNode]): Gene nodes
- `metabolites` (list[DataNode]): Metabolite nodes
- `interactions` (list[Interaction]): Pathway interactions

---

### Trial Models

#### `Trial`

**Location**: `src/lifesciences_mcp/models/trial.py`

Clinical trial from ClinicalTrials.gov.

**Key Fields:**
- `id` (str): NCT number (e.g., `NCT03997058`)
- `title` (str): Brief title
- `status` (str): Recruitment status
- `phase` (str): Clinical phase
- `conditions` (list[str]): Medical conditions
- `interventions` (list[str]): Interventions being studied
- `sponsor` (Sponsor): Lead sponsor and collaborators
- `eligibility` (EligibilityCriteria): Inclusion/exclusion criteria

#### `TrialLocation`

**Location**: `src/lifesciences_mcp/models/trial_location.py`

Study site location.

**Key Fields:**
- `facility_name` (str): Facility name
- `city`, `state`, `country` (str): Location
- `recruitment_status` (str): Site-specific status

---

### Database-Specific Models

#### `EntrezGene`
**Location**: `src/lifesciences_mcp/models/entrez.py`
**Purpose**: NCBI Gene records with PubMed links

#### `EnsemblGene`, `EnsemblTranscript`
**Location**: `src/lifesciences_mcp/models/ensembl.py`
**Purpose**: Ensembl genomic data

#### `PubChemCompound`
**Location**: `src/lifesciences_mcp/models/pubchem_compound.py`
**Purpose**: PubChem chemical compounds

#### `Ligand`, `PharmacologicalTarget`
**Location**: `src/lifesciences_mcp/models/pharmacology.py`
**Purpose**: IUPHAR pharmacology data

#### `Drug`, `DrugSearchCandidate`
**Location**: `src/lifesciences_mcp/models/drug.py`
**Purpose**: DrugBank drug records

#### `GeneticInteraction`, `InteractionResult`
**Location**: `src/lifesciences_mcp/models/biogrid.py`
**Purpose**: BioGRID interaction data

---

## MCP Server Tools

All tools accessible via the gateway server at `https://lifesciences-research.fastmcp.app/mcp`.

### Tools Summary

| Database | Search Tool | Get Tool | Additional Tools | Total |
|----------|------------|----------|------------------|-------|
| HGNC | `hgnc_search_genes` | `hgnc_get_gene` | - | 2 |
| UniProt | `uniprot_search_proteins` | `uniprot_get_protein` | - | 2 |
| ChEMBL | `chembl_search_compounds` | `chembl_get_compound` | `chembl_get_compounds_batch` | 3 |
| Open Targets | `opentargets_search_targets` | `opentargets_get_target` | `opentargets_get_associations` | 3 |
| STRING | `string_search_proteins` | `string_get_interactions` | `string_get_network_image_url` | 3 |
| BioGRID | `biogrid_search_genes` | `biogrid_get_interactions` | - | 2 |
| Ensembl | `ensembl_search_genes` | `ensembl_get_gene` | `ensembl_get_transcript` | 3 |
| Entrez | `entrez_search_genes` | `entrez_get_gene` | `entrez_get_pubmed_links` | 3 |
| PubChem | `pubchem_search_compounds` | `pubchem_get_compound` | - | 2 |
| IUPHAR | `iuphar_search_ligands`, `iuphar_search_targets` | `iuphar_get_ligand`, `iuphar_get_target` | - | 4 |
| WikiPathways | `wikipathways_search_pathways` | `wikipathways_get_pathway` | `wikipathways_get_pathways_for_gene`, `wikipathways_get_pathway_components` | 4 |
| ClinicalTrials | `clinicaltrials_search_trials` | `clinicaltrials_get_trial` | `clinicaltrials_get_trial_locations` | 3 |
| **Total** | | | | **34** |

### Tool Parameters

#### Standard Parameters (All Search Tools)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search term (min 2 chars) |
| `slim` | boolean | No | false | Return minimal fields |
| `cursor` | string | No | null | Opaque pagination cursor |
| `page_size` | integer | No | 50 | Results per page (1-100) |

#### Standard Parameters (All Get Tools)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `{id}` | string | Yes | - | CURIE identifier (e.g., `HGNC:1100`) |
| `slim` | boolean | No | false | Exclude large fields |

---

### HGNC Tools

#### `hgnc_search_genes`

**Server**: `hgnc.py`
**Description**: Fuzzy search for human genes in HGNC database

**Parameters:**
- `query` (string, required): Gene symbol, name, alias, or natural language
- `slim` (boolean, optional): Return minimal fields (default: false)
- `cursor` (string, optional): Pagination cursor
- `page_size` (integer, optional): Results per page (1-100, default: 50)

**Returns**: `PaginationEnvelope[SearchCandidate]` or `ErrorEnvelope`

**Features:**
- Alias boosting (aliases get score=1.0)
- Position-based scoring for non-exact matches
- Ambiguity detection (>100 results with <3 char query)

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "hgnc_search_genes",
    "arguments": {
      "query": "BRCA1",
      "page_size": 5
    }
  }
}
```

#### `hgnc_get_gene`

**Description**: Get complete gene record by HGNC CURIE

**Parameters:**
- `hgnc_id` (string, required): HGNC CURIE (format: `HGNC:NNNNN`)

**Returns**: `Gene` or `ErrorEnvelope`

**Validation**: Enforces CURIE format (rejects raw gene symbols)

**See Also**: [HGNCClient](#hgnc-client), [Gene model](#gene-models)

---

### UniProt Tools

#### `uniprot_search_proteins`

**Description**: Search for proteins with optional organism filtering

**Parameters:**
- `query` (string, required): Protein name, gene symbol, or accession
- `organism` (string, optional): Scientific name (e.g., "Homo sapiens")
- `slim` (boolean, optional): Return minimal fields
- `cursor` (string, optional): Pagination cursor
- `page_size` (integer, optional): Results per page (1-500)

**Returns**: `PaginationEnvelope[ProteinSearchCandidate]` or `ErrorEnvelope`

#### `uniprot_get_protein`

**Description**: Get protein record by UniProt accession

**Parameters:**
- `uniprot_id` (string, required): UniProt accession or CURIE
- `slim` (boolean, optional): Exclude large text fields

**Returns**: `Protein` or `ErrorEnvelope`

---

### ChEMBL Tools

#### `chembl_search_compounds`

**Description**: Search for chemical compounds

**Parameters:**
- `query` (string, required): Compound name, synonym, or identifier
- `slim` (boolean, optional): Return minimal fields (~20 tokens)
- Standard pagination parameters

**Returns**: `PaginationEnvelope[CompoundSearchCandidate]` or `ErrorEnvelope`

#### `chembl_get_compound`

**Description**: Get compound record by ChEMBL CURIE

**Parameters:**
- `chembl_id` (string, required): ChEMBL CURIE (format: `CHEMBL:NNNNN`)
- `slim` (boolean, optional): Exclude drug indications

**Returns**: `dict[str, Any]` or `ErrorEnvelope`

#### `chembl_get_compounds_batch`

**Description**: Batch retrieve up to 100 compounds

**Parameters:**
- `chembl_ids` (array[string], required): List of ChEMBL CURIEs (max 100)
- `slim` (boolean, optional): Exclude indications (default: true)

**Returns**: `list[dict[str, Any]]` or `ErrorEnvelope`

**Performance**: ~10x faster than individual requests for large batches

---

### STRING Tools

#### `string_search_proteins`

**Description**: Search for proteins to get STRING IDs

**Parameters:**
- `query` (string, required): Protein name or gene symbol
- `limit` (integer, optional): Max results (default: 10)

**Returns**: `PaginationEnvelope[InteractionSearchCandidate]` or `ErrorEnvelope`

#### `string_get_interactions`

**Description**: Get protein-protein interaction network

**Parameters:**
- `string_id` (string, required): STRING protein ID (format: `9606.ENSP00000269305`)
- `score_threshold` (integer, optional): Min confidence (0-1000, default: 400)
- `limit` (integer, optional): Max interactions (default: 100)

**Returns**: `InteractionNetwork` or `ErrorEnvelope`

**Score Thresholds:**
- 150: Low confidence
- 400: Medium confidence (default)
- 700: High confidence
- 900: Highest confidence

#### `string_get_network_image_url`

**Description**: Get URL to network visualization

**Parameters:**
- `string_ids` (array[string], required): List of STRING IDs
- `network_flavor` (string, optional): Visualization type (default: "evidence")

**Returns**: `string` (URL)

---

### WikiPathways Tools

#### `wikipathways_search_pathways`

**Description**: Search for biological pathways

**Parameters:**
- `query` (string, required): Pathway name or gene symbol
- `organism` (string, optional): Organism name (default: "Homo sapiens")
- Standard pagination parameters

**Returns**: `PaginationEnvelope[PathwaySearchCandidate]` or `ErrorEnvelope`

#### `wikipathways_get_pathway`

**Description**: Get pathway details by WikiPathways ID

**Parameters:**
- `pathway_id` (string, required): WikiPathways ID (e.g., `WP:254`)

**Returns**: `Pathway` or `ErrorEnvelope`

#### `wikipathways_get_pathways_for_gene`

**Description**: Find pathways containing a specific gene

**Parameters:**
- `gene_symbol` (string, required): Gene symbol (e.g., "TP53")
- `organism` (string, optional): Organism (default: "Homo sapiens")

**Returns**: `PaginationEnvelope[PathwaySearchCandidate]` or `ErrorEnvelope`

#### `wikipathways_get_pathway_components`

**Description**: Get detailed pathway components (genes, metabolites, interactions)

**Parameters:**
- `pathway_id` (string, required): WikiPathways ID

**Returns**: `PathwayComponents` or `ErrorEnvelope`

---

### Other Tool Groups

#### Open Targets Tools
- `opentargets_search_targets`: Search therapeutic targets
- `opentargets_get_target`: Get target details
- `opentargets_get_associations`: Get target-disease associations

#### Ensembl Tools
- `ensembl_search_genes`: Search genes by symbol or name
- `ensembl_get_gene`: Get gene by Ensembl ID
- `ensembl_get_transcript`: Get transcript details

#### Entrez Tools
- `entrez_search_genes`: Search NCBI Gene database
- `entrez_get_gene`: Get gene by Entrez ID
- `entrez_get_pubmed_links`: Get PubMed references for gene

#### BioGRID Tools
- `biogrid_search_genes`: Search for genes
- `biogrid_get_interactions`: Get genetic and protein interactions

#### PubChem Tools
- `pubchem_search_compounds`: Search chemical compounds
- `pubchem_get_compound`: Get compound by PubChem CID

#### IUPHAR Tools
- `iuphar_search_ligands`: Search pharmacological ligands
- `iuphar_get_ligand`: Get ligand details
- `iuphar_search_targets`: Search drug targets
- `iuphar_get_target`: Get target details

#### ClinicalTrials Tools
- `clinicaltrials_search_trials`: Search clinical trials
- `clinicaltrials_get_trial`: Get trial details by NCT number
- `clinicaltrials_get_trial_locations`: Get trial site locations

---

## Configuration

### Environment Variables

#### API Keys (Optional/Required)

```bash
# Optional but recommended (increases rate limit)
NCBI_API_KEY=your_ncbi_api_key

# Required for BioGRID
BIOGRID_API_KEY=your_biogrid_api_key

# Required for DrugBank (commercial)
DRUGBANK_API_KEY=your_drugbank_api_key
```

#### Rate Limiting (Custom Overrides)

```bash
# Override default rate limits (requests per second)
HGNC_RATE_LIMIT=10
UNIPROT_RATE_LIMIT=10
CHEMBL_RATE_LIMIT=10
STRING_RATE_LIMIT=1
PUBCHEM_RATE_LIMIT=5
```

#### Connection Pooling

```bash
# Max concurrent connections per client
HTTPX_MAX_CONNECTIONS=10

# Keep-alive connection pool size
HTTPX_MAX_KEEPALIVE_CONNECTIONS=10
```

#### Timeouts

```bash
# Request timeout in seconds
HTTPX_CONNECT_TIMEOUT=5.0
HTTPX_READ_TIMEOUT=30.0
HTTPX_WRITE_TIMEOUT=10.0
HTTPX_POOL_TIMEOUT=5.0
```

### Loading Environment Variables

```python
from dotenv import load_dotenv
load_dotenv()  # Load from .env file
```

### Client Configuration

```python
from lifesciences_mcp.clients import HGNCClient

# Use defaults
client = HGNCClient()

# Custom configuration (advanced)
from lifesciences_mcp.clients.base import LifeSciencesClient

custom_client = LifeSciencesClient(
    base_url="https://custom.api.url",
    timeout=60.0,
    max_connections=20
)
```

---

## Usage Patterns

### Pattern 1: Fuzzy-to-Fact Workflow

The recommended workflow for entity resolution.

```python
from lifesciences_mcp import HGNCClient, ErrorEnvelope

async with HGNCClient() as client:
    # Step 1: Fuzzy search (user input)
    results = await client.search_genes("breast cancer 1")

    if isinstance(results, ErrorEnvelope):
        print(f"Error: {results.error.recovery_hint}")
        return

    # Step 2: User selects best match
    top_match = results.items[0]
    print(f"Selected: {top_match.symbol} (score: {top_match.score})")

    # Step 3: Strict lookup (authoritative data)
    gene = await client.get_gene(top_match.id)

    if not isinstance(gene, ErrorEnvelope):
        print(f"Location: {gene.location}")
        print(f"Status: {gene.status}")
```

### Pattern 2: Cross-Database Navigation

Use cross-references to navigate between databases.

```python
from lifesciences_mcp import HGNCClient, UniProtClient, STRINGClient

# Start with gene symbol
async with HGNCClient() as hgnc:
    genes = await hgnc.search_genes("TP53")
    gene = await hgnc.get_gene(genes.items[0].id)

    # Navigate to UniProt
    uniprot_id = gene.cross_references.uniprot[0]

async with UniProtClient() as uniprot:
    protein = await uniprot.get_protein(uniprot_id)

    # Navigate to STRING (use gene symbol)
    async with STRINGClient() as string:
        proteins = await string.search_proteins(gene.symbol)
        network = await string.get_interactions(proteins.items[0].id)

        print(f"Found {len(network.interactions)} interactions")
```

### Pattern 3: Pagination

Handle large result sets with cursor-based pagination.

```python
from lifesciences_mcp import HGNCClient

async with HGNCClient() as client:
    cursor = None
    all_results = []

    # Fetch first 3 pages
    for page_num in range(3):
        results = await client.search_genes("kinase", cursor=cursor, page_size=50)

        if isinstance(results, ErrorEnvelope):
            break

        all_results.extend(results.items)
        cursor = results.pagination.cursor

        if cursor is None:  # No more pages
            break

        print(f"Page {page_num + 1}: {len(results.items)} results")

    print(f"Total: {len(all_results)} results")
```

### Pattern 4: Error Handling

Use recovery hints for agent self-correction.

```python
from lifesciences_mcp import HGNCClient, ErrorEnvelope
from lifesciences_mcp.models.envelopes import ErrorCode

async with HGNCClient() as client:
    result = await client.get_gene("BRCA1")  # Wrong: should be CURIE

    if isinstance(result, ErrorEnvelope):
        if result.error.code == ErrorCode.UNRESOLVED_ENTITY:
            # Agent learns: need to search first
            print(f"Recovery: {result.error.recovery_hint}")

            # Try correct approach
            search = await client.search_genes("BRCA1")
            if not isinstance(search, ErrorEnvelope):
                gene = await client.get_gene(search.items[0].id)
```

### Pattern 5: Batch Operations

Optimize performance for multiple entities.

```python
from lifesciences_mcp import ChEMBLClient

async with ChEMBLClient() as client:
    # Search for multiple compounds
    compound_ids = []
    for name in ["aspirin", "ibuprofen", "paracetamol"]:
        results = await client.search_compounds(name, page_size=1)
        if not isinstance(results, ErrorEnvelope):
            compound_ids.append(results.items[0].id)

    # Batch retrieve (much faster)
    compounds = await client.get_compounds_batch(compound_ids, slim=True)

    if not isinstance(compounds, ErrorEnvelope):
        for compound in compounds:
            print(f"{compound['name']}: {compound['molecular_formula']}")
```

### Pattern 6: Slim Mode for Token Efficiency

Reduce token usage by ~80%.

```python
from lifesciences_mcp import HGNCClient

async with HGNCClient() as client:
    # Regular mode: ~115-300 tokens per gene
    gene_full = await client.get_gene("HGNC:1100")

    # Slim mode: ~20 tokens per gene
    search_results = await client.search_genes("BRCA1", slim=True, page_size=10)

    # Use slim for large result sets
    # Use full for detailed analysis
```

---

## Best Practices

### 1. Always Use Context Managers
- Ensures proper connection cleanup
- Prevents resource leaks
- Handles exceptions gracefully

```python
# Good
async with HGNCClient() as client:
    result = await client.search_genes("TP53")

# Bad (manual cleanup required)
client = HGNCClient()
result = await client.search_genes("TP53")
await client.close()  # Easy to forget
```

### 2. Prefer Strict Lookups for Facts
- Use fuzzy search for discovery
- Use strict lookups for authoritative data
- Never skip CURIE validation

### 3. Use Slim Mode for Large Results
- Default mode: ~100+ tokens per entity
- Slim mode: ~20 tokens per entity
- Use slim for pagination, full for analysis

### 4. Cache Identifiers, Not Data
- Cache CURIEs for fast lookup
- Don't cache full records (data changes)
- Cross-references enable navigation

### 5. Handle Rate Limits Gracefully
- Clients enforce rate limits automatically
- Exponential backoff on 429 errors
- Retry after delay from Retry-After header

### 6. Validate CURIEs Before Lookup
- Use CURIE format for strict tools
- Fuzzy search returns validated CURIEs
- Invalid CURIEs return UNRESOLVED_ENTITY error

### 7. Use Cross-References for Integration
- Navigate between databases via cross-refs
- Check if cross-reference exists before use
- Handle None values gracefully

### 8. Implement Pagination for Large Datasets
- Use cursor-based pagination
- Don't fetch all results at once
- Respect page_size limits

### 9. Monitor and Log API Errors
- Check for ErrorEnvelope in responses
- Log recovery hints for debugging
- Track rate limit errors

### 10. Test with Real and Edge Case Data
- Test with valid and invalid CURIEs
- Test with ambiguous queries
- Test with empty results

### 11. Respect Upstream API Terms
- HGNC: 10 req/s
- STRING: 1 req/s (strict)
- BioGRID: Free API key required
- DrugBank: Commercial license required

### 12. Use Organism Filtering
- Speeds up protein searches
- Reduces ambiguous results
- Default: all organisms

### 13. Understand Token Costs
- SearchCandidate: ~20 tokens
- Full Gene: ~115-300 tokens
- Compound with indications: ~100+ tokens
- InteractionNetwork: ~50+ tokens per interaction

### 14. Handle Optional Cross-References
- Cross-references may be None
- Check existence before use
- Use `model_dump(exclude_none=True)` to omit

### 15. Leverage Evidence Scores
- STRING: combined_score (0-1000)
- Open Targets: association score (0.0-1.0)
- Use thresholds for filtering

---

## Appendices

### Appendix A: CURIE Formats

All databases use CURIE (Compact URI) format for identifiers.

| Database | Format | Example | Pattern |
|----------|--------|---------|---------|
| HGNC | `HGNC:NNNNN` | `HGNC:1100` | `^HGNC:\d+$` |
| UniProt | `UniProtKB:XXXXXX` | `UniProtKB:P04637` | `^UniProtKB:[A-Z][A-Z0-9]{5,9}$` |
| ChEMBL | `CHEMBL:NNNNN` | `CHEMBL:25` | `^CHEMBL:[0-9]+$` |
| Ensembl Gene | `ENSG...` | `ENSG00000012048` | `^ENSG\d{11}$` |
| Ensembl Transcript | `ENST...` | `ENST00000471181` | `^ENST\d{11}$` |
| Entrez | `NCBIGene:NNNNN` | `NCBIGene:7157` | `^NCBIGene:\d+$` |
| PubChem | `CID:NNNNN` | `CID:2244` | `^CID:\d+$` |
| STRING | `9606.ENSP...` | `9606.ENSP00000269305` | `^9606\.[A-Z0-9]+$` |
| WikiPathways | `WP:NNNNN` | `WP:254` | `^WP:\d+$` |
| ClinicalTrials | `NCT...` | `NCT03997058` | `^NCT\d{8}$` |
| IUPHAR | `IUPHAR:NNNNN` | `IUPHAR:5239` | `^IUPHAR:\d+$` |
| DrugBank | `DB:NNNNN` | `DB01050` | `^DB\d{5}$` |

### Appendix B: Cross-Reference Registry

The 22-key cross-reference registry (defined in `gene.py`).

**Core (6 keys):**
- ensembl_gene, ensembl_transcript, uniprot, entrez, refseq, hgnc

**Disease (4 keys):**
- omim, orphanet, mondo, efo

**Drug/Compound (4 keys):**
- chembl, drugbank, pubchem_compound, pubchem_substance

**Pathway (2 keys):**
- kegg, kegg_pathway

**Interaction (4 keys):**
- string, biogrid, stitch, iuphar

**Structural (1 key):**
- pdb

**Total: 21 keys** (hgnc is 22nd)

### Appendix C: Error Codes

Standard error codes from ADR-001 Appendix B.

| Code | Description | Recovery Hint |
|------|-------------|---------------|
| `UNRESOLVED_ENTITY` | Raw string passed to strict tool | Call search tool first |
| `ENTITY_NOT_FOUND` | Valid CURIE but no record | Verify format or try synonym search |
| `AMBIGUOUS_QUERY` | Too many results or too generic | Refine query with specific terms |
| `RATE_LIMITED` | Upstream API throttling | Retry after delay (check Retry-After) |
| `UPSTREAM_ERROR` | API failure or network error | Retry later or check API status |
| `INVALID_CROSS_REFERENCE` | Cross-ref format validation failed | Use search to get valid identifier |

### Appendix D: Rate Limit Defaults

Default rate limits enforced by clients (requests per second).

| API | Rate Limit | Delay (ms) | Notes |
|-----|------------|------------|-------|
| HGNC | 10 req/s | 100 | Conservative estimate |
| UniProt | 10 req/s | 100 | Conservative estimate |
| ChEMBL | 10 req/s | 100 | SDK wrapper with backoff |
| Open Targets | 10 req/s | 100 | GraphQL API |
| STRING | 1 req/s | 1000 | **Strict limit** |
| BioGRID | 10 req/s | 100 | API key required |
| Ensembl | 15 req/s | 67 | Auto rate limit headers |
| Entrez | 3 req/s | 333 | 10 req/s with API key |
| PubChem | 5 req/s | 200 | Official limit |
| IUPHAR | 10 req/s | 100 | Conservative estimate |
| WikiPathways | 10 req/s | 100 | SPARQL + REST |
| ClinicalTrials | 10 req/s | 100 | API v2 |

### Appendix E: Response Token Sizes

Typical token counts for different query types (GPT-4 tokenizer).

| Entity Type | Slim Mode | Full Mode | Notes |
|-------------|-----------|-----------|-------|
| SearchCandidate | ~20 | N/A | id, symbol, name, score only |
| Gene | N/A | ~115-300 | Depends on cross-references |
| Protein | N/A | ~150-400 | Includes function, sequence length |
| Compound | ~30 | ~100-200 | +100 tokens with indications |
| Interaction | N/A | ~50 | Per interaction in network |
| Pathway | ~40 | ~100-150 | Depends on description length |
| Trial | N/A | ~200-500 | Includes eligibility, outcomes |
| PaginationEnvelope | +10 | +10 | Overhead per response |
| ErrorEnvelope | ~50 | ~50 | With recovery hint |

### Appendix F: MCP Protocol Primer

**JSON-RPC 2.0 Format:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": { /* tool-specific args */ }
  }
}
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "id": "matching-request-id",
  "result": {
    "content": [{
      "type": "text",
      "text": "{ /* JSON serialized result */ }"
    }]
  }
}
```

**Error Format:**
```json
{
  "jsonrpc": "2.0",
  "id": "matching-request-id",
  "error": {
    "code": -32001,
    "message": "Error description"
  }
}
```

**Transport**: HTTP POST to `/mcp` endpoint with SSE response

### Appendix G: Source File Locations

Quick reference for implementation files.

**Clients:**
- Base: `src/lifesciences_mcp/clients/base.py`
- HGNC: `src/lifesciences_mcp/clients/hgnc.py`
- UniProt: `src/lifesciences_mcp/clients/uniprot.py`
- ChEMBL: `src/lifesciences_mcp/clients/chembl.py`
- [11 more clients...]

**Models:**
- Envelopes: `src/lifesciences_mcp/models/envelopes.py`
- Gene: `src/lifesciences_mcp/models/gene.py`
- Protein: `src/lifesciences_mcp/models/protein.py`
- Compound: `src/lifesciences_mcp/models/compound.py`
- [14 more model files...]

**Servers:**
- Gateway: `src/lifesciences_mcp/servers/gateway.py`
- HGNC: `src/lifesciences_mcp/servers/hgnc.py`
- UniProt: `src/lifesciences_mcp/servers/uniprot.py`
- [11 more servers...]

**Package Entry Point:**
- `src/lifesciences_mcp/__init__.py`

---

## Related Documentation

- **Component Inventory**: `01_component_inventory.md` - Detailed component breakdown
- **Architecture Diagrams**: `02_architecture_diagrams.md` - Visual system architecture
- **Data Flows**: `03_data_flows.md` - Sequence diagrams and interaction patterns

---

## Support & Contributing

**Issues**: Report bugs or request features via GitHub issues
**Documentation**: This API reference is generated from source code and architecture analysis
**Updates**: API reference version matches package version (currently 0.1.0)

**Key Design Documents:**
- ADR-001: Architecture Decision Record for Fuzzy-to-Fact protocol
- Constitution v1.1.0: Rate limiting and error handling standards

---

*Last Updated: 2026-01-08*
*Package Version: 0.1.0*
*Gateway URL: https://lifesciences-research.fastmcp.app/mcp*
