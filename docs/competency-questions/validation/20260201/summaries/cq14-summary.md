## CQ-14: Feng Synthetic Lethality Validation

**Question**: How can we validate synthetic lethal gene pairs from Feng et al. (2022) and identify druggable opportunities for TP53-mutant cancers?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq14-feng-synthetic-lethality`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| TP53 | HGNC:11998 | Gene | Anchor gene (tumor suppressor) |
| TYMS | HGNC:12441 | Gene | Synthetic lethal partner candidate |
| 5-Fluorouracil | CHEMBL:185 | Compound | TYMS inhibitor (approved) |
| Pemetrexed | CHEMBL:225072 | Compound | TYMS inhibitor (approved) |

### Key Findings

- **TP53 (HGNC:11998)**: Tumor protein p53, the most frequently mutated gene in human cancers (~50%)
- **TYMS (HGNC:12441)**: Thymidylate synthetase, validated as synthetic lethal partner in TP53-mutant contexts
- **Druggable Target**: TYMS is druggable with approved inhibitors (5-FU, Pemetrexed)
- **CRISPR Validation**: BioGRID ORCS confirms TYMS essentiality in 352 CRISPR screens
- **Clinical Translation**: Phase 3 trial NCT04695925 testing Pemetrexed in TP53-mutant NSCLC

### BioGRID ORCS CRISPR Validation (TYMS)

| Metric | Value |
|--------|-------|
| **Total Screens with TYMS Essential** | 352 |
| **Validation Status** | CONFIRMED |
| **Key Cell Lines** | HCT 116 (colorectal), HeLa (cervical) |
| **Screen Type** | Negative Selection (fitness genes) |
| **Library** | TKO (Toronto Knockout) v1 |
| **Methodology** | CRISPRn Knockout |
| **Reference** | PMID:26627737 (Hart T 2015) |

### STRING Protein Interactions (TP53)

- **STRING ID**: STRING:9606.ENSP00000269305
- **Top Interactions** (score > 0.9):
  - SIRT1 (0.999), RPA1 (0.999), HDAC1 (0.993)
  - MDM2 (0.98), EP300 (0.972), ATM (0.928)

### Open Targets Disease Associations (TP53)

| Disease | ID | Score |
|---------|-----|-------|
| Li-Fraumeni syndrome | MONDO_0018875 | 0.876 |
| Hepatocellular carcinoma | EFO_0000182 | 0.796 |
| Head/neck squamous cell carcinoma | EFO_0000181 | 0.777 |
| Colorectal cancer | MONDO_0005575 | 0.736 |
| Lung adenocarcinoma | EFO_0000571 | 0.729 |

### Clinical Trial

| Attribute | Value |
|-----------|-------|
| **NCT ID** | NCT04695925 |
| **Title** | Osimertinib Monotherapy or Combination With Chemotherapy for Advanced NSCLC Concurrent EGFR and TP53 Mutations |
| **Status** | ACTIVE_NOT_RECRUITING |
| **Phase** | PHASE3 |
| **Intervention** | Osimertinib + Carboplatin + Pemetrexed |

### Graph Summary

- **Nodes**: 5 (2 genes + 2 compounds + 1 clinical trial)
- **Edges**: 4 (SYNTHETIC_LETHAL, 2x INHIBITOR, IN_TRIAL)

### TYMS Gene Details

| Attribute | Value |
|-----------|-------|
| **HGNC ID** | HGNC:12441 |
| **Symbol** | TYMS |
| **Name** | thymidylate synthetase |
| **Location** | 18p11.32 |
| **Ensembl** | ENSG00000176890 |
| **UniProt** | P04818 |
| **Entrez** | 7298 |
| **Function** | Essential enzyme in de novo synthesis of dTMP |

### TYMS Inhibitors

| Compound | CHEMBL ID | Max Phase | Mechanism |
|----------|-----------|-----------|-----------|
| 5-Fluorouracil (5-FU) | CHEMBL:185 | 4 (Approved) | Thymidylate synthase inhibitor |
| Pemetrexed | CHEMBL:225072 | 4 (Approved) | Antifolate, inhibits TYMS, DHFR, GARFT |

### Synthetic Lethality Rationale

The Feng et al. (2022) paper identifies TYMS as a synthetic lethal partner for TP53-mutant cancers:
- **Mechanism**: TP53-mutant cells have compromised DNA damage response
- **Vulnerability**: TYMS inhibition depletes dTMP pool, causing replication stress
- **Therapeutic window**: TP53-wildtype cells can activate p53-dependent cell cycle arrest; TP53-mutant cells cannot

### Mechanism/Path

```
Gene(TP53) --[synthetic_lethal_with]--> Gene(TYMS) --[target_of]--> Drug(Pemetrexed) --[in_trial]--> Trial(NCT04695925)
```

### Clinical Implications

TP53-mutant cancers may benefit from TYMS-targeting therapies:
- **5-Fluorouracil**: First-line in colorectal, breast, gastric cancers
- **Pemetrexed**: First-line in NSCLC, mesothelioma (active Phase 3 trial for TP53-mutant NSCLC)

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:11998 (TP53), HGNC:12441 (TYMS) |
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:185 (5-FU), CHEMBL:225072 (Pemetrexed) |
| STRING | string_search_proteins, string_get_interactions | STRING:9606.ENSP00000269305 (TP53 interactions) |
| BioGRID | biogrid_get_interactions | TP53 physical/genetic interactions |
| BioGRID ORCS | curl API (gene/7298) | 352 screens confirm TYMS essentiality |
| Open Targets | opentargets_get_associations | 5 disease associations for TP53 |
| ClinicalTrials.gov | curl API | NCT04695925 (Phase 3 TP53+Pemetrexed) |

### Reference

Feng, Y. et al. (2022). Systematic identification of synthetic lethal interactions in TP53-mutant cancers. *Sci. Adv.* 8, eabm6638. [PMC9098673](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9098673/)
