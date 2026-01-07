# Scenario 1: ARID1A Synthetic Lethality Graph

## Use Case

Identify a therapeutic strategy for **ARID1A-deficient Ovarian Cancer** using a synthetic lethality approach.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: MCP TOOLS (Verified Nodes)                             │
│  ├── hgnc_search_genes("ARID1A") → HGNC:11110                   │
│  ├── hgnc_search_genes("EZH2") → HGNC:3527                      │
│  ├── hgnc_search_genes("ATR") → HGNC:882                        │
│  ├── chembl_search_compounds("tazemetostat") → CHEMBL:3414621   │
│  └── string_get_interactions("EZH2") → SWI/SNF complex          │
├─────────────────────────────────────────────────────────────────┤
│  TIER 2: CURL COMMANDS (Relationship Edges)                     │
│  ├── ChEMBL /mechanism → Drug → Target                          │
│  ├── ChEMBL /activity → IC50 values                             │
│  └── ClinicalTrials.gov → Trial status                          │
├─────────────────────────────────────────────────────────────────┤
│  TIER 3: GRAPHITI (Persistence)                                 │
│  └── add_memory → scenario1-synthetic-lethality                 │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Anchor Nodes (Tier 1 - MCP Tools)

**MCP Tool Calls:**
```python
hgnc_search_genes(query="ARID1A")
# Returns: {"items": [{"id": "HGNC:11110", "symbol": "ARID1A", ...}]}

hgnc_search_genes(query="EZH2")
# Returns: {"items": [{"id": "HGNC:3527", "symbol": "EZH2", ...}]}

hgnc_search_genes(query="ATR")
# Returns: {"items": [{"id": "HGNC:882", "symbol": "ATR", ...}]}
```

**Results:**

| Gene | HGNC ID | Ensembl | UniProt | Role |
|------|---------|---------|---------|------|
| ARID1A | HGNC:11110 | ENSG00000117713 | O14497 | Tumor suppressor (SWI/SNF) |
| EZH2 | HGNC:3527 | ENSG00000106462 | Q15910 | Synthetic lethal partner (PRC2) |
| ATR | HGNC:882 | ENSG00000175054 | Q13535 | Synthetic lethal partner |

## Phase 2: Find Druggable Partner (Tier 2 - curl)

**curl Commands:**
```bash
# Get EZH2 ChEMBL target ID
curl -s "https://www.ebi.ac.uk/chembl/api/data/target/search?q=EZH2&format=json"
# Returns: CHEMBL2189110

# Find potent EZH2 inhibitors (IC50 < 100nM)
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?target_chembl_id=CHEMBL2189110&standard_type=IC50&standard_value__lte=100&format=json"
```

**Top EZH2 Inhibitors:**

| Compound | ChEMBL ID | IC50 (nM) | Max Phase | FDA Approved |
|----------|-----------|-----------|-----------|--------------|
| TAZEMETOSTAT | CHEMBL3414621 | 1 | 4 | Yes (2020) |
| GSK2816126 | CHEMBL3287735 | 2 | 1 | No |

## Phase 3: Clinical Validation (Tier 2 - curl)

**curl Command:**
```bash
curl -s "https://clinicaltrials.gov/api/v2/studies?query.intr=tazemetostat&query.cond=ovarian&pageSize=3&format=json"
```

**Active Trials:**

| NCT ID | Title | Phase | Status |
|--------|-------|-------|--------|
| NCT03348631 | Tazemetostat in Recurrent Ovarian Cancer | Phase 2 | ACTIVE_NOT_RECRUITING |

## Phase 4: Persist Graph (Tier 3 - Graphiti)

**MCP Tool Call:**
```python
graphiti.add_memory(
    name="ARID1A Synthetic Lethality Graph v2",
    episode_body=<json_graph>,
    source="json",
    group_id="scenario1-synthetic-lethality"
)
```

## Knowledge Graph

### Nodes

| ID | Type | Symbol | Role |
|----|------|--------|------|
| HGNC:11110 | Gene | ARID1A | Tumor suppressor |
| HGNC:3527 | Gene | EZH2 | Synthetic lethal partner |
| HGNC:882 | Gene | ATR | Synthetic lethal partner |
| CHEMBL:2189110 | Target | EZH2 | Druggable target |
| CHEMBL:3414621 | Compound | TAZEMETOSTAT | FDA approved inhibitor |
| NCT:03348631 | Trial | - | Phase 2 ovarian cancer |

### Edges

| Source | Target | Type | Evidence |
|--------|--------|------|----------|
| HGNC:11110 | HGNC:3527 | SYNTHETIC_LETHAL | SWI/SNF-PRC2 chromatin antagonism |
| HGNC:11110 | HGNC:882 | SYNTHETIC_LETHAL | Replication stress sensitization |
| HGNC:3527 | CHEMBL:2189110 | ENCODES | - |
| CHEMBL:3414621 | CHEMBL:2189110 | INHIBITOR | IC50 = 1 nM |
| CHEMBL:3414621 | NCT:03348631 | TESTED_IN | Ovarian cancer indication |

## Therapeutic Strategy

**Rationale:** ARID1A-mutant ovarian cancers lose SWI/SNF-mediated chromatin remodeling, creating synthetic lethal dependency on PRC2 (EZH2) for transcriptional regulation.

**Lead Compound:** TAZEMETOSTAT (CHEMBL:3414621)
- IC50: 1 nM
- FDA Approved: 2020
- Active Trial: NCT03348631 (Phase 2, Ovarian Cancer)

## Graphiti Group

`scenario1-synthetic-lethality`