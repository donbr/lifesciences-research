# Enhanced Edge Discovery: CAR T-Cell Target Validation via Platform Skills

**Research Question**: Which CAR T-cell trials are currently navigating FDA or EMA milestones most rapidly? What regulatory hurdles are emerging in the field of personalized medicine in these different regions?

**Enhancement Objective**: Use platform skills (curl endpoints) to discover drug-target mechanisms, target tractability, and clinical precedence relationships that validate regulatory decisions and predict approval timelines.

**Date**: 2026-01-07
**Method**: Fuzzy-to-Fact Protocol + Platform Skills (lifesciences-pharmacology, lifesciences-clinical, lifesciences-proteomics)

---

## Research Hypothesis

**Hypothesis**: Trials targeting proteins with:
1. **High tractability** (antibody-druggable)
2. **Clinical precedence** (existing approved drugs)
3. **Strong drug-target mechanisms** (validated MOAs)

...will navigate FDA/EMA milestones faster due to **reduced regulatory uncertainty**.

**Prediction**: CD20 (MS4A1) and BCMA (TNFRSF17) targets should show strong clinical precedence, while GPRC5D (novel target) should show lower precedence but acceptable tractability.

---

## Phase 1: Target Tractability Assessment (Open Targets GraphQL)

**Objective**: Determine which CAR-T targets are druggable via antibodies (validates CAR-T as therapeutic modality).

**Hypothesis**: All CAR-T targets should show antibody tractability, as CAR-T is essentially an antibody-engineered T-cell.

### 1.1 CD19 Tractability

**Query Execution**:
```bash
# Query Open Targets for CD19 tractability
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000177455\") { approvedSymbol tractability { label modality value } } }"}' \
  | jq '.data.target'
```

**Results**: [TO BE POPULATED]

---

### 1.2 MS4A1/CD20 Tractability

**Query Execution**:
```bash
# Query Open Targets for CD20 tractability
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000156738\") { approvedSymbol tractability { label modality value } knownDrugs(page: {size: 10}) { rows { drug { name } phase mechanismOfAction } } } }"}' \
  | jq '.data.target'
```

**Results**: [TO BE POPULATED]

---

### 1.3 TNFRSF17/BCMA Tractability

**Query Execution**:
```bash
# Query Open Targets for BCMA tractability + known drugs
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000048462\") { approvedSymbol tractability { label modality value } knownDrugs(page: {size: 10}) { rows { drug { name } phase mechanismOfAction } } } }"}' \
  | jq '.data.target'
```

**Results**: [TO BE POPULATED]

---

### 1.4 GPRC5D Tractability (Novel Target)

**Query Execution**:
```bash
# Query Open Targets for GPRC5D tractability
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000111291\") { approvedSymbol tractability { label modality value } knownDrugs(page: {size: 5}) { rows { drug { name } phase mechanismOfAction } } } }"}' \
  | jq '.data.target'
```

**Results**: [TO BE POPULATED]

---

## Phase 2: Drug-Target Mechanism Discovery (ChEMBL)

**Objective**: Identify approved/clinical drugs targeting CAR-T antigens to establish clinical precedence.

**Regulatory Relevance**: Existing drugs validate target safety/efficacy, reducing regulatory risk for CAR-T trials.

### 2.1 Find ChEMBL Target IDs

**Query Execution**:
```bash
# Search ChEMBL for CD19 target
curl -s "https://www.ebi.ac.uk/chembl/api/data/target/search?q=CD19&format=json" \
  | jq '.targets[:3][] | {id: .target_chembl_id, name: .pref_name, type: .target_type, organism: .organism}'
```

**Results**: [TO BE POPULATED]

---

```bash
# Search ChEMBL for CD20/MS4A1 target
curl -s "https://www.ebi.ac.uk/chembl/api/data/target/search?q=CD20&format=json" \
  | jq '.targets[:3][] | {id: .target_chembl_id, name: .pref_name, type: .target_type, organism: .organism}'
```

**Results**: [TO BE POPULATED]

---

```bash
# Search ChEMBL for BCMA target
curl -s "https://www.ebi.ac.uk/chembl/api/data/target/search?q=BCMA&format=json" \
  | jq '.targets[:3][] | {id: .target_chembl_id, name: .pref_name, type: .target_type}'
```

**Results**: [TO BE POPULATED]

---

### 2.2 Drug Mechanisms Targeting CD20

**Query Execution**:
```bash
# Get all drugs targeting CD20 (rituximab, ofatumumab, etc.)
# Using placeholder CHEMBL ID - will update after 2.1 completes
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?target_chembl_id=CHEMBL1743050&format=json" \
  | jq '.mechanisms[:10][] | {drug_id: .molecule_chembl_id, drug_name: .molecule_pref_name, action: .action_type, mechanism: .mechanism_of_action}'
```

**Results**: [TO BE POPULATED]

---

### 2.3 Rituximab Drug Indications (CD20 antibody precedent)

**Query Execution**:
```bash
# Get approved indications for rituximab
curl -s "https://www.ebi.ac.uk/chembl/api/data/drug_indication?molecule_chembl_id=CHEMBL1201828&format=json" \
  | jq '.drug_indications[:10][] | {disease: .mesh_heading, efo: .efo_term, phase: .max_phase_for_ind}'
```

**Results**: [TO BE POPULATED]

---

## Phase 3: Functional Enrichment of Interaction Networks (STRING)

**Objective**: Discover GO terms and pathways enriched in CAR-T target interaction networks.

**Regulatory Relevance**: Pathway enrichment reveals off-target risks (e.g., immune suppression pathways).

### 3.1 CD19 Interaction Network Enrichment

**Query Execution**:
```bash
# Get STRING IDs for CD19 + top interactors (CD22, CD79A, LYN)
curl -s "https://string-db.org/api/json/get_string_ids?identifiers=CD19%0dCD22%0dCD79A%0dLYN%0dCD79B&species=9606&limit=1" \
  | jq '.[] | {query: .preferredName, stringId}'
```

**Results**: [TO BE POPULATED]

---

```bash
# Functional enrichment for CD19 network
curl -s "https://string-db.org/api/json/enrichment?identifiers=9606.ENSP00000313419%0d9606.ENSP00000085219%0d9606.ENSP00000221972%0d9606.ENSP00000428924%0d9606.ENSP00000376544&species=9606" \
  | jq '.[0:15] | .[] | {category, term, description, fdr, genes: .inputGenes}'
```

**Results**: [TO BE POPULATED]

---

### 3.2 BCMA Interaction Network Enrichment

**Query Execution**:
```bash
# Functional enrichment for BCMA network (TNFSF13B, TNFSF13, MZB1, TNFRSF13B)
curl -s "https://string-db.org/api/json/enrichment?identifiers=9606.ENSP00000053243%0d9606.ENSP00000365048%0d9606.ENSP00000343505%0d9606.ENSP00000303920%0d9606.ENSP00000261652&species=9606" \
  | jq '.[0:15] | .[] | {category, term, description, fdr, genes: .inputGenes}'
```

**Results**: [TO BE POPULATED]

---

## Phase 4: Evidence Breakdown for Target-Disease Associations

**Objective**: Decompose Open Targets association scores into evidence types (genetic, somatic, known_drug, pathway).

**Regulatory Relevance**: Strong "known_drug" evidence = clinical precedence → faster regulatory approval.

### 4.1 CD19-DLBCL Evidence Breakdown

**Query Execution**:
```bash
# Get evidence type scores for DLBCL (EFO_0000403)
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ disease(efoId: \"EFO_0000403\") { name associatedTargets(page: {size: 10}) { rows { target { approvedSymbol id } score datatypeScores { id score } } } } }"}' \
  | jq '.data.disease.associatedTargets.rows[] | select(.target.approvedSymbol == "CD19") | {target: .target.approvedSymbol, overall: .score, evidence: .datatypeScores}'
```

**Results**: [TO BE POPULATED]

---

### 4.2 BCMA-Multiple Myeloma Evidence Breakdown

**Query Execution**:
```bash
# Get evidence type scores for Multiple Myeloma (EFO_0001378)
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ disease(efoId: \"EFO_0001378\") { name associatedTargets(page: {size: 10}) { rows { target { approvedSymbol id } score datatypeScores { id score } } } } }"}' \
  | jq '.data.disease.associatedTargets.rows[] | select(.target.approvedSymbol == "TNFRSF17") | {target: .target.approvedSymbol, overall: .score, evidence: .datatypeScores}'
```

**Results**: [TO BE POPULATED]

---

### 4.3 GPRC5D-Multiple Myeloma Evidence Breakdown

**Query Execution**:
```bash
# Get evidence type scores for Multiple Myeloma (EFO_0001378) - GPRC5D
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ disease(efoId: \"EFO_0001378\") { name associatedTargets(page: {size: 50}) { rows { target { approvedSymbol id } score datatypeScores { id score } } } } }"}' \
  | jq '.data.disease.associatedTargets.rows[] | select(.target.approvedSymbol == "GPRC5D") | {target: .target.approvedSymbol, overall: .score, evidence: .datatypeScores}'
```

**Results**: [TO BE POPULATED]

---

## Phase 5: Clinical Trial Discovery for Existing Drugs

**Objective**: Find recruiting clinical trials for approved antibodies (rituximab, ofatumumab) targeting CAR-T antigens.

**Regulatory Relevance**: Active trials for antibodies indicate continued clinical interest and validate target relevance.

### 5.1 Rituximab Clinical Trials (CD20 Antibody)

**Query Execution**:
```bash
# Search for recruiting rituximab trials
curl -s "https://clinicaltrials.gov/api/v2/studies?query.intr=rituximab&filter.overallStatus=RECRUITING&pageSize=10&format=json" \
  | jq '.studies[] | {nct: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, conditions: .protocolSection.conditionsModule.conditions[0:3], phase: .protocolSection.designModule.phases}'
```

**Results**: [TO BE POPULATED]

---

## Phase 6: Synthesis - Target Validation Matrix

**Objective**: Create comprehensive target validation matrix linking tractability → drugs → trials → regulatory velocity.

### Target Validation Summary

| Target | Tractability (Antibody) | Known Drugs | Clinical Precedence | Evidence Type Scores | Regulatory Velocity Prediction |
|--------|-------------------------|-------------|---------------------|---------------------|-------------------------------|
| CD19 | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] |
| MS4A1/CD20 | [TO BE POPULATED] | Rituximab, Ofatumumab, Obinutuzumab | High (multiple approved antibodies) | [TO BE POPULATED] | Fast (clinical precedence) |
| TNFRSF17/BCMA | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] |
| GPRC5D | [TO BE POPULATED] | None (novel target) | Low (no precedent) | [TO BE POPULATED] | Moderate (novel but tractable) |
| CHRNA1 | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] | [TO BE POPULATED] |

---

## Enhanced Knowledge Graph Edges

### New Edge Types Discovered

**Target → Drug Edges** (TARGETED_BY):
- [TO BE POPULATED after curl execution]

**Drug → Disease Edges** (TREATS):
- [TO BE POPULATED after curl execution]

**Target → GO Term Edges** (ENRICHED_IN):
- [TO BE POPULATED after curl execution]

**Target → Evidence Type Edges** (SUPPORTED_BY):
- [TO BE POPULATED after curl execution]

---

## Key Findings

[TO BE POPULATED after curl execution]

---

## Regulatory Implications

[TO BE POPULATED after curl execution]

---

**Document Status**: Curl commands prepared, awaiting execution
**Next Steps**: Execute all curl commands sequentially, populate results, analyze findings
