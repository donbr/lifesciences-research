# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastMCP wrappers for essential life sciences APIs, enabling LLM agents to query biological databases for drug discovery and repurposing.

**Status:**
- HGNC server v0.1.0 - ✅ Complete (21 tests passing)
- UniProt server v0.1.0 - ✅ Complete (29 tests passing, all 4 User Stories)
- ChEMBL server v0.1.0 - ✅ Complete (112 tests, PR #10 merged)
- Open Targets server v0.1.0 - ✅ Complete (9 tests, PR #11 merged)
- DrugBank server v0.1.0 - ⛔ **BLOCKED** (33 unit tests, PR #12 open - API key required)
- STRING server v0.1.0 - ✅ Complete (3 tools, integration tests passing)
- BioGRID server v0.1.0 - ✅ Complete (11 integration tests passing, all 4 User Stories)
- Ensembl server v0.1.0 - ✅ Complete (86 tests: 62 unit + 24 integration)
- Entrez server v0.1.0 - ✅ Complete (58 tests: 38 unit + 20 integration)
- PubChem server v0.1.0 - ✅ Complete (100 tests: 81 unit + 19 integration)
- IUPHAR/GtoPdb server v0.1.0 - ✅ Complete (59 tests: 48 integration + 11 unit, all 5 User Stories)
- WikiPathways server v0.1.0 - ✅ Complete (4 tools: search_pathways, get_pathway, get_pathways_for_gene, get_pathway_components)
- ClinicalTrials.gov server v0.1.0 - ✅ Complete (3 tools, 13 unit tests passing | Manual curl testing required due to Cloudflare blocking)

**Platform Skills:**
- lifesciences-crispr - ✅ Complete (BioGRID ORCS 5-phase synthetic lethality validation workflow)
- lifesciences-genomics - ✅ Complete (Ensembl, NCBI, HGNC curl endpoints)
- lifesciences-proteomics - ✅ Complete (UniProt, STRING, BioGRID curl endpoints)
- lifesciences-pharmacology - ✅ Complete (ChEMBL, PubChem, DrugBank, IUPHAR curl endpoints)
- lifesciences-clinical - ✅ Complete (Open Targets, ClinicalTrials.gov curl endpoints)
- lifesciences-graph-builder - ✅ Complete (Fuzzy-to-Fact orchestration workflow)

## Key Documentation

| Document | Purpose |
|----------|---------|
| `docs/platform-engineering-rationale.md` | **Start here** - WHY we use Platform Engineering for agents |
| `docs/adr/accepted/adr-001-v1.2.md` | Binding architecture specification |
| `docs/adr/accepted/adr-002-v1.0.md` | ADR-002: Project Skills (the "Hardware") |
| `docs/adr/accepted/adr-003-v1.0.md` | ADR-003: SpecKit SDLC (the "Operating System") |
| `docs/adr/accepted/adr-004-v1.0.md` | ADR-004: FastMCP Lifecycle Management (shutdown hook antipattern) |
| `docs/adr/accepted/adr-005-v1.0.md` | ADR-005: Git Worktrees for Parallel Development (30-50% speedup) |
| `docs/speckit-standard-prompt.md` | **Standard prompt template** v1.1.0 for new MCP servers |

## Platform Skills

### SpecKit Workflow (Specification-Driven Development)

```
/speckit.constitution  → Establish project principles (one-time)
/speckit.specify       → Create feature specification
/speckit.clarify       → (optional) Surface underspecified areas
/speckit.plan          → Create implementation plan
/speckit.tasks         → Generate actionable tasks
/speckit.analyze       → (optional) Cross-artifact consistency check
/speckit.implement     → Execute bounded implementation
```

### Scaffolding Skills (Constitution Principle VI)

| Skill | Purpose | Usage |
|-------|---------|-------|
| `/scaffold-fastmcp` | Create new MCP server with standard structure | `/scaffold-fastmcp uniprot` |

The `/scaffold-fastmcp` skill generates:
- `src/lifesciences_mcp/servers/<api>.py` - FastMCP server with tool stubs
- Client class stub in `client.py`
- Integration test stubs
- Feature directory in `specs/`

## Development Commands

```bash
# Package management
uv sync                          # Install dependencies
uv sync --extra dev              # Install with dev dependencies

# Testing
uv run pytest tests/ -v
uv run pytest tests/unit/test_file.py::test_name -v  # Single test
uv run pytest -m "not integration"                    # Unit only

# Linting
uv run ruff check --fix . && uv run ruff format .
uv run pyright

# Run MCP server (when implemented)
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
uv run fastmcp run src/lifesciences_mcp/servers/wikipathways.py
```

## Manual Testing

### ClinicalTrials.gov API (Cloudflare Blocking Workaround)

**Issue**: ClinicalTrials.gov uses Cloudflare TLS fingerprinting that blocks Python httpx clients (403 Forbidden), while curl works fine.

**Root Cause**: Cloudflare bot protection detects and blocks automated Python clients. This is **NOT a code bug** - the API parameters are correct (verified via curl).

**Workaround - Manual Testing with curl**:

```bash
# Test 1: Simple search (verify API accepts parameters)
curl -s "https://clinicaltrials.gov/api/v2/studies?query.term=cancer&pageSize=1&format=json" | jq '.studies[0].protocolSection.identificationModule.nctId'
# Expected: Returns NCT ID (e.g., "NCT00963261")

# Test 2: Status filter (AGE-132 fix verification)
curl -s "https://clinicaltrials.gov/api/v2/studies?filter.overallStatus=RECRUITING&pageSize=1&format=json" | jq '.studies[0].protocolSection.statusModule.overallStatus'
# Expected: "RECRUITING"

# Test 3: Phase filter (AGE-132 fix verification)
curl -s "https://clinicaltrials.gov/api/v2/studies?filter.advanced=AREA[Phase]PHASE3&pageSize=1&format=json" | jq '.studies[0].protocolSection.designModule.phases[0]'
# Expected: "PHASE3"

# Test 4: Multi-filter search (AGE-132 complete test case)
curl -s "https://clinicaltrials.gov/api/v2/studies?query.cond=diabetes&filter.overallStatus=COMPLETED&filter.advanced=AREA[Phase]PHASE3&pageSize=1&format=json" | jq '.studies | length'
# Expected: Returns 1 (one study in results)

# Test 5: Get trial details by NCT ID
curl -s "https://clinicaltrials.gov/api/v2/studies/NCT00461032?format=json" | jq '.protocolSection.identificationModule.nctId'
# Expected: "NCT00461032"
```

**Unit Testing Alternative**:

Since integration tests can't run due to Cloudflare blocking, use unit tests with mocks to verify parameter building logic:

```bash
# Run unit tests (13 tests, all parameter validation)
uv run pytest tests/unit/test_clinicaltrials_client.py -v

# Key tests verify:
# - status uses filter.overallStatus (not query.overallStatus) ✅
# - phase uses filter.advanced with Essie syntax ✅
# - Multi-filter combinations work correctly ✅
```

**Technical Details**:

| Client | Result | Reason |
|--------|--------|--------|
| curl | ✅ 200 OK | Standard browser-like TLS fingerprint |
| httpx | ❌ 403 Forbidden | Python client detected by Cloudflare |
| wget | ✅ 200 OK | Standard TLS fingerprint |
| Python requests | ❌ 403 Forbidden | Python client detected |

**Not solvable at application layer** - would require browser automation (Playwright/Selenium) or proxy service.

**References**:
- AGE-132: Fixed `query.overallStatus` → `filter.overallStatus` bug
- Parameter fixes: `src/lifesciences_mcp/clients/clinicaltrials.py` lines 237-240
- Research documentation: `specs/013-clinicaltrials-mcp-server/research.md` lines 1015-1018

## Architecture (from ADR-001 v1.2)

### Current Structure
```
src/lifesciences_mcp/
├── __init__.py          # Package exports
├── clients/
│   ├── base.py          # LifeSciencesClient base class
│   ├── hgnc.py          # HGNCClient (async httpx)
│   ├── uniprot.py       # UniProtClient (async httpx)
│   ├── chembl.py        # ChEMBLClient (SDK + run_in_executor)
│   ├── opentargets.py   # OpenTargetsClient (async httpx + GraphQL)
│   ├── drugbank.py      # DrugBankClient (async httpx) ⛔ needs API key
│   ├── string.py        # STRINGClient (async httpx) ✅ Tier 1
│   ├── biogrid.py       # BioGridClient (async httpx) ✅ Tier 1
│   ├── ensembl.py       # EnsemblClient (async httpx) ✅ Tier 4
│   ├── entrez.py        # EntrezClient (async httpx + XML parsing) ✅ Tier 4
│   ├── pubchem.py       # PubChemClient (async httpx) ✅ Tier 2
│   ├── iuphar.py        # IUPHARClient (async httpx) ✅ Tier 2
│   ├── wikipathways.py  # WikiPathwaysClient (async httpx) ✅ Tier 3
│   └── clinicaltrials.py # ClinicalTrialsClient (async httpx) ✅ Tier 3
├── models/
│   ├── __init__.py      # Model exports
│   ├── envelopes.py     # PaginationEnvelope, ErrorEnvelope
│   ├── gene.py          # Gene, SearchCandidate, CrossReferences
│   ├── protein.py       # Protein, ProteinSearchCandidate
│   ├── compound.py      # Compound, CompoundSearchCandidate
│   ├── target.py        # Target, TargetSearchCandidate, Association
│   ├── drug.py          # Drug, DrugSearchCandidate, DrugCrossReferences
│   ├── interaction.py   # Interaction, InteractionNetwork, EvidenceScores (STRING)
│   ├── biogrid.py       # GeneticInteraction, InteractionResult, BioGridSearchCandidate
│   ├── ensembl.py       # EnsemblGene, EnsemblTranscript, GeneSearchCandidate
│   ├── entrez.py        # EntrezGene, GeneSearchCandidate, EntrezCrossReferences
│   ├── pubchem.py       # PubChemCompound, CompoundSearchCandidate
│   ├── iuphar.py        # Ligand, Target, LigandSearchCandidate, TargetSearchCandidate
│   ├── pathway.py       # Pathway, PathwaySearchCandidate, RevisionMetadata, ComponentCounts
│   ├── pathway_components.py # PathwayComponents, DataNode, Interaction
│   └── clinicaltrials.py # Trial, TrialSearchCandidate, TrialLocation
└── servers/
    ├── hgnc.py          # HGNC MCP server (search_genes, get_gene)
    ├── uniprot.py       # UniProt MCP server (search_proteins, get_protein)
    ├── chembl.py        # ChEMBL MCP server (search_compounds, get_compound, get_compounds_batch)
    ├── opentargets.py   # Open Targets MCP server (search_targets, get_target, get_associations)
    ├── drugbank.py      # DrugBank MCP server (search_drugs, get_drug) ⛔ needs API key
    ├── string.py        # STRING MCP server (search_proteins, get_interactions, get_network_image_url) ✅ Tier 1
    ├── biogrid.py       # BioGRID MCP server (search_genes, get_interactions) ✅ Tier 1
    ├── ensembl.py       # Ensembl MCP server (search_genes, get_gene, get_transcript) ✅ Tier 4
    ├── entrez.py        # Entrez MCP server (search_genes, get_gene, get_pubmed_links) ✅ Tier 4
    ├── pubchem.py       # PubChem MCP server (search_compounds, get_compound) ✅ Tier 2
    ├── iuphar.py        # IUPHAR MCP server (search_ligands, get_ligand, search_targets, get_target) ✅ Tier 2
    ├── wikipathways.py  # WikiPathways MCP server (search_pathways, get_pathway, get_pathways_for_gene, get_pathway_components) ✅ Tier 3
    ├── clinicaltrials.py # ClinicalTrials MCP server (search_trials, get_trial, get_trial_locations) ✅ Tier 3
    └── gateway.py       # Unified gateway server (mounts all 12 servers for FastMCP Cloud deployment)
```

### Implemented Tools

#### HGNC Server (Complete)

| Tool | Type | Description |
|------|------|-------------|
| `search_genes` | Fuzzy | Search by name/symbol/synonym, returns ranked SearchCandidates |
| `get_gene` | Strict | Lookup by HGNC CURIE, returns full Gene with cross_references |

**Usage:**
```bash
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
```

**Tests:**
```bash
uv run pytest tests/integration/test_hgnc_api.py -v -m integration
# 7/7 tests passing
```

#### UniProt Server (Complete - All 4 User Stories)

| Tool | Type | Description |
|------|------|-------------|
| `search_proteins` | Fuzzy | Search by protein name/gene/organism, returns ranked ProteinSearchCandidates |
| `get_protein` | Strict | Lookup by UniProt CURIE, returns full Protein with cross_references |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/uniprot.py
```

**Tests:**
```bash
uv run pytest tests/integration/ -v -m integration
# 29 integration tests passing (all 4 User Stories complete)
# US1: Fuzzy search, US2: Strict lookup, US3: Cross-DB integration, US4: Error recovery
```

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Fuzzy search
search_result = await client.call_tool("search_proteins", {"query": "BRCA1", "page_size": 10})
top_candidate = search_result["items"][0]  # {"id": "UniProtKB:P38398", ...}

# Phase 2: Strict lookup
protein = await client.call_tool("get_protein", {"uniprot_id": top_candidate["id"]})
# Returns complete protein with cross_references (HGNC, Ensembl, RefSeq, PDB, OMIM, etc.)
```

#### ChEMBL Server (Complete - All 4 User Stories)

| Tool | Type | Description |
|------|------|-------------|
| `search_compounds` | Fuzzy | Search by compound name/synonym/identifier, returns ranked CompoundSearchCandidates |
| `get_compound` | Strict | Lookup by ChEMBL CURIE, returns full Compound with cross_references |
| `get_compounds_batch` | Batch | Batch lookup to prevent thread pool exhaustion (uses SDK filter) |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/chembl.py
```

**Tests:**
```bash
uv run pytest tests/integration/test_chembl_api.py -v -m integration
uv run pytest tests/unit/test_chembl_models.py tests/unit/test_chembl_client.py -v
# 50+ tests covering all 4 User Stories
```

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Fuzzy search
search_result = await client.call_tool("search_compounds", {"query": "aspirin", "page_size": 10})
top_candidate = search_result["items"][0]  # {"id": "CHEMBL:25", ...}

# Phase 2: Strict lookup
compound = await client.call_tool("get_compound", {"chembl_id": top_candidate["id"]})
# Returns complete compound with cross_references (UniProt, PDB, PubChem, DrugBank, etc.)

# Batch operations (prevents thread pool exhaustion)
compounds = await client.call_tool("get_compounds_batch", {
    "chembl_ids": ["CHEMBL:25", "CHEMBL:941", "CHEMBL:1201583"],
    "slim": True  # default: minimal fields for token efficiency
})
```

**Note:** ChEMBL uses synchronous SDK (`chembl_webresource_client`). SDK calls are wrapped with `run_in_executor` per ADR-001 §2 exception. Batch operations use `molecule.filter()` for efficient single API calls.

#### Open Targets Server (Complete - PR #11 merged)

| Tool | Type | Description |
|------|------|-------------|
| `search_targets` | Fuzzy | Search by gene symbol/name, returns ranked TargetSearchCandidates |
| `get_target` | Strict | Lookup by Ensembl ID, returns full Target with cross_references |
| `get_associations` | Strict | Get target-disease associations with evidence scores |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/opentargets.py
```

**Tests:**
```bash
uv run pytest tests/integration/test_opentargets_api.py -v -m integration
# 9 integration tests passing
```

#### DrugBank Server (⛔ BLOCKED - PR #12 open)

| Tool | Type | Description |
|------|------|-------------|
| `search_drugs` | Fuzzy | Search by name/brand/indication, returns ranked DrugSearchCandidates |
| `get_drug` | Strict | Lookup by DrugBank CURIE, returns full Drug with cross_references |

**⚠️ API Access Required:**
DrugBank requires a commercial API key. The implementation is code-complete with 33 unit tests passing, but integration tests are skipped without `DRUGBANK_API_KEY`.

| Endpoint | Status | Notes |
|----------|--------|-------|
| `go.drugbank.com` (public) | ❌ Blocked | Cloudflare challenge |
| `api.drugbank.com` (commercial) | ❌ 401 | API key required |

**To enable DrugBank:**
```bash
# Obtain API key from https://go.drugbank.com or sales@drugbank.com
export DRUGBANK_API_KEY="your-key-here"

# Run tests
uv run pytest tests/integration/test_drugbank_api.py -v -m integration
```

**Tests (without API key):**
```bash
# Unit tests always run (mocked)
uv run pytest tests/unit/test_drugbank_client.py tests/unit/test_drugbank_models.py -v
# 33 unit tests passing

# Integration tests skip automatically without DRUGBANK_API_KEY
uv run pytest tests/integration/test_drugbank_api.py -v
# 7 skipped
```

#### Ensembl Server (✅ Complete - Tier 4)

| Tool | Type | Description |
|------|------|-------------|
| `search_genes` | Fuzzy | Search by gene symbol/name/description, returns ranked GeneSearchCandidates |
| `get_gene` | Strict | Lookup by Ensembl Gene ID (ENSG*), returns full EnsemblGene with cross_references |
| `get_transcript` | Strict | Lookup by Ensembl Transcript ID (ENST*), returns EnsemblTranscript with parent gene |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/ensembl.py
```

**Tests:**
```bash
uv run pytest tests/integration/test_ensembl_api.py -v -m integration
uv run pytest tests/unit/test_ensembl_models.py tests/unit/test_ensembl_client.py -v
# 86 tests (62 unit + 24 integration)
```

**API Details:**
- **Base URL**: `https://rest.ensembl.org`
- **Protocol**: REST (JSON output)
- **Auth**: None required
- **Rate Limit**: 15 req/s

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Fuzzy search
search_result = await client.call_tool("search_genes", {"query": "BRCA1", "species": "human"})
top_candidate = search_result["items"][0]  # {"id": "ENSG00000012048", "symbol": "BRCA1", ...}

# Phase 2: Strict lookup
gene = await client.call_tool("get_gene", {"ensembl_id": top_candidate["id"]})
# Returns EnsemblGene with cross_references (HGNC, UniProt, Entrez, RefSeq, PDB, OMIM, etc.)

# Phase 3: Get transcript details
transcript = await client.call_tool("get_transcript", {"transcript_id": gene["transcripts"][0]})
# Returns EnsemblTranscript with parent_gene, is_canonical flag
```

**Species Aliases:**
The server accepts common species aliases that are normalized to Ensembl format:
| Alias | Ensembl Format |
|-------|----------------|
| `human` | `homo_sapiens` |
| `mouse` | `mus_musculus` |
| `rat` | `rattus_norvegicus` |
| `zebrafish` | `danio_rerio` |
| `fly`, `drosophila` | `drosophila_melanogaster` |
| `worm`, `c.elegans` | `caenorhabditis_elegans` |
| `yeast` | `saccharomyces_cerevisiae` |

#### STRING Server (✅ Complete - Tier 1)

| Tool | Type | Description |
|------|------|-------------|
| `search_proteins` | Fuzzy | Search by gene symbol/protein name, returns ranked InteractionSearchCandidates |
| `get_interactions` | Strict | Lookup by STRING CURIE, returns InteractionNetwork with evidence scores |
| `get_network_image_url` | Utility | Generate network visualization URL |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/string.py
```

**API Details:**
- **Base URL**: `https://string-db.org/api`
- **Protocol**: REST (JSON output)
- **Auth**: None required
- **Rate Limit**: 1 req/sec

**Evidence Channels:**
STRING provides 7 evidence types per interaction:
| Channel | Description |
|---------|-------------|
| `nscore` | Neighborhood (gene proximity) |
| `fscore` | Gene fusion events |
| `pscore` | Phyletic profiles (co-occurrence) |
| `ascore` | Co-expression (mRNA correlation) |
| `escore` | Experimental (physical binding) |
| `dscore` | Database (curated knowledge) |
| `tscore` | Textmining (literature mentions) |

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Fuzzy search
search_result = await client.call_tool("search_proteins", {"query": "TP53", "species": 9606})
top_candidate = search_result["items"][0]  # {"id": "STRING:9606.ENSP00000269305", ...}

# Phase 2: Strict lookup
network = await client.call_tool("get_interactions", {
    "string_id": top_candidate["id"],
    "required_score": 700,  # High confidence
    "limit": 10
})
# Returns InteractionNetwork with MDM2, ATM, BRCA1 interactions
```

#### BioGRID Server (✅ Complete - Tier 1)

| Tool | Type | Description |
|------|------|-------------|
| `search_genes` | Fuzzy | Validate gene symbol for BioGRID queries (Phase 1), returns normalized gene symbol |
| `get_interactions` | Strict | Get genetic/protein interactions for validated gene symbol (Phase 2) with experimental evidence |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/biogrid.py
```

**API Details:**
- **Base URL**: `https://webservice.thebiogrid.org`
- **Protocol**: REST (JSON output)
- **Auth**: Required (BIOGRID_API_KEY)
- **Rate Limit**: 2 req/sec

**Tests:**
```bash
uv run pytest tests/integration/test_biogrid_api.py -v -m integration
# 11 integration tests passing (all 4 User Stories)
```

**Key Features:**
- **Experimental evidence types**: Affinity Capture, Two-hybrid, Co-immunoprecipitation, etc.
- **Physical vs genetic interactions**: experimental_system_type field distinguishes interaction types
- **Throughput metadata**: High/low throughput annotations for reliability assessment
- **Entrez cross-references**: Automatic gene ID mapping for database integration

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Validate gene symbol
search_result = await client.call_tool("search_genes", {"query": "TP53"})
validated_symbol = search_result["items"][0]["gene_symbol"]  # "TP53"

# Phase 2: Get interactions
interactions = await client.call_tool("get_interactions", {
    "gene_symbol": validated_symbol,
    "max_results": 100
})
# Returns InteractionResult with:
# - interactions: list of GeneticInteraction objects
# - physical_count: number of physical interactions
# - genetic_count: number of genetic interactions
# - cross_references: {"entrez": "7157"}
```

**Get API key (free):** https://webservice.thebiogrid.org/

#### Entrez Server (✅ Complete - Tier 4)

| Tool | Type | Description |
|------|------|-------------|
| `search_genes` | Fuzzy | Search by name/symbol/synonym, returns ranked GeneSearchCandidates with NCBIGene CURIEs |
| `get_gene` | Strict | Lookup by NCBIGene CURIE, returns full EntrezGene with cross_references |
| `get_pubmed_links` | Strict | Get PubMed IDs associated with a gene for literature discovery |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/entrez.py
```

**API Details:**
- **Base URL**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- **Protocol**: REST (JSON for esearch/esummary, XML for efetch)
- **Auth**: Optional NCBI_API_KEY for higher rate limits
- **Rate Limit**: 3 req/s (no key) or 10 req/s (with NCBI_API_KEY)

**Tests:**
```bash
uv run pytest tests/integration/test_entrez_api.py -v -m integration
# 20 integration tests passing (all 4 User Stories)
# 38 unit tests passing (models + client)
# Performance: 95th percentile = 1.029s < 2.0s (SC-001)
```

**Key Features:**
- **Two-step API pattern**: esearch (returns IDs) → efetch/esummary (returns data)
- **XML parsing**: Uses defusedxml for security (prevents XXE attacks)
- **Adaptive rate limiting**: Automatically adjusts based on NCBI_API_KEY presence
- **Cross-reference extraction**: Maps Entrezgene_xref XML to 22-key Agentic Biolink schema

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Fuzzy search
search_result = await client.call_tool("search_genes", {"query": "BRCA1", "organism": "human"})
top_candidate = search_result["items"][0]  # {"id": "NCBIGene:672", ...}

# Phase 2: Strict lookup
gene = await client.call_tool("get_gene", {"entrez_id": top_candidate["id"]})
# Returns EntrezGene with cross_references (HGNC, Ensembl, UniProt, RefSeq, etc.)

# Phase 3: Literature discovery
pubmed_ids = await client.call_tool("get_pubmed_links", {"entrez_id": top_candidate["id"], "limit": 10})
# Returns list of PubMed IDs for evidence gathering
```

**CURIE Format:**
- Pattern: `NCBIGene:\d+`
- Examples: `NCBIGene:7157` (TP53), `NCBIGene:672` (BRCA1)
- Validation: `^NCBIGene:\d+$`

**To obtain API key (free):** https://www.ncbi.nlm.nih.gov/account/settings/

#### PubChem Server (✅ Complete - Tier 2)

| Tool | Type | Description |
|------|------|-------------|
| `search_compounds` | Fuzzy | Search by compound name/synonym/identifier, returns ranked CompoundSearchCandidates |
| `get_compound` | Strict | Lookup by PubChem CURIE, returns full Compound with SMILES, InChI, and cross_references |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/pubchem.py
```

**API Details:**
- **Base URL**: `https://pubchem.ncbi.nlm.nih.gov/rest/pug`
- **Protocol**: REST (JSON output)
- **Auth**: None required
- **Rate Limit**: 5 req/s or 400 req/min

**Tests:**
```bash
uv run pytest tests/integration/test_pubchem_api.py -v -m integration
uv run pytest tests/unit/test_pubchem_models.py tests/unit/test_pubchem_client.py -v
# 100 tests (81 unit + 19 integration)
```

**Key Features:**
- **Chemical identifiers**: SMILES, InChI, InChIKey for computational chemistry
- **Cross-references**: ChEMBL, DrugBank, KEGG for drug discovery workflows
- **Slim mode**: Token-efficient responses for batch operations
- **CURIE validation**: `^PubChem:CID\d+$` pattern enforcement

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Fuzzy search
search_result = await client.call_tool("search_compounds", {"query": "aspirin", "page_size": 10})
top_candidate = search_result["items"][0]  # {"id": "PubChem:CID2244", ...}

# Phase 2: Strict lookup
compound = await client.call_tool("get_compound", {"pubchem_id": top_candidate["id"]})
# Returns Compound with:
# - molecular_formula: "C9H8O4"
# - smiles: "CC(=O)OC1=CC=CC=C1C(=O)O"
# - inchi: "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)"
# - cross_references: {"chembl": ["CHEMBL:25"], "drugbank": ["DB00945"], ...}
```

**CURIE Format:**
- Pattern: `PubChem:CID\d+`
- Examples: `PubChem:CID2244` (aspirin), `PubChem:CID2519` (caffeine)
- Validation: `^PubChem:CID\d+$`

#### IUPHAR/GtoPdb Server (✅ Complete - Tier 2)

| Tool | Type | Description |
|------|------|-------------|
| `search_ligands` | Fuzzy | Search pharmacological ligands (drugs, chemicals, peptides) by name, returns ranked LigandSearchCandidates |
| `get_ligand` | Strict | Lookup by IUPHAR CURIE, returns full Ligand with approval status and cross_references |
| `search_targets` | Fuzzy | Search pharmacological targets (receptors, enzymes, ion channels) by name, returns ranked TargetSearchCandidates |
| `get_target` | Strict | Lookup by IUPHAR CURIE, returns full Target with gene symbols and cross_references |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/iuphar.py
```

**API Details:**
- **Base URL**: `https://www.guidetopharmacology.org/services`
- **Protocol**: REST (JSON output)
- **Auth**: None required
- **Rate Limit**: Not specified

**Tests:**
```bash
uv run pytest tests/integration/test_iuphar_api.py -v -m integration
# 59 tests (48 integration + 11 unit, all 5 User Stories)
```

**Key Features:**
- **Approved drugs**: Filter by FDA/EMA approval status, WHO Essential Medicines List
- **Target classification**: GPCR, Enzyme, Ion channel, Nuclear receptor families
- **Cross-references**: ChEMBL, DrugBank, PubChem for ligands; UniProt, Ensembl, HGNC for targets
- **Shared ID space**: Ligands and targets share numeric IDs (use search tools to disambiguate)

**Fuzzy-to-Fact Workflow (Ligands):**
```python
# Phase 1: Fuzzy search for drug
search_result = await client.call_tool("search_ligands", {"query": "ibuprofen", "approved_only": True})
top_candidate = search_result["items"][0]  # {"id": "IUPHAR:2713", "approved": True, ...}

# Phase 2: Strict lookup
ligand = await client.call_tool("get_ligand", {"iuphar_id": top_candidate["id"]})
# Returns Ligand with:
# - approved: True
# - approval_source: "FDA (1974)"
# - who_essential: True
# - synonyms: ["Advil", "Motrin", "Nurofen"]
# - cross_references: {"chembl": "521", "drugbank": "DB01050", "pubchem_compound": "3672"}
```

**Fuzzy-to-Fact Workflow (Targets):**
```python
# Phase 1: Fuzzy search for receptor
search_result = await client.call_tool("search_targets", {"query": "dopamine", "type_filter": "GPCR"})
top_candidate = search_result["items"][0]  # {"id": "IUPHAR:215", "name": "D2 receptor", ...}

# Phase 2: Strict lookup
target = await client.call_tool("get_target", {"iuphar_id": top_candidate["id"]})
# Returns Target with:
# - gene_symbol: "DRD2"
# - species: "Homo sapiens"
# - target_family: "GPCR"
# - cross_references: {"uniprot": ["P14416"], "ensembl_gene": "ENSG00000149295", "hgnc": "HGNC:3023"}
```

**CURIE Format:**
- Pattern: `IUPHAR:\d+`
- Examples: `IUPHAR:2713` (ibuprofen ligand), `IUPHAR:215` (D2 receptor target)
- Validation: `^IUPHAR:\d+$`

#### WikiPathways Server (✅ Complete - Tier 3)

| Tool | Type | Description |
|------|------|-------------|
| `search_pathways` | Fuzzy | Search pathways by name/description/gene, returns ranked PathwaySearchCandidates |
| `get_pathway` | Strict | Lookup by WikiPathways CURIE, returns full Pathway with metadata and revision info |
| `get_pathways_for_gene` | Reverse | Find all pathways containing a specific gene (reverse lookup) |
| `get_pathway_components` | Strict | Extract biological entities (genes, proteins, metabolites, interactions) from pathway |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/wikipathways.py
```

**API Details:**
- **Base URL**: `https://webservice.wikipathways.org`
- **Protocol**: REST (JSON output)
- **Auth**: None required
- **Rate Limit**: Not specified

**Key Features:**
- **Reverse lookup**: Find pathways by gene symbol (e.g., all pathways containing BRCA1)
- **Component extraction**: Get genes, proteins, metabolites, and interactions from pathway diagrams
- **Species filtering**: Supports Homo sapiens, Mus musculus, and 20+ other organisms
- **Revision metadata**: Track pathway updates with revision number and last_edited timestamps

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Fuzzy search
search_result = await client.call_tool("search_pathways", {"query": "glycolysis", "organism": "Homo sapiens"})
top_candidate = search_result["items"][0]  # {"id": "WP:WP534", "name": "Glycolysis and Gluconeogenesis", ...}

# Phase 2: Strict lookup
pathway = await client.call_tool("get_pathway", {"pathway_id": top_candidate["id"]})
# Returns Pathway with:
# - name: "Glycolysis and Gluconeogenesis"
# - organism: "Homo sapiens"
# - description: "...metabolic pathway description..."
# - component_counts: {"genes": 25, "proteins": 30, "metabolites": 15, "interactions": 40}

# Phase 3: Extract components
components = await client.call_tool("get_pathway_components", {"pathway_id": top_candidate["id"]})
# Returns PathwayComponents with:
# - genes: [{"id": "HGNC:6535", "label": "HK1"}, ...]
# - proteins: [{"id": "UniProtKB:P19367", "label": "Hexokinase-1"}, ...]
# - metabolites: [{"id": "CHEBI:17234", "label": "Glucose"}, ...]
# - interactions: [{"source": "HK1", "target": "Glucose", "type": "catalysis"}, ...]
```

**Reverse Lookup Workflow:**
```python
# Find all pathways containing BRCA1
pathways = await client.call_tool("get_pathways_for_gene", {"gene_id": "BRCA1", "organism": "Homo sapiens"})
# Returns PaginationEnvelope with pathways:
# [{"id": "WP:WP4868", "name": "DNA Damage Response", ...}, ...]
```

**CURIE Format:**
- Pattern: `WP:WP\d+`
- Examples: `WP:WP534` (Glycolysis), `WP:WP4868` (DNA Damage Response)
- Validation: `^WP:WP\d+$`

#### ClinicalTrials.gov Server (✅ Complete - Tier 3)

| Tool | Type | Description |
|------|------|-------------|
| `search_trials` | Fuzzy | Search clinical trials by condition/intervention/location, returns ranked TrialSearchCandidates |
| `get_trial` | Strict | Lookup by NCT CURIE, returns full Trial with protocol, eligibility, and outcomes |
| `get_trial_locations` | Strict | Get facility locations and contact information for a trial |

**Usage:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/clinicaltrials.py
```

**API Details:**
- **Base URL**: `https://clinicaltrials.gov/api/v2`
- **Protocol**: REST (JSON output)
- **Auth**: None required
- **Rate Limit**: Not specified
- **⚠️ Cloudflare Blocking**: Python httpx clients blocked (403 Forbidden), use curl for manual testing

**Tests:**
```bash
# Unit tests (parameter validation)
uv run pytest tests/unit/test_clinicaltrials_client.py -v
# 13 unit tests passing

# Manual testing with curl (integration tests blocked by Cloudflare)
curl -s "https://clinicaltrials.gov/api/v2/studies?query.term=cancer&pageSize=1&format=json" | jq
```

**Key Features:**
- **Multi-filter search**: Condition, intervention, phase, status, location filters
- **Recruitment status**: RECRUITING, COMPLETED, NOT_YET_RECRUITING, etc.
- **Trial phases**: PHASE1, PHASE2, PHASE3, PHASE4, EARLY_PHASE1, NA
- **Geographic search**: Filter by city, state, or country
- **Facility details**: Contact names, phone numbers, emails for trial sites

**Fuzzy-to-Fact Workflow:**
```python
# Phase 1: Fuzzy search
search_result = await client.call_tool("search_trials", {
    "query": "breast cancer",
    "phase": "PHASE3",
    "status": "RECRUITING",
    "location": "Boston"
})
top_candidate = search_result["items"][0]  # {"id": "NCT:00461032", "title": "...", ...}

# Phase 2: Strict lookup
trial = await client.call_tool("get_trial", {"nct_id": top_candidate["id"]})
# Returns Trial with:
# - protocol: {study_type, allocation, intervention_model, masking, primary_purpose}
# - eligibility: {criteria_text, age_range, sex, healthy_volunteers}
# - outcomes: {primary: [...], secondary: [...]}
# - sponsors: {lead_sponsor, collaborators}

# Phase 3: Get trial locations
locations = await client.call_tool("get_trial_locations", {"nct_id": top_candidate["id"]})
# Returns list of TrialLocation objects:
# [{"facility_name": "Dana-Farber Cancer Institute", "city": "Boston", "recruitment_status": "RECRUITING", ...}]
```

**CURIE Format:**
- Pattern: `NCT:\d{8}`
- Examples: `NCT:00461032`, `NCT:04123456`
- Validation: `^NCT:\d{8}$`

**Cloudflare Blocking Workaround:**
See "Manual Testing" section at top of CLAUDE.md for curl-based verification commands.

### Core Patterns

1. **Hybrid Client:** Native `httpx` async for modern APIs; `run_in_executor` for ChEMBL SDK only
2. **Fuzzy-to-Fact Protocol:** Fuzzy search returns candidates → Strict tools require CURIEs
3. **Agentic Biolink Schema:** Flattened JSON with `cross_references` object
4. **Token Budgeting:** `slim=True` for batch operations (~20 vs ~115 tokens/entity)

### API Tiers (implementation priority)
| Tier | APIs | Focus |
|------|------|-------|
| 0 | ChEMBL, Open Targets, DrugBank | Drug Discovery Core |
| 1 | HGNC, UniProt, STRING, BioGRID | Gene/Protein Foundation |
| 2 | IUPHAR/GtoPdb, STITCH, PubChem | Pharmacology & Interactions |
| 3 | KEGG, OMIM, Orphanet | Pathways & Disease |
| 4 | Entrez, Ensembl | Genomics & Identifiers |

### Normative Schemas

**Pagination Envelope** (all list tools must use):
```json
{
  "items": [...],
  "pagination": {"cursor": "string|null", "total_count": "int|null", "page_size": 50}
}
```

**Error Envelope** (all errors must use):
```json
{
  "success": false,
  "error": {"code": "UNRESOLVED_ENTITY", "message": "...", "recovery_hint": "...", "invalid_input": "..."}
}
```

**Error Codes:** `UNRESOLVED_ENTITY`, `ENTITY_NOT_FOUND`, `AMBIGUOUS_QUERY`, `RATE_LIMITED`, `UPSTREAM_ERROR`, `INVALID_CROSS_REFERENCE`

### Cross-Reference Keys (22 total)
```
Core:        hgnc, ensembl_gene, ensembl_transcript, uniprot, entrez, refseq
Drugs:       chembl, drugbank
Interactions: string, biogrid, stitch, iuphar
Pathways:    kegg, kegg_pathway, omim, orphanet, mondo, efo
Structural:  pdb, pubchem_compound, pubchem_substance
```

**Null Handling:** Omit keys entirely if no cross-reference exists (never use `null` or empty string).

## Environment Variables

```bash
# Most life sciences APIs are public (no keys required)
# Required for specific servers:
BIOGRID_API_KEY=...              # BioGRID interactions (free: https://webservice.thebiogrid.org/)
DRUGBANK_API_KEY=...             # DrugBank (commercial tier)

# Optional for rate limit increases:
NCBI_API_KEY=...                 # Entrez/PubMed (free: https://www.ncbi.nlm.nih.gov/account/settings/)
```

## Git Workflow

```bash
# Specification work
git switch -c feature/<id>-<description>
# e.g., git switch -c feature/001-hgnc-mcp-server

# Implementation work (after spec merged)
git switch -c implement/<id>-<description>
# e.g., git switch -c implement/001-hgnc-mcp-server
```

## Linear Project

- Project: Life Sciences MCP Server
- Key Issues: AGE-65 (Discovery), AGE-66 (ADR v1.1), AGE-67 (Amendment)

## Active Technologies

**Core Stack:**
- Python 3.11+
- FastMCP >=2.0 (MCP protocol implementation)
- httpx >=0.27 (async HTTP client)
- pydantic >=2.0 (data validation and serialization)

**Special Dependencies:**
- `chembl_webresource_client` - ChEMBL SDK (wrapped with `run_in_executor`)
- `defusedxml` - Secure XML parsing for Entrez/PubMed

**Architecture:**
- Stateless design (live queries to REST APIs, no persistent storage)
- Fuzzy-to-Fact protocol (fuzzy search → CURIE resolution → strict lookup)
- Agentic Biolink schema (flattened JSON with cross_references)
- Token budgeting (`slim=True` parameter for batch operations)

## Recent Changes

### 008-ensembl-mcp-server: Ensembl Complete - All 4 User Stories (2026-01-02)
- **User Story 1 (Fuzzy Gene Search)** - Complete
  - `search_genes`: Fuzzy search with species aliases, cursor pagination, relevance ranking
  - Species alias mapping (human->homo_sapiens, mouse->mus_musculus, etc.)
  - CURIE validation: `^ENSG\d{11}$` for gene IDs
  - Rate limiting: 15 req/s with exponential backoff
- **User Story 2 (Strict Gene Lookup)** - Complete
  - `get_gene`: Strict ENSG ID lookup with complete gene records
  - Cross-reference mapping to 12 Ensembl-relevant databases (HGNC, UniProt, Entrez, RefSeq, PDB, OMIM, KEGG, ChEMBL, etc.)
  - Transcript ID list included in gene response
  - Error handling: UNRESOLVED_ENTITY, ENTITY_NOT_FOUND, UPSTREAM_ERROR with recovery hints
- **User Story 3 (Transcript Lookup)** - Complete
  - `get_transcript`: Strict ENST ID lookup with parent gene reference
  - Canonical transcript flag (`is_canonical`)
  - Cross-references to UniProt, RefSeq, CCDS
- **User Story 4 (Error Recovery)** - Complete
  - Actionable recovery hints for all error codes
  - Gene ID vs Transcript ID confusion detection with helpful hints
  - Complete error→hint→recovery→success cycle validation
- **Phase 7 Polish** - Complete
  - **86 tests passing** (62 unit + 24 integration)
  - **70/72 tasks complete (97%)**, 2 optional (performance test, CLAUDE.md update)
  - Module-level docstrings on all modules
  - Lint/type checks pass (ruff, pyright)

### 002-uniprot-mcp-server: UniProt Complete - All 4 User Stories (2025-12-22)
- **User Story 1 (Fuzzy Protein Search)** - Complete
  - `search_proteins`: Fuzzy search with cursor pagination, query validation, relevance ranking
  - Comprehensive research phase (R1-R7) documented in `specs/002-uniprot-mcp-server/research.md`
  - CURIE validation: `^UniProtKB:[A-Z][A-Z0-9]{5,9}$`
  - Rate limiting: 10 req/s with exponential backoff + thundering herd prevention
  - All HGNC code review lessons "shifted left" into functional requirements
- **User Story 2 (Strict Protein Lookup)** - Complete
  - `get_protein`: Strict CURIE lookup with complete protein records
  - Cross-reference mapping to 22-key Agentic Biolink schema (HGNC, Ensembl, RefSeq, PDB, KEGG, OMIM, etc.)
  - Error handling: UNRESOLVED_ENTITY, ENTITY_NOT_FOUND, UPSTREAM_ERROR with recovery hints
  - Slim mode implementation (~20 vs ~115-300 tokens)
  - End-to-end Fuzzy-to-Fact workflow validated
- **User Story 3 (Cross-Database Integration)** - Complete
  - 3 integration tests validating cross-reference extraction and mapping
  - HGNC mapping verification, omit-if-null pattern compliance (Constitution Principle III)
  - Cross-references to 22 biological databases (HGNC, Ensembl, RefSeq, PDB, KEGG, OMIM, etc.)
- **User Story 4 (Error Recovery)** - Complete
  - 11 error recovery tests (7 unit + 4 integration)
  - Actionable recovery hints for all error codes (AMBIGUOUS_QUERY, UNRESOLVED_ENTITY, ENTITY_NOT_FOUND, RATE_LIMITED, UPSTREAM_ERROR)
  - Complete error→hint→recovery→success cycle validation
  - New files: `test_error_envelopes.py`, `test_error_recovery.py`
- **Phase 7 Polish** - Complete
  - Performance tests validating SC-001 (<2s for 95% of queries)
  - Comprehensive quickstart guide with 4 workflows and error recovery examples
  - **50/50 tests passing** (29 integration + 21 unit)
  - **74/76 tasks complete (97%)**, 2 skipped per ADR-004
- **ADR-004: FastMCP Lifecycle Management** - Created
  - Documents shutdown hook antipattern (`@mcp.on_event` not supported in FastMCP)
  - Establishes module-level singleton pattern as normative
  - References MCP Protocol and FastMCP documentation
  - Resolves lifecycle management gap in ADR-002

### 001-hgnc-mcp-server: HGNC Complete (2025-12-21)
- Implemented HGNC MCP Server with Fuzzy-to-Fact protocol
  - `search_genes`: Fuzzy search returning ranked SearchCandidate results
  - `get_gene`: Strict lookup by HGNC CURIE returning full Gene with cross_references
  - Canonical envelopes: PaginationEnvelope, ErrorEnvelope (ADR-001 §8)
  - Rate limiting: 10 req/s with exponential backoff
  - 24 passing tests (14 unit, 10 integration)
  - Code review fixes applied: race conditions, resource cleanup, exponential backoff

### Platform Engineering
- Created `/scaffold-fastmcp` skill for Constitution Principle VI compliance
- Created standard prompt template (`docs/speckit-standard-prompt.md`) to prevent specification drift
