## CQ-5: MAPK Regulatory Cascade

**Question**: In the MAPK signaling cascade, which proteins regulate downstream targets and with what direction?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq5-mapk-regulatory-cascade`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| MAPK1 (ERK2) | HGNC:6871 | Gene | Terminal kinase (STRING:9606.ENSP00000215832) |
| MAP2K1 (MEK1) | HGNC:6840 | Gene | Upstream kinase (MAPKK) |
| MAP2K2 (MEK2) | HGNC:6842 | Gene | Upstream kinase (MAPKK) |
| RAF1 (c-Raf) | HGNC:9829 | Gene | Upstream kinase (MAPKKK, STRING:9606.ENSP00000401888) |
| BRAF | HGNC:1097 | Gene | Upstream kinase (MAPKKK) |
| KRAS | HGNC:6407 | Gene | Upstream GTPase |
| MAPK signaling | WP:WP382 | Pathway | WikiPathways context |
| MAPK cascade | WP:WP422 | Pathway | WikiPathways context |

### Key Findings

- Canonical cascade: KRAS (GTPase) --> RAF1/BRAF (MAPKKK) --> MAP2K1/MAP2K2 (MEK1/2) --> MAPK1 (ERK2)
- Direct upstream kinases of MAPK1: MAP2K1 (score 0.999), MAP2K2 (score 0.999)
- Downstream targets include: ELK1, JUN, TP53, STAT3, RPS6KA1, MKNK1
- Phosphatases that regulate the cascade: DUSP1, DUSP6, PTPN7, PTPRR
- This cascade mediates growth factor signals from membrane receptors to nuclear transcription factors

### Graph Summary

- **Nodes**: 8
- **Edges**: 8

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:6871 (MAPK1), HGNC:6840 (MAP2K1), HGNC:9829 (RAF1), HGNC:1097 (BRAF), HGNC:6407 (KRAS), HGNC:6842 (MAP2K2) |
| STRING | string_search_proteins, string_get_interactions | STRING:9606.ENSP00000215832 (MAPK1), STRING:9606.ENSP00000401888 (RAF1), scores 0.999 |
| WikiPathways | wikipathways_search_pathways | WP:WP382 (MAPK signaling), WP:WP422 (MAPK cascade) |

### Mechanism/Path

`KRAS (HGNC:6407)` --[ACTIVATES]--> `RAF1 (HGNC:9829)` --[PHOSPHORYLATES, 0.999]--> `MAP2K1 (HGNC:6840)` --[PHOSPHORYLATES, 0.999]--> `MAPK1 (HGNC:6871)`

`KRAS (HGNC:6407)` --[ACTIVATES]--> `BRAF (HGNC:1097)` --[PHOSPHORYLATES]--> `MAP2K1 (HGNC:6840)` --[PHOSPHORYLATES, 0.999]--> `MAPK1 (HGNC:6871)`

`MAP2K2 (HGNC:6842)` --[PHOSPHORYLATES, 0.999]--> `MAPK1 (HGNC:6871)`
