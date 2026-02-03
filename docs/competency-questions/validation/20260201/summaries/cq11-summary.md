## CQ-11: p53-MDM2-Nutlin Therapeutic Axis

**Question**: How do we build and validate a knowledge graph for the p53-MDM2-Nutlin therapeutic axis?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq11-p53-mdm2-nutlin`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| TP53 | HGNC:11998 | Gene | Tumor protein p53 (17p13.1), tumor suppressor |
| MDM2 | HGNC:6973 | Gene | MDM2 proto-oncogene (12q15), E3 ubiquitin ligase |
| TP53 protein | UniProt:P04637 | Protein | Guardian of the genome |
| MDM2 protein | UniProt:Q00987 | Protein | Negative regulator of p53 |
| Nutlin-3 | CHEMBL:191334 | Drug | p53-MDM2 PPI inhibitor (research tool) |
| Idasanutlin | CHEMBL:2402737 | Drug | p53-MDM2 inhibitor (Phase 3) |
| MDM2 target | CHEMBL:1907611 | Target | ChEMBL target for Idasanutlin |

### Key Findings

- Mechanism: MDM2 is an E3 ubiquitin ligase that binds and degrades p53. Nutlin-class inhibitors disrupt p53-MDM2 interaction, stabilizing p53
- Normal state: p53 activates MDM2 transcription -> MDM2 binds p53 -> p53 degradation (negative feedback loop)
- Cancer state: MDM2 amplification/overexpression -> constitutive p53 suppression -> loss of tumor suppression
- Therapeutic intervention: Nutlin binds MDM2 pocket -> displaces p53 -> p53 stabilization -> cell cycle arrest and apoptosis
- Clinical candidate: Idasanutlin (RG-7388, RO-5503781) in Phase 3 for AML, polycythemia vera, lymphoma
- Patient selection: Wild-type TP53 tumors ONLY (mutant p53 not reactivated by MDM2 inhibition)

### Graph Summary

- **Nodes**: 4
- **Edges**: 4

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:11998 (TP53), HGNC:6973 (MDM2) |
| STRING | string_search_proteins, string_get_interactions | STRING:9606.ENSP00000269305, TP53-MDM2 score=0.999, TP53-SIRT1 score=0.999, MDM2-EP300 score=0.999 |
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:191334 (Nutlin-3), CHEMBL:2402737 (Idasanutlin, max_phase=3) |
| ChEMBL API | curl mechanism endpoint | Idasanutlin: INHIBITOR of CHEMBL1907611 |

### Mechanism/Path

`HGNC:6973 (MDM2)` --[UBIQUITINATES]--> `HGNC:11998 (TP53)` (Degradation)

`HGNC:11998 (TP53)` --[TRANSCRIBES]--> `HGNC:6973 (MDM2)` (Negative feedback)

`CHEMBL:191334 (Nutlin-3)` --[INHIBITOR]--> `HGNC:6973 (MDM2)` (Blocks p53 binding)

`CHEMBL:2402737 (Idasanutlin)` --[INHIBITOR]--> `HGNC:6973 (MDM2)` (Clinical candidate)

### Clinical Context

| Aspect | Details |
|--------|---------|
| Patient selection | Wild-type TP53 tumors only (mutant p53 not reactivated) |
| Biomarkers | TP53 mutation status, MDM2 amplification |
| Combinations | With chemotherapy, BCL2 inhibitors (venetoclax) |
| Limitations | No effect in TP53-mutant cancers (~50% of all cancers) |
