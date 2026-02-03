## CQ-6: BRCA1 Regulatory Network

**Question**: What transcription factors regulate BRCA1 expression, and what genes does BRCA1 regulate?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq6-brca1-regulatory-network`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| BRCA1 | HGNC:1100 | Gene | Central node (STRING:9606.ENSP00000418960) |
| E2F1 | HGNC:3113 | Gene | Upstream transcription factor |
| SP1 | HGNC:11205 | Gene | Upstream transcription factor |
| MYC | HGNC:7553 | Gene | Regulatory partner |
| BARD1 | HGNC:952 | Gene | Binding partner |
| RAD51 | HGNC:9817 | Gene | Downstream target |
| BRCA2 | HGNC:1101 | Gene | Downstream partner |
| TP53 | HGNC:11998 | Gene | Regulatory partner |
| GADD45A | HGNC:4095 | Gene | Downstream target |

### Key Findings

- Upstream transcription factors: E2F1 (STRING score 0.879, binds BRCA1 promoter during S phase), SP1 (score 0.665, binds GC-rich promoter elements)
- Regulatory partners: MYC (score 0.999, BRCA1 represses MYC transcription), TP53 (score 0.949, BRCA1 co-activates TP53-dependent transcription)
- Binding partners: BARD1 (score 0.999, forms BRCA1-BARD1 E3 ubiquitin ligase heterodimer), BRCA2 (score 0.998, BRCA1-PALB2-BRCA2 complex)
- Downstream targets: RAD51 (BRCA1 recruits RAD51 for homologous recombination), GADD45A (BRCA1 activates transcription)
- Disease association: BRCA1 mutations cause hereditary breast/ovarian cancer syndrome

### Graph Summary

- **Nodes**: 9
- **Edges**: 8

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:1100 (BRCA1), HGNC:3113 (E2F1), HGNC:11205 (SP1), HGNC:7553 (MYC), HGNC:952 (BARD1), HGNC:9817 (RAD51), HGNC:1101 (BRCA2), HGNC:11998 (TP53), HGNC:4095 (GADD45A) |
| STRING | string_search_proteins, string_get_interactions | STRING:9606.ENSP00000418960 (BRCA1), scores: E2F1 0.879, SP1 0.665, MYC 0.999, BARD1 0.999, BRCA2 0.998, TP53 0.949 |
| STRING | curl API (multi-protein network) | BRCA1-E2F1-SP1-MYC network interactions |

### Mechanism/Path

Upstream Regulation:
`E2F1 (HGNC:3113)` --[REGULATES, 0.879]--> `BRCA1 (HGNC:1100)`
`SP1 (HGNC:11205)` --[REGULATES, 0.665]--> `BRCA1 (HGNC:1100)`

Downstream Regulation:
`BRCA1 (HGNC:1100)` --[REGULATES, 0.999]--> `MYC (HGNC:7553)` (represses)
`BRCA1 (HGNC:1100)` --[REGULATES]--> `RAD51 (HGNC:9817)` (recruits for HR)
`BRCA1 (HGNC:1100)` --[REGULATES]--> `GADD45A (HGNC:4095)` (activates)

Protein Interactions:
`BRCA1 (HGNC:1100)` --[INTERACTS, 0.999]--> `BARD1 (HGNC:952)` (E3 ubiquitin ligase)
`BRCA1 (HGNC:1100)` --[INTERACTS, 0.998]--> `BRCA2 (HGNC:1101)` (PALB2 complex)
`BRCA1 (HGNC:1100)` --[INTERACTS, 0.949]--> `TP53 (HGNC:11998)` (co-activation)
