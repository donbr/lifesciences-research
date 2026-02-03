## CQ-1: Palovarotene Mechanism for FOP

**Question**: By what mechanism does Palovarotene treat Fibrodysplasia Ossificans Progressiva (FOP)?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq1-fop-mechanism`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| Palovarotene | CHEMBL:2105648 | Compound | Drug (Max Phase 4, approved as "Sohonos") |
| Retinoic acid receptor gamma | HGNC:9866 | Gene | Target (RARG) |
| Activin A receptor type 1 | HGNC:171 | Gene | Causal gene (ACVR1/ALK2) |
| Fibrodysplasia ossificans progressiva | MONDO:0007606 | Disease | Indication (FOP) |

### Key Findings

- Palovarotene (CHEMBL:2105648) is a selective RARG agonist at Max Phase 4, approved as "Sohonos"
- Mechanism: RARG agonism downregulates BMP signaling through ACVR1 (ALK2), reducing ectopic bone formation
- ACVR1 (HGNC:171) is the causal gene for FOP with gain-of-function mutations causing aberrant heterotopic ossification
- Open Targets association score between ACVR1 and FOP: 0.816 (highest disease association)

### Graph Summary

- **Nodes**: 4
- **Edges**: 3

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:2105648, target CHEMBL2003 |
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:9866 (RARG), HGNC:171 (ACVR1) |
| Open Targets | opentargets_get_associations | ENSG00000115170 association score 0.816 |
| STRING | curl API | RARG-ACVR1 interaction score 0.435 |
| ChEMBL Mechanism API | curl | Action type: AGONIST |

### Mechanism/Path

`Palovarotene (CHEMBL:2105648)` --[AGONIST]--> `RARG (HGNC:9866)` --[REGULATES, score 0.435]--> `ACVR1 (HGNC:171)` --[CAUSES, score 0.816]--> `FOP (MONDO:0007606)`
