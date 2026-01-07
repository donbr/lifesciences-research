# Just-in-Time Graph Construction: Research Findings

**Date**: 2026-01-06
**Status**: Research Complete
**Thesis**: "Grounding the Ghost" blog post validation

---

## Executive Summary

The blog post thesis is **VALIDATED**. The Life Sciences MCPs provide a Just-in-Time Graph Construction Kit where:
- **MCPs provide verified NODES** (entity identity via Fuzzy-to-Fact)
- **Curl skills provide EDGES and DEEP DETAILS** (relationship APIs via edge discovery, plus rich data beyond MCP coverage like protein features, pathway components, and bioactivity metrics)
- **Graphiti persists the graph** for downstream reasoning

### Validated Graph: TP53 → BCL2 → Venetoclax

```
TP53 (HGNC:11998)
├── VERIFIED BY: HGNC MCP (search_genes → get_gene)
├── ENRICHED BY: UniProt P04637
│   └── function: "induces apoptosis via BAX stimulation, BCL2 repression"
│
├── EDGES FROM STRING (MCP):
│   ├── MDM2 (0.999) ─ negative regulator
│   ├── SIRT1 (0.999) ─ deacetylase
│   ├── ATM (0.995) ─ DNA damage kinase
│   └── PTEN (0.757) ─ tumor suppressor
│
├── EDGES FROM Open Targets (curl):
│   ├── Li-Fraumeni syndrome (0.876)
│   ├── hepatocellular carcinoma (0.796)
│   └── head/neck squamous carcinoma (0.777)
│
├── PATHWAY MEMBERSHIP (WikiPathways curl):
│   ├── WP1742: TP53 network
│   ├── WP366: TGF-beta signaling
│   └── WP5550: Lung adenocarcinoma
│
└── DOWNSTREAM EFFECTOR: BCL2 (HGNC:990)
    └── INHIBITOR: Venetoclax (CHEMBL:3137309)
        ├── max_phase: 4 (FDA approved)
        ├── mechanism: "Apoptosis regulator Bcl-2 inhibitor"
        └── indications: CLL (phase 4), Multiple Myeloma (phase 3)
```

---

## Edge API Catalog

### Tier 1: Production-Ready (MCP-Exposed)

| Edge Type | Source | MCP Tool | Confidence |
|-----------|--------|----------|------------|
| Gene → Protein | UniProt | `get_protein` | ✅ High |
| Protein ↔ Protein | STRING | `get_interactions` | ✅ High (0-1000 score) |
| Gene → Pathway | WikiPathways | `get_pathways_for_gene` | ✅ High |
| Target → Disease | Open Targets | `get_associations` | ✅ High (0-1 score) |
| Compound details | ChEMBL | `get_compound` | ✅ High |

### Tier 2: Curl-Discovered (Not in MCPs)

| Edge Type | API Endpoint | Curl Command | Notes |
|-----------|--------------|--------------|-------|
| **Drug → Target** | ChEMBL mechanism | `https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id={id}&format=json` | Returns action_type, target_chembl_id |
| **Target → Drugs** | ChEMBL mechanism | `https://www.ebi.ac.uk/chembl/api/data/mechanism?target_chembl_id={id}&format=json` | Reverse lookup |
| **Drug → Indication** | ChEMBL drug_indication | `https://www.ebi.ac.uk/chembl/api/data/drug_indication?molecule_chembl_id={id}&format=json` | mesh_heading, efo_term, max_phase |
| **Gene → PubMed** | NCBI elink | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=gene&db=pubmed&id={id}&retmode=json` | Evidence support |
| **Gene → Pathways** | WikiPathways | `http://webservice.wikipathways.org/findPathwaysByXref?ids={entrez_id}&codes=L&format=json` | Alternative to MCP |

---

## Curl Command Reference

### 1. ChEMBL Mechanism API (Drug → Target)

```bash
# Find what Venetoclax targets
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL3137309&format=json" \
  | jq '.mechanisms[] | {action_type, mechanism_of_action, target_chembl_id}'

# Output:
# {
#   "action_type": "INHIBITOR",
#   "mechanism_of_action": "Apoptosis regulator Bcl-2 inhibitor",
#   "target_chembl_id": "CHEMBL4860"
# }
```

### 2. ChEMBL Mechanism API (Target → Drugs)

```bash
# Find all BCL2 inhibitors
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?target_chembl_id=CHEMBL4860&format=json" \
  | jq '.mechanisms[] | {molecule_chembl_id, mechanism_of_action}'

# Output:
# CHEMBL3137309 (Venetoclax)
# CHEMBL2107358
# CHEMBL443684
```

### 3. ChEMBL Drug Indication API

```bash
# What diseases does Venetoclax treat?
curl -s "https://www.ebi.ac.uk/chembl/api/data/drug_indication?molecule_chembl_id=CHEMBL3137309&format=json" \
  | jq '.drug_indications[] | {mesh_heading, max_phase_for_ind}'

# Output:
# CLL (phase 4), Multiple Myeloma (phase 3), Non-Hodgkin (phase 2)...
```

### 4. Open Targets GraphQL (Gene → Disease)

```bash
# What diseases are associated with TP53?
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000141510\") { approvedSymbol associatedDiseases(page: {index: 0, size: 5}) { rows { disease { id name } score } } } }"}' \
  "https://api.platform.opentargets.org/api/v4/graphql" \
  | jq '.data.target.associatedDiseases.rows[]'

# Output:
# Li-Fraumeni syndrome (0.876), hepatocellular carcinoma (0.796)...
```

### 5. STRING Network API

```bash
# Get TP53 protein-protein interactions
curl -s "https://string-db.org/api/json/network?identifiers=TP53&species=9606&required_score=700&limit=10" \
  | jq '.[] | {preferredName_A, preferredName_B, score}'

# Output:
# SIRT1↔TP53 (0.999), MDM2↔TP53 (0.999), ATM↔TP53 (0.995)...
```

### 6. NCBI elink (Gene → PubMed)

```bash
# Find PubMed articles for TP53 (gene ID 7157)
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=gene&db=pubmed&id=7157&retmode=json" \
  | jq '.linksets[0].linksetdbs[] | select(.dbto=="pubmed") | {count: (.links | length)}'

# Output: 455 articles
```

### 7. WikiPathways Gene→Pathway

```bash
# Find pathways containing TP53 (Entrez ID 7157)
curl -s "http://webservice.wikipathways.org/findPathwaysByXref?ids=7157&codes=L&format=json" \
  | jq '.result[] | {pathway_id: .id, pathway_name: .name}'

# Output:
# WP1742: TP53 network
# WP366: TGF-beta signaling
# WP5550: Lung adenocarcinoma
```

---

## Graph Construction Workflow

### Phase 1: Anchor Node (Naming Skill)

```python
# MCP: HGNC
result = await hgnc.search_genes("p53")
# → TP53 (HGNC:11998), score=1.0

gene = await hgnc.get_gene("HGNC:11998")
# → cross_references: UniProt=P04637, Ensembl=ENSG00000141510, Entrez=7157
```

### Phase 2: Enrich Node (Functional Skill)

```python
# MCP: UniProt
protein = await uniprot.get_protein("UniProtKB:P04637")
# → function: "induces apoptosis via BAX stimulation, BCL2 repression"
# → cross_references: STRING=9606.ENSP00000269305
```

### Phase 3: Expand Edges (Interaction Skills)

```python
# MCP: STRING
interactions = await string.get_interactions("STRING:9606.ENSP00000269305", required_score=700)
# → MDM2 (0.999), SIRT1 (0.999), ATM (0.995), PTEN (0.757)

# Curl: Open Targets
diseases = curl_opentargets_associations("ENSG00000141510")
# → Li-Fraumeni (0.876), hepatocellular carcinoma (0.796)
```

### Phase 4: Target Traversal (Pharma Skill)

```python
# Extract BCL2 from UniProt function text
# MCP: HGNC
bcl2 = await hgnc.search_genes("BCL2")
# → HGNC:990

# MCP: ChEMBL
venetoclax = await chembl.search_compounds("Venetoclax")
# → CHEMBL:3137309

# Curl: ChEMBL mechanism (EDGE discovery)
mechanism = curl_chembl_mechanism("CHEMBL:3137309")
# → action_type: INHIBITOR, target: CHEMBL4860 (BCL2)
```

### Phase 5: Persist to Graphiti

```python
# Graph JSON for persistence
graph_episode = {
    "name": "TP53-BCL2-Venetoclax pathway",
    "episode_body": json.dumps({
        "nodes": [
            {"id": "HGNC:11998", "type": "Gene", "symbol": "TP53"},
            {"id": "HGNC:990", "type": "Gene", "symbol": "BCL2"},
            {"id": "CHEMBL:3137309", "type": "Compound", "name": "Venetoclax"}
        ],
        "edges": [
            {"source": "HGNC:11998", "target": "HGNC:990", "type": "REGULATES", "direction": "repression"},
            {"source": "CHEMBL:3137309", "target": "HGNC:990", "type": "INHIBITOR", "max_phase": 4}
        ]
    }),
    "source": "json",
    "group_id": "drug-repurposing"
}
await graphiti.add_memory(**graph_episode)
```

---

## Key Findings

### 1. MCP Strengths (Node Discovery)

| Skill | Strength | Gap |
|-------|----------|-----|
| HGNC | Perfect gene symbol resolution | - |
| UniProt | Rich functional text (mentions interactors) | No structured PPI |
| STRING | Confidence-scored PPI edges | No drug information |
| ChEMBL | Compound metadata, indications | mechanism API not exposed |
| Open Targets | Gene-disease associations | Requires Ensembl ID |

### 2. Curl Fills the Gaps (Edge Discovery)

| Gap | Curl Solution |
|-----|---------------|
| Drug → Target mechanism | ChEMBL `/mechanism` endpoint |
| Target → All drugs | ChEMBL `/mechanism?target_chembl_id=X` |
| Drug → Disease indication | ChEMBL `/drug_indication` endpoint |
| Gene → Literature evidence | NCBI elink to PubMed |

### 3. The Hybrid Pattern Works

```
MCP (Nodes)           Curl (Edges)              Graphiti (Persist)
    │                      │                         │
    ▼                      ▼                         ▼
[HGNC:TP53] ───────► [ChEMBL mechanism] ───────► [Knowledge Graph]
[UniProt:P04637]     [Open Targets GraphQL]
[CHEMBL:3137309]     [NCBI elink]
```

---

## Alternative Approaches (from API-Endpoint-Inventory-and-Research.md)

The comprehensive API research document reveals several **advanced endpoints** we didn't explore in the initial validation. These provide alternative graph construction patterns.

### Tier 3: Advanced APIs Not Yet Explored

| Edge Type | API | Endpoint | Value |
|-----------|-----|----------|-------|
| **Gene → Orthologs** | Ensembl | `/homology/id/:species/:id` | Evolutionary edges |
| **Variant → Consequences** | Ensembl VEP | `/vep/:species/hgvs` | Functional annotation |
| **SNP ↔ SNP (LD)** | Ensembl | `/ld/:species/pairwise/:id1/:id2` | GWAS fine-mapping |
| **Protein Set → Enrichment** | STRING | `/enrichment` | GO/KEGG/Reactome pathways |
| **Compound → Similar** | ChEMBL | `/similarity/{SMILES}/{threshold}` | Analog discovery |
| **Target → Tractability** | Open Targets | GraphQL `tractability` | Druggability assessment |
| **Gene → CRISPR Screens** | BioGRID ORCS | `/screen/{ID}` | Gene essentiality |
| **Bulk ID Mapping** | UniProt | `/idmapping/run` (async) | Cross-database translation |
| **Drug → Activity** | ChEMBL | `/activity?molecule_chembl_id={id}` | IC50, Ki, EC50 potency |

### Alternative Curl Commands

```bash
# 1. Ensembl Orthology (evolutionary edges)
curl -s "https://rest.ensembl.org/homology/id/human/ENSG00000141510?type=orthologues&content-type=application/json" \
  | jq '.data[0].homologies[:3][] | {species: .target.species, gene_id: .target.id}'

# 2. STRING Functional Enrichment (pathway context for protein sets)
curl -s "https://string-db.org/api/json/enrichment?identifiers=TP53,MDM2,ATM&species=9606" \
  | jq '.[:5][] | {term: .term, description: .description, p_value: .p_value}'

# 3. Open Targets Nested Query (target + drugs + diseases + tractability in one call)
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000141510\") { approvedSymbol tractability { label value } knownDrugs { rows { drug { name } mechanismOfAction } } } }"}' \
  "https://api.platform.opentargets.org/api/v4/graphql"

# 4. ChEMBL Activity Data (potency metrics)
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL3137309&format=json" \
  | jq '.activities[:3][] | {target: .target_pref_name, type: .standard_type, value: .standard_value, units: .standard_units}'

# 5. Ensembl Cross-References (comprehensive ID mapping)
curl -s "https://rest.ensembl.org/xrefs/id/ENSG00000141510?content-type=application/json" \
  | jq '.[] | select(.dbname | test("HGNC|UniProt|OMIM")) | {db: .dbname, id: .primary_id}'

# 6. UniProt Batch ID Mapping (async, up to 100K IDs)
curl -s "https://rest.uniprot.org/idmapping/run" \
  --form 'ids=P04637,P38398,P51587' \
  --form 'from=UniProtKB_AC-ID' \
  --form 'to=Ensembl'
```

### Architectural Pattern: NCBI History Server

The API document reveals NCBI's **stateful pipeline** pattern not used in our curl exploration:

```bash
# Pipeline: Search → Store on History Server → Link → Fetch
# Using EDirect (command-line wrapper for E-utilities)
esearch -db gene -query "TP53[sym] AND human[orgn]" \
  | elink -target pubmed -cmd neighbor_history \
  | efetch -format abstract -retmax 5
```

This enables chaining searches without re-transmitting UIDs - valuable for large-scale graph construction.

### Comparison: MCP vs Curl vs Advanced APIs

| Capability | MCP (Current) | Curl (Tier 2) | Advanced API (Tier 3) |
|------------|---------------|---------------|----------------------|
| Gene identity | ✅ HGNC | - | - |
| Protein details | ✅ UniProt | - | Batch ID mapping |
| PPI edges | ✅ STRING | - | Enrichment analysis |
| Drug-target edges | ❌ | ✅ ChEMBL mechanism | Activity data (IC50) |
| Gene-disease | ✅ Open Targets | - | Tractability + drugs |
| Evolutionary | ❌ | - | ✅ Ensembl homology |
| Variant annotation | ❌ | - | ✅ Ensembl VEP |
| GWAS LD | ❌ | - | ✅ Ensembl LD |
| Gene essentiality | ❌ | - | ✅ BioGRID ORCS |

---

## Recommendations

1. **Add ChEMBL mechanism endpoint to MCP** - Most valuable missing edge
2. **Expose drug_indication as MCP tool** - Completes drug→disease traversal
3. **Add STRING enrichment endpoint** - Provides pathway context for protein sets
4. **Add Ensembl homology endpoint** - Evolutionary edges for comparative analysis
5. **Create orchestration examples** - Document the TP53→BCL2→Venetoclax pattern
6. **Graphiti integration** - Persist validated subgraphs for RAG retrieval
7. **Explore Open Targets nested GraphQL** - One call for target+drugs+diseases+tractability
8. **Consider Ensembl VEP** - For variant annotation workflows

---

## Appendix: Raw Validation Data

### TP53 Gene Record (HGNC)
```json
{
  "id": "HGNC:11998",
  "symbol": "TP53",
  "name": "tumor protein p53",
  "location": "17p13.1",
  "cross_references": {
    "ensembl_gene": "ENSG00000141510",
    "uniprot": ["P04637"],
    "entrez": "7157",
    "omim": "191170"
  }
}
```

### UniProt Function Extract
> "Apoptosis induction seems to be mediated either by stimulation of **BAX** and **FAS** antigen expression, or by repression of **Bcl-2** expression."

### STRING Top Interactions
| Partner | Score | Evidence |
|---------|-------|----------|
| MDM2 | 0.999 | escore=0.886, dscore=0.9, tscore=0.99 |
| SIRT1 | 0.999 | escore=0.886, dscore=0.9, tscore=0.99 |
| RPA1 | 0.999 | escore=0.982, dscore=0.4, tscore=0.932 |
| ATM | 0.995 | dscore=0.75, tscore=0.955 |

### Venetoclax Complete Record
```json
{
  "id": "CHEMBL:3137309",
  "name": "VENETOCLAX",
  "max_phase": 4,
  "mechanism": "Apoptosis regulator Bcl-2 inhibitor",
  "indications": ["CLL", "Multiple Myeloma", "NHL", "AML", ...]
}
```
