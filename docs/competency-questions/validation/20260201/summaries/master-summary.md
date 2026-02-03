# Master Summary: Life Sciences Competency Questions Validation

**Date**: 2026-02-01
**Version**: 1.0
**Total CQs Validated**: 15

---

## 1. Executive Summary

This document consolidates the validation results for 15 competency questions (CQs) executed on 2026-02-01. These CQs demonstrate the capability of the Life Sciences MCP (Model Context Protocol) platform to answer complex drug discovery and repurposing questions by integrating data from multiple authoritative biological databases.

**Overall Status**: All 15 CQs successfully validated, demonstrating:
- Multi-hop reasoning across gene, protein, compound, disease, and clinical trial entities
- Fuzzy-to-Fact protocol for entity resolution via CURIEs
- Cross-database integration (HGNC, ChEMBL, STRING, UniProt, Open Targets, WikiPathways, ClinicalTrials.gov)
- Knowledge graph construction with provenance tracking

**Key Themes Covered**:
- Drug mechanism of action (CQ1, CQ11)
- Drug repurposing (CQ2, CQ7)
- Gene-protein interaction networks (CQ3, CQ5, CQ6)
- Therapeutic target identification (CQ4, CQ10)
- Synthetic lethality (CQ8, CQ14)
- Drug safety profiling (CQ9)
- Clinical trial landscape analysis (CQ12, CQ13, CQ15)

---

## 2. Overview Table

| CQ | Title | Question | Nodes | Edges | group_id | Status |
|----|-------|----------|-------|-------|----------|--------|
| CQ1 | Palovarotene Mechanism for FOP | By what mechanism does Palovarotene treat Fibrodysplasia Ossificans Progressiva (FOP)? | 4 | 3 | cq1-fop-mechanism | VALIDATED |
| CQ2 | FOP Drug Repurposing via BMP Pathway | What other drugs targeting the BMP Signaling Pathway could be repurposed for FOP? | 8 | 4 | cq2-fop-repurposing | VALIDATED |
| CQ3 | Alzheimer's Gene-Protein Interaction Network | What genes and proteins are implicated in Alzheimer's Disease progression, and how do they interact? | 11 | 8 | cq3-alzheimers-gene-network | VALIDATED |
| CQ4 | Alzheimer's Disease Therapeutic Targets | What drugs target amyloid-beta or tau proteins for Alzheimer's Disease treatment? | 8 | 5 | cq4-alzheimers-therapeutics | VALIDATED |
| CQ5 | MAPK Regulatory Cascade | In the MAPK signaling cascade, which proteins regulate downstream targets and with what direction? | 8 | 8 | cq5-mapk-regulatory-cascade | VALIDATED |
| CQ6 | BRCA1 Regulatory Network | What transcription factors regulate BRCA1 expression, and what genes does BRCA1 regulate? | 9 | 8 | cq6-brca1-regulatory-network | VALIDATED |
| CQ7 | NGLY1 Deficiency Multi-Hop Drug Repurposing | For NGLY1 deficiency, what are the associated genes, and what existing drugs target proteins in those pathways? | 5 | 3 | cq7-ngly1-drug-repurposing | VALIDATED |
| CQ8 | ARID1A Synthetic Lethality in Ovarian Cancer | How can we identify therapeutic strategies for ARID1A-deficient Ovarian Cancer using synthetic lethality? | 9 | 4 | cq8-arid1a-synthetic-lethality | VALIDATED |
| CQ9 | Dasatinib Off-Target Safety Profile | What are the off-target risks of Dasatinib, specifically cardiotoxicity from hERG (KCNH2) and DDR2 activity? | 5 | 4 | cq9-dasatinib-safety | VALIDATED |
| CQ10 | Huntington's Disease Novel Therapeutic Targets | What novel therapeutic targets exist for Huntington's Disease that are not covered by current Phase 3 interventions? | 8 | - | cq10-huntingtons-novel-targets | VALIDATED |
| CQ11 | p53-MDM2-Nutlin Therapeutic Axis | How do we build and validate a knowledge graph for the p53-MDM2-Nutlin therapeutic axis? | 4 | 4 | cq11-p53-mdm2-nutlin | VALIDATED |
| CQ12 | Health Emergencies Clinical Trial Landscape 2026 | What are the key health emergencies or emerging health priorities that multiple clinical trials are targeting right now? | 4 | 11 | cq12-health-emergencies-2026 | VALIDATED |
| CQ13 | High-Commercialization Phase 3 Trials | Which clinical trials have the highest potential for commercialization or are attracting the most investment interest? | 4 | 2 | cq13-high-commercialization-trials | VALIDATED |
| CQ14 | Feng Synthetic Lethality Validation | How can we validate synthetic lethal gene pairs from Feng et al. (2022) and identify druggable opportunities for TP53-mutant cancers? | 4 | - | cq14-feng-synthetic-lethality | VALIDATED (Partial) |
| CQ15 | CAR-T Regulatory Landscape | Which CAR-T cell trials are currently navigating FDA or EMA milestones most rapidly? | 8 | - | cq15-car-t-regulatory | VALIDATED |

---

## 3. Provenance Summary

### API Sources Used

| Source | CQs Using | Tools/Endpoints Used |
|--------|-----------|----------------------|
| **ChEMBL** | CQ1, CQ2, CQ4, CQ7, CQ8, CQ9, CQ11, CQ13, CQ14, CQ15 | chembl_search_compounds, chembl_get_compound, mechanism endpoint (curl) |
| **HGNC** | CQ1, CQ2, CQ3, CQ4, CQ5, CQ6, CQ7, CQ8, CQ9, CQ10, CQ11, CQ14, CQ15 | hgnc_search_genes, hgnc_get_gene |
| **STRING** | CQ1, CQ3, CQ5, CQ6, CQ7, CQ8, CQ10, CQ11 | string_search_proteins, string_get_interactions, curl API |
| **Open Targets** | CQ1, CQ3, CQ7, CQ10 | opentargets_get_associations |
| **WikiPathways** | CQ2, CQ5 | wikipathways_search_pathways, wikipathways_get_pathway_components |
| **ClinicalTrials.gov** | CQ4, CQ8, CQ10, CQ12, CQ13, CQ15 | curl API (query.intr, query.cond, filter.overallStatus) |
| **UniProt** | CQ11 | UniProt accessions referenced |
| **BioGRID ORCS** | CQ14 | curl API (requires access key - not fully validated) |

### CURIE Registry

All unique CURIEs across all 15 CQs, grouped by namespace:

#### HGNC (Gene)
| CURIE | Symbol | Name | Appears In |
|-------|--------|------|------------|
| HGNC:171 | ACVR1 | Activin A receptor type 1 | CQ1, CQ2 |
| HGNC:270 | PARP1 | Poly(ADP-ribose) polymerase 1 | CQ8 |
| HGNC:613 | APOE | Apolipoprotein E | CQ3 |
| HGNC:620 | APP | Amyloid precursor protein | CQ3, CQ4 |
| HGNC:882 | ATR | ATR serine/threonine kinase | CQ8 |
| HGNC:933 | BACE1 | Beta-secretase 1 | CQ3, CQ4 |
| HGNC:952 | BARD1 | BRCA1 associated RING domain 1 | CQ6 |
| HGNC:1033 | BDNF | Brain derived neurotrophic factor | CQ10 |
| HGNC:1076 | BMPR1A | Bone morphogenetic protein receptor type 1A | CQ2 |
| HGNC:1097 | BRAF | B-Raf proto-oncogene | CQ5 |
| HGNC:1100 | BRCA1 | BRCA1 DNA repair associated | CQ6 |
| HGNC:1101 | BRCA2 | BRCA2 DNA repair associated | CQ6 |
| HGNC:1633 | CD19 | CD19 molecule | CQ15 |
| HGNC:1979 | CDK5 | Cyclin dependent kinase 5 | CQ4 |
| HGNC:2095 | CLU | Clusterin | CQ3 |
| HGNC:2731 | DDR2 | Discoidin domain receptor tyrosine kinase 2 | CQ9 |
| HGNC:3113 | E2F1 | E2F transcription factor 1 | CQ6 |
| HGNC:3527 | EZH2 | Enhancer of zeste 2 polycomb repressive complex 2 subunit | CQ8 |
| HGNC:4095 | GADD45A | Growth arrest and DNA damage inducible alpha | CQ6 |
| HGNC:4617 | GSK3B | Glycogen synthase kinase 3 beta | CQ3, CQ4 |
| HGNC:4851 | HTT | Huntingtin | CQ10 |
| HGNC:6180 | ITPR1 | Inositol 1,4,5-trisphosphate receptor type 1 | CQ10 |
| HGNC:6251 | KCNH2 | Potassium voltage-gated channel subfamily H member 2 (hERG) | CQ9 |
| HGNC:6407 | KRAS | KRAS proto-oncogene | CQ5 |
| HGNC:6771 | SMAD5 | SMAD family member 5 | CQ2 |
| HGNC:6840 | MAP2K1 | Mitogen-activated protein kinase kinase 1 (MEK1) | CQ5 |
| HGNC:6842 | MAP2K2 | Mitogen-activated protein kinase kinase 2 (MEK2) | CQ5 |
| HGNC:6871 | MAPK1 | Mitogen-activated protein kinase 1 (ERK2) | CQ5 |
| HGNC:6893 | MAPT | Microtubule associated protein tau | CQ3, CQ4 |
| HGNC:6973 | MDM2 | MDM2 proto-oncogene | CQ11 |
| HGNC:7553 | MYC | MYC proto-oncogene | CQ6 |
| HGNC:7767 | NCSTN | Nicastrin | CQ3 |
| HGNC:7781 | NFE2L1 | NFE2 like bZIP transcription factor 1 (NRF1) | CQ7 |
| HGNC:9508 | PSEN1 | Presenilin 1 | CQ3, CQ4 |
| HGNC:9509 | PSEN2 | Presenilin 2 | CQ3 |
| HGNC:9817 | RAD51 | RAD51 recombinase | CQ6 |
| HGNC:9829 | RAF1 | Raf-1 proto-oncogene | CQ5 |
| HGNC:9866 | RARG | Retinoic acid receptor gamma | CQ1 |
| HGNC:9966 | REST | RE1 silencing transcription factor | CQ10 |
| HGNC:10935 | SLC18A2 | Solute carrier family 18 member A2 (VMAT2) | CQ10 |
| HGNC:11100 | SMARCA4 | SWI/SNF related matrix associated actin dependent regulator of chromatin subfamily a member 4 | CQ8 |
| HGNC:11103 | SMARCB1 | SWI/SNF related matrix associated actin dependent regulator of chromatin subfamily b member 1 | CQ8 |
| HGNC:11108 | SMARCC1 | SWI/SNF related matrix associated actin dependent regulator of chromatin subfamily c member 1 | CQ8 |
| HGNC:11109 | SMARCC2 | SWI/SNF related matrix associated actin dependent regulator of chromatin subfamily c member 2 | CQ8 |
| HGNC:11110 | ARID1A | AT-rich interaction domain 1A | CQ8 |
| HGNC:11185 | SORL1 | Sortilin related receptor 1 | CQ3 |
| HGNC:11205 | SP1 | Sp1 transcription factor | CQ6 |
| HGNC:11283 | SRC | SRC proto-oncogene | CQ9 |
| HGNC:11913 | TNFRSF17 | TNF receptor superfamily member 17 (BCMA) | CQ15 |
| HGNC:11998 | TP53 | Tumor protein p53 | CQ6, CQ11, CQ14 |
| HGNC:12441 | TYMS | Thymidylate synthetase | CQ14 |
| HGNC:12666 | VCP | Valosin containing protein | CQ7 |
| HGNC:16508 | PSENEN | Presenilin enhancer gamma-secretase subunit | CQ3 |
| HGNC:17646 | NGLY1 | N-glycanase 1 | CQ7 |
| HGNC:18040 | ARID1B | AT-rich interaction domain 1B | CQ8 |
| HGNC:28454 | DERL1 | Derlin 1 | CQ7 |
| HGNC:76 | ABL1 | ABL proto-oncogene 1 | CQ9 |

#### ChEMBL (Compound)
| CURIE | Name | Max Phase | Appears In |
|-------|------|-----------|------------|
| CHEMBL:185 | 5-Fluorouracil | 4 (Approved) | CQ14 |
| CHEMBL:191334 | Nutlin-3 | Research | CQ11 |
| CHEMBL:325041 | Bortezomib | 4 (Approved) | CQ7 |
| CHEMBL:478629 | Dorsomorphin | Preclinical | CQ2 |
| CHEMBL:601719 | Crizotinib | 4 (Approved) | CQ2 |
| CHEMBL:1421 | Dasatinib | 4 (Approved) | CQ9 |
| CHEMBL:1642 | Imatinib | 4 (Approved) | CQ9 |
| CHEMBL:2103868 | Cabozantinib | 4 (Approved) | CQ2 |
| CHEMBL:2105648 | Palovarotene | 4 (Approved) | CQ1 |
| CHEMBL:2143592 | BMS-794833 | Phase 1 | CQ2 |
| CHEMBL:2360464 | Pemetrexed | 4 (Approved) | CQ14 |
| CHEMBL:2402737 | Idasanutlin | Phase 3 | CQ11 |
| CHEMBL:3039540 | Aducanumab | 4 (Approved) | CQ4 |
| CHEMBL:3301574 | Tisagenlecleucel | 4 (Approved) | CQ15 |
| CHEMBL:3414621 | Tazemetostat | 4 (Approved) | CQ8 |
| CHEMBL:3833321 | Lecanemab | 4 (Approved) | CQ4 |
| CHEMBL:3989989 | Axicabtagene ciloleucel | 4 (Approved) | CQ15 |
| CHEMBL:4297245 | Donanemab | 4 (Approved) | CQ4 |
| CHEMBL:4297839 | Tirzepatide | 4 (Approved) | CQ13 |
| CHEMBL:5095485 | Retatrutide | Phase 3 | CQ13 |
| CHEMBL:5303350 | LDN-193189 | Preclinical | CQ2 |

#### STRING (Protein)
| CURIE | Protein | Appears In |
|-------|---------|------------|
| STRING:9606.ENSP00000215832 | MAPK1 | CQ5 |
| STRING:9606.ENSP00000269305 | TP53 | CQ11 |
| STRING:9606.ENSP00000280700 | NGLY1 | CQ7 |
| STRING:9606.ENSP00000284981 | APP | CQ3 |
| STRING:9606.ENSP00000320485 | ARID1A | CQ8 |
| STRING:9606.ENSP00000326366 | PSEN1 | CQ3 |
| STRING:9606.ENSP00000347184 | HTT | CQ10 |
| STRING:9606.ENSP00000401888 | RAF1 | CQ5 |
| STRING:9606.ENSP00000418960 | BRCA1 | CQ6 |

#### MONDO (Disease)
| CURIE | Name | Appears In |
|-------|------|------------|
| MONDO:0004975 | Alzheimer disease | CQ3, CQ4 |
| MONDO:0007606 | Fibrodysplasia ossificans progressiva | CQ1, CQ2 |
| MONDO:0007739 | Huntington disease | CQ10 |
| MONDO:0800044 | NGLY1 deficiency | CQ7 |

#### WikiPathways (Pathway)
| CURIE | Name | Appears In |
|-------|------|------------|
| WP:WP382 | MAPK signaling | CQ5 |
| WP:WP422 | MAPK cascade | CQ5 |
| WP:WP2760 | Signaling by BMP | CQ2 |

#### UniProt (Protein)
| CURIE | Protein | Appears In |
|-------|---------|------------|
| UniProt:P04637 | TP53 protein | CQ11 |
| UniProt:Q00987 | MDM2 protein | CQ11 |

#### ClinicalTrials.gov (NCT)
| CURIE | Title | Phase | Appears In |
|-------|-------|-------|------------|
| NCT:02516046 | 18F-AV-1451 Autopsy Study | - | CQ4 |
| NCT:03225846 | WVE-120102 | - | CQ10 |
| NCT:03348631 | Tazemetostat in Recurrent Ovarian or Endometrial Cancer | Phase 2 | CQ8 |
| NCT:04396873 | PET Imaging of Cyclooxygenases in Neurodegeneration | Phase 1 | CQ12 |
| NCT:04807673 | Pembrolizumab + Chemo vs CRT for ESCC | Phase 3 | CQ12 |
| NCT:05548231 | LY3437943 Trial (China) | Phase 3 | CQ13 |
| NCT:05791396 | FMT to Eradicate Carbapenem-resistant Enterobacteriaceae | Phase 1 | CQ12 |
| NCT:05882045 | Retatrutide CVD | Phase 3 | CQ13 |
| NCT:05903352 | Customized Antibiotic Duration for CAP | Phase 3 | CQ12 |
| NCT:06399368 | LEQEMBI Effect on Cerebral and Retinal Amyloid | Observational | CQ12 |
| NCT:06436146 | Liraglutide for Obesity in HIV | Phase 4 | CQ12 |
| NCT:06463861 | Sequential CD19 CARNK and CAR-T in B Cell Lymphoma | Phase 1 | CQ12, CQ15 |
| NCT:06661383 | Retatrutide vs Tirzepatide | Phase 3 | CQ13 |
| NCT:06938088 | Tirzepatide for Alcohol Use in Schizophrenia | Phase 2 | CQ12 |
| NCT:07136714 | Semaglutide for Depression with Obesity | Phase 4 | CQ12 |
| NCT:07288879 | DALY II Japan/MB-CART2019.1 for DLBCL | Phase 2 | CQ12 |
| NCT:07324161 | Transcranial Magnetic Stimulation for Alzheimer's | N/A | CQ12 |

---

## 4. Cross-CQ Entity Index

Entities appearing in multiple CQs:

| Entity | Symbol | CURIEs | Appears In |
|--------|--------|--------|------------|
| Tumor protein p53 | TP53 | HGNC:11998, STRING:9606.ENSP00000269305, UniProt:P04637 | CQ6, CQ11, CQ14 |
| Activin A receptor type 1 | ACVR1 | HGNC:171 | CQ1, CQ2 |
| Amyloid precursor protein | APP | HGNC:620, STRING:9606.ENSP00000284981 | CQ3, CQ4 |
| Microtubule associated protein tau | MAPT | HGNC:6893 | CQ3, CQ4 |
| Presenilin 1 | PSEN1 | HGNC:9508, STRING:9606.ENSP00000326366 | CQ3, CQ4 |
| Beta-secretase 1 | BACE1 | HGNC:933 | CQ3, CQ4 |
| Glycogen synthase kinase 3 beta | GSK3B | HGNC:4617 | CQ3, CQ4 |
| Fibrodysplasia ossificans progressiva | FOP | MONDO:0007606 | CQ1, CQ2 |
| Alzheimer disease | AD | MONDO:0004975 | CQ3, CQ4 |

---

## 5. Knowledge Graph Statistics

### Total Counts (Aggregated)

| Metric | Count |
|--------|-------|
| Total unique nodes (estimated) | 95+ |
| Total unique edges (estimated) | 76+ |
| Total unique HGNC gene CURIEs | 56 |
| Total unique ChEMBL compound CURIEs | 21 |
| Total unique STRING protein CURIEs | 9 |
| Total unique MONDO disease CURIEs | 4 |
| Total unique WikiPathways CURIEs | 3 |
| Total unique clinical trial CURIEs | 17 |

### Nodes by Type

| Type | Count | Examples |
|------|-------|----------|
| Gene | 56 | TP53, BRCA1, APP, HTT, MAPK1, ACVR1 |
| Compound/Drug | 21 | Palovarotene, Dasatinib, Lecanemab, Tazemetostat |
| Disease | 4 | FOP, Alzheimer, Huntington, NGLY1 deficiency |
| Pathway | 3 | BMP signaling, MAPK cascade, MAPK signaling |
| Clinical Trial | 17 | Various Phase 1-4 and observational studies |
| Protein | 9 | TP53, APP, BRCA1, HTT, NGLY1 (STRING IDs) |

### Edges by Type

| Edge Type | Count | Examples |
|-----------|-------|----------|
| AGONIST | 1 | Palovarotene -> RARG |
| INHIBITOR | 12+ | Dorsomorphin -> ACVR1, Tazemetostat -> EZH2, Dasatinib -> ABL1 |
| REGULATES | 8+ | E2F1 -> BRCA1, BRCA1 -> MYC, RAF1 -> MAP2K1 |
| INTERACTS | 15+ | APP <-> APOE, BRCA1 <-> BARD1, NGLY1 <-> VCP |
| SYNTHETIC_LETHAL | 5+ | ARID1A <-> EZH2, TP53 <-> TYMS |
| PHOSPHORYLATES | 6+ | MAP2K1 -> MAPK1, GSK3B -> MAPT |
| CLEAVES | 2 | BACE1 -> APP, PSEN1 -> APP |
| CAUSES | 2 | ACVR1 -> FOP, HTT-mutant -> disease phenotypes |
| TARGETS | 10+ | Lecanemab -> APP, Tazemetostat -> EZH2 |
| MEMBER_OF | 2+ | ACVR1 -> BMP Pathway, genes in MAPK cascade |
| UBIQUITINATES | 1 | MDM2 -> TP53 |
| TRANSCRIBES | 1 | TP53 -> MDM2 |

---

## 6. Graphiti Persistence Summary

| group_id | CQ | Episode Name | Status |
|----------|-----|--------------|--------|
| cq1-fop-mechanism | CQ1 | Palovarotene Mechanism for FOP | Persisted |
| cq2-fop-repurposing | CQ2 | FOP Drug Repurposing via BMP Pathway | Persisted |
| cq3-alzheimers-gene-network | CQ3 | Alzheimer's Gene-Protein Interaction Network | Persisted |
| cq4-alzheimers-therapeutics | CQ4 | Alzheimer's Disease Therapeutic Targets | Persisted |
| cq5-mapk-regulatory-cascade | CQ5 | MAPK Regulatory Cascade | Persisted |
| cq6-brca1-regulatory-network | CQ6 | BRCA1 Regulatory Network | Persisted |
| cq7-ngly1-drug-repurposing | CQ7 | NGLY1 Deficiency Multi-Hop Drug Repurposing | Persisted |
| cq8-arid1a-synthetic-lethality | CQ8 | ARID1A Synthetic Lethality in Ovarian Cancer | Persisted |
| cq9-dasatinib-safety | CQ9 | Dasatinib Off-Target Safety Profile | Persisted |
| cq10-huntingtons-novel-targets | CQ10 | Huntington's Disease Novel Therapeutic Targets | Persisted |
| cq11-p53-mdm2-nutlin | CQ11 | p53-MDM2-Nutlin Therapeutic Axis | Persisted |
| cq12-health-emergencies-2026 | CQ12 | Health Emergencies Clinical Trial Landscape 2026 | Persisted |
| cq13-high-commercialization-trials | CQ13 | High-Commercialization Phase 3 Trials | Persisted |
| cq14-feng-synthetic-lethality | CQ14 | Feng Synthetic Lethality Validation | Persisted (Partial) |
| cq15-car-t-regulatory | CQ15 | CAR-T Regulatory Landscape | Persisted |

---

## 7. Validation Notes

### Fully Validated CQs (14/15)
All CQs except CQ14 were fully validated with complete API access.

### Partial Validation (1/15)
- **CQ14 (Feng Synthetic Lethality)**: BioGRID ORCS API requires access key for CRISPR screen data validation. Gene and compound data validated via HGNC and ChEMBL.

### API Access Requirements
| API | Access Type | Notes |
|-----|-------------|-------|
| HGNC | Public | No API key required |
| ChEMBL | Public | No API key required |
| STRING | Public | No API key required |
| Open Targets | Public | No API key required |
| WikiPathways | Public | No API key required |
| ClinicalTrials.gov | Public | Cloudflare blocking for Python clients; curl works |
| BioGRID ORCS | Restricted | Requires API access key |

---

## 8. Appendix: Key Mechanisms Discovered

### Drug Mechanism Highlights

1. **Palovarotene (CQ1)**: RARG agonist -> downregulates BMP signaling -> reduces ectopic bone formation in FOP
2. **Anti-amyloid antibodies (CQ4)**: Lecanemab, Aducanumab, Donanemab target amyloid protofibrils
3. **Tazemetostat (CQ8)**: EZH2 inhibitor synthetic lethal with ARID1A loss in ovarian cancer
4. **Idasanutlin (CQ11)**: MDM2 inhibitor restores p53 function in WT-TP53 tumors
5. **Dasatinib (CQ9)**: Multi-kinase inhibitor with off-target hERG (cardiotoxicity) and DDR2 (pleural effusion)

### Synthetic Lethality Pairs

| Anchor Gene | Partner | Mechanism | Drugs |
|-------------|---------|-----------|-------|
| ARID1A | EZH2 | PRC2 antagonizes SWI/SNF | Tazemetostat |
| ARID1A | ATR | Replication stress dependency | VX-970, AZD6738 |
| ARID1A | PARP1 | HR deficiency (BRCAness) | Olaparib |
| TP53 | TYMS | DNA damage response defect | 5-FU, Pemetrexed |

### Novel Therapeutic Targets (Underexplored)

| Disease | Covered Targets | Underexplored Targets |
|---------|-----------------|----------------------|
| Huntington's | VMAT2 (symptomatic) | ITPR1, REST, BDNF, CREBBP, HAP1, mitochondrial |
| Alzheimer's | Amyloid-beta, BACE1 | Tau (MAPT), GSK3B, CDK5, neuroinflammation |

---

*Generated: 2026-02-01*
*Platform: Life Sciences MCP v0.1.0*
*Validation Framework: Competency Questions Catalog v1.0*
