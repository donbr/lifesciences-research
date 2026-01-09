# Competency Questions Catalog

**Purpose**: Research questions for building knowledge graphs using the `lifesciences-graph-builder` skill.

**Target**: Use `graphiti-docker` for development/testing. Only use `graphiti-aura` for curated production graphs.

---

## Scenarios

### Scenario 1: Synthetic Lethality

**Question**: How can we identify therapeutic strategies for ARID1A-deficient Ovarian Cancer using synthetic lethality?

**Key Entities**:
| Entity | CURIE | Role |
|--------|-------|------|
| ARID1A | HGNC:11110 | Tumor suppressor (SWI/SNF) |
| EZH2 | HGNC:3527 | Synthetic lethal partner (PRC2) |
| ATR | HGNC:882 | Synthetic lethal partner |
| Tazemetostat | CHEMBL:3414621 | EZH2 inhibitor (FDA approved) |
| NCT03348631 | NCT:03348631 | Phase 2 trial |

**Workflow**:
1. **Anchor**: `hgnc_search_genes("ARID1A")` → HGNC:11110
2. **Enrich**: `uniprot_get_protein("UniProtKB:O14497")` → SWI/SNF function
3. **Expand**: `string_get_interactions()` → SWI/SNF complex members
4. **Traverse**: `chembl_search_compounds("tazemetostat")` → CHEMBL:3414621
5. **Validate**: curl ChEMBL /mechanism → EZH2 inhibitor
6. **Persist**: `mcp__graphiti-docker__add_memory(group_id="scenario1-synthetic-lethality")`

**Source Documentation**: `docs/scenarios/scenario1-walkthrough.md`

**Target group_id**: `scenario1-synthetic-lethality`

---

### Scenario 2: Drug Safety Profiling

**Question**: What are the off-target risks of Dasatinib, specifically cardiotoxicity from hERG (KCNH2) and DDR2 activity?

**Key Entities**:
| Entity | CURIE | Role |
|--------|-------|------|
| Dasatinib | CHEMBL:1421 | Index compound |
| Imatinib | CHEMBL:941 | Cleaner alternative |
| ABL1 | CHEMBL:1862 | Primary target |
| DDR2 | CHEMBL:5122 | Off-target (pleural effusion) |
| hERG/KCNH2 | HGNC:6251 | Safety target (cardiotoxicity) |

**Workflow**:
1. **Anchor**: `chembl_search_compounds("dasatinib")` → CHEMBL:1421
2. **Mechanisms**: curl ChEMBL /mechanism → ABL1, PDGFR, KIT targets
3. **Activity**: curl ChEMBL /activity → IC50 values vs DDR2
4. **Compare**: `chembl_search_compounds("imatinib")` → cleaner profile
5. **Safety Genes**: `hgnc_search_genes("KCNH2")` → HGNC:6251
6. **Persist**: `mcp__graphiti-docker__add_memory(group_id="scenario2-safety-profile")`

**Source Documentation**: `docs/scenarios/scenario2-walkthrough.md`

**Target group_id**: `scenario2-safety-profile`

---

### Scenario 3: Orphan Drug Discovery

**Question**: What novel therapeutic targets exist for Huntington's Disease that are not covered by current Phase 3 interventions?

**Key Entities**:
| Entity | CURIE | Role |
|--------|-------|------|
| HTT | HGNC:4851 | Causal gene |
| SLC18A2/VMAT2 | CHEMBL:1893 | Current target (covered) |
| Tetrabenazine | CHEMBL:117785 | Approved drug |
| SLC2A3/GLUT3 | ENSG00000059804 | Novel target opportunity |

**Workflow**:
1. **Anchor**: `hgnc_search_genes("HTT")` → HGNC:4851
2. **Trial Landscape**: curl ClinicalTrials.gov → Phase 3 trials
3. **Drug Mechanisms**: curl ChEMBL /mechanism → VMAT2 inhibitors
4. **Gap Analysis**: `opentargets_get_associations()` → ranked targets
5. **Find Novel**: Filter for targets with no drug coverage
6. **Persist**: `mcp__graphiti-docker__add_memory(group_id="scenario3-huntington-sprint")`

**Source Documentation**: `docs/scenarios/scenario3-huntington-orphan-drug.md`

**Target group_id**: `scenario3-huntington-sprint`

---

### Scenario 4: Pathway Validation

**Question**: How do we build and validate a knowledge graph for the p53-MDM2-Nutlin therapeutic axis?

**Key Entities**:
| Entity | CURIE | Role |
|--------|-------|------|
| TP53 | HGNC:11998 | Tumor suppressor |
| MDM2 | HGNC:6973 | Oncogene (E3 ligase) |
| Nutlin-3 | CHEMBL:191334 | MDM2 inhibitor |

**Workflow**:
1. **Anchor**: `hgnc_search_genes("TP53")` → HGNC:11998
2. **Partner**: `hgnc_search_genes("MDM2")` → HGNC:6973
3. **Interactions**: `string_get_interactions()` → TP53-MDM2 (score 0.999)
4. **Drug**: `chembl_search_compounds("Nutlin-3")` → CHEMBL:191334
5. **Mechanism**: curl ChEMBL /mechanism → MDM2 inhibitor
6. **Persist**: `mcp__graphiti-docker__add_memory(group_id="oncology-demo")`

**Source Documentation**: `docs/scenarios/scenario4-p53-mdm2-nutlin.md`

**Target group_id**: `oncology-demo`

---

## Research Reports

### Research 1: Health Emergencies 2026

**Question**: What are the key health emergencies or emerging health priorities that multiple clinical trials are targeting right now?

**Key Findings**:
- Cancer: 21,584 recruiting trials (immunotherapy revolution)
- Metabolic epidemic: 5,552 trials (GLP-1 transformation)
- Long COVID: 186 trials (emerging chronic disease)
- Alzheimer's: 617 trials (neuromodulation renaissance)
- AI/Digital Health: 932 trials (cross-cutting platform)

**Workflow**:
1. **Disease Discovery**: `clinicaltrials_search_trials()` → parallel searches by disease
2. **Innovation Discovery**: Search CAR-T, GLP-1, immunotherapy, AI trials
3. **Pattern Analysis**: Identify therapeutic convergence across diseases
4. **Persist**: `mcp__graphiti-docker__add_memory(group_id="health-emergencies-2026")`

**Source Documentation**: `docs/research-reports/health-emergencies-2026-analysis.md`

**Target group_id**: `health-emergencies-2026`

---

### Research 2: High-Commercialization Trials

**Question**: Which clinical trials have the highest potential for commercialization or are attracting the most investment interest?

**Key Findings**:
1. **Retatrutide** (NCT:07232719) - Eli Lilly - Obesity - VERY HIGH potential
2. **Sacituzumab Govitecan** (NCT:06486441) - Gilead - Endometrial Cancer - HIGH potential
3. **Ficerafusp Alfa** (NCT:06788990) - Bicara - Head & Neck Cancer - MODERATE-HIGH (acquisition target)

**Workflow**:
1. **Trial Discovery**: `clinicaltrials_search_trials(phase="PHASE3", status="RECRUITING")`
2. **Drug Identification**: `chembl_search_compounds()` → CURIEs
3. **Mechanism Extraction**: curl ChEMBL /mechanism → Drug→Target edges
4. **Target Validation**: `opentargets_get_associations()` → disease associations
5. **Persist**: `mcp__graphiti-docker__add_memory(group_id="high-commercialization-trials")`

**Source Documentation**: `docs/research-reports/high-commercialization-trials-research.md`

**Target group_id**: `high-commercialization-trials`

---

### Research 3: CAR-T Regulatory Landscape

**Question**: Which CAR-T cell trials are currently navigating FDA or EMA milestones most rapidly? What regulatory hurdles are emerging in personalized medicine?

**Key Findings**:
- 324 trials analyzed (27 Phase 3, 297 Phase 2)
- Top velocity trials: ENACT-2, ABALL2, HebeCART, CALM, NXC-201
- Regulatory patterns: FDA breakthrough designation, EMA PRIME pathway

**Workflow**:
1. **Trial Search**: `clinicaltrials_search_trials("CAR-T cell therapy", phase="PHASE3")`
2. **Protocol Analysis**: `clinicaltrials_get_trial()` → sponsor, timeline, endpoints
3. **Drug Mechanisms**: `chembl_search_compounds()` + curl /mechanism
4. **Regulatory Signals**: Extract FDA/EMA designations from trial data
5. **Persist**: `mcp__graphiti-docker__add_memory(group_id="car-t-regulatory-landscape")`

**Source Documentation**: `docs/research-reports/car-t-regulatory-landscape.md`

**Target group_id**: `car-t-regulatory-landscape`

---

## Re-run Instructions

### Using the lifesciences-graph-builder Skill

To re-run any competency question:

1. **Invoke the skill**:
   ```
   "Build a knowledge graph for [competency question]"
   ```

2. **Follow the 5-phase Fuzzy-to-Fact protocol**:
   - Phase 1: Anchor Node (naming)
   - Phase 2: Enrich Node (functional)
   - Phase 3: Expand Edges (interactions)
   - Phase 4: Target Traversal (pharma)
   - Phase 5: Persist Graph

3. **Target graphiti-docker**:
   ```python
   mcp__graphiti-docker__add_memory(
       name="[Episode Name]",
       episode_body=json.dumps({"nodes": [...], "edges": [...]}),
       source="json",
       group_id="[target group_id]"
   )
   ```

### Graphiti Instance Selection

| Context | MCP Tool | group_id Pattern |
|---------|----------|------------------|
| **Development/Testing** | `mcp__graphiti-docker__add_memory()` | `scenario*`, `dev-*`, `test-*` |
| **Production** | `mcp__graphiti-aura__add_memory()` | `graphiti_*`, curated namespaces |

**Default**: Use `graphiti-docker` for all scenario work and research exploration.

---

## Quick Reference

| # | Category | Question Summary | group_id |
|---|----------|------------------|----------|
| 1 | Synthetic Lethality | ARID1A-deficient Ovarian Cancer | `scenario1-synthetic-lethality` |
| 2 | Drug Safety | Dasatinib off-target risks | `scenario2-safety-profile` |
| 3 | Orphan Drug | Huntington's novel targets | `scenario3-huntington-sprint` |
| 4 | Pathway Validation | p53-MDM2-Nutlin axis | `oncology-demo` |
| 5 | Health Emergencies | 2026 clinical trial priorities | `health-emergencies-2026` |
| 6 | Commercialization | High-investment Phase 3 trials | `high-commercialization-trials` |
| 7 | CAR-T Regulatory | FDA/EMA milestone velocity | `car-t-regulatory-landscape` |

---

**Last Updated**: 2026-01-09
