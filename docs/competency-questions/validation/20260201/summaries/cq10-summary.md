## CQ-10: Huntington's Disease Novel Therapeutic Targets

**Question**: What novel therapeutic targets exist for Huntington's Disease that are not covered by current Phase 3 interventions?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq10-huntingtons-novel-targets`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| Huntington disease | MONDO:0007739 | Disease | Target disease (CAG repeat expansion) |
| HTT | HGNC:4851 | Gene | Huntingtin (4p16.3), causal gene |
| SLC18A2 | HGNC:10935 | Gene | VMAT2 (current Phase 3 target) |
| ITPR1 | HGNC:6180 | Gene | IP3 receptor type 1, calcium signaling |
| REST | HGNC:9966 | Gene | RE1 silencing transcription factor |
| BDNF | HGNC:1033 | Gene | Brain derived neurotrophic factor |
| CREBBP | - | Gene | CREB binding protein |
| HAP1 | - | Gene | Huntingtin associated protein 1 |
| SNCA | - | Gene | Alpha-synuclein |

### Key Findings

- Current Phase 3: VMAT2 (Valbenazine/Ingrezza) for symptomatic chorea management only
- Novel targets NOT in Phase 3:
  - ITPR1: Calcium signaling dysregulation (STRING score 0.995)
  - REST: Trapped by mutant HTT in cytoplasm (STRING score 0.991)
  - BDNF: Transport impaired by mHTT
  - CREBBP: Transcriptional dysregulation (STRING score 0.997)
  - HAP1: Vesicle trafficking impairment (STRING score 0.999)
  - SNCA: Protein aggregation cross-seeding (STRING score 0.989)
- Emerging approaches: HTT lowering (ASOs, RNAi), splicing modulators (PTC518)

### Graph Summary

- **Nodes**: 8
- **Edges**: Not explicitly counted (persisted as targets)

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:4851 (HTT), HGNC:10935 (SLC18A2), HGNC:6180 (ITPR1), HGNC:9966 (REST), HGNC:1033 (BDNF) |
| STRING | string_search_proteins, string_get_interactions | STRING:9606.ENSP00000347184, scores: HAP1=0.999, CREBBP=0.997, ITPR1=0.995, REST=0.991, SNCA=0.989 |
| Open Targets | opentargets_get_associations | ENSG00000197386 associations |
| ClinicalTrials.gov | curl API | NCT03225846 (WVE-120102), Valbenazine trials |

### Mechanism/Path

`HGNC:4851 (HTT mutant)` --[TRAPS]--> `HGNC:9966 (REST)` (Cytoplasmic sequestration)

`HGNC:4851 (HTT mutant)` --[IMPAIRS]--> `HGNC:1033 (BDNF)` (Transport dysfunction)

`HGNC:4851 (HTT mutant)` --[DYSREGULATES]--> `HGNC:6180 (ITPR1)` (Calcium signaling)

### Gap Analysis

| Category | Targets |
|----------|---------|
| Covered by drugs | VMAT2 (symptomatic chorea) |
| Underexplored | ITPR1 (calcium), REST (transcription), BDNF (trophic support), Mitochondrial targets |
