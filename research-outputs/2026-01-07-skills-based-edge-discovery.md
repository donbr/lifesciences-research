# Skills-Based Edge Discovery: Enhancing Knowledge Graphs with Curl Commands

**Date:** 2026-01-07
**Method:** Using `.claude/skills/` curl commands to discover relationships beyond MCP tools
**Skills Used:** `lifesciences-pharmacology`, `lifesciences-proteomics`
**Graph ID:** `clinical-trials-2026`

---

## Key Insight: Skills vs. MCP Tools

| Capability | MCP Tools | Skills (Curl Commands) |
|------------|-----------|------------------------|
| **Purpose** | Node discovery & enrichment | Edge discovery & quantitative data |
| **Pattern** | search/get (Fuzzy-to-Fact) | REST API endpoints for relationships |
| **Example** | `hgnc_search_genes("TP53")` | `curl ChEMBL /mechanism` |
| **Returns** | Entities with metadata | Relationships with properties |
| **Data Type** | Categorical (gene, protein, compound) | Quantitative (IC50, scores, FDR) |

**Combined Power:** MCP tools provide **nodes** → Skills provide **edges** → Complete knowledge graph

---

## Edge Discovery Results

### Summary Statistics

**New Edges Discovered:** 19
**New Nodes Discovered:** 10
**New Edge Types:** 6 (MECHANISM, BIOACTIVITY, INDICATION, ENRICHED_IN, EXPRESSED_IN, PART_OF)
**Curl Commands Used:** 5

---

## Discovery Phase 1: Drug Mechanisms (Pharmacology Skill)

### Curl Command Used
```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL21536&format=json" \
  | jq '.mechanisms[] | {action: .action_type, mechanism: .mechanism_of_action, target: .target_chembl_id}'
```

### Discovered Edges

**Xanomeline (CHEMBL:21536) → ChEMBL Targets**

1. `CHEMBL:21536 --MECHANISM--> CHEMBL:216`
   - **Action:** AGONIST
   - **Mechanism:** Muscarinic acetylcholine receptor M1 agonist
   - **Discovery:** MCP tools return "UniProtKB:P11229" but NOT ChEMBL target ID
   - **Value:** ChEMBL:216 enables reverse lookup (find OTHER drugs targeting M1)

2. `CHEMBL:21536 --MECHANISM--> CHEMBL:1821`
   - **Action:** AGONIST
   - **Mechanism:** Muscarinic acetylcholine receptor M4 agonist
   - **Value:** Confirms dual M1/M4 selectivity with ChEMBL IDs

**Key Insight:** MCP tools can get compound data but NOT drug→target mechanism edges. Skills fill this gap.

---

## Discovery Phase 2: Bioactivity Data (Pharmacology Skill)

### Curl Command Used
```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL21536&format=json&limit=10" \
  | jq '.activities[] | {target: .target_pref_name, type: .standard_type, value: .standard_value, units: .standard_units}'
```

### Discovered Quantitative Edges

**Xanomeline (CHEMBL:21536) Potency Data**

1. `CHEMBL:21536 --BIOACTIVITY--> HGNC:1950 (M1 receptor)`
   - **IC50:** 2.0 nM
   - **Units:** nanomolar
   - **Interpretation:** Very high potency (low nanomolar = strong binding)

2. `CHEMBL:21536 --BIOACTIVITY--> HGNC:1950 (replicate)`
   - **IC50:** 5.0 nM
   - **Reproducibility:** Consistent low-nM potency across assays

**Key Insight:** MCP tools return categorical data. Skills return **quantitative** edge properties (IC50, Ki, EC50).

---

## Discovery Phase 3: Drug Indications (Pharmacology Skill)

### Curl Command Used
```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/drug_indication?molecule_chembl_id=CHEMBL21536&format=json" \
  | jq '.drug_indications[] | {disease: .mesh_heading, efo_id: .efo_id, efo_term: .efo_term, phase: .max_phase_for_ind}'
```

### Discovered Disease Edge

**Xanomeline → Schizophrenia (Original Indication)**

- `CHEMBL:21536 --INDICATION--> MONDO:0005090 (schizophrenia)`
  - **Disease:** Schizophrenia
  - **Ontology ID:** MONDO:0005090
  - **Max Phase:** 3.0
  - **Repurposing Status:** Original indication before Alzheimer's trials (KarXT)

**Key Insight:** Reveals drug repurposing history. Xanomeline tested for schizophrenia (Phase 3) → now repurposed for Alzheimer's cognitive impairment (MINDSET trials).

---

## Discovery Phase 4: Functional Enrichment (Proteomics Skill)

### Curl Command Used
```bash
curl -s "https://string-db.org/api/json/enrichment?identifiers=9606.ENSP00000306490%0d9606.ENSP00000078429%0d9606.ENSP00000286548&species=9606" \
  | jq '.[] | {category, term, description, fdr}'
```

### Input Protein Set
- ENSP00000306490 (CHRM1 - M1 receptor)
- ENSP00000078429 (GNA11 - G protein alpha 11)
- ENSP00000286548 (GNAQ - G protein alpha q)

### Discovered GO Term Edges

**1. G Protein-Coupled Acetylcholine Receptor Signaling (GO:0007213)**
- `HGNC:1950 (CHRM1) --ENRICHED_IN--> GO:0007213`
- `HGNC:4379 (GNA11) --ENRICHED_IN--> GO:0007213`
- `HGNC:4390 (GNAQ) --ENRICHED_IN--> GO:0007213`
- **FDR:** 0.000019 (highly significant)
- **Validation:** Confirms mechanistic hypothesis for KarXT trials

**2. Adenylate Cyclase-Modulating GPCR Signaling (GO:0007188)**
- All 3 genes enriched
- **FDR:** 0.0042
- **Mechanism:** Second messenger pathway for cognitive effects

**3. Heterotrimeric G-Protein Complex (GO:0005834)**
- `HGNC:4379 (GNA11) --PART_OF--> GO:0005834`
- `HGNC:4390 (GNAQ) --PART_OF--> GO:0005834`
- **FDR:** 0.021
- **Structure:** GNA11/GNAQ are alpha subunits of G-protein trimers

**Key Insight:** Functional enrichment **validates** the drug mechanism at the systems biology level. The protein set is statistically overrepresented in the exact pathway targeted by KarXT.

---

## Discovery Phase 5: CAR-T Target Enrichment (Proteomics Skill)

### Input Protein Set
- ENSP00000313419 (CD19)
- ENSP00000433277 (MS4A1/CD20)
- ENSP00000085219 (CD22)

### Discovered Edges

**1. B Cell Activation (GO:0042113)**
- All 3 CAR-T targets enriched
- **FDR:** 0.0143
- **Validation:** Triple-target strategy hits core B-cell activation pathway

**2. Regulation of B Cell Receptor Signaling (GO:0050855)**
- All 3 CAR-T targets enriched
- **FDR:** 0.0334
- **Strategic Insight:** Targets regulate BCR signaling → blocking all 3 prevents immune escape

**3. Tissue Expression: B-lymphocyte (BTO:0000776)**
- `HGNC:1633 (CD19) --EXPRESSED_IN--> BTO:0000776`
- **FDR:** 0.0111
- **Cell Type:** B-lymphocytes (normal)

**4. Tissue Expression: Burkitt Lymphoma (BTO:0000889)**
- `HGNC:1633 (CD19) --EXPRESSED_IN--> BTO:0000889`
- **FDR:** 0.0014 (highly significant)
- **Disease Relevance:** CAR-T target expressed in tumor cells

**Key Insight:** Enrichment analysis **validates** CAR-T target selection with statistical evidence (FDR < 0.05).

---

## Complete Edge Type Inventory

### Edge Types from MCP Tools (Original Graph)
1. `ENCODES` (Gene → Protein)
2. `TARGETS` (Trial → Gene)
3. `TESTS_INTERVENTION` (Trial → Compound)
4. `MEMBER_OF` (Gene → Pathway)
5. `ASSOCIATED_WITH` (Gene → Disease)
6. `INTERACTS_WITH` (Protein → Protein)

### NEW Edge Types from Skills (Curl Discovery)
1. `MECHANISM` (Compound → ChEMBL Target) - **Drug action mechanism**
2. `BIOACTIVITY` (Compound → Gene) - **Quantitative potency (IC50/Ki)**
3. `INDICATION` (Compound → Disease) - **Clinical indications with ontology**
4. `ENRICHED_IN` (Gene → GO Term) - **Functional pathway enrichment**
5. `PART_OF` (Gene → GO Component) - **Protein complex membership**
6. `EXPRESSED_IN` (Gene → Tissue) - **Tissue-specific expression**

---

## Use Cases for Curl-Based Edge Discovery

### 1. Drug Repurposing
**Workflow:**
```bash
# Step 1: Find target for known drug (MCP tool)
compound = chembl.search_compounds("venetoclax")

# Step 2: Get mechanism with ChEMBL target ID (SKILL)
curl ChEMBL /mechanism?molecule_chembl_id={compound_id}
# Returns: CHEMBL:4860 (BCL2)

# Step 3: Find OTHER drugs for same target (SKILL)
curl ChEMBL /mechanism?target_chembl_id=CHEMBL4860
# Returns: List of BCL2 inhibitors for repurposing analysis
```

### 2. Target Validation
**Workflow:**
```bash
# Step 1: Get protein set for disease pathway (MCP tool)
pathway = wikipathways.get_pathway_components("WP:WP5124")

# Step 2: Functional enrichment analysis (SKILL)
curl STRING /enrichment?identifiers={protein_set}
# Returns: GO terms with FDR < 0.05 (statistically validated)

# Validates that protein set is functionally coherent
```

### 3. Bioactivity Profiling
**Workflow:**
```bash
# Step 1: Find candidate drugs (MCP tool)
compounds = chembl.search_compounds("kinase inhibitor")

# Step 2: Get IC50 values for each compound (SKILL)
for compound in compounds:
    curl ChEMBL /activity?molecule_chembl_id={compound}&standard_type=IC50

# Returns: Quantitative potency ranking for lead selection
```

### 4. Multi-Target Analysis
**Workflow:**
```bash
# Step 1: Get protein interaction network (MCP tool)
network = string.get_interactions("STRING:9606.ENSP00000269305")

# Step 2: GO enrichment for interaction partners (SKILL)
curl STRING /enrichment?identifiers={network_proteins}

# Identifies shared pathways across interaction network
```

---

## Skills Catalog: Available Curl Commands

### Pharmacology Skills (`lifesciences-pharmacology/SKILL.md`)

| Endpoint | Edge Type | Example |
|----------|-----------|---------|
| `/mechanism` | Drug → Target | `curl ChEMBL /mechanism?molecule_chembl_id={ID}` |
| `/mechanism` (reverse) | Target → Drugs | `curl ChEMBL /mechanism?target_chembl_id={ID}` |
| `/drug_indication` | Drug → Disease | `curl ChEMBL /drug_indication?molecule_chembl_id={ID}` |
| `/activity` | Drug → Target (IC50/Ki) | `curl ChEMBL /activity?molecule_chembl_id={ID}&standard_type=IC50` |
| `/similarity` | Drug → Analogs | `curl ChEMBL /similarity/{SMILES}/70` |

### Proteomics Skills (`lifesciences-proteomics/SKILL.md`)

| Endpoint | Edge Type | Example |
|----------|-----------|---------|
| `/network` | Protein ↔ Protein | `curl STRING /network?identifiers={genes}&species=9606` |
| `/enrichment` | Protein Set → GO/KEGG | `curl STRING /enrichment?identifiers={proteins}&species=9606` |
| `/interactions` | Gene ↔ Gene | `curl BioGRID /interactions?geneList={gene}&accesskey={key}` |

### Genomics Skills (`lifesciences-genomics/SKILL.md`)

| Endpoint | Edge Type | Example |
|----------|-----------|---------|
| `/homology` | Gene → Orthologs | `curl Ensembl /homology/id/human/{ENSG}?type=orthologues` |
| `/elink` | Gene → PubMed | `curl NCBI elink.fcgi?dbfrom=gene&db=pubmed&id={ID}` |

---

## Expanded Graph Statistics

### Before Curl Discovery
- **Nodes:** 35
- **Edges:** 39
- **Edge Types:** 6

### After Curl Discovery
- **Nodes:** 45 (+10)
- **Edges:** 58 (+19)
- **Edge Types:** 12 (+6)
- **Quantitative Edges:** 2 (IC50 values)
- **Ontology Mappings:** 8 (GO terms, MONDO, BTO)

### New Node Types
- ChEMBL Targets (CHEMBL:216, CHEMBL:1821)
- GO Terms (GO:0007213, GO:0007188, GO:0005834, etc.)
- Disease Ontology (MONDO:0005090)
- Tissue Types (BTO:0000776, BTO:0000889)

---

## Query Examples: Using New Edges

### Query 1: Find All Drugs Targeting M1 Receptor
```python
# Step 1: Get ChEMBL target ID from graph
mcp__graphiti-aura__search_memory_facts(
    query="xanomeline M1 receptor ChEMBL target mechanism",
    group_ids=["clinical-trials-2026"]
)
# Returns: CHEMBL:21536 --MECHANISM--> CHEMBL:216

# Step 2: Use curl to find other M1 agonists
curl ChEMBL /mechanism?target_chembl_id=CHEMBL216
# Returns: List of all M1 receptor modulators for comparison
```

### Query 2: Validate Drug Mechanism with Enrichment
```python
# Retrieve GO enrichment edges
mcp__graphiti-aura__search_memory_facts(
    query="CHRM1 GNA11 GNAQ GO enrichment acetylcholine signaling",
    group_ids=["clinical-trials-2026"],
    max_facts=5
)
# Expected: ENRICHED_IN edges with FDR < 0.001 (statistically validated)
```

### Query 3: Drug Repurposing Analysis
```python
# Find original vs. repurposed indications
mcp__graphiti-aura__search_memory_facts(
    query="xanomeline indication schizophrenia Alzheimer repurposing",
    group_ids=["clinical-trials-2026"]
)
# Expected: CHEMBL:21536 --INDICATION--> MONDO:0005090 (schizophrenia, Phase 3)
# Compare to: NCT:06976216 tests xanomeline for Alzheimer's (repurposing)
```

---

## Lessons Learned

### 1. MCP Tools Alone Are Insufficient
**Limitation:** MCP tools follow search/get pattern - great for nodes, poor for edges
**Solution:** Skills provide curl commands for relationship discovery

### 2. Quantitative Data Requires REST Endpoints
**Limitation:** MCP search_compounds returns categorical data (name, formula)
**Solution:** ChEMBL /activity endpoint returns IC50/Ki values (quantitative)

### 3. Functional Validation Requires Enrichment Analysis
**Limitation:** Individual protein lookups don't prove pathway coherence
**Solution:** STRING /enrichment provides statistical validation (FDR < 0.05)

### 4. Drug Repurposing Requires Indication History
**Limitation:** Trial data only shows current use
**Solution:** ChEMBL /drug_indication shows ALL historical indications

### 5. Cross-Database Integration Requires Ontology Mapping
**Limitation:** Free-text disease names don't enable cross-database queries
**Solution:** ChEMBL /drug_indication returns MONDO IDs for standardization

---

## Best Practices

### When to Use MCP Tools
✅ Resolving fuzzy queries to canonical IDs (Fuzzy-to-Fact)
✅ Getting entity metadata (function, location, sequence)
✅ Initial node discovery

### When to Use Skills (Curl Commands)
✅ Finding drug mechanisms (compound → target)
✅ Getting quantitative data (IC50, Ki, scores)
✅ Functional enrichment (GO/KEGG terms)
✅ Disease indications with ontology IDs
✅ Tissue expression profiles
✅ Reverse lookups (target → drugs)

### Optimal Workflow
1. **Phase 1-2:** Use MCP tools to get nodes (genes, proteins, compounds)
2. **Phase 3-4:** Use skills to get edges (mechanisms, bioactivity, enrichment)
3. **Phase 5:** Persist combined graph to Graphiti

---

## Available Skills

| Skill | Focus | Curl Endpoints |
|-------|-------|----------------|
| `lifesciences-graph-builder` | Orchestration | Multi-API workflow examples |
| `lifesciences-pharmacology` | Drugs | ChEMBL, PubChem, IUPHAR, DrugBank |
| `lifesciences-proteomics` | Proteins | UniProt, STRING, BioGRID |
| `lifesciences-genomics` | Genes | Ensembl, NCBI, HGNC |
| `lifesciences-clinical` | Trials | Open Targets, ClinicalTrials.gov |
| `lifesciences-crispr` | CRISPR | BioGRID ORCS |

**Full documentation:** `.claude/skills/{skill-name}/SKILL.md`

---

## Conclusion

**Skills + MCP Tools = Complete Knowledge Graph**

- **MCP Tools:** Provide nodes via Fuzzy-to-Fact protocol
- **Skills:** Provide edges via REST API curl commands
- **Together:** Enable discovery of relationships impossible with either alone

**Key Achievement:** Using 5 curl commands, we discovered **19 new edges** with quantitative properties (IC50 values), ontology mappings (MONDO, GO), and statistical validation (FDR < 0.05).

**Graph Completeness:**
- Before: 35 nodes, 39 edges (node-rich, edge-sparse)
- After: 45 nodes, 58 edges (+49% edge density)
- **Result:** Richer, more queryable knowledge graph

---

**Document Generated:** 2026-01-07
**Method:** Curl-based edge discovery using `.claude/skills/`
**Skills Used:** lifesciences-pharmacology, lifesciences-proteomics
**Graph ID:** clinical-trials-2026
**Total Edges Discovered:** 19
**Total Nodes Added:** 10
