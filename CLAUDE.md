# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastMCP wrappers for essential life sciences APIs, enabling LLM agents to query biological databases for drug discovery and repurposing.

**Status:**
- HGNC server v0.1.0 - ✅ Complete (7 integration tests passing)
- UniProt server v0.1.0 - ✅ Complete (12 integration tests passing, all 4 User Stories)
- ChEMBL server v0.1.0 - ✅ Complete (62 tests: 20 integration + 42 unit, PR #10 merged)
- Open Targets server v0.1.0 - ✅ Complete (9 tests, PR #11 merged)
- DrugBank server v0.1.0 - ⛔ **BLOCKED** (33 unit tests, PR #12 open - API key required)
- STRING server v0.1.0 - ✅ Complete (3 tools, 11 integration tests passing)
- BioGRID server v0.1.0 - ✅ Complete (11 integration tests passing, all 4 User Stories)
- Ensembl server v0.1.0 - ✅ Complete (86 tests: 62 unit + 24 integration)
- Entrez server v0.1.0 - ✅ Complete (58 tests: 38 unit + 20 integration)
- PubChem server v0.1.0 - ✅ Complete (85 tests: 66 unit + 19 integration)
- IUPHAR/GtoPdb server v0.1.0 - ✅ Complete (59 tests: 48 integration + 11 unit, all 5 User Stories)
- WikiPathways server v0.1.0 - ✅ Complete (4 tools, 17 integration tests passing)
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
| `docs/competency-questions/competency-questions-catalog.md` | Research questions catalog for knowledge graph building |
| `docs/adr/accepted/adr-001-v1.4.md` | Binding architecture specification (schemas, protocols, error codes) |
| `docs/adr/accepted/adr-002-v1.0.md` | Project Skills (the "Hardware") |
| `docs/adr/accepted/adr-003-v1.0.md` | SpecKit SDLC (the "Operating System") |
| `docs/adr/accepted/adr-004-v1.0.md` | FastMCP Lifecycle Management (shutdown hook antipattern) |
| `docs/adr/accepted/adr-005-v1.0.md` | Git Worktrees for Parallel Development |
| `docs/adr/accepted/adr-006-v1.0.md` | Single Writer Package Architecture |
| `docs/speckit-standard-prompt.md` | Standard prompt template for new MCP servers |

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

# Testing (marker-based approach - recommended)
uv run pytest -m unit -v                              # Unit tests (399 tests, no network)
uv run pytest -m integration -v                       # Integration tests (294 tests)
uv run pytest -m e2e -v                               # End-to-end tests (4 tests)
uv run pytest -m "not integration" -v                 # Fast local dev (excludes network)

# Test specific API
uv run pytest -m "unit and clinicaltrials" -v         # ClinicalTrials unit tests only
uv run pytest -m "integration and chembl" -v          # ChEMBL integration tests only

# Single test
uv run pytest tests/unit/test_file.py::test_name -v

# Linting
uv run ruff check --fix . && uv run ruff format .
uv run pyright

# Run MCP server (when implemented)
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
uv run fastmcp run src/lifesciences_mcp/servers/wikipathways.py
```

## Manual Testing

### ClinicalTrials.gov API (Cloudflare Blocking Workaround for pytest)

**Issue**: ClinicalTrials.gov uses Cloudflare TLS fingerprinting that blocks Python httpx clients (403 Forbidden), while MCP endpoints and curl works fine.

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
│   ├── cross_references.py # CrossReferences (shared cross-reference schema)
│   ├── gene.py          # Gene, SearchCandidate
│   ├── protein.py       # Protein, ProteinSearchCandidate
│   ├── compound.py      # Compound, CompoundSearchCandidate
│   ├── target.py        # Target, TargetSearchCandidate, Association
│   ├── drug.py          # Drug, DrugSearchCandidate, DrugCrossReferences
│   ├── interaction.py   # Interaction, InteractionNetwork, EvidenceScores (STRING)
│   ├── biogrid.py       # GeneticInteraction, InteractionResult, BioGridSearchCandidate
│   ├── ensembl.py       # EnsemblGene, EnsemblTranscript, GeneSearchCandidate
│   ├── entrez.py        # EntrezGene, GeneSearchCandidate, EntrezCrossReferences
│   ├── pubchem_compound.py # PubChemCompound, PubChemSearchCandidate
│   ├── pharmacology.py  # Ligand, Target, LigandSearchCandidate, TargetSearchCandidate (IUPHAR/GtoPdb)
│   ├── pathway.py       # Pathway, PathwaySearchCandidate, RevisionMetadata, ComponentCounts
│   ├── pathway_components.py # PathwayComponents, DataNode, Interaction
│   ├── provenance.py    # Provenance tracking models
│   ├── trial.py         # Trial, TrialSearchCandidate, TrialProtocol, EligibilityCriteria
│   └── trial_location.py # TrialLocation
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

### Implemented Tools (Summary)

All 12 servers follow the **Fuzzy-to-Fact Protocol**: fuzzy search returns ranked candidates → strict lookup requires resolved CURIE.

| Server | Tools | CURIE Format | Tests |
|--------|-------|--------------|-------|
| **HGNC** | `search_genes`, `get_gene` | `HGNC:1100` | 7 |
| **UniProt** | `search_proteins`, `get_protein` | `UniProtKB:P38398` | 12 |
| **ChEMBL** | `search_compounds`, `get_compound`, `get_compounds_batch` | `CHEMBL:25` | 62 |
| **Open Targets** | `search_targets`, `get_target`, `get_associations` | `ENSG00000141510` | 9 |
| **STRING** | `search_proteins`, `get_interactions`, `get_network_image_url` | `STRING:9606.ENSP00000269305` | 11 |
| **BioGRID** | `search_genes`, `get_interactions` | Gene symbol | 11 |
| **Ensembl** | `search_genes`, `get_gene`, `get_transcript` | `ENSG*`, `ENST*` | 86 |
| **Entrez** | `search_genes`, `get_gene`, `get_pubmed_links` | `NCBIGene:7157` | 58 |
| **PubChem** | `search_compounds`, `get_compound` | `PubChem:CID2244` | 85 |
| **IUPHAR** | `search_ligands`, `get_ligand`, `search_targets`, `get_target` | `IUPHAR:2713` | 59 |
| **WikiPathways** | `search_pathways`, `get_pathway`, `get_pathways_for_gene`, `get_pathway_components` | `WP:WP534` | 17 |
| **ClinicalTrials** | `search_trials`, `get_trial`, `get_trial_locations` | `NCT:00461032` | 13 |
| **DrugBank** | `search_drugs`, `get_drug` | `DrugBank:DB00945` | 33 (⛔ API key required) |

**Run any server:**
```bash
uv run fastmcp dev src/lifesciences_mcp/servers/<server>.py
```

**Fuzzy-to-Fact Example:**
```python
# Phase 1: Fuzzy search
result = await client.call_tool("search_genes", {"query": "BRCA1"})
curie = result["items"][0]["id"]  # "HGNC:1100"

# Phase 2: Strict lookup
gene = await client.call_tool("get_gene", {"hgnc_id": curie})
# Returns Gene with cross_references to UniProt, Ensembl, RefSeq, etc.
```

For detailed server documentation (API details, rate limits, workflows), see the server source files in `src/lifesciences_mcp/servers/`.

**Note:** DrugBank requires commercial API key (`DRUGBANK_API_KEY`). Implementation complete, integration tests skipped without key.

**Note:** ClinicalTrials.gov integration tests blocked by Cloudflare. See Manual Testing section above for curl-based verification.  This does not impact production MCP usage.

**Note:** BioGRID requires free API key (`BIOGRID_API_KEY`) from https://webservice.thebiogrid.org/.  The API key exists in the current environment in the `.env` file.

**Note:** NCBI/Entrez optionally uses `NCBI_API_KEY` for higher rate limits (3→10 req/s). Free at https://www.ncbi.nlm.nih.gov/account/settings/  . The API key exists in the current environment in the `.env` file.

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

See [ADR-001 v1.3](docs/adr/accepted/adr-001-v1.4.md) for complete specifications:
- **§8 Pagination Envelope** - All list tools must use
- **§8 Error Envelope** - All errors must use with recovery hints
- **§9 Error Code Registry** - 6 standard error codes
- **§5 Cross-Reference Keys** - 22-key Agentic Biolink schema
- **§4 Null Handling** - Omit keys entirely (never use `null` or empty string)

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

## Future Work / Technical Debt

### Health Check Fixture Scope Optimization (PR #18 Review Feedback)

**Context:** PR #18 added health check fixtures to integration tests. Currently, fixtures use `scope="function"` (default), meaning each test function triggers a health check HTTP request.

**Proposed Improvement:** Change scope to `scope="session"` or `scope="module"` so health checks run once per test session/module rather than per test function. This reduces redundant API calls during test runs.

**Location:** `tests/integration/conftest.py` - all `check_*_available` fixtures

**Trade-off:** Session scope is more efficient but means if an API goes down mid-test-run, subsequent tests won't skip. Module scope is a middle ground.

**Reference:** PR #18 review comment suggested this optimization.
