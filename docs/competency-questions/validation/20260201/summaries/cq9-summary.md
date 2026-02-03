## CQ-9: Dasatinib Off-Target Safety Profile

**Question**: What are the off-target risks of Dasatinib, specifically cardiotoxicity from hERG (KCNH2) and DDR2 activity?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq9-dasatinib-safety`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| Dasatinib | CHEMBL:1421 | Compound | Index drug (multi-kinase inhibitor, Phase 4) |
| ABL1 | HGNC:76 | Gene | Primary target (BCR-ABL CML therapeutic) |
| SRC | HGNC:11283 | Gene | Off-target (bleeding, immunosuppression) |
| DDR2 | HGNC:2731 | Gene | Off-target (pleural effusion) |
| KCNH2 (hERG) | HGNC:6251 | Gene | Safety target (QT prolongation, cardiotoxicity) |
| Imatinib | CHEMBL:1642 | Compound | Comparator drug (cleaner safety profile) |

### Key Findings

- Dasatinib is a multi-kinase inhibitor approved for CML (Phase 4)
- Primary targets: ABL1 (CHEMBL:1862), BCR/ABL fusion protein (CHEMBL:2096618)
- Off-targets causing adverse events: SRC, PDGFR-beta, c-KIT, Ephrin-A2, DDR2
- Safety-critical target: hERG/KCNH2 - QT prolongation and cardiac arrhythmia risk
- DDR2 inhibition associated with pleural effusion (15-35% incidence)
- Imatinib has 4 targets vs Dasatinib's 6+, with lower pleural effusion risk

### Graph Summary

- **Nodes**: 5
- **Edges**: 4

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:1421 (Dasatinib), CHEMBL:1642 (Imatinib) |
| ChEMBL API (curl) | mechanism endpoint | CHEMBL:1862 (ABL1), CHEMBL:2096618 (BCR-ABL), CHEMBL:2363074 (SRC), CHEMBL:1913 (PDGFR-beta), CHEMBL:1936 (c-KIT), CHEMBL:2068 (Ephrin-A2) |
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:76, HGNC:11283, HGNC:2731, HGNC:6251 |

### Target Profile Comparison

| Target | ChEMBL Target | Dasatinib | Imatinib | Safety Concern |
|--------|---------------|-----------|----------|----------------|
| ABL1 | CHEMBL:1862 | Yes | Yes | Primary therapeutic |
| BCR-ABL | CHEMBL:2096618 | Yes | Yes | Primary therapeutic |
| c-KIT | CHEMBL:1936 | Yes | Yes | Myelosuppression |
| PDGFR-beta | CHEMBL:1913 | Yes | Yes | Fluid retention, edema |
| SRC | CHEMBL:2363074 | Yes | No | Bleeding events, immunosuppression |
| Ephrin-A2 | CHEMBL:2068 | Yes | No | Potential developmental effects |

### Adverse Events

| Event | Frequency | Mechanism |
|-------|-----------|-----------|
| Pleural effusion | 15-35% | Possibly DDR2 or PDGFR-related |
| QT prolongation | Rare but serious | hERG/KCNH2 inhibition |
| Myelosuppression | Common | c-KIT inhibition |
| Fluid retention/edema | Common | PDGFR inhibition |
| Bleeding events | Moderate | Platelet dysfunction via SRC family kinases |

### Mechanism/Path

`Dasatinib (CHEMBL:1421)` --[INHIBITOR, primary]--> `ABL1 (HGNC:76)`

`Dasatinib (CHEMBL:1421)` --[INHIBITOR, off-target]--> `SRC (HGNC:11283)`

`Dasatinib (CHEMBL:1421)` --[INHIBITOR, off-target]--> `DDR2 (HGNC:2731)` --> Pleural effusion

`Dasatinib (CHEMBL:1421)` --[INHIBITOR, safety_target]--> `KCNH2/hERG (HGNC:6251)` --> QT prolongation

### Cross-References

| Gene | CURIE | Full Name |
|------|-------|-----------|
| KCNH2 | HGNC:6251 | Potassium voltage-gated channel subfamily H member 2 |
| DDR2 | HGNC:2731 | Discoidin domain receptor tyrosine kinase 2 |
