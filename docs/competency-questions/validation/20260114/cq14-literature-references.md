# CQ14 Literature References

**Validation Date**: January 14, 2026
**Competency Question**: CQ14 - Feng et al. Synthetic Lethality Validation

---

## Core Reference Paper

### Feng et al. 2022 - Original Competency Question Source

**Citation**: Feng, W., et al. (2022). *Science Advances*, 8(19), eabm6638.

**PubMed**: [PMC9098673](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9098673/)

**Title**: Genome-wide CRISPR screens using isogenic cells reveal vulnerabilities conferred by loss of tumor suppressors

**Key Contribution**: Identified synthetic lethal gene pairs in TP53-mutant cancers through genome-wide CRISPR screening. This paper provides the foundational dataset for CQ14.

**Associated Datasets**:
- [dwb2023/sl_gene_pairs](https://huggingface.co/datasets/dwb2023/sl_gene_pairs) - 209 SL pairs
- [dwb2023/pmc_35559673_table_s6_sl_gene_detail](https://huggingface.co/datasets/dwb2023/pmc_35559673_table_s6_sl_gene_detail) - 81 genes

---

## Evidence Papers Discovered During Validation

### 1. TP53-TYMS Synthetic Lethality (BONUS DISCOVERY)

**PubMed ID**: 35559673

**Significance**: This paper provides **direct experimental evidence** for TP53-TYMS negative genetic interaction from BioGRID. This was discovered by validation Agent 4 and represents the "smoking gun" evidence for the synthetic lethality hypothesis.

**Year**: 2022

**Evidence Type**: BioGRID Negative Genetic Interaction

**Link**: https://pubmed.ncbi.nlm.nih.gov/35559673/

---

### 2. CHEK1-TYMS Synthetic Lethality

**PubMed ID**: 28319113

**Significance**: Establishes negative genetic interaction between CHEK1 (checkpoint kinase 1) and TYMS. Since TP53-deficient cells rely heavily on CHEK1 for intra-S and G2/M checkpoints, this connection is mechanistically important.

**Evidence Type**: BioGRID Negative Genetic Interaction

**Link**: https://pubmed.ncbi.nlm.nih.gov/28319113/

---

### 3. BioGRID Physical Interactions for TYMS

The following papers provided physical interaction data for TYMS from BioGRID:

| PubMed ID | Interaction Type | Key Finding |
|-----------|------------------|-------------|
| 21900206 | Two-hybrid | SH3GL2-TYMS |
| 22939629 | Co-fractionation | Multiple interactors |
| 22863883 | Co-fractionation | MAPK14-TYMS |
| 26344197 | Co-fractionation | DUT-TYMS, TXN-TYMS |
| 26638075 | Proximity Label-MS | POC5-TYMS |
| 35831314 | Co-fractionation | TPMT-TYMS |

---

## Drug Mechanism Literature

### Fluorouracil (5-FU)

**Key Papers** (from UniProt/ChEMBL annotations):

1. **Mechanism of Action**: 5-FU is converted to FdUMP which forms a covalent ternary complex with thymidylate synthase and 5,10-methylenetetrahydrofolate.

2. **Resistance Mechanisms**: Overexpression of TYMS or increased DPD (dihydropyrimidine dehydrogenase) activity.

3. **Additional Mechanisms**: 5-FU also incorporates into RNA (as FUTP) interfering with RNA processing.

**Review**: [Fluorouracil: Mechanisms of Resistance and Reversal Strategies - PMC6244944](https://pmc.ncbi.nlm.nih.gov/articles/PMC6244944/)

---

### Pemetrexed

**Key Papers**:

1. **Multi-target Mechanism**: Pemetrexed inhibits three enzymes:
   - Thymidylate synthase (CHEMBL:1952) - primary
   - Dihydrofolate reductase (CHEMBL:202) - secondary
   - Glycinamide ribonucleotide formyltransferase (CHEMBL:3972) - tertiary

**Review**: [Pemetrexed: biochemical and cellular pharmacology - Molecular Cancer Therapeutics](https://aacrjournals.org/mct/article/6/2/404/236244/)

---

## p21 (CDKN1A) Literature

**Foundational Papers** (from HGNC/UniProt):

| PubMed ID | Citation |
|-----------|----------|
| 8101826 | Original p21/CIP1 identification |
| 8118801 | p21 as CDK inhibitor |
| 7911228 | p21 in cell cycle regulation |
| 7698009 | p21 mechanism of action |

**Functional Note**: p21 is transcriptionally activated by TP53 and inhibits CDK2, CDK4, and CDK6, causing G1/S cell cycle arrest. In TP53-mutant cells, p21 is not induced, allowing cells to enter S-phase without the normal checkpoint.

---

## GADD45A Literature

**Foundational Papers** (from HGNC/UniProt):

| PubMed ID | Citation |
|-----------|----------|
| 1990262 | GADD45 identification |
| 8226988 | GADD45 function |
| 30617255 | Recent review |

**Functional Note**: GADD45A coordinates nucleotide excision repair (NER) and base excision repair (BER) pathways. TP53-dependent expression is required for efficient DNA repair after damage.

---

## Clinical Trial Literature

### IDOL Trial (NCT:06976892)

**Trial Title**: A Phase I/Ib Trial of Idetrexed (Alpha Folate Receptor Targeted Thymidylate Synthase Inhibitor) in Combination With Olaparib (a PARP Inhibitor) at Different Doses in Patients With Ovarian Cancer

**Sponsor**: Institute of Cancer Research, United Kingdom

**Collaborator**: Algok Bio Inc.

**Status**: RECRUITING (as of 2026-01-14)

**Registry Link**: https://clinicaltrials.gov/study/NCT06976892

**Key Innovation**: "Dual synthetic lethality" approach combining:
1. TYMS inhibition (Idetrexed) - causes thymidine depletion
2. PARP inhibition (Olaparib) - blocks DNA repair

---

## Machine Learning and Computational Literature

### PARIS: ML-based Synthetic Lethality Prediction

**PubMed ID**: 34454516

**Journal**: Molecular Cancer, 2021

**Key Finding**: Machine learning validation of synthetic lethality between CDKN2A, TYMP, and TYMS. Tested in RPE1 TP53-/- cells.

**Link**: https://pubmed.ncbi.nlm.nih.gov/34454516/

---

## Related Synthetic Lethality Papers (2022)

### Tang et al. - TP53 and ENDOD1

**Journal**: Nature Communications, 2022

**Link**: https://www.nature.com/articles/s41467-022-30311-w

**Relevance**: Shows active 2022 research on TP53 synthetic lethality with different targets.

---

## Computational Methods Reviews

**Computational methods, databases and tools for synthetic lethality prediction**

**PMC**: PMC9116379

**Relevance**: Overview of tools and databases for synthetic lethality research, including BioGRID and STRING.

---

## Summary: Key Papers by Evidence Type

| Evidence Type | PubMed IDs |
|---------------|------------|
| Synthetic Lethality | 35559673, 28319113, 34454516 |
| Drug Mechanisms | PMC6244944 (5-FU review) |
| Gene Functions | 8101826, 8118801, 1990262 |
| Clinical Trials | NCT:06976892 |

---

*Generated: 2026-01-14*
*Part of CQ14 validation package*
