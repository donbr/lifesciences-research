## CQ-2: FOP Drug Repurposing via BMP Pathway

**Question**: What other drugs targeting the BMP Signaling Pathway could be repurposed for FOP?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq2-fop-repurposing`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| ACVR1/ALK2 | HGNC:171 | Gene | Causal gene (gain-of-function mutations cause FOP) |
| BMPR1A | HGNC:1076 | Gene | Pathway member (BMP type I receptor) |
| SMAD5 | HGNC:6771 | Gene | Downstream effector |
| Signaling by BMP | WP:WP2760 | Pathway | Target pathway |
| Dorsomorphin | CHEMBL:478629 | Compound | BMP pathway inhibitor (preclinical) |
| Crizotinib | CHEMBL:601719 | Compound | Multi-kinase inhibitor including ALK (Phase 4) |
| Cabozantinib | CHEMBL:2103868 | Compound | Multi-kinase inhibitor (Phase 4) |
| BMS-794833 | CHEMBL:2143592 | Compound | ACVR1 inhibitor (Phase 1) |
| LDN-193189 | CHEMBL:5303350 | Compound | Selective ALK2/ALK3 inhibitor (research tool) |
| Fibrodysplasia Ossificans Progressiva | MONDO:0007606 | Disease | Target disease |

### Key Findings

- FOP is caused by gain-of-function mutations in ACVR1 (ALK2), a BMP type I receptor
- Drugs that inhibit ACVR1 or downstream SMAD signaling could reduce aberrant heterotopic ossification
- Pathway WP:WP2760 contains 6 receptors (ACVR1/ALK2, BMPR1A, BMPR1B, BMPR2, ACVR2A, ACVR2B) and 6 SMADs (SMAD1, SMAD4, SMAD5, SMAD6, SMAD7, SMAD9)
- Repurposing candidates include dorsomorphin derivatives and selective ALK2 inhibitors

### Graph Summary

- **Nodes**: 8
- **Edges**: 4

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_get_gene, hgnc_search_genes | HGNC:171, HGNC:1076, HGNC:6771 |
| WikiPathways | wikipathways_search_pathways, wikipathways_get_pathway_components | WP:WP2760 |
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:478629, CHEMBL:601719, CHEMBL:2103868, CHEMBL:2143592, CHEMBL:5303350 |
| ChEMBL API (curl) | mechanism endpoint | CHEMBL:3717 (ACVR1 target) |

### Mechanism/Path

`ACVR1 (HGNC:171)` --[MEMBER_OF]--> `BMP Pathway (WP:WP2760)` --[SIGNALS_TO]--> `SMAD5 (HGNC:6771)`

`Dorsomorphin (CHEMBL:478629)` --[INHIBITOR]--> `ACVR1 (HGNC:171)`

`BMS-794833 (CHEMBL:2143592)` --[INHIBITOR]--> `ACVR1 (HGNC:171)`

### Repurposing Candidates

| Compound | Rationale | Status |
|----------|-----------|--------|
| Dorsomorphin (CHEMBL:478629) | Direct BMP pathway inhibitor, blocks SMAD1/5/8 phosphorylation | Preclinical tool compound |
| BMS-794833 (CHEMBL:2143592) | Phase 1 ACVR1 inhibitor | Phase 1 |
| LDN-193189 | Selective ALK2/ALK3 inhibitor, widely used in FOP research | Preclinical |
