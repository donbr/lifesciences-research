---
name: lifesciences-graph-builder
description: "Orchestrates life sciences APIs to build knowledge graphs using the Fuzzy-to-Fact protocol, combining MCPs for nodes and curl for edges, then persisting to Graphiti. This skill should be used when the user asks to \"build knowledge graphs\", \"find biological connections\", \"explore drug repurposing\", \"validate drug targets\", or mentions traversing gene→protein→pathway→drug→disease paths, multi-API orchestration, or graph persistence workflows."
---

# Life Sciences Graph Builder

Orchestrate multi-API graph construction using the **Fuzzy-to-Fact** protocol.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GRAPH CONSTRUCTION KIT                          │
├─────────────────────────────────────────────────────────────────────────┤
│  TIER 1: MCP TOOLS (Verified Nodes)                                     │
│  ├── HGNC: search_genes, get_gene                                       │
│  ├── UniProt: search_proteins, get_protein                              │
│  ├── ChEMBL: search_compounds, get_compound                             │
│  ├── STRING: search_proteins, get_interactions                          │
│  ├── Open Targets: search_targets, get_associations                     │
│  └── WikiPathways: get_pathways_for_gene, get_pathway_components        │
├─────────────────────────────────────────────────────────────────────────┤
│  TIER 2: CURL COMMANDS (Relationship Edges)                             │
│  ├── ChEMBL /mechanism: Drug → Target                                   │
│  ├── ChEMBL /drug_indication: Drug → Disease                            │
│  ├── ChEMBL /activity: Drug → Target (with Ki/IC50)                     │
│  ├── Ensembl /homology: Gene → Orthologs                                │
│  ├── STRING /enrichment: Protein Set → GO/KEGG terms                    │
│  └── NCBI elink: Gene → PubMed                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  TIER 3: GRAPHITI (Persistence)                                         │
│  └── add_memory: Persist validated subgraph as JSON episode             │
└─────────────────────────────────────────────────────────────────────────┘
```

## Workflow: Fuzzy-to-Fact Protocol

### Phase 1: Anchor Node (Naming)

Resolve fuzzy user input to canonical identifier.

```python
# MCP: HGNC
result = hgnc.search_genes("p53")
gene = hgnc.get_gene("HGNC:11998")  # → cross_references: UniProt, Ensembl, Entrez
```

### Phase 2: Enrich Node (Functional)

Decorate node with metadata and cross-references.

```python
# MCP: UniProt
protein = uniprot.get_protein("UniProtKB:P04637")
# → function text reveals interactors: BAX, BCL2, FAS
```

### Phase 3: Expand Edges (Interactions)

Build adjacency list from interaction databases.

```python
# MCP: STRING
interactions = string.get_interactions("STRING:9606.ENSP00000269305")
# → MDM2 (0.999), SIRT1 (0.999), ATM (0.995)
```

```bash
# Curl: Open Targets (gene-disease)
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000141510\") { associatedDiseases(page: {size: 5}) { rows { disease { name } score } } } }"}'
```

### Phase 4: Target Traversal (Pharma)

Follow edges to actionable targets.

```python
# MCP: HGNC (resolve downstream effector)
bcl2 = hgnc.search_genes("BCL2")  # → HGNC:990

# MCP: ChEMBL (find inhibitors)
venetoclax = chembl.search_compounds("Venetoclax")  # → CHEMBL:3137309
```

```bash
# Curl: ChEMBL mechanism (Drug → Target edge)
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL3137309&format=json" \
  | jq '.mechanisms[] | {action: .action_type, target: .target_chembl_id}'
# → INHIBITOR → CHEMBL4860 (BCL2)
```

### Phase 5: Persist Graph

Store validated subgraph in Graphiti.

```python
# MCP: Graphiti
graphiti.add_memory(
    name="TP53-BCL2-Venetoclax pathway",
    episode_body=json.dumps({
        "nodes": [
            {"id": "HGNC:11998", "type": "Gene", "symbol": "TP53"},
            {"id": "HGNC:990", "type": "Gene", "symbol": "BCL2"},
            {"id": "CHEMBL:3137309", "type": "Compound", "name": "Venetoclax"}
        ],
        "edges": [
            {"source": "HGNC:11998", "target": "HGNC:990", "type": "REGULATES"},
            {"source": "CHEMBL:3137309", "target": "HGNC:990", "type": "INHIBITOR"}
        ]
    }),
    source="json",
    group_id="drug-repurposing"
)
```

## Quick Edge Discovery Commands

| Edge Type | Curl Command |
|-----------|--------------|
| Drug → Target | `curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id={ID}&format=json"` |
| Target → Drugs | `curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?target_chembl_id={ID}&format=json"` |
| Drug → Disease | `curl -s "https://www.ebi.ac.uk/chembl/api/data/drug_indication?molecule_chembl_id={ID}&format=json"` |
| Gene → Disease | Open Targets GraphQL (see Phase 3) |
| Gene → Orthologs | `curl -s "https://rest.ensembl.org/homology/id/human/{ENSG}?type=orthologues&content-type=application/json"` |
| Protein Set → GO | `curl -s "https://string-db.org/api/json/enrichment?identifiers={IDs}&species=9606"` |
| Gene → PubMed | `curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=gene&db=pubmed&id={ID}&retmode=json"` |

## Example: Drug Repurposing Graph

Build a complete subgraph for drug repurposing analysis:

```bash
# Step 1: Anchor - Resolve gene
# MCP: hgnc.search_genes("TP53") → HGNC:11998

# Step 2: Get protein context
# MCP: uniprot.get_protein("UniProtKB:P04637")
# → function mentions BCL2

# Step 3: Find BCL2 inhibitors
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?target_chembl_id=CHEMBL4860&format=json" \
  | jq '.mechanisms[] | {drug: .molecule_chembl_id, action: .action_type}'

# Step 4: Get drug indications
curl -s "https://www.ebi.ac.uk/chembl/api/data/drug_indication?molecule_chembl_id=CHEMBL3137309&format=json" \
  | jq '.drug_indications[:3][] | {disease: .mesh_heading, phase: .max_phase_for_ind}'

# Step 5: Find clinical trials
curl -s "https://clinicaltrials.gov/api/v2/studies?query.intr=venetoclax&filter.overallStatus=RECRUITING&pageSize=3&format=json" \
  | jq '.studies[] | {nct: .protocolSection.identificationModule.nctId}'

# Step 6: Persist to Graphiti
# MCP: graphiti.add_memory(...)
```

## Node Types (Canonical CURIEs)

| Type | CURIE Pattern | Example |
|------|---------------|---------|
| Gene | `HGNC:\d+` | HGNC:11998 |
| Protein | `UniProtKB:[A-Z0-9]+` | UniProtKB:P04637 |
| Compound | `CHEMBL:\d+` | CHEMBL:3137309 |
| Target | `CHEMBL:\d+` | CHEMBL:4860 |
| Disease | `EFO_\d+` or `MONDO_\d+` | EFO_0000574 |
| Pathway | `WP:WP\d+` | WP:WP1742 |
| Trial | `NCT:\d+` | NCT:00461032 |

## Edge Types

| Edge | Source | Target | Properties |
|------|--------|--------|------------|
| ENCODES | Gene | Protein | - |
| REGULATES | Gene | Gene | direction: activation/repression |
| INTERACTS | Protein | Protein | score, evidence_type |
| INHIBITOR | Compound | Target | Ki, IC50 |
| AGONIST | Compound | Target | EC50 |
| TREATS | Compound | Disease | max_phase |
| ASSOCIATED_WITH | Gene | Disease | score, evidence_sources |
| MEMBER_OF | Gene | Pathway | - |

## Query Best Practices

### Gene Discovery (Human-Centric)
- **Default to species=9606** (human) for gene/protein searches
- Use `page_size=10` for exploration, `page_size=50` for batch operations
- Use `slim=True` for batch operations to reduce token usage
- Only use `organism=null` for comparative genomics across species

### Drug Discovery vs Repurposing
- **Drug repurposing**: Use `max_phase≥2` (clinical validation, shorter approval path)
- **General discovery**: No phase filter (include preclinical tools, mechanism probes)
- Check mechanisms before bioactivity data

### Clinical Landscape
- **Default status=RECRUITING** for active research
- Use phase filter only for specific analysis:
  - PHASE3+ for commercialization analysis
  - PHASE1/2 for early pipeline
  - No filter for full landscape

## See Also

- **lifesciences-genomics**: Ensembl, NCBI, HGNC endpoints
- **lifesciences-proteomics**: UniProt, STRING, BioGRID endpoints
- **lifesciences-pharmacology**: ChEMBL, PubChem, IUPHAR endpoints
- **lifesciences-clinical**: Open Targets, ClinicalTrials.gov endpoints
