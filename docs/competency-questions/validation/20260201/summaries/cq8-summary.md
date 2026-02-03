## CQ-8: ARID1A Synthetic Lethality in Ovarian Cancer

**Question**: How can we identify therapeutic strategies for ARID1A-deficient Ovarian Cancer using synthetic lethality?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq8-arid1a-synthetic-lethality`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| ARID1A | HGNC:11110 | Gene | Anchor gene (tumor suppressor, SWI/SNF complex) |
| EZH2 | HGNC:3527 | Gene | Synthetic lethal partner (PRC2 component) |
| ATR | HGNC:882 | Gene | Synthetic lethal partner (checkpoint kinase) |
| PARP1 | HGNC:270 | Gene | Synthetic lethal partner (DNA repair) |
| ARID1B | HGNC:18040 | Gene | Paralog, mutual exclusivity |
| SMARCA4 | HGNC:11100 | Gene | SWI/SNF ATPase subunit |
| SMARCB1 | HGNC:11103 | Gene | SWI/SNF core subunit |
| SMARCC1 | HGNC:11108 | Gene | SWI/SNF core subunit |
| SMARCC2 | HGNC:11109 | Gene | SWI/SNF core subunit |
| Tazemetostat | CHEMBL:3414621 | Compound | EZH2 inhibitor (FDA approved, Phase 4) |

### Key Findings

- ARID1A is mutated in ~50% of ovarian clear cell carcinomas
- ARID1A is a tumor suppressor in the SWI/SNF (BAF) chromatin remodeling complex
- EZH2 inhibition is synthetic lethal with ARID1A loss (PRC2 antagonizes SWI/SNF)
- ATR dependency in ARID1A-deficient cells due to replication stress
- PARP inhibitors may be effective due to HR deficiency (BRCAness phenotype)
- Clinical trial NCT03348631: Tazemetostat in Recurrent Ovarian or Endometrial Cancer (Phase 2)

### Graph Summary

- **Nodes**: 9
- **Edges**: 4

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:11110, HGNC:3527, HGNC:882, HGNC:270, HGNC:18040, HGNC:11100 |
| STRING | string_search_proteins, string_get_interactions | STRING:9606.ENSP00000320485 (ARID1A) |
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:3414621 (Tazemetostat) |
| ClinicalTrials.gov | curl API | NCT03348631 |

### Synthetic Lethal Partners

| Partner | CURIE | Mechanism | Drug | Evidence |
|---------|-------|-----------|------|----------|
| EZH2 | HGNC:3527 | PRC2-mediated silencing antagonizes SWI/SNF; EZH2 inhibition is synthetic lethal with ARID1A loss | Tazemetostat | Preclinical + Phase 2 trial |
| ATR | HGNC:882 | ARID1A-deficient cells have replication stress and depend on ATR for survival | VX-970, AZD6738 | Preclinical |
| PARP1 | HGNC:270 | ARID1A loss causes homologous recombination defects similar to BRCA | Olaparib | Preclinical + clinical investigation |

### Mechanism/Path

`ARID1A (HGNC:11110)` --[SYNTHETIC_LETHAL]--> `EZH2 (HGNC:3527)`

`ARID1A (HGNC:11110)` --[SYNTHETIC_LETHAL]--> `ATR (HGNC:882)`

`ARID1A (HGNC:11110)` --[SYNTHETIC_LETHAL]--> `PARP1 (HGNC:270)`

`Tazemetostat (CHEMBL:3414621)` --[INHIBITOR]--> `EZH2 (HGNC:3527)`

### Clinical Trial

| Field | Value |
|-------|-------|
| NCT ID | NCT:03348631 |
| Title | Tazemetostat in Treating Patients With Recurrent Ovarian or Endometrial Cancer |
| Phase | Phase 2 |
| Status | Active, not recruiting |

### Cross-References

| Gene | Ensembl | UniProt | Location |
|------|---------|---------|----------|
| ARID1A | ENSG00000117713 | O14497 | 1p36.11 |
| Aliases | BAF250, BAF250a | | |
