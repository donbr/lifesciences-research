## CQ-4: Alzheimer's Disease Therapeutic Targets

**Question**: What drugs target amyloid-beta or tau proteins for Alzheimer's Disease treatment?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq4-alzheimers-therapeutics`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| Alzheimer disease | MONDO:0004975 | Disease | Target disease |
| APP | HGNC:620 | Gene | Amyloid beta precursor protein |
| BACE1 | HGNC:933 | Gene | Beta-secretase 1, cleaves APP at beta-site |
| PSEN1 | HGNC:9508 | Gene | Presenilin 1, gamma-secretase catalytic subunit |
| MAPT | HGNC:6893 | Gene | Microtubule associated protein tau (17q21.31) |
| GSK3B | HGNC:4617 | Gene | Glycogen synthase kinase 3 beta, tau phosphorylation |
| CDK5 | HGNC:1979 | Gene | Tau phosphorylation kinase |
| Lecanemab | CHEMBL:3833321 | Drug | Anti-amyloid-beta antibody (FDA 2023) |
| Aducanumab | CHEMBL:3039540 | Drug | Anti-amyloid-beta antibody (FDA 2021) |
| Donanemab | CHEMBL:4297245 | Drug | Anti-amyloid-beta antibody (FDA 2024) |

### Key Findings

- Three FDA-approved anti-amyloid antibodies: Lecanemab (Leqembi, 2023), Aducanumab (Aduhelm, 2021), Donanemab (Kisunla, 2024)
- BACE1 inhibitors failed clinical trials due to cognitive worsening
- Tau-targeting approaches in development: Anti-tau antibodies (Semorinemab, Tilavonemab - Phase 2-3), Tau aggregation inhibitors (LMTM - Phase 3 failed), ASOs (BIIB080 - Phase 1-2)
- All approved drugs target amyloid protofibrils/plaques via ChEMBL target CHEMBL2487

### Graph Summary

- **Nodes**: 8
- **Edges**: 5

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:933 (BACE1), HGNC:6893 (MAPT), HGNC:620 (APP), HGNC:4617 (GSK3B), HGNC:9508 (PSEN1) |
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:3833321, CHEMBL:3039540, CHEMBL:4297245 |
| ChEMBL API | curl mechanism endpoint | Target: CHEMBL2487, Actions: INHIBITOR, BINDING AGENT |
| ClinicalTrials.gov | curl API | NCT02516046 (18F-AV-1451 Autopsy Study) |

### Mechanism/Path

`CHEMBL:3833321 (Lecanemab)` --[TARGETS]--> `HGNC:620 (APP)` (Anti-amyloid antibody)

`CHEMBL:3039540 (Aducanumab)` --[TARGETS]--> `HGNC:620 (APP)` (Anti-amyloid antibody)

`CHEMBL:4297245 (Donanemab)` --[TARGETS]--> `HGNC:620 (APP)` (Anti-amyloid antibody)

`HGNC:933 (BACE1)` --[CLEAVES]--> `HGNC:620 (APP)` (Beta-secretase cleavage)

`HGNC:4617 (GSK3B)` --[PHOSPHORYLATES]--> `HGNC:6893 (MAPT)` (Tau hyperphosphorylation)
