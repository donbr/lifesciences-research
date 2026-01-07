# API Reference

## Overview

The Life Sciences MCP package provides a comprehensive suite of clients and servers for querying biological databases. The architecture follows the **Fuzzy-to-Fact protocol**, where users:

1. **Search** for entities using natural language queries (fuzzy search)
2. **Resolve** to canonical identifiers (CURIEs)
3. **Fetch** complete entity records with cross-references (strict lookup)

All responses use standardized envelope patterns:
- `PaginationEnvelope[T]` for search/list operations
- `ErrorEnvelope` for all errors with recovery hints
- Direct entity models (Gene, Protein, Compound, etc.) for strict lookups

**Key Features:**
- 13 biological database clients (HGNC, UniProt, ChEMBL, OpenTargets, etc.)
- FastMCP-based servers with 40+ MCP tools
- Unified gateway server for cloud deployment
- Rate limiting and exponential backoff on all clients
- Cross-reference validation using 22-key Agentic Biolink registry

---

## Quick Start

```python
import asyncio
from lifesciences_mcp.clients import HGNCClient, UniProtClient

async def main():
    # Example 1: Gene resolution (Fuzzy-to-Fact)
    async with HGNCClient() as hgnc:
        # Phase 1: Fuzzy search
        search_result = await hgnc.search_genes("BRCA1", page_size=5)
        if search_result.items:
            gene_id = search_result.items[0].id  # "HGNC:1100"

            # Phase 2: Strict lookup
            gene = await hgnc.get_gene(gene_id)
            print(f"Gene: {gene.symbol}, UniProt: {gene.cross_references.uniprot}")

    # Example 2: Protein search
    async with UniProtClient() as uniprot:
        proteins = await uniprot.search_proteins("p53 human", page_size=5)
        if proteins.items:
            protein_id = proteins.items[0].id  # "UniProtKB:P04637"
            protein = await uniprot.get_protein(protein_id)
            print(f"Protein: {protein.name}, Function: {protein.function[:100]}...")

asyncio.run(main())
```

---

## Client Classes

### Base Client

#### `LifeSciencesClient`

**Source:** [`src/lifesciences_mcp/clients/base.py:16-66`](src/lifesciences_mcp/clients/base.py#L16-L66)

Base class for all domain-specific API clients. Provides async HTTP client with connection pooling.

**Constructor:**

```python
def __init__(
    self,
    base_url: str,
    timeout: float = 30.0,
    max_connections: int = 10
) -> None
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | required | Base URL for the API |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `max_connections` | `int` | `10` | Maximum concurrent connections |

**Methods:**

##### `async def close() -> None`

Close the HTTP client and cleanup resources.

**Example:**
```python
from lifesciences_mcp.clients import HGNCClient

client = HGNCClient()
try:
    result = await client.search_genes("TP53")
finally:
    await client.close()
```

**Context Manager Support:**

All clients support async context managers for automatic cleanup:

```python
async with HGNCClient() as client:
    result = await client.search_genes("TP53")
# Client automatically closed
```

---

### Gene Clients

#### `HGNCClient`

**Source:** [`src/lifesciences_mcp/clients/hgnc.py:29-353`](src/lifesciences_mcp/clients/hgnc.py#L29-L353)

HGNC (HUGO Gene Nomenclature Committee) REST API client for gene symbol resolution.

**Features:**
- Rate limiting: 10 req/s (100ms delay)
- Exponential backoff on 429/403/503 errors
- Alias boosting (e.g., "p53" → TP53)
- Thundering herd prevention

**Constructor:**

```python
def __init__() -> None
```

No parameters required. Uses default base URL: `https://rest.genenames.org`

**Methods:**

##### `async def search_genes(query: str, slim: bool = False, cursor: str | None = None, page_size: int = 50) -> PaginationEnvelope[SearchCandidate] | ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/clients/hgnc.py:110-254`](src/lifesciences_mcp/clients/hgnc.py#L110-L254)

Fuzzy search for genes by symbol, name, synonym, or natural language.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | Search term (min 2 characters) |
| `slim` | `bool` | `False` | If true, return minimal fields (~20 tokens/entity) |
| `cursor` | `str \| None` | `None` | Opaque cursor from previous response |
| `page_size` | `int` | `50` | Results per page (1-100) |

**Returns:**
- `PaginationEnvelope[SearchCandidate]` with ranked results
- `ErrorEnvelope` on failure (AMBIGUOUS_QUERY, RATE_LIMITED, UPSTREAM_ERROR)

**Example:**
```python
async with HGNCClient() as client:
    # Search for TP53
    result = await client.search_genes("TP53", page_size=5)

    if hasattr(result, 'error'):
        print(f"Error: {result.error.message}")
        print(f"Recovery: {result.error.recovery_hint}")
    else:
        for candidate in result.items:
            print(f"{candidate.id}: {candidate.symbol} - {candidate.name} (score={candidate.score})")

        # Pagination
        if result.pagination.cursor:
            next_page = await client.search_genes("TP53", cursor=result.pagination.cursor)
```

**Example Response:**
```json
{
  "items": [
    {
      "id": "HGNC:11998",
      "symbol": "TP53",
      "name": "tumor protein p53",
      "score": 1.0
    }
  ],
  "pagination": {
    "cursor": "eyJvZmZzZXQiOiA1MH0=",
    "total_count": 1,
    "page_size": 50
  }
}
```

##### `async def get_gene(hgnc_id: str) -> Gene | ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/clients/hgnc.py:273-332`](src/lifesciences_mcp/clients/hgnc.py#L273-L332)

Get complete gene record by HGNC CURIE (strict lookup).

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hgnc_id` | `str` | required | HGNC CURIE format: `HGNC:NNNNN` |

**Returns:**
- `Gene` with complete metadata and cross-references
- `ErrorEnvelope` with code:
  - `UNRESOLVED_ENTITY` if CURIE format invalid
  - `ENTITY_NOT_FOUND` if gene doesn't exist
  - `RATE_LIMITED` if API rate limit exceeded

**Example:**
```python
async with HGNCClient() as client:
    gene = await client.get_gene("HGNC:1100")

    if hasattr(gene, 'error'):
        print(f"Error: {gene.error.message}")
    else:
        print(f"Symbol: {gene.symbol}")
        print(f"Name: {gene.name}")
        print(f"Location: {gene.location}")
        print(f"UniProt: {gene.cross_references.uniprot}")
        print(f"Ensembl: {gene.cross_references.ensembl_gene}")
        print(f"Entrez: {gene.cross_references.entrez}")
```

**Example Response:**
```json
{
  "id": "HGNC:1100",
  "symbol": "BRCA1",
  "name": "BRCA1 DNA repair associated",
  "status": "Approved",
  "locus_type": "gene with protein product",
  "locus_group": "protein-coding gene",
  "location": "17q21.31",
  "alias_symbols": ["BRCC1", "FANCS", "PNCA4"],
  "cross_references": {
    "ensembl_gene": "ENSG00000012048",
    "uniprot": ["P38398"],
    "entrez": "672",
    "refseq": ["NM_007294"],
    "omim": "113705"
  }
}
```

---

#### `EntrezClient`

**Source:** [`src/lifesciences_mcp/clients/entrez.py:40-268`](src/lifesciences_mcp/clients/entrez.py#L40-L268)

NCBI Entrez Gene database client for gene information and PubMed linkage.

**Key Methods:**

##### `async def search_genes(query: str, page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[EntrezGeneSearchCandidate] | ErrorEnvelope`

Search NCBI Gene database by gene symbol or name.

##### `async def get_gene(entrez_id: str) -> EntrezGene | ErrorEnvelope`

Get complete gene record by Entrez CURIE format: `NCBIGene:NNNNN`

##### `async def get_pubmed_links(entrez_id: str, limit: int = 10) -> list[str] | ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/clients/entrez.py:240-268`](src/lifesciences_mcp/clients/entrez.py#L240-L268)

Get PubMed article IDs associated with a gene.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `entrez_id` | `str` | required | Entrez CURIE format: `NCBIGene:NNNNN` |
| `limit` | `int` | `10` | Maximum PubMed IDs to return (1-100) |

**Returns:** `list[str]` of PubMed IDs

**Example:**
```python
async with EntrezClient() as client:
    # Get PubMed links for TP53 (NCBIGene:7157)
    pubmed_ids = await client.get_pubmed_links("NCBIGene:7157", limit=5)
    for pmid in pubmed_ids:
        print(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
```

---

#### `EnsemblClient`

**Source:** [`src/lifesciences_mcp/clients/ensembl.py:57-323`](src/lifesciences_mcp/clients/ensembl.py#L57-L323)

Ensembl REST API client for genomic annotations (genes, transcripts).

**Key Methods:**

##### `async def search_genes(query: str, species: str = "human", page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[EnsemblGeneSearchCandidate] | ErrorEnvelope`

Search Ensembl for genes by symbol.

##### `async def get_gene(ensembl_id: str) -> EnsemblGene | ErrorEnvelope`

Get complete gene record by Ensembl CURIE: `ENSG00000000003`

##### `async def get_transcript(transcript_id: str) -> EnsemblTranscript | ErrorEnvelope`

Get transcript details by Ensembl transcript ID: `ENST00000000233`

---

### Protein Clients

#### `UniProtClient`

**Source:** [`src/lifesciences_mcp/clients/uniprot.py:29-461`](src/lifesciences_mcp/clients/uniprot.py#L29-L461)

UniProt REST API client for protein sequence and annotation data.

**Features:**
- Rate limiting: 10 req/s
- Server-side pagination with opaque cursors
- Cross-reference mapping to 22-key registry

**Key Methods:**

##### `async def search_proteins(query: str, slim: bool = False, cursor: str | None = None, page_size: int = 50) -> PaginationEnvelope[ProteinSearchCandidate] | ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/clients/uniprot.py:170-313`](src/lifesciences_mcp/clients/uniprot.py#L170-L313)

Fuzzy search for proteins by name, accession, gene, or organism.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | Search term (min 2 characters) |
| `slim` | `bool` | `False` | Return minimal fields |
| `cursor` | `str \| None` | `None` | UniProt API cursor for pagination |
| `page_size` | `int` | `50` | Results per page (1-500) |

**Example:**
```python
async with UniProtClient() as client:
    result = await client.search_proteins("p53 human", page_size=5)
    for protein in result.items:
        print(f"{protein.id}: {protein.name}")
        print(f"  Organism: {protein.organism}")
        print(f"  Genes: {', '.join(protein.gene_names or [])}")
        print(f"  Score: {protein.score}")
```

##### `async def get_protein(uniprot_id: str, slim: bool = False) -> Protein | ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/clients/uniprot.py:314-461`](src/lifesciences_mcp/clients/uniprot.py#L314-L461)

Get complete protein record by UniProt CURIE.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `uniprot_id` | `str` | required | UniProt CURIE: `UniProtKB:P04637` |
| `slim` | `bool` | `False` | If true, exclude cross-references |

**Returns:**
- `Protein` with complete metadata, including:
  - Basic info: name, organism, gene names
  - Sequence: length, function description
  - Cross-references: HGNC, Ensembl, PDB, OMIM, etc.

**Example:**
```python
async with UniProtClient() as client:
    protein = await client.get_protein("UniProtKB:P04637")

    print(f"Protein: {protein.name}")
    print(f"Gene: {', '.join(protein.gene_names)}")
    print(f"Length: {protein.sequence_length} aa")
    print(f"Function: {protein.function[:200]}...")

    # Cross-references
    xrefs = protein.cross_references
    print(f"HGNC: {xrefs.hgnc}")
    print(f"Ensembl Gene: {xrefs.ensembl_gene}")
    print(f"PDB Structures: {xrefs.pdb[:5]}")  # First 5
```

---

### Compound & Drug Clients

#### `ChEMBLClient`

**Source:** [`src/lifesciences_mcp/clients/chembl.py:40-681`](src/lifesciences_mcp/clients/chembl.py#L40-L681)

ChEMBL bioactivity database client for compounds and drug data.

**Implementation Note:** Uses synchronous `chembl_webresource_client` SDK wrapped with `run_in_executor` for async compatibility.

**Features:**
- Rate limiting: 10 req/s with exponential backoff
- Batch operations for efficient multi-compound lookup
- Drug indication data from separate endpoint

**Key Methods:**

##### `async def search_compounds(query: str, slim: bool = False, cursor: str | None = None, page_size: int = 50) -> PaginationEnvelope[CompoundSearchCandidate] | ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/clients/chembl.py:453-518`](src/lifesciences_mcp/clients/chembl.py#L453-L518)

Fuzzy search for compounds by name, synonym, or SMILES.

**Example:**
```python
async with ChEMBLClient() as client:
    result = await client.search_compounds("Aspirin", page_size=5)
    for compound in result.items:
        print(f"{compound.id}: {compound.name}")
        print(f"  Formula: {compound.molecular_formula}")
        print(f"  Score: {compound.score}")
```

##### `async def get_compound(chembl_id: str, slim: bool = False) -> dict | ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/clients/chembl.py:519-587`](src/lifesciences_mcp/clients/chembl.py#L519-L587)

Get complete compound record by ChEMBL CURIE.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chembl_id` | `str` | required | ChEMBL CURIE: `CHEMBL:25` |
| `slim` | `bool` | `False` | If true, return only id/name/formula |

**Returns:** `Compound` dict with:
- Basic info: name, molecular formula, weight
- Structure: SMILES, InChI
- Drug data: max_phase (0-4), indications
- Synonyms and cross-references

**Example:**
```python
async with ChEMBLClient() as client:
    compound = await client.get_compound("CHEMBL:25")  # Aspirin

    print(f"Name: {compound['name']}")
    print(f"Formula: {compound['molecular_formula']}")
    print(f"Weight: {compound['molecular_weight']} g/mol")
    print(f"SMILES: {compound['smiles']}")
    print(f"Max Phase: {compound['max_phase']}")  # 4 = Approved
    print(f"Indications: {', '.join(compound['indications'])}")
```

##### `async def get_compounds_batch(chembl_ids: list[str], slim: bool = True) -> list[dict] | ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/clients/chembl.py:588-674`](src/lifesciences_mcp/clients/chembl.py#L588-L674)

Batch lookup for multiple compounds (max 100 per request).

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chembl_ids` | `list[str]` | required | List of ChEMBL CURIEs |
| `slim` | `bool` | `True` | Return minimal fields for efficiency |

**Returns:** `list[dict]` in same order as input (may include individual ErrorEnvelopes)

**Example:**
```python
async with ChEMBLClient() as client:
    compounds = await client.get_compounds_batch([
        "CHEMBL:25",      # Aspirin
        "CHEMBL:939",     # Gefitinib
        "CHEMBL:521686"   # Olaparib
    ], slim=True)

    for compound in compounds:
        if 'error' in compound:
            print(f"Error: {compound['error']['message']}")
        else:
            print(f"{compound['id']}: {compound['name']}")
```

---

#### `PubChemClient`

**Source:** [`src/lifesciences_mcp/clients/pubchem.py:31-397`](src/lifesciences_mcp/clients/pubchem.py#L31-L397)

PubChem REST API client for chemical compound data and cross-references.

**Key Methods:**

##### `async def search_compounds(query: str, page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[PubChemSearchCandidate] | ErrorEnvelope`

Search PubChem for compounds by name or synonym.

##### `async def get_compound(cid: str) -> PubChemCompound | ErrorEnvelope`

Get compound details by PubChem CURIE: `CID:2244`

**Returns:** `PubChemCompound` with properties, synonyms, and cross-references

---

#### `DrugBankClient`

**Source:** [`src/lifesciences_mcp/clients/drugbank.py:55-350`](src/lifesciences_mcp/clients/drugbank.py#L55-L350)

DrugBank API client for approved drug information.

**Authentication:** Requires `DRUGBANK_API_KEY` environment variable (commercial license required).

**Key Methods:**

##### `async def search_drugs(query: str, page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[DrugSearchCandidate] | ErrorEnvelope`

Search DrugBank for drugs by name or synonym.

##### `async def get_drug(drugbank_id: str) -> Drug | ErrorEnvelope`

Get complete drug record by DrugBank CURIE: `DB:00945`

---

#### `IUPHARClient`

**Source:** [`src/lifesciences_mcp/clients/iuphar.py:26-437`](src/lifesciences_mcp/clients/iuphar.py#L26-L437)

IUPHAR/GtoPdb (Guide to Pharmacology) client for pharmacological ligands and targets.

**Key Methods:**

##### `async def search_ligands(query: str, page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[LigandSearchCandidate] | ErrorEnvelope`

Search for pharmacological ligands (drugs, endogenous compounds).

**Example:**
```python
async with IUPHARClient() as client:
    ligands = await client.search_ligands("Crizotinib", page_size=5)
    for ligand in ligands.items:
        print(f"{ligand.id}: {ligand.name}")
        print(f"  Type: {ligand.ligand_type}")
        print(f"  Approved: {ligand.approved}")
```

##### `async def get_ligand(ligand_id: str) -> Ligand | ErrorEnvelope`

Get complete ligand record by IUPHAR CURIE: `IUPHAR:4903`

##### `async def search_targets(query: str, page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[PharmacologicalTargetSearchCandidate] | ErrorEnvelope`

Search for pharmacological targets (receptors, enzymes).

##### `async def get_target(target_id: str) -> PharmacologicalTarget | ErrorEnvelope`

Get complete target record by IUPHAR CURIE: `IUPHAR:1735`

---

### Target & Disease Clients

#### `OpenTargetsClient`

**Source:** [`src/lifesciences_mcp/clients/opentargets.py:123-621`](src/lifesciences_mcp/clients/opentargets.py#L123-L621)

Open Targets Platform GraphQL API client for target-disease associations.

**Features:**
- GraphQL API with rate limiting (10 req/s)
- Evidence-based disease associations
- Overall association scores

**Key Methods:**

##### `async def search_targets(query: str, page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[TargetSearchCandidate] | ErrorEnvelope`

Search for targets by gene symbol or name.

**Example:**
```python
async with OpenTargetsClient() as client:
    targets = await client.search_targets("EGFR", page_size=5)
    for target in targets.items:
        print(f"{target.id}: {target.approved_symbol}")
        print(f"  Name: {target.approved_name}")
```

##### `async def get_target(ensembl_id: str) -> Target | ErrorEnvelope`

Get complete target record by Ensembl gene ID: `ENSG00000146648`

##### `async def get_associations(ensembl_id: str, page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[Association] | ErrorEnvelope`

Get disease associations for a target gene.

**Returns:** `PaginationEnvelope[Association]` with:
- Disease EFO IDs and names
- Overall association scores
- Evidence counts by data type

**Example:**
```python
async with OpenTargetsClient() as client:
    assocs = await client.get_associations("ENSG00000146648", page_size=10)
    for assoc in assocs.items:
        print(f"Disease: {assoc.disease_name}")
        print(f"  Score: {assoc.overall_score:.3f}")
        print(f"  Evidence: {assoc.evidence_count} sources")
```

---

### Interaction Clients

#### `STRINGClient`

**Source:** [`src/lifesciences_mcp/clients/string.py:36-440`](src/lifesciences_mcp/clients/string.py#L36-L440)

STRING database client for protein-protein interaction networks.

**Key Methods:**

##### `async def search_proteins(query: str, species: int = 9606, limit: int = 10) -> PaginationEnvelope[InteractionSearchCandidate] | ErrorEnvelope`

Search STRING for proteins by name or identifier.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | Protein name or identifier |
| `species` | `int` | `9606` | NCBI taxonomy ID (9606=human) |
| `limit` | `int` | `10` | Maximum results |

##### `async def get_interactions(protein_id: str, required_score: int = 400, limit: int = 10) -> InteractionNetwork | ErrorEnvelope`

Get protein-protein interactions for a given protein.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `protein_id` | `str` | required | STRING ID: `STRING:9606.ENSP00000269305` |
| `required_score` | `int` | `400` | Minimum confidence (0-1000) |
| `limit` | `int` | `10` | Maximum interactions |

**Returns:** `InteractionNetwork` with:
- Query protein details
- List of interactions with scores (experimental, database, textmining, etc.)

**Example:**
```python
async with STRINGClient() as client:
    # Get TP53 interactions
    network = await client.get_interactions(
        "STRING:9606.ENSP00000269305",  # TP53
        required_score=700,  # High confidence
        limit=10
    )

    for interaction in network.interactions:
        print(f"{interaction.partner_id}: {interaction.partner_name}")
        print(f"  Combined score: {interaction.scores.combined_score}")
        print(f"  Experimental: {interaction.scores.experimental_score}")
```

##### `async def get_network_image_url(protein_ids: list[str], required_score: int = 400) -> str | ErrorEnvelope`

Get URL for network visualization image.

**Returns:** URL string for PNG/SVG network diagram

---

#### `BioGridClient`

**Source:** [`src/lifesciences_mcp/clients/biogrid.py:40-375`](src/lifesciences_mcp/clients/biogrid.py#L40-L375)

BioGRID database client for genetic and protein interactions.

**Authentication:** Requires `BIOGRID_API_KEY` environment variable (free API key from https://webservice.thebiogrid.org/).

**Key Methods:**

##### `async def search_genes(query: str) -> PaginationEnvelope[BioGridSearchCandidate] | ErrorEnvelope`

Search BioGRID for genes by symbol or name.

##### `async def get_interactions(gene_symbol: str, max_results: int = 100) -> InteractionResult | ErrorEnvelope`

Get genetic and physical interactions for a gene.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gene_symbol` | `str` | required | Gene symbol (e.g., "BRCA1") |
| `max_results` | `int` | `100` | Maximum interactions per type |

**Returns:** `InteractionResult` with:
- Query gene symbol and BioGRID ID
- Physical interactions list
- Genetic interactions list
- Total counts

**Example:**
```python
async with BioGridClient() as client:
    result = await client.get_interactions("BRCA1", max_results=50)

    print(f"Gene: {result.query_gene}")
    print(f"Physical: {result.physical_count} interactions")
    print(f"Genetic: {result.genetic_count} interactions")

    for interaction in result.interactions[:10]:
        print(f"  {interaction.partner_symbol} ({interaction.interaction_type})")
        print(f"    Method: {interaction.detection_method}")
        print(f"    PubMed: {interaction.pubmed_id}")
```

---

### Pathway Clients

#### `WikiPathwaysClient`

**Source:** [`src/lifesciences_mcp/clients/wikipathways.py:41-613`](src/lifesciences_mcp/clients/wikipathways.py#L41-L613)

WikiPathways API client for biological pathway data.

**Features:**
- Rate limiting: 1 req/s (conservative)
- Pathway component extraction (genes, proteins, metabolites, interactions)
- Cross-reference caching for performance

**Key Methods:**

##### `async def search_pathways(query: str, organism: str = "Homo sapiens", page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[PathwaySearchCandidate] | ErrorEnvelope`

Search for pathways by keyword.

**Example:**
```python
async with WikiPathwaysClient() as client:
    pathways = await client.search_pathways("TP53", page_size=10)
    for pathway in pathways.items:
        print(f"{pathway.id}: {pathway.title}")
        print(f"  Organism: {pathway.organism}")
        print(f"  Score: {pathway.score}")
```

##### `async def get_pathway(pathway_id: str) -> Pathway | ErrorEnvelope`

Get complete pathway metadata by WikiPathways CURIE.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pathway_id` | `str` | required | WikiPathways CURIE: `WP:WP534` |

**Returns:** `Pathway` with:
- Basic info: title, organism, description
- Revision metadata: version, curators
- Component counts: genes, proteins, metabolites, interactions
- Cross-references: KEGG, Reactome, GO

##### `async def get_pathways_for_gene(gene_id: str, organism: str = "Homo sapiens", page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[PathwaySearchCandidate] | ErrorEnvelope`

Reverse lookup: find pathways containing a specific gene.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gene_id` | `str` | required | Gene symbol or identifier |
| `organism` | `str` | `"Homo sapiens"` | Scientific organism name |

**Example:**
```python
async with WikiPathwaysClient() as client:
    pathways = await client.get_pathways_for_gene("BRCA1", page_size=10)
    print(f"Found {pathways.pagination.total_count} pathways containing BRCA1")
    for pathway in pathways.items:
        print(f"  {pathway.id}: {pathway.title}")
```

##### `async def get_pathway_components(pathway_id: str) -> PathwayComponents | ErrorEnvelope`

Extract detailed pathway components (genes, proteins, metabolites, interactions).

**Returns:** `PathwayComponents` with:
- `genes`: List of gene nodes with labels and identifiers
- `proteins`: List of protein nodes
- `metabolites`: List of metabolite nodes
- `interactions`: List of interaction edges

**Example:**
```python
async with WikiPathwaysClient() as client:
    components = await client.get_pathway_components("WP:WP1742")  # TP53 network

    print(f"Genes: {len(components.genes)}")
    print(f"Proteins: {len(components.proteins)}")
    print(f"Interactions: {len(components.interactions)}")

    # Extract gene symbols
    gene_symbols = {node.label for node in components.genes}
    print(f"Gene symbols: {', '.join(sorted(gene_symbols)[:10])}")
```

---

### Clinical Trial Clients

#### `ClinicalTrialsClient`

**Source:** [`src/lifesciences_mcp/clients/clinicaltrials.py:28-496`](src/lifesciences_mcp/clients/clinicaltrials.py#L28-L496)

ClinicalTrials.gov API client for clinical trial data.

**Important Note:** ClinicalTrials.gov uses Cloudflare bot protection that may block Python HTTP clients. See project documentation for workarounds.

**Key Methods:**

##### `async def search_trials(query: str, phase: str | None = None, status: str | None = None, page_size: int = 50, cursor: str | None = None) -> PaginationEnvelope[TrialSearchCandidate] | ErrorEnvelope`

Search for clinical trials by condition, intervention, or keywords.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | Search query (disease, drug, etc.) |
| `phase` | `str \| None` | `None` | Filter: PHASE1, PHASE2, PHASE3, PHASE4 |
| `status` | `str \| None` | `None` | Filter: RECRUITING, COMPLETED, etc. |
| `page_size` | `int` | `50` | Results per page |

##### `async def get_trial(nct_id: str) -> Trial | ErrorEnvelope`

Get complete trial record by NCT CURIE: `NCT:03456076`

**Returns:** `Trial` with:
- Protocol details: study type, allocation, masking
- Eligibility criteria: age, sex, inclusion/exclusion
- Outcomes: primary and secondary endpoints
- Sponsors and collaborators
- Cross-references: PubMed articles, MeSH terms

##### `async def get_trial_locations(nct_id: str) -> list[TrialLocation] | ErrorEnvelope`

Get trial sites/locations for a clinical trial.

**Returns:** `list[TrialLocation]` with facility names, cities, countries, and recruitment status

---

## Model Classes

### Envelope Models

#### `PaginationEnvelope[T]`

**Source:** [`src/lifesciences_mcp/models/envelopes.py:119-145`](src/lifesciences_mcp/models/envelopes.py#L119-L145)

Standard pagination envelope for all list/search operations.

**Generic Type Parameter:** `T` - The item type (e.g., `SearchCandidate`, `Protein`)

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `items` | `list[T]` | Data payload (results) |
| `pagination` | `Pagination` | Pagination metadata |

**Pagination Metadata:**
| Field | Type | Description |
|-------|------|-------------|
| `cursor` | `str \| None` | Opaque cursor for next page (null = end) |
| `total_count` | `int \| None` | Total items if known |
| `page_size` | `int` | Items per page |

**Example:**
```python
# Generic usage
result: PaginationEnvelope[SearchCandidate] = await client.search_genes("TP53")

# Access items
for item in result.items:
    print(item)

# Check pagination
if result.pagination.cursor:
    next_page = await client.search_genes("TP53", cursor=result.pagination.cursor)

print(f"Total results: {result.pagination.total_count}")
print(f"Page size: {result.pagination.page_size}")
```

**Factory Method:**
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

---

#### `ErrorEnvelope`

**Source:** [`src/lifesciences_mcp/models/envelopes.py:36-109`](src/lifesciences_mcp/models/envelopes.py#L36-L109)

Canonical error envelope for all error responses.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Always `False` for errors |
| `error` | `ErrorDetail` | Error details with recovery hint |

**ErrorDetail Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `code` | `ErrorCode` | Standard error code from registry |
| `message` | `str` | Human-readable error message |
| `recovery_hint` | `str` | Agent-actionable guidance for recovery |
| `invalid_input` | `str \| None` | The input that caused the error |

**Error Codes:**
| Code | Description | When Used |
|------|-------------|-----------|
| `UNRESOLVED_ENTITY` | Invalid CURIE format | Passing raw string to strict lookup |
| `ENTITY_NOT_FOUND` | Valid CURIE but no record | Entity doesn't exist in database |
| `AMBIGUOUS_QUERY` | Too many/few results | Query too vague or short |
| `RATE_LIMITED` | API rate limit exceeded | Too many requests |
| `UPSTREAM_ERROR` | External API failure | Network error, timeout, 500+ status |
| `INVALID_CROSS_REFERENCE` | Bad cross-reference | Malformed identifier |

**Factory Methods:**

```python
# UNRESOLVED_ENTITY - for invalid CURIE format
ErrorEnvelope.unresolved_entity("p53")
# → "Call search_genes to resolve the identifier first."

# ENTITY_NOT_FOUND - for valid CURIE with no record
ErrorEnvelope.entity_not_found("HGNC:999999")
# → "Verify the HGNC ID format or try a synonym search."

# AMBIGUOUS_QUERY - for too many/few results
ErrorEnvelope.ambiguous_query("p", 10000)
# → "Refine query with more specific terms."

# RATE_LIMITED - for API throttling
ErrorEnvelope.rate_limited(retry_after=60)
# → "Retry after 60 seconds."

# UPSTREAM_ERROR - for API failures
ErrorEnvelope.upstream_error(503, "Service Unavailable")
# → "HGNC API may be temporarily unavailable. Retry later."
```

**Example Usage:**
```python
result = await client.get_gene("p53")  # Invalid CURIE

if hasattr(result, 'error'):
    print(f"Error Code: {result.error.code}")
    print(f"Message: {result.error.message}")
    print(f"Recovery Hint: {result.error.recovery_hint}")
    print(f"Invalid Input: {result.error.invalid_input}")

    # Agent can use recovery hint for self-correction
    if result.error.code == "UNRESOLVED_ENTITY":
        # Try fuzzy search instead
        search_result = await client.search_genes("p53")
```

---

### Domain Models

#### `Gene`

**Source:** [`src/lifesciences_mcp/models/gene.py:166-215`](src/lifesciences_mcp/models/gene.py#L166-L215)

Complete gene record from HGNC with Agentic Biolink cross-references.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | HGNC CURIE (pattern: `HGNC:\d+`) |
| `symbol` | `str` | Official gene symbol |
| `name` | `str` | Full gene name |
| `status` | `str` | Approval status (Approved, Withdrawn, Entry Withdrawn) |
| `locus_type` | `str \| None` | Gene type classification |
| `locus_group` | `str \| None` | Gene group classification |
| `location` | `str \| None` | Chromosomal location |
| `alias_symbols` | `list[str] \| None` | Alternative symbols |
| `alias_names` | `list[str] \| None` | Alternative names |
| `prev_symbols` | `list[str] \| None` | Previous symbols |
| `prev_names` | `list[str] \| None` | Previous names |
| `cross_references` | `CrossReferences` | External database identifiers |

**Token Budget:** ~115-300 tokens depending on cross-references

**Example:**
```json
{
  "id": "HGNC:11998",
  "symbol": "TP53",
  "name": "tumor protein p53",
  "status": "Approved",
  "locus_type": "gene with protein product",
  "location": "17p13.1",
  "alias_symbols": ["P53", "TRP53"],
  "cross_references": {
    "ensembl_gene": "ENSG00000141510",
    "uniprot": ["P04637"],
    "entrez": "7157",
    "omim": "191170"
  }
}
```

---

#### `SearchCandidate`

**Source:** [`src/lifesciences_mcp/models/gene.py:145-164`](src/lifesciences_mcp/models/gene.py#L145-L164)

Lightweight gene representation for fuzzy search results.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | HGNC CURIE (pattern: `HGNC:\d+`) |
| `symbol` | `str` | Official gene symbol |
| `name` | `str` | Full gene name |
| `score` | `float` | Relevance score (0.0-1.0) |

**Token Budget:** ~20 tokens per entity (93% reduction vs full Gene)

---

#### `CrossReferences`

**Source:** [`src/lifesciences_mcp/models/gene.py:27-143`](src/lifesciences_mcp/models/gene.py#L27-L143)

External database identifiers using the 22-key Agentic Biolink registry.

**Omit-if-null Pattern:** Keys are omitted entirely if no value exists (never null or empty string).

**Registry Keys (22 total):**

**Core Identifiers:**
| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `ensembl_gene` | `str \| None` | `"ENSG00000012048"` | Ensembl gene ID |
| `ensembl_transcript` | `list[str] \| None` | `["ENST00000357654"]` | Ensembl transcript IDs |
| `uniprot` | `list[str] \| None` | `["P38398"]` | UniProt accessions |
| `entrez` | `str \| None` | `"672"` | NCBI Entrez gene ID |
| `refseq` | `list[str] \| None` | `["NM_007294"]` | RefSeq accessions |
| `hgnc` | `str \| None` | `"HGNC:1100"` | HGNC gene ID |

**Disease/Phenotype:**
| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `omim` | `str \| None` | `"113705"` | OMIM ID |
| `orphanet` | `str \| None` | `"ORPHA:558"` | Orphanet rare disease ID |
| `mondo` | `str \| None` | `"MONDO:0007254"` | MONDO disease ontology ID |
| `efo` | `str \| None` | `"EFO:0000305"` | Experimental Factor Ontology ID |

**Drug/Compound:**
| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `chembl` | `str \| None` | `"CHEMBL:1201583"` | ChEMBL target/compound ID |
| `drugbank` | `str \| None` | `"DB:01050"` | DrugBank ID |
| `pubchem_compound` | `str \| None` | `"2244"` | PubChem compound ID |
| `pubchem_substance` | `str \| None` | `"46506019"` | PubChem substance ID |

**Pathway Databases:**
| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `kegg` | `str \| None` | `"hsa:672"` | KEGG gene ID |
| `kegg_pathway` | `list[str] \| None` | `["hsa04110"]` | KEGG pathway IDs |

**Interaction Databases:**
| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `string` | `str \| None` | `"9606.ENSP00000269305"` | STRING protein ID |
| `biogrid` | `str \| None` | `"112"` | BioGRID gene ID |
| `stitch` | `str \| None` | `"CIDm00002244"` | STITCH chemical-protein ID |
| `iuphar` | `str \| None` | `"IUPHAR:4903"` | IUPHAR/GtoPdb ligand/target ID |

**Structural:**
| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `pdb` | `list[str] \| None` | `["1TUP", "1TSR"]` | Protein Data Bank IDs |

**Validation:** All values are validated against regex patterns defined in ADR-001 Appendix A.

**Example:**
```python
xrefs = gene.cross_references

# Single-value references
print(f"Ensembl: {xrefs.ensembl_gene}")  # ENSG00000012048
print(f"Entrez: {xrefs.entrez}")          # 672
print(f"HGNC: {xrefs.hgnc}")              # HGNC:1100

# Multi-value references
print(f"UniProt: {', '.join(xrefs.uniprot)}")  # P38398
print(f"RefSeq: {', '.join(xrefs.refseq)}")    # NM_007294, NM_007300

# Check if reference exists
if xrefs.pdb:
    print(f"PDB structures: {', '.join(xrefs.pdb)}")
```

---

#### `Protein`

**Source:** [`src/lifesciences_mcp/models/protein.py:44-92`](src/lifesciences_mcp/models/protein.py#L44-L92)

Complete protein record from UniProt with cross-references.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | UniProt CURIE (pattern: `UniProtKB:[A-Z][A-Z0-9]{5,9}`) |
| `accession` | `str` | Raw UniProt accession (e.g., `P04637`) |
| `name` | `str` | Protein name |
| `full_name` | `str \| None` | Recommended full name |
| `gene_names` | `list[str] \| None` | Associated gene symbols |
| `organism` | `str` | Scientific name (e.g., `Homo sapiens`) |
| `organism_id` | `int \| None` | NCBI Taxonomy ID |
| `function` | `str \| None` | Functional description |
| `sequence_length` | `int \| None` | Amino acid sequence length |
| `cross_references` | `CrossReferences` | Cross-references using 22-key registry |

---

#### `Compound`

**Source:** [`src/lifesciences_mcp/models/compound.py:73-178`](src/lifesciences_mcp/models/compound.py#L73-L178)

Complete ChEMBL compound record with Agentic Biolink cross-references.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | ChEMBL CURIE (pattern: `CHEMBL:[0-9]+`) |
| `name` | `str \| None` | Preferred compound name |
| `molecular_formula` | `str \| None` | Molecular formula |
| `molecular_weight` | `float \| None` | Molecular weight in g/mol |
| `smiles` | `str \| None` | SMILES notation |
| `inchi` | `str \| None` | InChI identifier |
| `max_phase` | `int \| None` | Maximum clinical phase (0-4) |
| `indications` | `list[str]` | Approved indications (MeSH headings) |
| `canonical_name` | `str \| None` | Canonical IUPAC name |
| `synonyms` | `list[str]` | Alternative names |
| `cross_references` | `dict[str, list[str]]` | Cross-references to other databases |

**Token Budget:** ~115-300 tokens in full mode, ~20 tokens in slim mode

**Slim Mode:**
```python
compound.to_slim()  # Returns dict with only id, name, molecular_formula
```

---

#### `Trial`

**Source:** [`src/lifesciences_mcp/models/trial.py:91-154`](src/lifesciences_mcp/models/trial.py#L91-L154)

Complete clinical trial entity from ClinicalTrials.gov.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | NCT CURIE (pattern: `NCT:\d{8}`) |
| `title` | `str` | Official trial title |
| `brief_summary` | `str` | Brief description |
| `detailed_description` | `str \| None` | Full protocol description |
| `protocol` | `TrialProtocol` | Protocol design details |
| `eligibility_criteria` | `EligibilityCriteria \| None` | Patient eligibility |
| `primary_outcomes` | `list[Outcome]` | Primary endpoints |
| `secondary_outcomes` | `list[Outcome]` | Secondary endpoints |
| `sponsors` | `list[Sponsor]` | Lead sponsor and collaborators |
| `phase` | `str \| None` | Trial phase |
| `status` | `str` | Recruitment status |
| `enrollment` | `int \| None` | Target/actual enrollment |
| `start_date` | `str \| None` | Study start date |
| `completion_date` | `str \| None` | Primary completion date |
| `conditions` | `list[str]` | Disease/condition names |
| `interventions` | `list[str]` | Treatment/intervention names |
| `cross_references` | `dict[str, Any]` | PubMed, MeSH terms |

**Token Budget:** ~5K-10K tokens (deep nested structure)

---

#### `Pathway`

**Source:** [`src/lifesciences_mcp/models/pathway.py:40-110`](src/lifesciences_mcp/models/pathway.py#L40-L110)

Complete pathway entity from WikiPathways.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | WikiPathways CURIE (pattern: `WP:WP\d+`) |
| `title` | `str` | Pathway name |
| `organism` | `str` | Scientific organism name |
| `description` | `str` | Pathway description |
| `revision` | `RevisionMetadata` | Version, curators |
| `component_counts` | `ComponentCounts` | Gene/protein/metabolite counts |
| `cross_references` | `dict` | Reactome, KEGG, GO |
| `url` | `str` | WikiPathways pathway URL |

**Token Budget:** ~300 tokens

---

## MCP Servers

### Gateway Server

**Source:** [`src/lifesciences_mcp/servers/gateway.py`](src/lifesciences_mcp/servers/gateway.py)

Unified gateway server composing all 13 individual MCP servers for cloud deployment.

**Available Tools:** 40+ tools accessible with domain prefixes

**Usage:**
```bash
# Local testing
uv run fastmcp run src/lifesciences_mcp/servers/gateway.py

# FastMCP Cloud deployment
# Entrypoint: src/lifesciences_mcp/servers/gateway.py:mcp
```

**Included Servers:**
- HGNC (genes)
- UniProt (proteins)
- ChEMBL (compounds)
- Open Targets (target-disease)
- STRING (protein interactions)
- BioGRID (genetic interactions)
- Ensembl (genomics)
- Entrez (NCBI genes)
- PubChem (chemistry)
- IUPHAR (pharmacology)
- WikiPathways (pathways)
- ClinicalTrials (trials)

**Excluded:** DrugBank (requires commercial API key)

---

### Domain Servers

#### HGNC Server

**Source:** [`src/lifesciences_mcp/servers/hgnc.py`](src/lifesciences_mcp/servers/hgnc.py)

**Tools:**
- `search_genes` - Fuzzy search for genes
- `get_gene` - Strict lookup by HGNC CURIE

**Usage:**
```bash
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
```

#### UniProt Server

**Source:** [`src/lifesciences_mcp/servers/uniprot.py`](src/lifesciences_mcp/servers/uniprot.py)

**Tools:**
- `search_proteins` - Fuzzy search for proteins
- `get_protein` - Strict lookup by UniProt CURIE

#### ChEMBL Server

**Source:** [`src/lifesciences_mcp/servers/chembl.py`](src/lifesciences_mcp/servers/chembl.py)

**Tools:**
- `search_compounds` - Fuzzy search for compounds
- `get_compound` - Strict lookup by ChEMBL CURIE
- `get_compounds_batch` - Batch lookup (max 100)

#### Open Targets Server

**Source:** [`src/lifesciences_mcp/servers/opentargets.py`](src/lifesciences_mcp/servers/opentargets.py)

**Tools:**
- `search_targets` - Fuzzy search for targets
- `get_target` - Strict lookup by Ensembl gene ID
- `get_associations` - Get target-disease associations

#### STRING Server

**Source:** [`src/lifesciences_mcp/servers/string.py`](src/lifesciences_mcp/servers/string.py)

**Tools:**
- `search_proteins` - Fuzzy search for proteins
- `get_interactions` - Get protein-protein interactions
- `get_network_image_url` - Get network visualization URL

#### BioGRID Server

**Source:** [`src/lifesciences_mcp/servers/biogrid.py`](src/lifesciences_mcp/servers/biogrid.py)

**Tools:**
- `search_genes` - Search genes by symbol
- `get_interactions` - Get genetic/physical interactions

**Authentication:** Requires `BIOGRID_API_KEY` environment variable

#### WikiPathways Server

**Source:** [`src/lifesciences_mcp/servers/wikipathways.py`](src/lifesciences_mcp/servers/wikipathways.py)

**Tools:**
- `search_pathways` - Fuzzy search for pathways
- `get_pathway` - Strict lookup by pathway CURIE
- `get_pathways_for_gene` - Reverse lookup: pathways for gene
- `get_pathway_components` - Extract pathway components

#### ClinicalTrials Server

**Source:** [`src/lifesciences_mcp/servers/clinicaltrials.py`](src/lifesciences_mcp/servers/clinicaltrials.py)

**Tools:**
- `search_trials` - Search trials by condition/intervention
- `get_trial` - Strict lookup by NCT CURIE
- `get_trial_locations` - Get trial sites

#### Additional Servers

**Ensembl Server:** `search_genes`, `get_gene`, `get_transcript`
**Entrez Server:** `search_genes`, `get_gene`, `get_pubmed_links`
**PubChem Server:** `search_compounds`, `get_compound`
**IUPHAR Server:** `search_ligands`, `get_ligand`, `search_targets`, `get_target`
**DrugBank Server:** `search_drugs`, `get_drug` (requires API key)

---

## MCP Tools Reference

### Gene Tools

| Tool Name | Server | Description | Parameters | Returns |
|-----------|--------|-------------|------------|---------|
| `hgnc_search_genes` | HGNC | Fuzzy search for genes | `query: str`, `slim: bool`, `cursor: str`, `page_size: int` | `PaginationEnvelope[SearchCandidate]` |
| `hgnc_get_gene` | HGNC | Strict lookup by HGNC CURIE | `hgnc_id: str` | `Gene` |
| `entrez_search_genes` | Entrez | Search NCBI Gene database | `query: str`, `page_size: int`, `cursor: str` | `PaginationEnvelope[EntrezGeneSearchCandidate]` |
| `entrez_get_gene` | Entrez | Get gene by Entrez CURIE | `entrez_id: str` | `EntrezGene` |
| `entrez_get_pubmed_links` | Entrez | Get PubMed articles for gene | `entrez_id: str`, `limit: int` | `list[str]` |
| `ensembl_search_genes` | Ensembl | Search Ensembl for genes | `query: str`, `species: str`, `page_size: int` | `PaginationEnvelope[EnsemblGeneSearchCandidate]` |
| `ensembl_get_gene` | Ensembl | Get gene by Ensembl ID | `ensembl_id: str` | `EnsemblGene` |
| `ensembl_get_transcript` | Ensembl | Get transcript by ID | `transcript_id: str` | `EnsemblTranscript` |

### Protein Tools

| Tool Name | Server | Description | Parameters | Returns |
|-----------|--------|-------------|------------|---------|
| `uniprot_search_proteins` | UniProt | Fuzzy search for proteins | `query: str`, `slim: bool`, `cursor: str`, `page_size: int` | `PaginationEnvelope[ProteinSearchCandidate]` |
| `uniprot_get_protein` | UniProt | Strict lookup by UniProt CURIE | `uniprot_id: str`, `slim: bool` | `Protein` |

### Compound Tools

| Tool Name | Server | Description | Parameters | Returns |
|-----------|--------|-------------|------------|---------|
| `chembl_search_compounds` | ChEMBL | Fuzzy search for compounds | `query: str`, `slim: bool`, `cursor: str`, `page_size: int` | `PaginationEnvelope[CompoundSearchCandidate]` |
| `chembl_get_compound` | ChEMBL | Strict lookup by ChEMBL CURIE | `chembl_id: str`, `slim: bool` | `Compound` dict |
| `chembl_get_compounds_batch` | ChEMBL | Batch lookup (max 100) | `chembl_ids: list[str]`, `slim: bool` | `list[dict]` |
| `pubchem_search_compounds` | PubChem | Search compounds | `query: str`, `page_size: int` | `PaginationEnvelope[PubChemSearchCandidate]` |
| `pubchem_get_compound` | PubChem | Get compound by CID | `cid: str` | `PubChemCompound` |

### Drug Tools

| Tool Name | Server | Description | Parameters | Returns |
|-----------|--------|-------------|------------|---------|
| `drugbank_search_drugs` | DrugBank | Search approved drugs | `query: str`, `page_size: int` | `PaginationEnvelope[DrugSearchCandidate]` |
| `drugbank_get_drug` | DrugBank | Get drug by DrugBank ID | `drugbank_id: str` | `Drug` |
| `iuphar_search_ligands` | IUPHAR | Search pharmacological ligands | `query: str`, `page_size: int` | `PaginationEnvelope[LigandSearchCandidate]` |
| `iuphar_get_ligand` | IUPHAR | Get ligand by IUPHAR ID | `ligand_id: str` | `Ligand` |
| `iuphar_search_targets` | IUPHAR | Search pharmacological targets | `query: str`, `page_size: int` | `PaginationEnvelope[PharmacologicalTargetSearchCandidate]` |
| `iuphar_get_target` | IUPHAR | Get target by IUPHAR ID | `target_id: str` | `PharmacologicalTarget` |

### Target-Disease Tools

| Tool Name | Server | Description | Parameters | Returns |
|-----------|--------|-------------|------------|---------|
| `opentargets_search_targets` | OpenTargets | Fuzzy search for targets | `query: str`, `page_size: int` | `PaginationEnvelope[TargetSearchCandidate]` |
| `opentargets_get_target` | OpenTargets | Get target by Ensembl ID | `ensembl_id: str` | `Target` |
| `opentargets_get_associations` | OpenTargets | Get target-disease associations | `ensembl_id: str`, `page_size: int` | `PaginationEnvelope[Association]` |

### Interaction Tools

| Tool Name | Server | Description | Parameters | Returns |
|-----------|--------|-------------|------------|---------|
| `string_search_proteins` | STRING | Search proteins | `query: str`, `species: int`, `limit: int` | `PaginationEnvelope[InteractionSearchCandidate]` |
| `string_get_interactions` | STRING | Get protein-protein interactions | `protein_id: str`, `required_score: int`, `limit: int` | `InteractionNetwork` |
| `string_get_network_image_url` | STRING | Get network visualization URL | `protein_ids: list[str]`, `required_score: int` | `str` |
| `biogrid_search_genes` | BioGRID | Search genes | `query: str` | `PaginationEnvelope[BioGridSearchCandidate]` |
| `biogrid_get_interactions` | BioGRID | Get genetic/physical interactions | `gene_symbol: str`, `max_results: int` | `InteractionResult` |

### Pathway Tools

| Tool Name | Server | Description | Parameters | Returns |
|-----------|--------|-------------|------------|---------|
| `wikipathways_search_pathways` | WikiPathways | Search pathways | `query: str`, `organism: str`, `page_size: int` | `PaginationEnvelope[PathwaySearchCandidate]` |
| `wikipathways_get_pathway` | WikiPathways | Get pathway by CURIE | `pathway_id: str` | `Pathway` |
| `wikipathways_get_pathways_for_gene` | WikiPathways | Find pathways for gene | `gene_id: str`, `organism: str`, `page_size: int` | `PaginationEnvelope[PathwaySearchCandidate]` |
| `wikipathways_get_pathway_components` | WikiPathways | Extract pathway components | `pathway_id: str` | `PathwayComponents` |

### Clinical Trial Tools

| Tool Name | Server | Description | Parameters | Returns |
|-----------|--------|-------------|------------|---------|
| `clinicaltrials_search_trials` | ClinicalTrials | Search trials | `query: str`, `phase: str`, `status: str`, `page_size: int` | `PaginationEnvelope[TrialSearchCandidate]` |
| `clinicaltrials_get_trial` | ClinicalTrials | Get trial by NCT ID | `nct_id: str` | `Trial` |
| `clinicaltrials_get_trial_locations` | ClinicalTrials | Get trial sites | `nct_id: str` | `list[TrialLocation]` |

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BIOGRID_API_KEY` | BioGRID API key (free) | None | For BioGRID tools |
| `DRUGBANK_API_KEY` | DrugBank API key (commercial) | None | For DrugBank tools |
| `LIFESCIENCES_TIMEOUT` | Request timeout (seconds) | `30.0` | No |

**Getting API Keys:**
- **BioGRID:** Free registration at https://webservice.thebiogrid.org/
- **DrugBank:** Commercial license required at https://www.drugbank.ca/

### Client Configuration

All clients accept standard parameters in their constructors:

```python
# Base client configuration
client = LifeSciencesClient(
    base_url="https://api.example.com",
    timeout=30.0,        # Request timeout in seconds
    max_connections=10   # Connection pool size
)

# Most domain clients use defaults
hgnc_client = HGNCClient()  # Uses HGNC_BASE_URL, timeout=30.0
```

**Rate Limiting Configuration:**

Rate limits are hardcoded per API documentation:
- **HGNC:** 10 req/s (100ms delay)
- **UniProt:** 10 req/s (100ms delay)
- **ChEMBL:** 10 req/s (100ms delay)
- **Open Targets:** 10 req/s (100ms delay)
- **WikiPathways:** 1 req/s (1000ms delay, conservative)

All clients implement exponential backoff on rate limit errors (429, 403, 503).

---

## Usage Patterns

### Pattern 1: Fuzzy-to-Fact Protocol

The core pattern for entity resolution:

```python
async def fuzzy_to_fact_example():
    async with HGNCClient() as client:
        # Phase 1: Fuzzy search (natural language)
        search_result = await client.search_genes("breast cancer 1", page_size=10)

        if hasattr(search_result, 'error'):
            print(f"Search failed: {search_result.error.recovery_hint}")
            return

        # Phase 2: Review candidates and select
        print("Search Results:")
        for candidate in search_result.items:
            print(f"  {candidate.id}: {candidate.symbol} - {candidate.name} (score={candidate.score})")

        # Select top match
        if search_result.items:
            gene_id = search_result.items[0].id

            # Phase 3: Strict lookup for complete record
            gene = await client.get_gene(gene_id)

            if hasattr(gene, 'error'):
                print(f"Lookup failed: {gene.error.recovery_hint}")
                return

            # Use complete gene record with cross-references
            print(f"\nComplete Gene Record:")
            print(f"  Symbol: {gene.symbol}")
            print(f"  Location: {gene.location}")
            print(f"  UniProt: {gene.cross_references.uniprot}")
            print(f"  Ensembl: {gene.cross_references.ensembl_gene}")
```

### Pattern 2: Cross-Reference Navigation

Navigate between databases using cross-references:

```python
async def cross_reference_navigation():
    # Start with gene
    async with HGNCClient() as hgnc:
        gene = await hgnc.get_gene("HGNC:1100")  # BRCA1
        uniprot_id = gene.cross_references.uniprot[0]  # P38398

    # Navigate to protein
    async with UniProtClient() as uniprot:
        protein = await uniprot.get_protein(f"UniProtKB:{uniprot_id}")
        pdb_ids = protein.cross_references.pdb[:5]  # First 5 structures

    # Use cross-references for validation
    print(f"Gene: {gene.symbol}")
    print(f"Protein: {protein.name}")
    print(f"PDB Structures: {', '.join(pdb_ids)}")
```

### Pattern 3: Entity Triangulation

Validate entity identity by triangulating across multiple databases:

```python
async def entity_triangulation():
    query = "TP53"

    # Get entity from multiple sources
    async with HGNCClient() as hgnc:
        hgnc_result = await hgnc.search_genes(query, page_size=1)
        hgnc_gene_id = hgnc_result.items[0].id if hgnc_result.items else None

    async with EntrezClient() as entrez:
        entrez_result = await entrez.search_genes(query, page_size=1)
        entrez_gene_id = entrez_result.items[0].id if entrez_result.items else None

    async with EnsemblClient() as ensembl:
        ensembl_result = await ensembl.search_genes(query, page_size=1)
        ensembl_gene_id = ensembl_result.items[0].id if ensembl_result.items else None

    # Verify cross-references match
    async with HGNCClient() as hgnc:
        gene = await hgnc.get_gene(hgnc_gene_id)

        # Validate triangulation
        assert gene.cross_references.entrez in entrez_gene_id
        assert gene.cross_references.ensembl_gene in ensembl_gene_id

        print(f"✓ Entity validated across 3 databases:")
        print(f"  HGNC: {hgnc_gene_id}")
        print(f"  Entrez: {entrez_gene_id}")
        print(f"  Ensembl: {ensembl_gene_id}")
```

### Pattern 4: Batch Operations

Optimize token usage with batch operations:

```python
async def batch_compound_lookup():
    async with ChEMBLClient() as client:
        # Get multiple compounds in single API call
        compounds = await client.get_compounds_batch([
            "CHEMBL:25",      # Aspirin
            "CHEMBL:939",     # Gefitinib
            "CHEMBL:521686",  # Olaparib
            "CHEMBL:1946170", # Pembrolizumab
            "CHEMBL:2105717"  # Nivolumab
        ], slim=True)  # Use slim mode for efficiency

        for compound in compounds:
            if 'error' in compound:
                print(f"Error: {compound['error']['message']}")
            else:
                print(f"{compound['id']}: {compound['name']} ({compound['molecular_formula']})")
```

### Pattern 5: Pagination Handling

Handle large result sets with pagination:

```python
async def pagination_example():
    async with WikiPathwaysClient() as client:
        all_pathways = []
        cursor = None

        # Iterate through pages
        while True:
            result = await client.search_pathways(
                "TP53",
                page_size=50,
                cursor=cursor
            )

            if hasattr(result, 'error'):
                print(f"Error: {result.error.message}")
                break

            all_pathways.extend(result.items)

            # Check for more pages
            cursor = result.pagination.cursor
            if not cursor:
                break

        print(f"Total pathways: {len(all_pathways)}")
```

### Pattern 6: Error Recovery

Implement agent self-correction using error recovery hints:

```python
async def error_recovery_example():
    async with HGNCClient() as client:
        # Attempt 1: Try strict lookup with invalid CURIE
        result = await client.get_gene("p53")

        if hasattr(result, 'error'):
            if result.error.code == "UNRESOLVED_ENTITY":
                # Recovery: Use fuzzy search as suggested
                print(f"Recovery hint: {result.error.recovery_hint}")

                # Attempt 2: Fuzzy search
                search_result = await client.search_genes("p53")
                if search_result.items:
                    # Attempt 3: Retry with valid CURIE
                    gene_id = search_result.items[0].id
                    gene = await client.get_gene(gene_id)
                    print(f"✓ Recovered: {gene.symbol}")
```

---

## Best Practices

### 1. Always Use Fuzzy Search First

**Why:** Strict lookup tools require exact CURIE format and will fail on natural language queries.

**Bad:**
```python
# This will fail with UNRESOLVED_ENTITY error
gene = await client.get_gene("breast cancer gene 1")
```

**Good:**
```python
# Search first, then lookup
search_result = await client.search_genes("breast cancer gene 1")
if search_result.items:
    gene = await client.get_gene(search_result.items[0].id)
```

### 2. Handle Rate Limits Gracefully

**Why:** All clients implement rate limiting and exponential backoff, but you should still handle rate limit errors.

**Pattern:**
```python
async def rate_limit_aware():
    async with HGNCClient() as client:
        for query in queries:
            result = await client.search_genes(query)

            if hasattr(result, 'error') and result.error.code == "RATE_LIMITED":
                # Wait as suggested
                print(f"Rate limited: {result.error.recovery_hint}")
                await asyncio.sleep(60)
                # Retry
                result = await client.search_genes(query)
```

### 3. Use Cross-References for Validation

**Why:** Cross-references enable entity triangulation and validation across databases.

**Pattern:**
```python
async def validate_with_xrefs():
    async with HGNCClient() as hgnc:
        gene = await hgnc.get_gene("HGNC:1100")

        # Validate UniProt cross-reference exists
        if gene.cross_references.uniprot:
            uniprot_id = gene.cross_references.uniprot[0]

            # Verify in UniProt
            async with UniProtClient() as uniprot:
                protein = await uniprot.get_protein(f"UniProtKB:{uniprot_id}")

                # Validate reverse cross-reference
                assert protein.cross_references.hgnc == "HGNC:1100"
                print("✓ Cross-reference validated")
```

### 4. Use Context Managers for Cleanup

**Why:** Ensures HTTP clients are properly closed and connections released.

**Bad:**
```python
client = HGNCClient()
result = await client.search_genes("TP53")
# Client never closed - connection leak
```

**Good:**
```python
async with HGNCClient() as client:
    result = await client.search_genes("TP53")
# Client automatically closed
```

### 5. Optimize Token Usage with Slim Mode

**Why:** Slim mode reduces response size by 80-95%, saving tokens for AI applications.

**Pattern:**
```python
# Phase 1: Search with slim mode for candidate review
search_result = await client.search_genes("TP53", slim=True)
# ~20 tokens per candidate

# Phase 2: Get full record only for selected candidate
gene = await client.get_gene(search_result.items[0].id)
# ~300 tokens for complete record
```

### 6. Batch When Possible

**Why:** Batch operations reduce API calls and improve performance.

**Pattern:**
```python
# Single API call for 100 compounds
compounds = await chembl.get_compounds_batch(chembl_ids, slim=True)

# vs. 100 separate API calls
for chembl_id in chembl_ids:
    compound = await chembl.get_compound(chembl_id)
```

### 7. Check Error Codes Before Retrying

**Why:** Some errors should not be retried (e.g., ENTITY_NOT_FOUND, UNRESOLVED_ENTITY).

**Pattern:**
```python
result = await client.get_gene(gene_id)

if hasattr(result, 'error'):
    if result.error.code in ["ENTITY_NOT_FOUND", "UNRESOLVED_ENTITY"]:
        # Don't retry - these are permanent failures
        print(f"Permanent error: {result.error.recovery_hint}")
    elif result.error.code in ["RATE_LIMITED", "UPSTREAM_ERROR"]:
        # Retry after delay
        await asyncio.sleep(60)
        result = await client.get_gene(gene_id)
```

---

## Error Handling

### Error Code Reference

| Error Code | HTTP Status | Retry? | Recovery Strategy |
|------------|-------------|--------|-------------------|
| `UNRESOLVED_ENTITY` | 400 | No | Use fuzzy search first |
| `ENTITY_NOT_FOUND` | 404 | No | Verify CURIE or try alternate IDs |
| `AMBIGUOUS_QUERY` | 400 | No | Refine query terms |
| `RATE_LIMITED` | 429 | Yes | Wait `retry_after` seconds |
| `UPSTREAM_ERROR` | 500-599 | Yes | Retry with exponential backoff |
| `INVALID_CROSS_REFERENCE` | 400 | No | Validate cross-reference format |

### Error Handling Examples

**Example 1: UNRESOLVED_ENTITY Recovery**

```python
async def handle_unresolved_entity():
    async with HGNCClient() as client:
        result = await client.get_gene("BRCA1")  # Invalid - missing CURIE prefix

        if hasattr(result, 'error'):
            if result.error.code == "UNRESOLVED_ENTITY":
                # Agent-actionable recovery
                print(f"Recovery: {result.error.recovery_hint}")
                # "Call search_genes to resolve the identifier first."

                # Implement recovery
                search_result = await client.search_genes(result.error.invalid_input)
                if search_result.items:
                    gene = await client.get_gene(search_result.items[0].id)
                    return gene
```

**Example 2: Rate Limit Handling**

```python
async def handle_rate_limits():
    async with UniProtClient() as client:
        result = await client.search_proteins("p53")

        if hasattr(result, 'error'):
            if result.error.code == "RATE_LIMITED":
                # Extract retry_after from recovery_hint
                # "Retry after 60 seconds."
                retry_after = 60  # Parse from hint or use default

                print(f"Rate limited. Waiting {retry_after}s...")
                await asyncio.sleep(retry_after)

                # Retry
                result = await client.search_proteins("p53")
```

**Example 3: Upstream Error Retry**

```python
async def handle_upstream_errors():
    async with ChEMBLClient() as client:
        max_retries = 3

        for attempt in range(max_retries):
            result = await client.get_compound("CHEMBL:25")

            if hasattr(result, 'error'):
                if result.error.code == "UPSTREAM_ERROR":
                    if attempt < max_retries - 1:
                        delay = 2 ** attempt  # Exponential backoff
                        print(f"Upstream error. Retry {attempt+1}/{max_retries} in {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"Failed after {max_retries} retries")
                        return None
            else:
                # Success
                return result
```

**Example 4: Comprehensive Error Handler**

```python
async def robust_gene_lookup(gene_id: str):
    async with HGNCClient() as client:
        result = await client.get_gene(gene_id)

        if hasattr(result, 'error'):
            error = result.error

            # Log error details
            print(f"Error Code: {error.code}")
            print(f"Message: {error.message}")
            print(f"Recovery Hint: {error.recovery_hint}")
            print(f"Invalid Input: {error.invalid_input}")

            # Error-specific recovery
            if error.code == "UNRESOLVED_ENTITY":
                # Try fuzzy search
                search_result = await client.search_genes(error.invalid_input)
                if search_result.items:
                    return await client.get_gene(search_result.items[0].id)

            elif error.code == "ENTITY_NOT_FOUND":
                # Try alternative identifiers
                print("Entity not found. Try alternative gene symbol.")
                return None

            elif error.code == "RATE_LIMITED":
                # Wait and retry
                await asyncio.sleep(60)
                return await client.get_gene(gene_id)

            elif error.code == "UPSTREAM_ERROR":
                # Retry with backoff
                await asyncio.sleep(5)
                return await client.get_gene(gene_id)

            else:
                # Unknown error
                print(f"Unknown error: {error.code}")
                return None

        # Success
        return result
```

---

## Appendix

### Type Definitions

**CURIE Patterns (Regex):**

```python
# Gene identifiers
HGNC_CURIE_PATTERN = r"^HGNC:\d+$"
NCBI_GENE_CURIE_PATTERN = r"^NCBIGene:\d+$"

# Protein identifiers
UNIPROT_CURIE_PATTERN = r"^UniProtKB:[A-Z][A-Z0-9]{5,9}$"

# Compound identifiers
CHEMBL_CURIE_PATTERN = r"^CHEMBL:[0-9]+$"
PUBCHEM_CURIE_PATTERN = r"^CID:\d+$"

# Trial identifiers
NCT_CURIE_PATTERN = r"^NCT:\d{8}$"

# Pathway identifiers
WP_CURIE_PATTERN = r"^WP:WP\d+$"

# Cross-reference patterns
ENSEMBL_GENE_PATTERN = r"^ENSG\d{11}$"
ENSEMBL_TRANSCRIPT_PATTERN = r"^ENST\d{11}$"
ENTREZ_PATTERN = r"^\d+$"
REFSEQ_PATTERN = r"^[NX][MR]_\d+$"
OMIM_PATTERN = r"^\d{6}$"
```

**Enums:**

```python
# Error codes
class ErrorCode(str, Enum):
    UNRESOLVED_ENTITY = "UNRESOLVED_ENTITY"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    INVALID_CROSS_REFERENCE = "INVALID_CROSS_REFERENCE"

# Trial phases
class TrialPhase(str, Enum):
    EARLY_PHASE1 = "EARLY_PHASE1"
    PHASE1 = "PHASE1"
    PHASE2 = "PHASE2"
    PHASE3 = "PHASE3"
    PHASE4 = "PHASE4"
    NA = "NA"

# Trial status
class TrialStatus(str, Enum):
    RECRUITING = "RECRUITING"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
```

---

### Cross-Reference Registry (22 Keys)

Complete list of supported cross-reference keys in the Agentic Biolink schema:

| Key | Type | Database | Example |
|-----|------|----------|---------|
| `ensembl_gene` | `str` | Ensembl | `ENSG00000012048` |
| `ensembl_transcript` | `list[str]` | Ensembl | `["ENST00000357654"]` |
| `uniprot` | `list[str]` | UniProt | `["P38398"]` |
| `entrez` | `str` | NCBI Entrez | `672` |
| `refseq` | `list[str]` | RefSeq | `["NM_007294"]` |
| `hgnc` | `str` | HGNC | `HGNC:1100` |
| `omim` | `str` | OMIM | `113705` |
| `orphanet` | `str` | Orphanet | `ORPHA:558` |
| `mondo` | `str` | MONDO | `MONDO:0007254` |
| `efo` | `str` | EFO | `EFO:0000305` |
| `chembl` | `str` | ChEMBL | `CHEMBL:1201583` |
| `drugbank` | `str` | DrugBank | `DB:01050` |
| `pubchem_compound` | `str` | PubChem | `2244` |
| `pubchem_substance` | `str` | PubChem | `46506019` |
| `kegg` | `str` | KEGG | `hsa:672` |
| `kegg_pathway` | `list[str]` | KEGG | `["hsa04110"]` |
| `string` | `str` | STRING | `9606.ENSP00000269305` |
| `biogrid` | `str` | BioGRID | `112` |
| `stitch` | `str` | STITCH | `CIDm00002244` |
| `iuphar` | `str` | IUPHAR/GtoPdb | `IUPHAR:4903` |
| `pdb` | `list[str]` | PDB | `["1TUP", "1TSR"]` |

---

### Performance Benchmarks

**Typical Latencies (SC-001 target: <2s):**

| Operation | Typical Latency | Notes |
|-----------|----------------|-------|
| Fuzzy search (50 results) | 200-500ms | HGNC, UniProt, ChEMBL |
| Strict lookup | 100-300ms | Single entity fetch |
| Batch lookup (100 items) | 500-1000ms | ChEMBL batch operation |
| Interaction network | 500-1500ms | STRING, BioGRID |
| Pathway components | 1000-2000ms | WikiPathways GPML parsing |

**Token Budgets:**

| Model | Slim Mode | Full Mode | Reduction |
|-------|-----------|-----------|-----------|
| SearchCandidate | 20 tokens | N/A | N/A |
| Gene | N/A | 115-300 tokens | N/A |
| Protein | 20 tokens | 200-400 tokens | 90% |
| Compound | 20 tokens | 115-300 tokens | 93% |
| Pathway | 20 tokens | 300 tokens | 93% |
| Trial | 100-200 tokens | 5K-10K tokens | 98% |

---

### Version Information

**Package Version:** 0.1.0

**API Versions:**
- HGNC REST API: v1 (https://rest.genenames.org)
- UniProt REST API: 2024.03 (https://rest.uniprot.org)
- ChEMBL Web Service: v33 (https://www.ebi.ac.uk/chembl/api/data)
- Open Targets Platform: v23.12 (GraphQL)
- STRING: v12.0 (https://string-db.org/api)
- BioGRID: v4.4 (https://webservice.thebiogrid.org)
- WikiPathways: 2024.12 (https://webservice.wikipathways.org)
- ClinicalTrials.gov: v2 (https://clinicaltrials.gov/api/v2)

**Dependencies:**
- Python: >=3.11
- httpx: ^0.27.0
- pydantic: ^2.0.0
- fastmcp: ^0.2.0
- chembl-webresource-client: ^0.10.8

---

### Related Documentation

**Architecture:**
- [ADR-001: Agentic Biolink Architecture](docs/decisions/001-agentic-biolink-architecture.md)
- [Constitution v1.1.0](docs/CONSTITUTION.md)
- [Implementation Plan](docs/research/IMPLEMENTATION_PLAN.md)

**Usage Guides:**
- [Competency Questions Walkthrough](docs/research/deep-research/competency_questions_walkthrough_2026.md)
- [Integration Test Suite](tests/integration/test_competency_questions.py)

**Project Information:**
- [README](README.md)
- [CLAUDE.md - Known Issues](CLAUDE.md)
