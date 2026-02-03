# Evidence Quality Assessment Report
## 15 Competency Questions - 2026-02-01 Validation Round

**Report Date**: 2026-02-01
**Assessment Period**: Complete validation suite
**Total CQs Evaluated**: 15
**Overall Quality Distribution**: 7 HIGH, 7 MEDIUM, 1 LOW

---

## Executive Summary

The competency question validation suite demonstrates robust evidence collection across 15 diverse biomedical research scenarios. With an average of **7.3 CURIEs per CQ** and **5.3 API tools per CQ**, the evidence base is comprehensive and well-distributed. However, clinical trial-focused questions (CQ-12, CQ-13, CQ-15) show lower provenance diversity, relying primarily on ClinicalTrials.gov API.

**Key Findings**:
- **46.7%** of CQs achieve HIGH quality rating (7 CQs)
- **46.7%** achieve MEDIUM quality (7 CQs)
- **6.7%** flagged for LOW quality (1 CQ) - CQ-12 due to minimal API tool diversity
- HGNC gene identifiers dominate (65 of 110 CURIEs, 59%)
- Clinical trial research relies on single API endpoint, reducing redundancy and validation opportunity

---

## Evidence Quality Scorecard

| CQ | Title | CURIEs | API Tools | Scores | Quality |
|-----|---------|--------|-----------|--------|---------|
| **CQ-1** | Palovarotene Mechanism for FOP | 4 | 7 | 2 | **HIGH** ⭐ |
| **CQ-2** | FOP Drug Repurposing via BMP | 9 | 7 | 0 | MEDIUM |
| **CQ-3** | Alzheimer's Gene-Protein Network | 11 | 5 | 7 | **HIGH** ⭐⭐ |
| **CQ-4** | Alzheimer's Disease Therapeutics | 10 | 6 | 0 | MEDIUM |
| **CQ-5** | MAPK Regulatory Cascade | 8 | 5 | 2 | **HIGH** ⭐ |
| **CQ-6** | BRCA1 Regulatory Network | 9 | 5 | 6 | **HIGH** ⭐⭐ |
| **CQ-7** | NGLY1 Deficiency Drug Repurposing | 6 | 7 | 2 | **HIGH** ⭐ |
| **CQ-8** | ARID1A Synthetic Lethality | 10 | 7 | 0 | MEDIUM |
| **CQ-9** | Dasatinib Off-Target Safety | 6 | 5 | 0 | MEDIUM |
| **CQ-10** | Huntington's Disease Novel Targets | 6 | 6 | 5 | **HIGH** ⭐ |
| **CQ-11** | p53-MDM2-Nutlin Axis | 6 | 7 | 3 | **HIGH** ⭐ |
| **CQ-12** | Health Emergencies Clinical Trial Landscape | 11 | 1 | 0 | **LOW** ⚠️ |
| **CQ-13** | High-Commercialization Phase 3 Trials | 5 | 3 | 0 | MEDIUM |
| **CQ-14** | Feng Synthetic Lethality Validation | 4 | 5 | 0 | MEDIUM |
| **CQ-15** | CAR-T Regulatory Landscape | 5 | 4 | 0 | MEDIUM |

---

## Statistical Summary

### CURIE Counts
```
Mean:     7.3 CURIEs per CQ
Median:   6.0
Std Dev:  2.4
Range:    4-11 identifiers
```

**Distribution**:
- 4 CURIEs (Minimal): CQ-1, CQ-14 (2 CQs)
- 5 CURIEs: CQ-13, CQ-15 (2 CQs)
- 6 CURIEs: CQ-7, CQ-9, CQ-10, CQ-11 (4 CQs)
- 8-11 CURIEs (Rich): CQ-2, CQ-3, CQ-4, CQ-5, CQ-6, CQ-8, CQ-12 (7 CQs)

**Interpretation**: Strong entity resolution across all CQs. Even minimal-evidence CQs (CQ-1 at 4 CURIEs) contain high-quality, focused evidence.

### API Tools Count
```
Mean:     5.3 tools per CQ
Median:   5.0
Std Dev:  1.8
Range:    1-7 tools
```

**Tool Frequency**:
- Single tool: CQ-12 (1 tool - ClinicalTrials.gov only)
- 3-5 tools: CQ-4, CQ-5, CQ-6, CQ-9, CQ-13, CQ-14, CQ-15 (7 CQs)
- 6-7 tools: CQ-1, CQ-2, CQ-7, CQ-8, CQ-11 (5 CQs)

**Interpretation**: Most CQs use 5-7 diverse APIs, enabling triangulation and validation. CQ-12's single-tool reliance is anomalous.

### Confidence Scores
```
Mean:     1.8 scores per CQ
Median:   0.0
Std Dev:  2.3
Range:    0-7 scores
```

**Score Distribution**:
- 0 scores (No quantified confidence): CQ-2, CQ-4, CQ-8, CQ-9, CQ-12, CQ-13, CQ-14, CQ-15 (8 CQs = 53%)
- 2 scores: CQ-1, CQ-5, CQ-7 (3 CQs)
- 3+ scores: CQ-3 (7 scores), CQ-6 (6 scores), CQ-10 (5 scores), CQ-11 (3 scores) (4 CQs)

**Interpretation**: Protein-protein interactions (STRING) and disease associations (Open Targets) provide quantified confidence. Drug discovery CQs often lack numerical metrics.

---

## Quality Assessment Details

### HIGH Quality CQs (7)

**Criteria Met**: ≥4 CURIEs + ≥5 API tools OR ≥3 confidence scores

| CQ | Strengths | Evidence Type |
|----|-----------|---------------|
| **CQ-1** | 4 CURIEs, 7 API tools, drug mechanism validated with STRING (0.435) and OT (0.816) | Focused drug-target mechanism |
| **CQ-3** | 11 CURIEs (largest), 5 API tools, 7 STRING scores (0.956-0.999) proving protein interactions | Multi-hop gene network |
| **CQ-5** | 8 CURIEs, 5 API tools, canonical MAPK cascade with 0.999 phosphorylation scores | Signaling pathway |
| **CQ-6** | 9 CURIEs, 5 API tools, 6 STRING scores demonstrating BRCA1 regulatory network (0.665-0.999) | Regulatory network |
| **CQ-7** | 6 CURIEs, 7 API tools, ERAD pathway with interaction scores (0.905, 0.999) | Protein complex |
| **CQ-10** | 6 CURIEs, 6 API tools, 5 STRING scores (HTT interactions 0.989-0.999) | Disease pathway |
| **CQ-11** | 6 CURIEs, 7 API tools, p53-MDM2 validation with 0.999 interaction scores | Therapeutic axis |

**Common Pattern**: Gene/protein-focused queries with STRING interaction validation. All use 2+ complementary APIs.

### MEDIUM Quality CQs (7)

**Criteria Met**: ≥4 CURIEs but <5 API tools OR 0 confidence scores

| CQ | Evidence Gap | Reason |
|----|--------------|--------|
| **CQ-2** | 0 confidence scores | Drug repurposing hypothesis lacks quantified support (9 CURIEs adequate) |
| **CQ-4** | 0 confidence scores | Therapeutic candidates identified but no STRING/OT interaction metrics |
| **CQ-8** | 0 confidence scores | SWI/SNF complex and synthetic lethality partners identified (10 CURIEs) but unquantified |
| **CQ-9** | 0 confidence scores | Dasatinib target profile mapped (6 CURIEs) but no interaction evidence metrics |
| **CQ-13** | 3 API tools (low) | Retatrutide vs Tirzepatide comparison uses ClinicalTrials + ChEMBL (5 CURIEs) |
| **CQ-14** | 0 confidence scores | TYMS synthetic lethality validated via HGNC + ChEMBL (4 CURIEs, partial validation) |
| **CQ-15** | 4 API tools (low), 0 scores | 6 approved CAR-T therapies catalogued via ClinicalTrials + ChEMBL (5 CURIEs) |

**Common Pattern**: Drug discovery and clinical evidence focus lacks quantified interaction metrics. Adequate entity counts offset by scoring gap.

### LOW Quality CQ (1)

**CQ-12: Health Emergencies Clinical Trial Landscape**

```
CURIEs:        11 (strong - 11 trial NCT IDs)
API Tools:     1  (weak - ClinicalTrials.gov only)
Scores:        0  (none)
Status:        LOW QUALITY ⚠️
```

**Issues**:
1. **Single API Endpoint Dependency**: Entirely relies on `curl (ClinicalTrials.gov API)` with no cross-validation
2. **No Entity Grounding**: 11 NCT IDs are strong but disconnected from genes/proteins/compounds
3. **No Provenance Diversity**: Cannot triangulate evidence across HGNC, ChEMBL, STRING, or other databases
4. **Categorical Summary**: Focus on health priority categories rather than mechanistic entities

**Recommendation**: Enhance by linking trial entities (genes, drugs, biomarkers) to underlying databases:
- Link disease conditions to MONDO identifiers
- Resolve trial interventions to ChEMBL compounds
- Map target genes via HGNC
- Add Open Targets disease associations

---

## API Tool Analysis

### Top-Used Tools (Frequency Across 15 CQs)

```
Rank  Tool                              Used in CQs      Coverage %
----  --------------------------------  ---------------  ----------
 1.   hgnc_search_genes                 13 CQs           86.7%
 2.   hgnc_get_gene                     12 CQs           80.0%
 3.   chembl_search_compounds           10 CQs           66.7%
 4.   chembl_get_compound               10 CQs           66.7%
 5.   string_search_proteins            7 CQs            46.7%
 6.   string_get_interactions           7 CQs            46.7%
 7.   curl (ClinicalTrials.gov)         6 CQs            40.0%
 8.   opentargets_get_associations      4 CQs            26.7%
 9.   curl (ChEMBL API mechanism)       4 CQs            26.7%
10.   wikipathways_*                    2 CQs            13.3%
```

### API Ecosystem Contribution

| API Server | Role | Used in # CQs | Uniqueness |
|-----------|------|---------------|-----------|
| **HGNC** | Gene identifier resolution (Tier 1) | 13 | Critical - gene foundation |
| **ChEMBL** | Drug/compound discovery and targets | 10 | Critical - drug mechanism |
| **STRING** | Protein-protein interactions (high confidence) | 7 | Quantifies relationships |
| **Open Targets** | Disease-gene associations | 4 | Validates clinical relevance |
| **WikiPathways** | Biological pathway context | 2 | Situates genes in pathways |
| **ClinicalTrials.gov** | Trial evidence and recruitment | 6 | Clinical stage evidence |

**Observation**: HGNC + ChEMBL form the foundational axis. STRING adds quantified confidence to 47% of CQs. Clinical integration (ClinicalTrials.gov) is present but underexplored for gene-mechanism CQs.

---

## CURIE Type Distribution

### By Database

```
Database     Count   % of Total   Example CURIEs
-----------  ------  ----------   -----------------------------------
HGNC         65      59.1%        HGNC:11998 (TP53), HGNC:620 (APP)
ChEMBL       21      19.1%        CHEMBL:2105648 (Palovarotene)
NCT (Trial)  15      13.6%        NCT:06463861 (CAR-T trial)
MONDO        4       3.6%         MONDO:0004975 (Alzheimer disease)
WikiPath     3       2.7%         WP:WP2760 (BMP pathway)
UniProt      2       1.8%         UniProt:P04637 (TP53 protein)
TOTAL        110     100%
```

### Quality Implications

**Strength**: Heavy HGNC presence (59%) indicates gene-centric design, appropriate for mechanistic questions.

**Weakness**: Only 3.6% MONDO disease identifiers. Most CQs mention diseases by name (e.g., "Alzheimer disease") without formalized MONDO links.

**Opportunity**: WikiPathways coverage (2.7%) suggests underutilized pathway-level evidence. Only 2 CQs (CQ-2, CQ-5) leverage pathway context.

---

## Provenance Strength Assessment

### Exemplary Provenance (HIGH Confidence)

**CQ-3: Alzheimer's Gene-Protein Interaction Network**
```
Evidence Trail:
1. HGNC queries resolve APP, PSEN1, PSEN2, APOE, MAPT → gene identifiers
2. STRING interactions confirm: APP-APOE (0.999), APOE-CLU (0.999)
3. Open Targets disease association: APP-Alzheimer disease (0.786)
4. Cross-references: Ensembl, UniProt, chromosomal locations

Confidence: Very High (quantified STRING + disease association)
Reproducibility: Excellent (all tools publicly available, no auth required)
```

**CQ-6: BRCA1 Regulatory Network**
```
Evidence Trail:
1. HGNC resolves BRCA1, E2F1, SP1, MYC, BARD1, RAD51, TP53 (9 genes)
2. STRING confirms: E2F1-BRCA1 (0.879), MYC-BRCA1 (0.999), BARD1-BRCA1 (0.999)
3. Multi-protein network via STRING curl API
4. Literature-known: E2F1 regulates BRCA1 S-phase, BARD1 E3 ligase complex

Confidence: High (6 interaction scores, functional biology validated)
```

### Weaker Provenance Examples (MEDIUM Confidence)

**CQ-2: FOP Drug Repurposing via BMP Pathway**
```
Evidence Trail:
1. HGNC resolves ACVR1, BMPR1A, SMAD5 (gene curation)
2. WikiPathways identifies WP:WP2760 containing 6 receptors, 6 SMADs
3. ChEMBL maps 5 compounds (Dorsomorphin, Crizotinib, etc.)
4. MISSING: No STRING interactions, no Open Targets associations

Confidence: Medium (mechanistic hypothesis sound but unquantified)
Validation Gap: Need protein-protein evidence + disease association scores
```

**CQ-9: Dasatinib Off-Target Safety Profile**
```
Evidence Trail:
1. ChEMBL resolves Dasatinib, Imatinib compounds
2. ChEMBL mechanism data lists 6 off-target kinases (ABL1, SRC, DDR2, KCNH2)
3. HGNC validates gene names
4. MISSING: No STRING interaction validation, no quantified safety metrics

Confidence: Medium (known from literature but unevidenced via APIs)
Validation Gap: STRING interaction strength for off-target effects
```

### Minimal Provenance (LOW Confidence)

**CQ-12: Health Emergencies Clinical Trial Landscape**
```
Evidence Trail:
1. ClinicalTrials.gov API returns 11 trial NCT IDs
2. Trials organized into 4 health priority categories
3. MISSING: No gene/protein entity grounding
4. MISSING: No drug-compound mapping
5. MISSING: No disease formalization (MONDO)

Confidence: Low (trial evidence valid but decontextualized)
Validation Gap: Link trials to underlying molecular mechanisms
Remediation: Map trial conditions → MONDO, interventions → ChEMBL, targets → HGNC
```

---

## Cross-Question Patterns

### Gene Coverage (HGNC)
Most gene-centric CQs (CQ-1 through CQ-11) leverage 6-11 HGNC identifiers each, providing robust entity resolution.

### Drug-Gene Bridge (ChEMBL ↔ HGNC)
**Pattern**: CQs combining mechanism (gene target) + therapeutic (compound) use both APIs:
- CQ-1, CQ-2, CQ-4, CQ-7, CQ-8, CQ-9, CQ-11 (7 CQs with drug-gene links)

### Interaction Quantification (STRING)
**Pattern**: Protein-protein interaction scores provided in 7 CQs. Enables ranking:
- Highest: CQ-3 (7 scores), CQ-6 (6 scores)
- Moderate: CQ-10 (5 scores), CQ-11 (3 scores)
- Absent: Drug repurposing and safety CQs (CQ-2, CQ-4, CQ-8, CQ-9)

### Clinical Integration (ClinicalTrials.gov)
**Pattern**: Only 6 CQs use clinical trial evidence. Opportunity:
- CQ-4, CQ-8, CQ-10, CQ-12, CQ-13, CQ-15 integrate trials
- CQ-1 through CQ-11 (mechanism-focused) treat trials as secondary validation

---

## Recommendations for Evidence Enhancement

### Immediate (CQ-12 Remediation)

1. **Add Entity Grounding to CQ-12**
   - Map trial conditions → MONDO identifiers
   - Map trial interventions → ChEMBL compounds
   - Map target genes → HGNC (where applicable)
   - Expected improvement: 1 API tool → 4-5 tools, +8-10 entity CURIEs

2. **Cross-Validate Clinical Evidence**
   - For approved drugs in trials, add ChEMBL mechanism data
   - For disease conditions, add Open Targets associations
   - Expected: 0 confidence scores → 3-5 scores

### Short-Term (Scoring Gaps)

3. **Add STRING Validation to Drug Repurposing CQs**
   - CQ-2, CQ-4, CQ-8, CQ-9: Fetch STRING interactions for identified drug targets
   - Quantify confidence in repurposing hypotheses
   - Expected: 0 scores → 3-5 scores per CQ, move to HIGH quality

4. **Enhance Open Targets Coverage**
   - Currently used in 4 CQs (26.7%)
   - Add disease association scores to CQ-2, CQ-4, CQ-8, CQ-9, CQ-14
   - Expected: +8-12 confidence metrics

### Medium-Term (Pathway Integration)

5. **Leverage WikiPathways More Broadly**
   - CQ-2, CQ-5 use pathways (2/15 = 13%)
   - Apply pathway context to CQ-3 (Alzheimer's), CQ-4, CQ-6, CQ-10
   - Enriches mechanistic understanding of nodes

6. **Add MONDO Disease Formalization**
   - Currently: 4 MONDO identifiers (3.6%)
   - Map disease names → MONDO for all 15 CQs
   - Expected: +15-20 MONDO CURIEs

### Long-Term (Knowledge Graph Completeness)

7. **Document Validation Traces**
   - Record API query parameters and response timestamps
   - Enable reproducibility and temporal tracking
   - Link each CURIE to source tool invocation

---

## Conclusion

The 15-CQ validation suite demonstrates **strong evidence quality overall** with 93.3% of CQs achieving MEDIUM or HIGH ratings. The evidence base is well-distributed across gene (59%), drug (19%), and clinical trial (14%) domains.

**Key Strengths**:
- HGNC + ChEMBL axis provides robust gene-drug entity resolution
- STRING interaction scores quantify protein-level confidence in 47% of CQs
- Diverse API ecosystem enables triangulation (median 5 tools per CQ)
- Focused, mechanistic evidence in gene-centric CQs (CQ-1, CQ-3, CQ-6)

**Key Weaknesses**:
- Clinical trial CQs (CQ-12, CQ-13, CQ-15) lack molecular grounding
- Drug repurposing CQs (CQ-2, CQ-4, CQ-8, CQ-9) lack quantified confidence scores
- WikiPathways underutilized (2 of 15 CQs)
- MONDO disease formalization sparse (3.6%)

**Action Items**:
1. Remediate CQ-12 with entity grounding (MONDO, ChEMBL, HGNC)
2. Add STRING/Open Targets validation to 4 drug repurposing CQs
3. Broaden pathway context integration across all mechanism-focused CQs

**Overall Assessment**: **VALID with recommendations for enhancement**

