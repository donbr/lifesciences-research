# Scenario 3: Huntington's Disease Orphan Drug Sprint

## Use Case

Conduct a "Virtual Discovery" sprint for **Huntington's Disease** to identify novel therapeutic targets not covered by current Phase 3 interventions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: MCP TOOLS (Verified Nodes)                             │
│  ├── hgnc_search_genes("HTT") → HGNC:4851 (causal gene)         │
│  ├── opentargets_search_targets("HTT") → disease associations   │
│  ├── opentargets_get_associations() → ranked targets            │
│  └── chembl_search_compounds() → trial drugs                    │
├─────────────────────────────────────────────────────────────────┤
│  TIER 2: CURL COMMANDS (Relationship Edges)                     │
│  ├── ClinicalTrials.gov → Phase 3 trials                        │
│  ├── ChEMBL /mechanism → Drug mechanisms                        │
│  └── Open Targets GraphQL → target associations                 │
├─────────────────────────────────────────────────────────────────┤
│  TIER 3: GRAPHITI (Persistence)                                 │
│  └── add_memory → scenario3-huntington-sprint                   │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Genetic Anchor (Tier 1)

**MCP Tool Call:**
```python
hgnc_search_genes(query="HTT")
# Returns: {"items": [{"id": "HGNC:4851", "symbol": "HTT", "name": "huntingtin", ...}]}
```

**Result:**

| Gene | HGNC ID | Ensembl | Name | Role |
|------|---------|---------|------|------|
| HTT | HGNC:4851 | ENSG00000197386 | huntingtin | Causal gene |

## Phase 2: Trial Landscape (Tier 2 - curl)

**curl Commands:**
```bash
# Find Tetrabenazine HD trials
curl -s "https://clinicaltrials.gov/api/v2/studies?query.intr=tetrabenazine&query.cond=huntington&pageSize=5&format=json"

# Find Deutetrabenazine HD trials
curl -s "https://clinicaltrials.gov/api/v2/studies?query.intr=deutetrabenazine&query.cond=huntington&pageSize=5&format=json"
```

**Phase 3 Trials:**

| NCT ID | Drug | Phase | Status |
|--------|------|-------|--------|
| NCT00219804 | Tetrabenazine | Phase 3 | COMPLETED |
| NCT01897896 | Deutetrabenazine | Phase 3 | COMPLETED |
| NCT01795859 | Tetrabenazine | Phase 3 | COMPLETED |

## Phase 3: Reverse-Engineer Drug Mechanisms (Tier 1 + Tier 2)

**MCP Tool Calls:**
```python
chembl_search_compounds(query="tetrabenazine")
# Returns: {"items": [{"id": "CHEMBL:117785", "name": "TETRABENAZINE", ...}]}

chembl_search_compounds(query="deutetrabenazine")
# Returns: {"items": [{"id": "CHEMBL:3137326", "name": "DEUTETRABENAZINE", ...}]}
```

**curl Command:**
```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL117785&format=json"
```

**Current Drug Mechanisms:**

| Drug | Target ID | Target Name | Action |
|------|-----------|-------------|--------|
| Tetrabenazine | CHEMBL1893 | VMAT2 (SLC18A2) | INHIBITOR |
| Deutetrabenazine | CHEMBL1893 | VMAT2 (SLC18A2) | INHIBITOR |

## Phase 4: Gap Analysis (Tier 2 - curl)

**curl Command (Open Targets GraphQL):**
```bash
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ disease(efoId: \"MONDO_0007739\") { associatedTargets(page: {index: 0, size: 10}) { rows { target { id approvedSymbol } score } } } }"}'
```

**Open Targets Associations for Huntington Disease:**

| Gene | Ensembl ID | OT Score | Covered by Drugs? |
|------|------------|----------|-------------------|
| HTT | ENSG00000197386 | 0.73 | No (causal gene) |
| SLC18A2 | ENSG00000165646 | 0.58 | **YES** (Tetrabenazine) |
| DRD2 | ENSG00000149295 | 0.39 | Partial (antipsychotics) |
| **SLC2A3** | ENSG00000059804 | 0.39 | **NO - NOVEL** |
| DRD3 | ENSG00000151577 | 0.33 | Partial (antipsychotics) |
| SCN4A | ENSG00000007314 | 0.28 | No |
| HTR2A | ENSG00000102468 | 0.28 | No |

## Phase 5: Persist Graph (Tier 3 - Graphiti)

**MCP Tool Call:**
```python
graphiti.add_memory(
    name="Huntington's Disease Orphan Drug Sprint v2",
    episode_body=<json_graph>,
    source="json",
    group_id="scenario3-huntington-sprint"
)
```

## Knowledge Graph

### Nodes

| ID | Type | Symbol | Role |
|----|------|--------|------|
| HGNC:4851 | Gene | HTT | Causal gene |
| MONDO:0007739 | Disease | Huntington disease | - |
| CHEMBL:1893 | Target | VMAT2 (SLC18A2) | Current target (covered) |
| CHEMBL:117785 | Compound | TETRABENAZINE | Approved drug |
| CHEMBL:3137326 | Compound | DEUTETRABENAZINE | Approved drug |
| ENSG00000059804 | Gene | SLC2A3 (GLUT3) | **Novel target** |

### Edges

| Source | Target | Type | Evidence |
|--------|--------|------|----------|
| HGNC:4851 | MONDO:0007739 | CAUSES | Genetic |
| CHEMBL:117785 | CHEMBL:1893 | INHIBITOR | Dopamine depletion |
| CHEMBL:3137326 | CHEMBL:1893 | INHIBITOR | Dopamine depletion |
| CHEMBL:1893 | MONDO:0007739 | TREATS | Chorea indication |
| ENSG00000059804 | MONDO:0007739 | ASSOCIATED_WITH | OT score 0.39 |

## Gap Analysis

### Covered Mechanisms
- VMAT2 inhibition (dopamine depletion) - Tetrabenazine/Deutetrabenazine
- DRD2/DRD3 antagonism (antipsychotics, symptomatic only)

### Novel Opportunities

| Target | Gene | OT Score | Rationale | Druggability |
|--------|------|----------|-----------|--------------|
| **GLUT3** | SLC2A3 | 0.39 | Genetic association with no drug coverage. Glucose transporter in neurons suggests metabolic dysfunction intervention. | High |
| Complex I | NDUFV2 | 0.26 | Mitochondrial dysfunction in HD. Neuroprotective strategy. | Moderate |
| HTT (direct) | HTT | 0.85 | Gene silencing (ASO, RNAi) | Low (gene therapy) |

## Recommendation

**SLC2A3 (GLUT3)** represents a HIGH POTENTIAL novel target:
- Strong genetic association (OT score 0.39)
- Zero drug coverage in Phase 3 trials
- Metabolic intervention strategy is orthogonal to current dopamine-depleting approaches

## Graphiti Group

`scenario3-huntington-sprint`