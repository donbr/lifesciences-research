# Scenario 4: p53-MDM2-Nutlin Graph Persistence Test

## Use Case

Build and persist a knowledge graph for the **p53-MDM2-Nutlin** axis using the Fuzzy-to-Fact protocol, testing the Graphiti persistence layer.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: MCP TOOLS (Verified Nodes)                             │
│  ├── hgnc_search_genes("TP53") → HGNC:11998                     │
│  ├── hgnc_search_genes("MDM2") → HGNC:6973                      │
│  ├── chembl_search_compounds("Nutlin-3") → CHEMBL:191334        │
│  └── string_get_interactions("TP53") → MDM2 score               │
├─────────────────────────────────────────────────────────────────┤
│  TIER 2: CURL COMMANDS (Relationship Edges)                     │
│  ├── STRING /network → interaction score                        │
│  └── ChEMBL /activity → Ki/IC50 values                          │
├─────────────────────────────────────────────────────────────────┤
│  TIER 3: GRAPHITI (Persistence)                                 │
│  └── add_memory → oncology-demo                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Resolve Nodes (Tier 1)

**MCP Tool Calls:**
```python
hgnc_search_genes(query="TP53")
# Returns: {"items": [{"id": "HGNC:11998", "symbol": "TP53", ...}]}

hgnc_search_genes(query="MDM2")
# Returns: {"items": [{"id": "HGNC:6973", "symbol": "MDM2", ...}]}

chembl_search_compounds(query="Nutlin-3")
# Returns: {"items": [{"id": "CHEMBL:191334", "name": "NUTLIN-3", ...}]}
```

**Results:**

| Entity | ID | Name | Role |
|--------|-----|------|------|
| TP53 | HGNC:11998 | tumor protein p53 | Tumor suppressor |
| MDM2 | HGNC:6973 | MDM2 proto-oncogene | Oncogene (E3 ligase) |
| Nutlin-3 | CHEMBL:191334 | NUTLIN-3 | MDM2 inhibitor |

**Cross-References:**

| Gene | Ensembl | UniProt | Entrez |
|------|---------|---------|--------|
| TP53 | ENSG00000141510 | P04637 | 7157 |
| MDM2 | ENSG00000135679 | Q00987 | 4193 |

## Phase 2: Build Edges (Tier 2 - curl)

**curl Commands:**
```bash
# Get MDM2 ChEMBL target ID
curl -s "https://www.ebi.ac.uk/chembl/api/data/target/search?q=MDM2&format=json"
# Returns: CHEMBL5023

# Get Nutlin-3 activity against MDM2
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL191334&target_chembl_id=CHEMBL5023&format=json"
```

**Results:**

| Compound | Target | Assay Type | Ki (nM) |
|----------|--------|------------|---------|
| Nutlin-3 | MDM2 (CHEMBL5023) | Binding | 36 |

**STRING Interaction:**

| Gene A | Gene B | Score |
|--------|--------|-------|
| TP53 | MDM2 | 0.999 (highest confidence) |

## Phase 3: Persist Graph (Tier 3 - Graphiti)

**MCP Tool Call:**
```python
graphiti.add_memory(
    name="p53-MDM2-Nutlin Axis Graph v2",
    episode_body=<json_graph>,
    source="json",
    group_id="oncology-demo"
)
```

## Knowledge Graph

### Nodes

| ID | Type | Symbol | Role |
|----|------|--------|------|
| HGNC:11998 | Gene | TP53 | Tumor suppressor |
| HGNC:6973 | Gene | MDM2 | Oncogene |
| CHEMBL:5023 | Target | E3 ubiquitin-protein ligase Mdm2 | Druggable target |
| CHEMBL:191334 | Compound | NUTLIN-3 | MDM2 inhibitor |

### Edges

| Source | Target | Type | Properties |
|--------|--------|------|------------|
| HGNC:6973 | HGNC:11998 | REGULATES | mechanism: ubiquitin-mediated degradation, effect: negative, STRING score: 0.999 |
| HGNC:11998 | HGNC:6973 | REGULATES | mechanism: transcriptional activation, effect: positive |
| HGNC:6973 | CHEMBL:5023 | ENCODES | - |
| CHEMBL:191334 | CHEMBL:5023 | INHIBITOR | Ki: 36 nM |

## Biological Context

### p53-MDM2 Negative Feedback Loop

```
TP53 ──transcriptional activation──▶ MDM2
  ▲                                    │
  │                                    │
  └──ubiquitin-mediated degradation────┘
```

1. **TP53** transcriptionally activates **MDM2** expression
2. **MDM2** ubiquitinates **TP53**, targeting it for proteasomal degradation
3. This creates a negative feedback loop that normally keeps p53 levels low

### Therapeutic Rationale

In cancers with:
- Wild-type p53 (functional)
- MDM2 amplification/overexpression

**MDM2 inhibition** (e.g., Nutlin-3) disrupts the p53-MDM2 interaction, leading to:
- p53 stabilization
- Cell cycle arrest
- Apoptosis

### Clinical Applications
- Sarcomas
- Acute Myeloid Leukemia (AML)
- Solid tumors with wild-type p53

## Key Findings

| Metric | Value |
|--------|-------|
| STRING Interaction Score | 0.999 (maximum) |
| Nutlin-3 Ki vs MDM2 | 36 nM |
| Mechanism | Blocks p53 binding pocket on MDM2 |

## Graphiti Group

`oncology-demo`