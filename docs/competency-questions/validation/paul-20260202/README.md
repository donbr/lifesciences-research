# Paul's Competency Questions Validation

**Status**: ALL 12 QUESTIONS VALIDATED
**Date**: 2026-02-02
**Validation Agent Team**: 4 parallel research agents (FA1-FA4)

## Overview

This directory contains validation artifacts for 12 competency questions designed to support Paul Zamora's research at DMV Petri Dish. The questions focus on clinical outcomes, established drugs (Doxorubicin), tumor microenvironment, and lung cancer therapeutic approaches.

## Methodology

All research followed the **Fuzzy-to-Fact Protocol**:

1. **ANCHOR**: Resolve natural language queries to CURIEs via fuzzy search
2. **ENRICH**: Fetch full entity details with cross-references
3. **EXPAND**: Build edges via cross-reference validation
4. **VALIDATE**: Confirm with literature and clinical trial data
5. **PERSIST**: Store validated entities to knowledge graph

## Question Catalog

### Focus Area 1: Doxorubicin (CQ1-CQ4)

| File | Question | Status |
|------|----------|--------|
| [cq1-cardiotoxicity.md](cq1-cardiotoxicity.md) | Cardiotoxicity mechanisms (TOP2B) | VALIDATED |
| [cq2-resistance.md](cq2-resistance.md) | Resistance & escape mechanisms (ABC transporters) | VALIDATED |
| [cq3-protective-pathways.md](cq3-protective-pathways.md) | Toxicity-minimizing pathways (NRF2) | VALIDATED |
| [cq4-clinical-correlation.md](cq4-clinical-correlation.md) | Pre-clinical to clinical correlation | VALIDATED |

### Focus Area 2: Tumor Microenvironment (CQ5-CQ7)

| File | Question | Status |
|------|----------|--------|
| [cq5-immune-evasion.md](cq5-immune-evasion.md) | Immune hijacking mechanisms | VALIDATED |
| [cq6-metastasis.md](cq6-metastasis.md) | Metastasis gene expression (EMT) | VALIDATED |
| [cq7-protease-secretion.md](cq7-protease-secretion.md) | Protease secretion & intravasation | VALIDATED |

### Focus Area 3: NSCLC / Synthetic Lethality (CQ8-CQ9)

| File | Question | Status |
|------|----------|--------|
| [cq8-nsclc-candidates.md](cq8-nsclc-candidates.md) | NSCLC drug candidates | VALIDATED |
| [cq9-synthetic-lethality.md](cq9-synthetic-lethality.md) | Synthetic lethality state of art | VALIDATED |

### Focus Area 4: Method Validation (CQ10-CQ12)

| File | Question | Status |
|------|----------|--------|
| [cq10-method-steps.md](cq10-method-steps.md) | Pharmacological method steps | VALIDATED |
| [cq11-omix-validation.md](cq11-omix-validation.md) | Omix data validation pipeline | VALIDATED |
| [cq12-reasoning-chain.md](cq12-reasoning-chain.md) | Full reasoning chain demonstration | VALIDATED |

## Key CURIEs Resolved

### Compounds
| Entity | CURIE | Source |
|--------|-------|--------|
| Doxorubicin | CHEMBL:53463 | ChEMBL |
| Dexrazoxane | CHEMBL:1738 | ChEMBL |
| Tariquidar | CHEMBL:348475 | ChEMBL |
| Olaparib | CHEMBL:521686 | ChEMBL |
| Sotorasib | CHEMBL:4594399 | ChEMBL |
| Osimertinib | CHEMBL:3353410 | ChEMBL |

### Genes
| Entity | CURIE | Function |
|--------|-------|----------|
| TOP2B | HGNC:11990 | Cardiotoxicity target |
| ABCB1/MDR1 | HGNC:40 | Drug efflux |
| NFE2L2/NRF2 | HGNC:7782 | Antioxidant master regulator |
| CD274/PD-L1 | HGNC:17635 | Immune checkpoint |
| KRAS | HGNC:6407 | Oncogene |
| EGFR | HGNC:3236 | Receptor tyrosine kinase |
| BRCA1 | HGNC:1100 | DNA repair |

### Pathways
| Entity | CURIE | Description |
|--------|-------|-------------|
| Oxidative stress response | WP:WP408 | 34 genes |
| ABC-family transport | WP:WP1780 | Drug efflux |
| EMT in cancer | WP:WP3493 | Metastasis |
| PD-L1 expression | WP:WP4557 | Immune evasion |

## Tools Used

| Tool | Purpose | Calls |
|------|---------|-------|
| mcp__lifesciences-research__chembl_* | Compound lookup | 25+ |
| mcp__lifesciences-research__hgnc_* | Gene resolution | 40+ |
| mcp__lifesciences-research__string_* | Interaction networks | 15+ |
| mcp__lifesciences-research__opentargets_* | Disease associations | 10+ |
| mcp__lifesciences-research__wikipathways_* | Pathway context | 12+ |
| mcp__lifesciences-research__entrez_* | PubMed links | 8+ |
| ClinicalTrials.gov (curl) | Trial data | 20+ |

## Graphiti Persistence

All validated entities persisted to graphiti-docker with group_ids:

| group_id | Focus Area | CQs |
|----------|------------|-----|
| paul-fa1-doxorubicin | Doxorubicin | CQ1-CQ4 |
| paul-fa2-tme | Tumor Microenvironment | CQ5-CQ7 |
| paul-fa3-nsclc | NSCLC/Synthetic Lethality | CQ8-CQ9 |
| paul-fa4-method | Method Validation | CQ10-CQ12 |

## Navigation

- [EXECUTIVE-SUMMARY.md](EXECUTIVE-SUMMARY.md) - Consolidated findings
- [../../../competency-questions-paul.md](../../../competency-questions-paul.md) - Original questions
