## CQ-15: CAR-T Regulatory Landscape

**Question**: Which CAR-T cell trials are currently navigating FDA or EMA milestones most rapidly?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq15-car-t-regulatory`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| Tisagenlecleucel (Kymriah) | CHEMBL:3301574 | CAR-T Therapy | FDA approved 2017, EMA 2018 |
| Axicabtagene ciloleucel (Yescarta) | CHEMBL:3989989 | CAR-T Therapy | FDA approved 2017, EMA 2018 |
| Brexucabtagene autoleucel (Tecartus) | - | CAR-T Therapy | FDA/EMA approved 2020 |
| Lisocabtagene maraleucel (Breyanzi) | - | CAR-T Therapy | FDA 2021, EMA 2022 |
| Idecabtagene vicleucel (Abecma) | - | CAR-T Therapy | FDA/EMA approved 2021 |
| Ciltacabtagene autoleucel (Carvykti) | - | CAR-T Therapy | FDA/EMA approved 2022 |
| CD19 | HGNC:1633 | Gene/Target | B-cell malignancies target |
| TNFRSF17 (BCMA) | HGNC:11913 | Gene/Target | Multiple myeloma target |

### Key Findings

- **6 FDA-approved CAR-T products**: Kymriah, Yescarta, Tecartus, Breyanzi, Abecma, Carvykti
- **Primary Targets**: CD19 (B-cell malignancies) and BCMA (multiple myeloma)
- **Regulatory Pathways**: Breakthrough Therapy Designation, Accelerated Approval, Priority Review, RMAT (FDA); PRIME, Conditional Marketing Authorization (EMA)
- **Emerging Trends**: Allogeneic CAR-T (off-the-shelf), dual-target CAR-T (CD19/CD22, BCMA/CD38), solid tumor expansion, autoimmune disease applications

### Graph Summary

- **Nodes**: 8 (6 approved therapies + 2 target genes)
- **Edges**: Multiple (TARGETS, TREATS, APPROVED_BY relationships)

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| ClinicalTrials.gov | curl API queries | NCT:06463861 (CD19 CARNK + 7x19 CAR-T trial) |
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:3301574 (Tisagenlecleucel), CHEMBL:3989989 (Axicabtagene ciloleucel) |
| HGNC | hgnc_search_genes | HGNC:1633 (CD19), HGNC:11913 (TNFRSF17/BCMA) |

### Approved CAR-T Therapies Detail

| Product | Brand | Target | Sponsor | FDA | EMA | Indications |
|---------|-------|--------|---------|-----|-----|-------------|
| Tisagenlecleucel | Kymriah | CD19 | Novartis | 2017 | 2018 | r/r B-ALL, r/r DLBCL, r/r FL |
| Axicabtagene ciloleucel | Yescarta | CD19 | Kite/Gilead | 2017 | 2018 | r/r DLBCL, r/r FL, r/r MCL |
| Brexucabtagene autoleucel | Tecartus | CD19 | Kite/Gilead | 2020 | 2020 | r/r MCL, r/r B-ALL (adult) |
| Lisocabtagene maraleucel | Breyanzi | CD19 | BMS/Juno | 2021 | 2022 | r/r DLBCL, r/r FL |
| Idecabtagene vicleucel | Abecma | BCMA | BMS/bluebird bio | 2021 | 2021 | r/r Multiple Myeloma |
| Ciltacabtagene autoleucel | Carvykti | BCMA | J&J/Legend | 2022 | 2022 | r/r Multiple Myeloma |

### Regulatory Framework

**FDA Pathways:**
- BLA (Biologics License Application)
- Breakthrough Therapy Designation
- Accelerated Approval
- Priority Review
- RMAT (Regenerative Medicine Advanced Therapy)

**EMA Pathways:**
- Centralized Marketing Authorization
- PRIME (PRIority MEdicines)
- Conditional Marketing Authorization
- Accelerated Assessment

### Key Considerations

- Manufacturing consistency
- Vein-to-vein time optimization
- Cytokine Release Syndrome (CRS) management
- Neurotoxicity (ICANS) monitoring

### Regulatory Challenges

- Manufacturing variability
- Long-term safety monitoring (secondary malignancies)
- Pricing and reimbursement
- Real-world evidence requirements

### Mechanism/Path

`CD19` --[TARGET_OF]--> `Kymriah/Yescarta/Tecartus/Breyanzi` --[TREATS]--> `B-cell malignancies`

`BCMA` --[TARGET_OF]--> `Abecma/Carvykti` --[TREATS]--> `Multiple Myeloma`
