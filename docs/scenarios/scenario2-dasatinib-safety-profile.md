# Scenario 2: Dasatinib Off-Target Safety Profile

## Use Case

Safety profile analysis for the kinase inhibitor **Dasatinib**, focusing on cardiotoxicity risk from off-target activity against hERG (KCNH2) and DDR2.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: MCP TOOLS (Verified Nodes)                             │
│  ├── chembl_search_compounds("dasatinib") → CHEMBL:1421         │
│  ├── hgnc_search_genes("KCNH2") → HGNC:6251 (hERG)              │
│  └── hgnc_search_genes("DDR2") → HGNC:2731                      │
├─────────────────────────────────────────────────────────────────┤
│  TIER 2: CURL COMMANDS (Relationship Edges)                     │
│  ├── ChEMBL /mechanism → Drug → Target edges                    │
│  ├── ChEMBL /activity → IC50/Ki values                          │
│  └── ChEMBL /target → Target details                            │
├─────────────────────────────────────────────────────────────────┤
│  TIER 3: GRAPHITI (Persistence)                                 │
│  └── add_memory → scenario2-safety-profile                      │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Resolve Drug & Safety Targets (Tier 1)

**MCP Tool Calls:**
```python
chembl_search_compounds(query="dasatinib")
# Returns: {"items": [{"id": "CHEMBL:1421", "name": "DASATINIB", ...}]}

hgnc_search_genes(query="KCNH2")
# Returns: {"items": [{"id": "HGNC:6251", "symbol": "KCNH2", ...}]}

hgnc_search_genes(query="DDR2")
# Returns: {"items": [{"id": "HGNC:2731", "symbol": "DDR2", ...}]}
```

**Results:**

| Entity | ID | Name | Role |
|--------|-----|------|------|
| Dasatinib | CHEMBL:1421 | DASATINIB | Multi-kinase inhibitor (FDA 2006) |
| hERG | HGNC:6251 | KCNH2 | Safety target (cardiotoxicity) |
| DDR2 | HGNC:2731 | DDR2 | Off-target (pleural effusion) |

## Phase 2: Get Drug Mechanisms (Tier 2 - curl)

**curl Command:**
```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL1421&format=json"
```

**Dasatinib Primary Targets:**

| Target ID | Target Name | Action |
|-----------|-------------|--------|
| CHEMBL1862 | Tyrosine-protein kinase ABL1 | INHIBITOR |
| CHEMBL1913 | PDGFR-beta | INHIBITOR |
| CHEMBL1936 | KIT receptor | INHIBITOR |
| CHEMBL2068 | Ephrin type-A receptor 2 | INHIBITOR |

## Phase 3: Audit Off-Target Activity (Tier 2 - curl)

**curl Commands:**
```bash
# Dasatinib vs DDR2
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL1421&target_chembl_id=CHEMBL5122&format=json"

# Dasatinib vs ABL1 (primary)
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL1421&target_chembl_id=CHEMBL1862&format=json"
```

**Dasatinib Activity Data:**

| Target | IC50 (nM) | Kd (nM) | Concern |
|--------|-----------|---------|---------|
| ABL1 (primary) | 1.0 | - | Primary target |
| DDR2 (off-target) | 54 | 70 | Pleural effusion risk |

## Phase 4: Find Cleaner Alternative (Tier 1 + Tier 2)

**MCP Tool Call:**
```python
chembl_search_compounds(query="imatinib")
# Returns: {"items": [{"id": "CHEMBL:941", "name": "IMATINIB", ...}]}
```

**curl Commands:**
```bash
# Imatinib vs DDR2
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL941&target_chembl_id=CHEMBL5122&format=json"

# Imatinib vs ABL1
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL941&target_chembl_id=CHEMBL1862&format=json"
```

**Imatinib Activity Data:**

| Target | IC50 (nM) | Kd (nM) |
|--------|-----------|---------|
| ABL1 (primary) | 38 | - |
| DDR2 (off-target) | 141 | 15 |

## Phase 5: Persist Graph (Tier 3 - Graphiti)

**MCP Tool Call:**
```python
graphiti.add_memory(
    name="Dasatinib Off-Target Safety Profile v2",
    episode_body=<json_graph>,
    source="json",
    group_id="scenario2-safety-profile"
)
```

## Safety Comparison

| Drug | ABL1 IC50 (nM) | DDR2 IC50 (nM) | Selectivity Window |
|------|----------------|----------------|-------------------|
| **Dasatinib** | 1.0 | 54 | 54x (off-target concern) |
| **Imatinib** | 38 | 141 | 3.7x (cleaner profile) |

## Knowledge Graph

### Nodes

| ID | Type | Name | Role |
|----|------|------|------|
| CHEMBL:1421 | Compound | DASATINIB | Index compound |
| CHEMBL:941 | Compound | IMATINIB | Cleaner alternative |
| CHEMBL:1862 | Target | ABL1 | Primary target |
| CHEMBL:5122 | Target | DDR2 | Off-target |
| HGNC:6251 | Gene | KCNH2 | Safety target (hERG) |
| HGNC:2731 | Gene | DDR2 | Off-target gene |

### Edges

| Source | Target | Type | IC50 (nM) |
|--------|--------|------|-----------|
| CHEMBL:1421 | CHEMBL:1862 | INHIBITOR | 1.0 |
| CHEMBL:1421 | CHEMBL:5122 | INHIBITOR | 54 |
| CHEMBL:941 | CHEMBL:1862 | INHIBITOR | 38 |
| CHEMBL:941 | CHEMBL:5122 | INHIBITOR | 141 |

## Recommendation

**Imatinib has ~3x lower DDR2 affinity relative to ABL1 potency**, making it a cleaner alternative for patients at risk of DDR2-mediated pleural effusion.

## Graphiti Group

`scenario2-safety-profile`