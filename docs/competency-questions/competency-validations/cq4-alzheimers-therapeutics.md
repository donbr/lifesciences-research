# CQ-4: Alzheimer's Therapeutic Targets Validation

**Date**: 2026-01-10

**Question**: What drugs target amyloid-beta or tau proteins for Alzheimer's Disease treatment?

**Status**: VALIDATED (via MCP)

**Source**: Li, D., Yang, S., Tan, Z., et al. (2024). *DALK: Dynamic Co-Augmentation of LLMs and KG to answer Alzheimer's Disease Questions with Scientific Literature*. arXiv:2405.04819v1.

---

## Phase 1: Drug Targets

### BACE1 (Beta-Secretase)

| Property | Value |
|----------|-------|
| CURIE | HGNC:933 |
| Full Name | beta-secretase 1 |
| Role | Cleaves APP to produce amyloid-beta |

---

## Phase 2: BACE1 Inhibitors (Small Molecules)

| Drug | CHEMBL ID | Max Phase | MW | Indication |
|------|-----------|-----------|-----|------------|
| **Verubecestat** | CHEMBL:3301601 | Phase 3 | 409.42 | Alzheimer Disease |
| **Lanabecestat** | CHEMBL:3989948 | Phase 3 | 412.54 | Alzheimer Disease |
| **Atabecestat** | CHEMBL:3916243 | Phase 2 | 367.41 | Alzheimer Disease |

### Verubecestat (MK-8931)
- **Sponsor**: Merck
- **Synonyms**: MK-8931, SCH-900931
- **Status**: Phase 3 (discontinued due to lack of efficacy)

### Lanabecestat (AZD-3293)
- **Sponsor**: AstraZeneca/Eli Lilly
- **Synonyms**: AZD-3293, LY-3314814
- **Status**: Phase 3 (discontinued)

---

## Phase 3: Anti-Amyloid Antibodies (Biologics)

| Drug | CHEMBL ID | Max Phase | Trade Name | Indication |
|------|-----------|-----------|------------|------------|
| **Aducanumab** | CHEMBL:3039540 | Phase 4 (FDA Approved) | Aduhelm | Alzheimer Disease |
| **Lecanemab** | CHEMBL:3833321 | Phase 4 (FDA Approved) | Leqembi | Alzheimer Disease |

### Aducanumab (Aduhelm)
- **Sponsor**: Biogen
- **Synonyms**: BIIB-037
- **Target**: Aggregated amyloid-beta plaques
- **FDA Approval**: 2021 (accelerated approval)

### Lecanemab (Leqembi)
- **Sponsor**: Eisai/Biogen
- **Synonyms**: BAN-2401
- **Target**: Amyloid-beta protofibrils
- **FDA Approval**: 2023 (full approval)

---

## Phase 4: Clinical Trials (via MCP)

Query: `clinicaltrials_search_trials("Alzheimer amyloid", phase="PHASE3")`

**Results**: 99 Phase 3 trials

| NCT ID | Drug | Status | Sponsor Context |
|--------|------|--------|-----------------|
| NCT:05508789 | Donanemab | RECRUITING | Eli Lilly global study |
| NCT:06529732 | Lecanemab | RECRUITING | DIVA Study (surgical combo) |
| NCT:02245737 | Lanabecestat | TERMINATED | AMARANTH Study (failed) |
| NCT:03444870 | Gantenerumab | TERMINATED | Roche (failed) |
| NCT:02008357 | Solanezumab | COMPLETED | A4 Study (prevention) |

---

## Validated Knowledge Graph

```json
{
  "nodes": [
    {"id": "HGNC:933", "name": "BACE1", "type": "biolink:Gene", "role": "Beta-Secretase Target"},
    {"id": "HGNC:620", "name": "APP", "type": "biolink:Gene", "role": "Amyloid Precursor"},
    {"id": "CHEMBL:3301601", "name": "Verubecestat", "type": "biolink:SmallMolecule", "max_phase": 3},
    {"id": "CHEMBL:3989948", "name": "Lanabecestat", "type": "biolink:SmallMolecule", "max_phase": 3},
    {"id": "CHEMBL:3916243", "name": "Atabecestat", "type": "biolink:SmallMolecule", "max_phase": 2},
    {"id": "CHEMBL:3039540", "name": "Aducanumab", "type": "biolink:Antibody", "max_phase": 4, "trade_name": "Aduhelm"},
    {"id": "CHEMBL:3833321", "name": "Lecanemab", "type": "biolink:Antibody", "max_phase": 4, "trade_name": "Leqembi"},
    {"id": "MONDO:0004975", "name": "Alzheimer's Disease", "type": "biolink:Disease"}
  ],
  "edges": [
    {"source": "HGNC:933", "target": "HGNC:620", "type": "CLEAVES", "product": "Amyloid-beta"},
    {"source": "CHEMBL:3301601", "target": "HGNC:933", "type": "INHIBITOR"},
    {"source": "CHEMBL:3989948", "target": "HGNC:933", "type": "INHIBITOR"},
    {"source": "CHEMBL:3916243", "target": "HGNC:933", "type": "INHIBITOR"},
    {"source": "CHEMBL:3039540", "target": "MONDO:0004975", "type": "TREATS"},
    {"source": "CHEMBL:3833321", "target": "MONDO:0004975", "type": "TREATS"},
    {"source": "CHEMBL:3039540", "target": "HGNC:620", "type": "TARGETS_PRODUCT", "target": "Amyloid-beta plaques"},
    {"source": "CHEMBL:3833321", "target": "HGNC:620", "type": "TARGETS_PRODUCT", "target": "Amyloid-beta protofibrils"}
  ]
}
```

---

## Key Findings

1. **Two Approved Anti-Amyloid Antibodies**: Aducanumab (2021) and Lecanemab (2023) are FDA-approved
2. **BACE1 Inhibitors Failed**: All Phase 3 BACE1 inhibitors (Verubecestat, Lanabecestat) were discontinued
3. **Active Development**: Donanemab (Eli Lilly) is in recruiting Phase 3 trials
4. **99 Phase 3 Amyloid Trials**: Large pipeline of AD therapeutics
5. **Mechanism Shift**: Field has shifted from small molecule BACE1 inhibitors to anti-amyloid antibodies

---

## Therapeutic Landscape Summary

| Approach | Status | Examples |
|----------|--------|----------|
| BACE1 Inhibitors | FAILED | Verubecestat, Lanabecestat |
| Anti-Amyloid Plaque | APPROVED | Aducanumab (Aduhelm) |
| Anti-Amyloid Protofibril | APPROVED | Lecanemab (Leqembi) |
| Anti-Tau | IN DEVELOPMENT | Semorinemab, others |

---

## Tools Used

| Phase | Tool | Purpose |
|-------|------|---------|
| 1 | `hgnc_search_genes("BACE1")` | Target resolution |
| 2 | `chembl_search_compounds()` | BACE1 inhibitor discovery |
| 2 | `chembl_get_compound()` | Drug enrichment |
| 3 | `chembl_search_compounds()` | Antibody discovery |
| 4 | `clinicaltrials_search_trials()` | Trial landscape |

---

## Target group_id

`alzheimers-therapeutics`
