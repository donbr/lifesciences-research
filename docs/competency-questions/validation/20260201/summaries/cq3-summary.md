## CQ-3: Alzheimer's Gene-Protein Interaction Network

**Question**: What genes and proteins are implicated in Alzheimer's Disease progression, and how do they interact?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq3-alzheimers-gene-network`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| APP | HGNC:620 | Gene | Amyloid precursor protein, cleaved to Abeta peptides |
| PSEN1 | HGNC:9508 | Gene | Gamma-secretase catalytic subunit |
| PSEN2 | HGNC:9509 | Gene | Gamma-secretase catalytic subunit |
| APOE | HGNC:613 | Gene | Major genetic risk factor (E4 allele) |
| MAPT | HGNC:6893 | Gene | Tau protein, neurofibrillary tangles |
| BACE1 | HGNC:933 | Gene | Beta-secretase, cleaves APP |
| SORL1 | HGNC:11185 | Gene | Sorting receptor, regulates APP trafficking |
| CLU | HGNC:2095 | Gene | Clusterin, AD risk gene |
| GSK3B | HGNC:4617 | Gene | Tau kinase |
| NCSTN | HGNC:7767 | Gene | Gamma-secretase complex component |
| PSENEN | HGNC:16508 | Gene | Gamma-secretase complex component |
| Alzheimer disease | MONDO:0004975 | Disease | Target disease |

### Key Findings

- Core AD genes: APP, PSEN1, PSEN2, APOE with high-confidence interactions
- Gamma-secretase complex: PSEN1/PSEN2 (catalytic), NCSTN, APH1A/APH1B, PSENEN
- Disease association: APP to Alzheimer disease type 1 (score 0.786)
- APOE E4 allele is a major late-onset AD risk factor
- Key protein-protein interactions confirmed via STRING with scores > 0.9

### Graph Summary

- **Nodes**: 11
- **Edges**: 8

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:620, HGNC:9508, HGNC:9509, HGNC:613, HGNC:6893, HGNC:933, HGNC:11185, HGNC:2095 |
| STRING | string_search_proteins, string_get_interactions | STRING:9606.ENSP00000284981 (APP), STRING:9606.ENSP00000326366 (PSEN1) |
| Open Targets | opentargets_get_associations | ENSG00000142192 (APP) - AD association score 0.786 |

### Interaction Scores (STRING)

| Source | Target | Score | Evidence |
|--------|--------|-------|----------|
| APP (HGNC:620) | APOE (HGNC:613) | 0.999 | STRING |
| APP (HGNC:620) | SORL1 (HGNC:11185) | 0.999 | STRING (SORL1 regulates APP trafficking) |
| APOE (HGNC:613) | MAPT (HGNC:6893) | 0.991 | STRING |
| APOE (HGNC:613) | PSEN1 (HGNC:9508) | 0.956 | STRING |
| APOE (HGNC:613) | PSEN2 (HGNC:9509) | 0.961 | STRING |
| APOE (HGNC:613) | CLU (HGNC:2095) | 0.999 | STRING |

### Mechanism/Path

`APP (HGNC:620)` --[CLEAVED_BY]--> `BACE1 (HGNC:933)` (beta-site cleavage)

`PSEN1 (HGNC:9508)` --[CLEAVES]--> `APP (HGNC:620)` (gamma-secretase cleavage)

`APP (HGNC:620)` --[INTERACTS]--> `APOE (HGNC:613)` --[INTERACTS]--> `MAPT (HGNC:6893)`

### Cross-References

| Gene | Ensembl | UniProt | Location |
|------|---------|---------|----------|
| APP | ENSG00000142192 | P05067 | 21q21.3 |
| PSEN1 | ENSG00000080815 | P49768 | 14q24.2 |
| PSEN2 | ENSG00000143801 | P49810 | 1q42.13 |
| APOE | ENSG00000130203 | P02649 | 19q13.32 |
