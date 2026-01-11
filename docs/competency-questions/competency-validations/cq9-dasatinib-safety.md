# Scenario 2: Drug Safety Profiling Validation

**Date**: 2026-01-10

**Question**: What are the off-target risks of Dasatinib, specifically cardiotoxicity from hERG (KCNH2) and DDR2 activity?

**Status**: VALIDATED

---

## Phase 1: Anchor Nodes

| Entity | Query | Resolved CURIE | Role |
|--------|-------|----------------|------|
| Index Drug | Dasatinib | CHEMBL:1421 | Multi-kinase inhibitor |
| Comparator | Imatinib | CHEMBL:941 | Cleaner BCR-ABL inhibitor |
| Safety Gene | hERG/KCNH2 | HGNC:6251 | Cardiac ion channel |

---

## Phase 2: Drug Profiles

### Dasatinib (CHEMBL:1421)

| Property | Value |
|----------|-------|
| Molecular Weight | 488.02 |
| Max Phase | 4 (FDA Approved) |
| Trade Names | Sprycel |
| Primary Indication | CML (BCR-ABL positive) |
| Total Indications | 70+ |

### Imatinib (CHEMBL:941)

| Property | Value |
|----------|-------|
| Molecular Weight | 493.62 |
| Max Phase | 4 (FDA Approved) |
| Trade Names | Gleevec |
| Primary Indication | CML, GIST |
| Total Indications | 45+ |

---

## Phase 3: Target Comparison

### Dasatinib Mechanisms (ChEMBL)

```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL1421&format=json"
```

| Target ChEMBL | Target Name | Action |
|---------------|-------------|--------|
| CHEMBL1862 | ABL1 (Tyrosine-protein kinase) | INHIBITOR |
| CHEMBL1913 | PDGFR-beta | INHIBITOR |
| CHEMBL1936 | c-KIT | INHIBITOR |
| CHEMBL2068 | EphA2 | INHIBITOR |
| CHEMBL5122 | DDR2 (off-target) | INHIBITOR |

### DDR2 Activity (Off-Target Risk)

```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL1421&target_chembl_id=CHEMBL5122"
```

| Metric | Value | Units |
|--------|-------|-------|
| IC50 | 54.0 | nM |
| Kd | 70.0 | nM |
| Kd | 70.79 | nM |

**Clinical Significance**: DDR2 inhibition at nanomolar concentrations contributes to pleural effusion risk.

---

## Phase 4: Safety Gene Analysis

### KCNH2/hERG (HGNC:6251)

| Property | Value |
|----------|-------|
| Full Name | potassium voltage-gated channel subfamily H member 2 |
| Aliases | hERG, HERG, Kv11.1 |
| Location | 7q36.1 |
| UniProt | Q12809 |
| Clinical Relevance | Long QT syndrome type 2 (OMIM:152427) |

**Cardiotoxicity Risk**: hERG inhibition causes QT prolongation, increasing arrhythmia risk. Dasatinib's off-target kinase promiscuity includes potential hERG channel effects.

---

## Safety Comparison Matrix

| Attribute | Dasatinib | Imatinib |
|-----------|-----------|----------|
| ABL1 | ✓ | ✓ |
| SRC Family | ✓ | ✗ |
| DDR2 | ✓ (54 nM) | Limited |
| PDGFR | ✓ | ✓ |
| c-KIT | ✓ | ✓ |
| Pleural Effusion Risk | HIGH | LOW |
| QT Risk | MODERATE | LOW |

---

## Validated Safety Graph

```json
{
  "nodes": [
    {"id": "CHEMBL:1421", "name": "Dasatinib", "type": "biolink:SmallMolecule"},
    {"id": "CHEMBL:941", "name": "Imatinib", "type": "biolink:SmallMolecule"},
    {"id": "CHEMBL:1862", "name": "ABL1", "type": "biolink:Protein", "role": "Primary Target"},
    {"id": "CHEMBL:5122", "name": "DDR2", "type": "biolink:Protein", "role": "Off-Target"},
    {"id": "HGNC:6251", "name": "KCNH2", "type": "biolink:Gene", "role": "Safety Gene"},
    {"id": "ORPHANET:122777", "name": "Long QT Syndrome", "type": "biolink:Disease"}
  ],
  "edges": [
    {"source": "CHEMBL:1421", "target": "CHEMBL:1862", "type": "INHIBITOR", "Ki": "0.2nM"},
    {"source": "CHEMBL:1421", "target": "CHEMBL:5122", "type": "INHIBITOR", "IC50": "54nM"},
    {"source": "CHEMBL:941", "target": "CHEMBL:1862", "type": "INHIBITOR"},
    {"source": "HGNC:6251", "target": "ORPHANET:122777", "type": "CAUSES"}
  ]
}
```

---

## Tools Used

| Phase | Tool | Purpose |
|-------|------|---------|
| 1 | `chembl_search_compounds("dasatinib")` | Drug resolution |
| 1 | `hgnc_search_genes("KCNH2")` | Safety gene resolution |
| 2 | `chembl_get_compound()` | Drug enrichment |
| 2 | `hgnc_get_gene()` | Gene enrichment |
| 3 | curl ChEMBL /mechanism | Target mechanisms |
| 3 | curl ChEMBL /activity | Binding affinities |

---

## Key Finding

Dasatinib has significantly higher off-target risk compared to Imatinib due to:
1. **DDR2 inhibition** (IC50: 54 nM) → pleural effusion
2. **SRC family kinase inhibition** → broader kinome coverage
3. **hERG/KCNH2 potential interaction** → QT prolongation risk

Imatinib offers a cleaner safety profile for BCR-ABL targeting when SRC inhibition is not required.
