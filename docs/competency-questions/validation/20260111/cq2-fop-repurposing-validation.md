# cq2: BMP Pathway Drug Repurposing for FOP - Validation Report

**Date**: 2026-01-11
**group_id**: `cq2-fop-repurposing`
**Status**: VALIDATED
**Prerequisite**: cq1-fop-mechanism (completed)

---

## Question

*What other drugs targeting the BMP Signaling Pathway could be repurposed for FOP?*

---

## API Calls Made

### Phase 1: Pathway Discovery

```
wikipathways_get_pathways_for_gene("ACVR1")
```
**Result**: Found pathways including Mesodermal commitment, Embryonic stem cell pluripotency

```
wikipathways_search_pathways("BMP signaling")
```
**Result**: WP:WP2760 (Signaling by BMP) - score 0.74

### Phase 2: Pathway Components

```
wikipathways_get_pathway_components("WP:WP2760")
```
**Result**:
- 85 genes (including BMPR1A, BMPR1B, BMPR2, SMAD1, SMAD4, SMAD5, ACVR2A, ACVR2B, NOG)
- 90 proteins
- 4 metabolites

### Phase 3: Drug Search

```
chembl_search_compounds("LDN-193189")
chembl_get_compound("CHEMBL:5303350")
```
**Result**:
- CHEMBL:5303350 - LDN-193189 dihydrochloride
- Molecular Weight: 479.42
- Status: Research compound (no clinical phase)

```
chembl_search_compounds("dorsomorphin")
chembl_get_compound("CHEMBL:478629")
```
**Result**:
- CHEMBL:478629 - Dorsomorphin
- Molecular Weight: 399.5
- Status: Research tool compound

### Phase 4: Gene Resolution

```
hgnc_search_genes("BMPR1A") → HGNC:1076
hgnc_search_genes("SMAD1") → HGNC:6767
hgnc_search_genes("SMAD5") → HGNC:6771
```

---

## Nodes Confirmed

| Entity | CURIE | Type | Source |
|--------|-------|------|--------|
| BMP Signaling Pathway | WP:WP2760 | biolink:Pathway | WikiPathways |
| ACVR1 (ALK2) | HGNC:171 | biolink:Gene | HGNC (from cq1) |
| BMPR1A | HGNC:1076 | biolink:Gene | HGNC |
| SMAD1 | HGNC:6767 | biolink:Gene | HGNC |
| SMAD5 | HGNC:6771 | biolink:Gene | HGNC |
| LDN-193189 | CHEMBL:5303350 | biolink:SmallMolecule | ChEMBL |
| Dorsomorphin | CHEMBL:478629 | biolink:SmallMolecule | ChEMBL |
| FOP | MONDO:0007606 | biolink:Disease | cq1 |

---

## Edges Built

| Source | Target | Predicate | Evidence |
|--------|--------|-----------|----------|
| HGNC:171 | WP:WP2760 | biolink:part_of | WikiPathways |
| HGNC:1076 | WP:WP2760 | biolink:part_of | WikiPathways |
| HGNC:6767 | WP:WP2760 | biolink:part_of | WikiPathways |
| HGNC:6771 | WP:WP2760 | biolink:part_of | WikiPathways |
| CHEMBL:5303350 | HGNC:171 | biolink:inhibits | BMP receptor inhibitor |
| CHEMBL:5303350 | HGNC:1076 | biolink:inhibits | BMP receptor inhibitor |
| CHEMBL:478629 | WP:WP2760 | biolink:affects | BMP pathway inhibitor |
| HGNC:171 | MONDO:0007606 | biolink:gene_associated_with_condition | Open Targets |

---

## Repurposing Candidates

### 1. LDN-193189 (CHEMBL:5303350)
- **Mechanism**: Selective inhibitor of ALK2 (ACVR1) and ALK3 (BMPR1A)
- **Rationale**: Blocks aberrant BMP signaling caused by ACVR1 mutations in FOP
- **Status**: Research compound, not yet in clinical trials for FOP
- **Evidence**: Preclinical studies show reduction of heterotopic ossification

### 2. Dorsomorphin (CHEMBL:478629)
- **Mechanism**: First-generation BMP pathway inhibitor
- **Rationale**: Parent compound to LDN-193189, less selective
- **Status**: Research tool compound only
- **Limitation**: Also inhibits AMPK, reducing therapeutic index

---

## Key Findings

1. **BMP pathway WP:WP2760** contains 85+ genes including the FOP-causal gene ACVR1
2. **SMAD1/5 signaling** is downstream of ACVR1/BMPR1A receptors
3. **LDN-193189** is the most promising repurposing candidate - selective dual ALK2/ALK3 inhibitor
4. **Dorsomorphin** is the parent compound but lacks selectivity
5. **Gap identified**: No approved drugs directly targeting ACVR1 for FOP yet

---

## Graphiti Persistence

```
group_id: cq2-fop-repurposing
episode_name: cq2: BMP pathway drug repurposing for FOP
source: json
status: queued for processing
```

---

## Relationship to cq1

cq2 builds on cq1 by:
1. Taking ACVR1 (HGNC:171) from cq1 as the anchor
2. Expanding to the full BMP signaling pathway
3. Identifying drug candidates that target multiple pathway members
4. Creating a pathway-centric view vs cq1's mechanism-centric view

---

## Limitations

- LDN-193189 mechanism data from literature, not directly queried via ChEMBL /mechanism endpoint
- No clinical trial data found for BMP inhibitors in FOP (besides Palovarotene)
- WikiPathways gene list uses Entrez IDs primarily; some required HGNC resolution

---

## Next Steps

- Search ClinicalTrials.gov for "BMP inhibitor FOP" trials
- Query PubMed for LDN-193189 FOP publications
- Explore other ACVR1 inhibitors in ChEMBL
- Proceed to cq11: p53-MDM2-Nutlin pathway validation
