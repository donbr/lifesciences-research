# SpecKit Standard Prompt Template

## Architectural Compliance Standard & ADR Registry

This prompt template serves as the **enforcement mechanism** for the Life Sciences MCP Architecture. The following table summarizes all Accepted ADRs and how they are applied in this process:

| ADR | Title | Application Mode | Key Mandate |
| :--- | :--- | :--- | :--- |
| **[ADR-001](../docs/adr/accepted/adr-001-v1.4.md)** | **Agentic-First Architecture** | 🔴 **Explicit Constraint** | Async-First, Fuzzy-to-Fact, Canonical Envelopes. |
| **[ADR-002](../docs/adr/accepted/adr-002-v1.0.md)** | **Platform Skills** | 🟢 **Foundational** | Skills like `scaffold-fastmcp` MUST be used over manual coding. |
| **[ADR-003](../docs/adr/accepted/adr-003-v1.0.md)** | **SpecKit SDLC** | 🟢 **Foundational** | The `/specify` → `/plan` → `/implement` workflow itself. |
| **[ADR-004](../docs/adr/accepted/adr-004-v1.0.md)** | **Lifecycle Management** | 🔴 **Explicit Constraint** | Module-level singleton pattern; `@mcp.on_event` is **FORBIDDEN**. |
| **[ADR-005](../docs/adr/accepted/adr-005-v1.0.md)** | **Git Worktrees** | 🟡 **Pre-requisite** | Step 0: Use worktrees for parallelizing 3+ servers. |
| **[ADR-006](../docs/adr/accepted/adr-006-v1.0.md)** | **Single Writer Package** | 🔴 **Explicit Constraint** | Split `client.py` into `clients/` package to enable ADR-005. |

> [!IMPORTANT]
> **Constraint Injection**
> ADRs marked as 🔴 **Explicit Constraint** are injected directly into the prompt text below. This forces the agent to retrieve and adhere to these specific rules during generation.

**Purpose:** Ensure all MCP server specifications pass the Constitution check on the first try by injecting ADR citations directly into the prompt.

**Problem Solved:** Prevents "Specification Drift" - where loosely-worded requests (e.g., "Build a UniProt wrapper") cause the agent to forget core patterns like Fuzzy-to-Fact or Canonical Envelopes, forcing correction rounds in `/clarify`.



## Acknowledgements & Methodologies

<div align="center">
  <em>We tip our hat to the giants whose shoulders we stand upon:</em>
</div>

| Contribution | Source | Role in Architecture |
| :--- | :--- | :--- |
| **Data Validation** | **[Pydantic](https://docs.pydantic.dev/)** | The bedrock of our schema determinism and TypeAdapter patterns. |
| **Org Patterns** | **[Team Topologies](https://teamtopologies.com/)** | The "Enabling Team" pattern that inspired our "Platform Skill" delegation strategy. |
| **Tool Protocol** | **[Model Context Protocol](https://modelcontextprotocol.io/)** | The open standard connecting our specialized knowledge graph to agentic reasoning. |
| **Server Framework** | **[FastMCP](https://github.com/jlowin/fastmcp)** | The ergonomic framework that makes "Async-First" implementation intuitive. |
| **Scientific Data** | **UniProt, HGNC, EMBL-EBI, NCBI** | The stewards of the biological knowledge we are privileging to serve. |

---

## The Template

```text
/speckit.specify "Build the [API_NAME] MCP Server.

Core Requirements:
1. **Architecture:** Implement `[ClientName]Client` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2).
   - **Structure:** Must use `src/lifesciences_mcp/clients/[module].py` (ADR-006) with `validate_id` static method.
   - **Concurrency:** Implement client-side rate limiting using `asyncio.Lock` and `_rate_limited_call` wrapper.
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_[entities](query)` (Fuzzy) returning ranked candidates.
   - Tool 2: `get_[entity]([id_type])` (Strict) accepting ONLY resolved CURIEs.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4) and Cognitive Hooks.
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases and concurrency."
```

## Why This Works

This prompt is **Constraint Injection** - each ADR citation maps to a Constitution Principle:

| Citation | Forces | Constitution Principle |
|----------|--------|------------------------|
| "ADR-001 §2" | `async httpx` clients | I. Async-First Architecture |
| "ADR-006" | `clients/` package structure | VI. Platform Skill Delegation |
| "ADR-004" | No shutdown hooks | I. Async-First Architecture |
| "Fuzzy-to-Fact" | 2-tool pattern (search → get) | II. Fuzzy-to-Fact Resolution |
| "Agentic Biolink" | 22-key `cross_references` registry | III. Schema Determinism |
| "Canonical Envelopes" | `PaginationEnvelope`, `ErrorEnvelope` | III. Schema Determinism |
| "Junior Dev ambiguity" | Edge case test coverage | IV. Token Budgeting |

## Workflow

### Step 0: Parallel Development Setup (Optional, ADR-005)

For implementing 3+ servers in parallel (or recreating the entire ecosystem), use git worktrees for filesystem isolation:

```bash
# Create worktrees for parallel development
mkdir -p .worktrees

# Foundation (Tier 1)
git worktree add .worktrees/hgnc -b implement/001-hgnc-mcp-server
git worktree add .worktrees/uniprot -b implement/002-uniprot-mcp-server

# Drug Discovery Core (Tier 0)
git worktree add .worktrees/chembl -b implement/003-chembl-mcp-server
git worktree add .worktrees/opentargets -b implement/004-opentargets-mcp-server
git worktree add .worktrees/drugbank -b implement/005-drugbank-mcp-server

# Interaction Networks (Tier 1-2)
git worktree add .worktrees/string -b implement/006-string-mcp-server
git worktree add .worktrees/biogrid -b implement/007-biogrid-mcp-server
git worktree add .worktrees/iuphar -b implement/011-iuphar-mcp-server

# Genomics & Identifiers (Tier 4)
git worktree add .worktrees/ensembl -b implement/008-ensembl-mcp-server
git worktree add .worktrees/entrez -b implement/009-entrez-mcp-server
git worktree add .worktrees/pubchem -b implement/010-pubchem-mcp-server

# Pathways & Clinical (Tier 3-5)
git worktree add .worktrees/wikipathways -b implement/012-wikipathways-mcp-server
git worktree add .worktrees/clinicaltrials -b implement/013-clinicaltrials-mcp-server

# Initialize environments in parallel (batching to prevent resource exhaustion)
(cd .worktrees/hgnc && uv sync) &
(cd .worktrees/uniprot && uv sync) &
(cd .worktrees/chembl && uv sync) &
(cd .worktrees/opentargets && uv sync) &
wait

(cd .worktrees/drugbank && uv sync) &
(cd .worktrees/string && uv sync) &
(cd .worktrees/biogrid && uv sync) &
(cd .worktrees/iuphar && uv sync) &
wait

(cd .worktrees/ensembl && uv sync) &
(cd .worktrees/entrez && uv sync) &
(cd .worktrees/pubchem && uv sync) &
(cd .worktrees/wikipathways && uv sync) &
(cd .worktrees/clinicaltrials && uv sync) &
wait
```

**Benefits**:
- Each agent operates in isolated working directory (no filesystem conflicts)
- All share the same .git repository (efficient disk usage)
- Conflicts deferred to PR merge time (controlled, sequential)

See [ADR-005](../docs/adr/accepted/adr-005-v1.0.md) and [Claude Code Worktrees Workflow](https://code.claude.com/docs/en/common-workflows#run-parallel-claude-code-sessions-with-git-worktrees) for details.

### Step 1: Scaffold the Server

```bash
/scaffold-fastmcp-v2 [api_name]
```

This creates:
- `src/lifesciences_mcp/servers/[api].py` - FastMCP server with tool stubs
- Client class stub in `src/lifesciences_mcp/clients/[api].py` - Context-managed client (ADR-006)
- Integration test stubs in `tests/integration/`
- Feature directory in `specs/[NNN]-[api]-mcp-server/`

### Step 2: Run the Standard Prompt

Use the template above, substituting:
- `[API_NAME]` - Human-readable name (e.g., "UniProt", "ChEMBL", "Open Targets")
- `[ClientName]` - PascalCase client class (e.g., "UniProt", "ChEMBL", "OpenTargets")
- `[entities]` - Plural entity type for search (e.g., "proteins", "compounds", "targets")
- `[entity]` - Singular entity type for get (e.g., "protein", "compound", "target")
- `[id_type]` - ID parameter name (e.g., "uniprot_id", "chembl_id", "target_id")

### Step 3: Continue SpecKit Workflow

```bash
/speckit.clarify    # Optional - surface underspecified areas
/speckit.plan       # Create implementation plan
/speckit.tasks      # Generate actionable tasks
/speckit.analyze    # Optional - cross-artifact consistency check
/speckit.implement  # Execute bounded implementation
```

> ⚠️ **PROMPT SIZE LIMIT (v1.4.0)**: When using `claude -p` for non-interactive execution, the `-p` flag has a ~20KB prompt limit. If your `tasks.md` exceeds ~20KB (typically >150 tasks), you must use **interactive mode**:
> ```bash
> # Check file sizes first
> wc -c specs/*/tasks.md
>
> # If over ~20KB, use interactive mode:
> cd .worktrees/ensembl
> claude
> # Then type: /speckit.implement specs/008-ensembl-mcp-server/tasks.md
> ```
> See [ADR-005 v1.1.0](../docs/adr/accepted/adr-005-v1.0.md) for details.

## Server Specification Inventory

> [!TIP]
> **Canonical Prompts**
> These are the PRE-APPROVED specifications for the Life Sciences MCP ecosystem. Use these exact prompts to ensure compliance with all Architecture Decision Records.

### HGNC (Gene Nomenclature)

```text
/speckit.specify "Build the HGNC MCP Server.

Core Requirements:
1. **Architecture:** Implement `HGNCClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2).
   - **Structure:** Must use `src/lifesciences_mcp/clients/hgnc.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_genes(query)` (Fuzzy) returning ranked candidates.
   - Tool 2: `get_gene(hgnc_id)` (Strict) accepting ONLY resolved CURIEs (HGNC:*).
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4).
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases."
```

### UniProt (Protein Data)

```text
/speckit.specify "Build the UniProt MCP Server.

Core Requirements:
1. **Architecture:** Implement `UniProtClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2).
   - **Structure:** Must use `src/lifesciences_mcp/clients/uniprot.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_proteins(query)` (Fuzzy) returning ranked candidates.
   - Tool 2: `get_protein(uniprot_id)` (Strict) accepting ONLY resolved CURIEs.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4).
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases."
```

### ChEMBL (Drug/Compound Data)

```text
/speckit.specify "Build the ChEMBL MCP Server.

Core Requirements:
1. **Architecture:** Implement `ChEMBLClient` extending `LifeSciencesClient`. NOTE: ChEMBL uses a synchronous SDK - wrap with `run_in_executor` per ADR-001 §2 exception.
   - **Structure:** Must use `src/lifesciences_mcp/clients/chembl.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_compounds(query)` (Fuzzy) returning ranked candidates.
   - Tool 2: `get_compound(chembl_id)` (Strict) accepting ONLY resolved CURIEs.
   - Tool 3: `get_compounds_batch(chembl_ids)` for batch operations (prevents thread pool exhaustion).
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4).
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases."
```

### DrugBank (Drug Data)

```text
/speckit.specify "Build the DrugBank MCP Server.

Core Requirements:
1. **Architecture:** Implement `DrugBankClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2).
   - **Structure:** Must use `src/lifesciences_mcp/clients/drugbank.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_drugs(query)` (Fuzzy) returning ranked candidates.
   - Tool 2: `get_drug(drugbank_id)` (Strict) accepting ONLY resolved CURIEs (DrugBank:DB*).
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4).
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases."
```

### Open Targets (Target-Disease Associations)

```text
/speckit.specify "Build the Open Targets MCP Server.

Core Requirements:
1. **Architecture:** Implement `OpenTargetsClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Use GraphQL API.
   - **Structure:** Must use `src/lifesciences_mcp/clients/opentargets.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_targets(query)` (Fuzzy) returning ranked target candidates.
   - Tool 2: `get_target(ensembl_id)` (Strict) accepting ONLY resolved Ensembl gene IDs.
   - Tool 3: `get_associations(target_id, disease_id)` for target-disease evidence.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4).
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases."
```

### STRING (Protein-Protein Interactions)

```text
/speckit.specify "Build the STRING MCP Server.

Core Requirements:
1. **Architecture:** Implement `STRINGClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://string-db.org/api
   - **Structure:** Must use `src/lifesciences_mcp/clients/string.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_proteins(query)` (Fuzzy) returning ranked protein candidates with STRING CURIEs.
   - Tool 2: `get_interactions(string_id)` (Strict) accepting ONLY resolved STRING CURIEs (format: STRING:TAXID.ENSPNNNNN).
   - Tool 3: `get_network_image_url(identifiers)` for network visualization URLs.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Include 7 evidence channel scores (nscore, fscore, pscore, ascore, escore, dscore, tscore).
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases. Rate limit: 1 req/sec."
```

### BioGRID (Genetic/Protein Interactions)

```text
/speckit.specify "Build the BioGRID MCP Server.

Core Requirements:
1. **Architecture:** Implement `BioGridClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://webservice.thebiogrid.org. Requires BIOGRID_API_KEY (free registration).
   - **Structure:** Must use `src/lifesciences_mcp/clients/biogrid.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_genes(query)` (Fuzzy) validating gene symbols for BioGRID queries.
   - Tool 2: `get_interactions(gene_symbol)` (Strict) accepting validated gene symbols. Returns genetic and physical interactions with experimental evidence.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Include experimental_system and experimental_system_type (physical/genetic) per interaction.
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases. API key error handling required."
```

### Ensembl (Genomic Annotations)

```text
/speckit.specify "Build the Ensembl MCP Server.

Core Requirements:
1. **Architecture:** Implement `EnsemblClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://rest.ensembl.org
   - **Structure:** Must use `src/lifesciences_mcp/clients/ensembl.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_genes(query)` (Fuzzy) returning ranked candidates.
   - Tool 2: `get_gene(ensembl_id)` (Strict) accepting ONLY resolved Ensembl IDs (ENSG*).
   - Tool 3: `get_transcript(transcript_id)` for transcript details (ENST*).
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Include biotype, assembly_name, strand, genomic coordinates.
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases. Rate limit: 15 req/sec."
```

### NCBI Entrez (Gene Database)

```text
/speckit.specify "Build the NCBI Entrez MCP Server.

Core Requirements:
1. **Architecture:** Implement `EntrezClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/. API returns XML by default - include XML parsing.
   - **Structure:** Must use `src/lifesciences_mcp/clients/entrez.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_genes(query)` (Fuzzy) returning ranked candidates.
   - Tool 2: `get_gene(entrez_id)` (Strict) accepting ONLY resolved Entrez Gene IDs (NCBIGene:*).
   - Tool 3: `get_pubmed_links(entrez_id)` for associated literature.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Include Summary, MapLocation, OtherAliases.
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases. Rate limit: 3 req/sec (10/sec with API key)."
```

### PubChem (Chemical Structures)

```text
/speckit.specify "Build the PubChem MCP Server.

Core Requirements:
1. **Architecture:** Implement `PubChemClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://pubchem.ncbi.nlm.nih.gov/rest/pug
   - **Structure:** Must use `src/lifesciences_mcp/clients/pubchem.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_compounds(query)` (Fuzzy) returning ranked candidates.
   - Tool 2: `get_compound(pubchem_id)` (Strict) accepting ONLY resolved PubChem CIDs (PubChem:CID*).
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Include SMILES, InChI, molecular properties (formula, weight, IUPAC name).
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases. Rate limit: 5 req/sec, 400 req/min."
```

### IUPHAR/GtoPdb (Pharmacology)

```text
/speckit.specify "Build the IUPHAR/GtoPdb MCP Server.

Core Requirements:
1. **Architecture:** Implement `IUPHARClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://www.guidetopharmacology.org/services
   - **Structure:** Must use `src/lifesciences_mcp/clients/iuphar.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_ligands(query)` (Fuzzy) returning ranked ligand candidates.
   - Tool 2: `get_ligand(iuphar_id)` (Strict) accepting ONLY resolved IUPHAR ligand IDs.
   - Tool 3: `search_targets(query)` (Fuzzy) returning ranked target candidates.
   - Tool 4: `get_target(iuphar_id)` (Strict) accepting ONLY resolved IUPHAR target IDs.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Include ligand/target type, approvedName, synonyms, species, targetFamily.
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases. Rate limit: Conservative 1 req/sec."
```

### WikiPathways (Biological Pathways)

```text
/speckit.specify "Build the WikiPathways MCP Server.

Core Requirements:
1. **Architecture:** Implement `WikiPathwaysClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://www.wikipathways.org/api/. Open CC0 license - no restrictions.
   - **Structure:** Must use `src/lifesciences_mcp/clients/wikipathways.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_pathways(query, organism)` (Fuzzy) returning ranked pathway candidates with organism filtering.
   - Tool 2: `get_pathway(pathway_id)` (Strict) accepting ONLY resolved pathway IDs (WP format).
   - Tool 3: `get_pathways_for_gene(gene_id)` for reverse gene→pathway lookup.
   - Tool 4: `get_pathway_components(pathway_id)` extracting genes, proteins, metabolites from pathway.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Include pathway reactions, participants, data-nodes, organism, revision info.
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases. Rate limit: Conservative 1 req/sec."
```

### ClinicalTrials.gov (Clinical Trials Registry)

```text
/speckit.specify "Build the ClinicalTrials.gov MCP Server.

Core Requirements:
1. **Architecture:** Implement `ClinicalTrialsClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://clinicaltrials.gov/api/v2/. Public API, no authentication required.
   - **Structure:** Must use `src/lifesciences_mcp/clients/clinicaltrials.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_trials(query, condition, intervention, status, location, phase)` (Fuzzy) with comprehensive filters returning ranked trial candidates.
   - Tool 2: `get_trial(nct_id)` (Strict) accepting ONLY resolved NCT IDs (format: NCT########).
   - Tool 3: `get_trial_locations(nct_id)` for geographic facility/contact information.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Include protocol, eligibility criteria, outcomes, sponsors, phase, status, enrollment, dates.
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8).
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases. Rate limit: Conservative 1 req/sec."
```

### DepMap (Genotype-Selective Dependencies)

```text
/speckit.specify "Build the DepMap MCP Server.

Core Requirements:
1. **Architecture:** Implement `DepMapClient` extending `LifeSciencesClient` using `httpx` and native `asyncio` (ADR-001 §2). Base URL: https://api.cellmodelpassports.sanger.ac.uk (Sanger Cell Model Passports, JSON:API v1.0). Public API, no key. NON-COMMERCIAL; third-party application use requires prior permission (depmap@sanger.ac.uk) - surface this in tool descriptions, not only docstrings.
   - **Structure:** Must use `src/lifesciences_mcp/clients/depmap.py` (ADR-006).
   - **Lifecycle:** Use module-level singleton pattern; `@mcp.on_event` is FORBIDDEN (ADR-004).
   - **Rate limiting:** 1 req/sec via `asyncio.Lock` with exponential backoff. Cohort pagination is the real exposure (an RB1 deletion cohort is ~501 models across several sequential pages).
2. **Protocol:** Implement the 'Fuzzy-to-Fact' workflow (ADR-001 §3):
   - Tool 1: `search_models(query, slim, page_size)` (Fuzzy) returning ranked cell-model candidates with `SIDM:NNNNN` CURIEs.
     CONSTRAINT: the upstream `names` filter accepts ONLY the `any` operator (every other operator returns HTTP 500) and matches EXACTLY and CASE-SENSITIVELY. Measured: `a549`, `MCF-7` and `hela` return zero hits; `HeLa` returns a hit and `HELA` does not. Upper-casing the query is NOT a fix. Build a LOCAL normalised alias index instead: one request to `/models?fields[model]=names&page[size]=2500` (2266 rows, ~250 KB, ~1.7 s), case-folded and punctuation-stripped, cached for the process lifetime.
   - Tool 2: `get_model(model_id)` (Strict) accepting ONLY resolved CURIEs (`SIDM:NNNNN`; normalise the bare upstream `SIDM00903` form). Free text MUST return UNRESOLVED_ENTITY before any network call.
   - Tool 3: `models_with_mutation(gene, mutation_type, slim, cursor, page_size)` (Strict) for genotype-cohort assembly.
     CONSTRAINT: `mutation_type` is REQUIRED with NO default and MUST be validated against the closed set the API states in its own 404 body: frameshift, snp, insertion, deletion, splice_variant, mutation. The value `mutation` means ANY variant - it returns 2185 of 2266 models for RB1, which would put ~96% of the catalogue in the mutant arm and destroy the contrast. Echo the chosen class on every result.
   - Tool 4: `get_dependency(gene_id, model_id, data_source)` (Strict) returning gene-effect, provenance-labelled.
   - Tool 5: `genotype_contrast_by_gene(target_gene_id, genotype_gene_id, mutation_type, min_lines, data_source)` (Strict) returning WT-vs-mutant Δdependency, Mann-Whitney p, BH FDR, n per cohort, and direction. THE key capability.
     CONSTRAINT (measured 2026-09-02, re-verify before trusting): Sanger CRISPR KO essentiality IS live-queryable - `/datasets/crispr_ko` holds 22,218,273 rows and `/models/<SIDM>/datasets/crispr_ko` returns 35,294 rows for A549, carrying `bf` (BAGEL Bayes factor), `bf_scaled`, `fc_clean_qn`, `mageck_fdr`, `qc_pass`, `source`, linked to gene (SIDG) and model (SIDM). What is NOT possible is filtering that route by gene: `gene_id`, `gene` and `gene.id` all return HTTP 400/500, so isolating one target gene means paging all 35,294 rows for a model (36 pages at page[size]=1000, ~5.6 s each). A 501-model cohort contrast is therefore ~3 hours of paging at the 1 req/sec limit. Broad Chronos gene-effect is genuinely absent (`/datasets/chronos`, `/datasets/gene_effect`, `/datasets/depmap` all 500). CONCLUSION: cohort-scale contrasts MUST read a checksum-pinned cached release - for COST, not availability - and return UPSTREAM_ERROR naming the missing release when none is configured, never a zero that reads as a measurement. A single-gene, single-model `get_dependency` against Sanger IS implementable live and should be, with per-model caching. Do NOT expose a tool that takes the per-model vectors as arguments: that requires an agent to serialise ~2000 entries per call. Keep the maths as an internal, unit-tested function.
   - Gene arguments accept a resolved HGNC CURIE (`HGNC:NNNN`). Do NOT add a `search_genes` tool - gene resolution belongs to the HGNC and Entrez servers (cross-server Fuzzy-to-Fact); duplicating it here creates a second, divergent gene index. Bridge internally instead: `/genes?filter=[{"name":"symbol","op":"eq","val":"AURKB"}]` returns SIDG01983 carrying `hgnc_id: HGNC:11390`, so a Sanger SIDG id is reachable from an HGNC CURIE without a second public search tool.
3. **Schema:** All outputs must use the 'Agentic Biolink' schema with `cross_references` (ADR-001 §4). Cell-line identifiers are not in the Appendix A registry, so use a feature-local cross-reference model (precedent: `DrugCrossReferences`, `EnsemblCrossReferences`) carrying `ccle` and `cosmic`, both confirmed resolvable via `/models/CCLE_ID/<id>` and `/models/cosmic_id/<id>`. NOTE: `model_name` is NOT a valid resolve source (404). Every record MUST carry `data_source ∈ {broad_24q2, sanger_project_score}` - the two are different screens and their numbers are not comparable.
   - Null handling (ADR-001 §4): omit keys entirely. Use the `model_dump` override pattern; `ConfigDict(exclude_none=True)` is NOT a valid Pydantic v2 key and is SILENTLY IGNORED.
4. **Envelopes:** Must use Canonical Pagination and Error envelopes (ADR-001 §8). `page_size` MUST be clamped (`max(1, min(100, page_size))`) and MUST report the REQUESTED size, not the item count. Propagate the upstream `links.next` as an opaque cursor - never truncate a cohort at a cap while presenting it as complete. An empty result set is an empty PaginationEnvelope, NOT an ENTITY_NOT_FOUND error. Error messages MUST name Cell Model Passports; `ErrorEnvelope.upstream_error()` hardcodes HGNC's name and MUST NOT be used here.
   - Slim mode (ADR-001 §7): `slim=True` returns `id`, `name`, `score`. Candidates MUST carry a relevance `score` like every other SearchCandidate in the tree.
5. **Testing:** Include a `pytest-asyncio` test plan covering the 'Junior Dev' ambiguity cases (mixed-case and punctuation-variant cell-line names; an unaccepted mutation_type; free text passed to a strict tool), the genotype-contrast maths against a frozen fixture (mutant-selective, WT-selective, exact tie → direction 'none', small-cohort n<min_lines → tested=False with the statistics OMITTED, NaN exclusion), provenance labelling, and cursor pagination reaching a second page. Acceptance: `genotype_contrast_by_gene('AURKB','RB1')` reproduces the RB1-mutant-selective AURKB / RB-E2F result from sprime-lung-repro on Broad 24Q2."
```

## API Tier Reference

Use this to prioritize which servers to build next:

| Tier | APIs | Focus |
|------|------|-------|
| 0 | **ChEMBL** ✅, **Open Targets** ✅, **DrugBank** ⛔ | Drug Discovery Core |
| 1 | **HGNC** ✅, **UniProt** ✅, **STRING** ✅, **BioGRID** ✅ | Gene/Protein Foundation |
| 2 | **IUPHAR** ✅, **PubChem** ✅, ~~**STITCH**~~ ❌ | Pharmacology & Interactions |
| 3 | **WikiPathways** 🔨, **Reactome** ⏭️, **KEGG** ⏭️, **OMIM** ⏭️, **Orphanet** ⚠️ | Pathways & Disease (HIGH PRIORITY) |
| 4 | **Entrez** ✅, **Ensembl** ✅ | Genomics & Identifiers |
| 5 | **ClinicalTrials.gov** 🔨 | Clinical/Translational Research |
| 6 | **DepMap / Cell Model Passports** ✅ | Functional Genomics & Dependencies |

**Legend:** ✅ Complete | 🔨 In Progress (AGE-128, AGE-129) | ⛔ Blocked (paid) | ❌ Out of Scope | ⏭️ Future | ⚠️ Unclear

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| "Build a UniProt wrapper" | Too vague, forgets Fuzzy-to-Fact | Use the standard template |
| Skip `/scaffold-fastmcp` | Creates non-standard structure | Always scaffold first |
| Omit ADR citations | Agent may deviate from Constitution | Include explicit citations |
| Single generic tool | Violates Fuzzy-to-Fact protocol | Always include search + get |
| Custom envelope format | Breaks schema determinism | Use Canonical Envelopes |

## Future Considerations

- **Robust Error Logging:** Consider using `repr(e)` instead of `str(e)` in exception handlers (e.g., `f"Unexpected error: {e!r}"`) to ensure informative log messages even for exceptions with empty string representations (like some connection errors).

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-22 | Initial template after HGNC success |
| 1.1.0 | 2025-12-22 | Added Step 0: Git Worktrees for parallel development (ADR-005) |
| 1.2.0 | 2025-12-23 | Added STRING and BioGRID examples; updated Tier Reference with status |
| 1.3.0 | 2025-12-24 | Added Phase 2 examples (Ensembl, Entrez, PubChem, IUPHAR); marked STITCH as deprecated; updated status legend |
| 1.4.0 | 2026-01-02 | **CRITICAL**: Added prompt size limit warning (~20KB for `-p` flag); interactive mode required for large tasks.md |
| 1.5.0 | 2026-01-03 | Added WikiPathways and ClinicalTrials.gov examples (AGE-128, AGE-129); created Tier 5 for Clinical/Translational; marked Tier 3 as HIGH PRIORITY |
| 1.6.0 | 2026-01-09 | Added explicit ADR-004 and ADR-006 citations to template and preamble to strictly enforce architectural compliance |
| 1.7.0 | 2026-01-09 | Added "Future Considerations" regarding robust error logging with `repr(e)` |
| 1.8.0 | 2026-09-02 | Added DepMap (AGE-681) with measured live-API constraints injected; created Tier 6 (Functional Genomics) |
