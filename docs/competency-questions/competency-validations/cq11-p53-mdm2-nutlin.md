# Scenario 4: Pathway Validation (p53-MDM2-Nutlin)

**Date**: 2026-01-10

**Question**: How do we build and validate a knowledge graph for the p53-MDM2-Nutlin therapeutic axis?

**Status**: VALIDATED

---

## Phase 1: Anchor Nodes

| Entity | Query | Resolved CURIE | Role |
|--------|-------|----------------|------|
| Tumor Suppressor | TP53 | HGNC:11998 | Central node |
| Oncogene | MDM2 | HGNC:6973 | E3 ubiquitin ligase |
| Drug | Nutlin-3 | CHEMBL:191334 | MDM2 inhibitor |

---

## Phase 2: Entity Enrichment

### TP53 (STRING: 9606.ENSP00000269305)

> Cellular tumor antigen p53; Acts as a tumor suppressor in many tumor types; induces growth arrest or apoptosis depending on the physiological circumstances and cell type.

### Nutlin-3 (CHEMBL:191334)

| Property | Value |
|----------|-------|
| Molecular Weight | 581.5 |
| SMILES | Complex imidazoline structure |
| Ki (vs MDM2) | 36 nM |
| Potency | 300 nM |

---

## Phase 3: STRING Interaction Network

```python
string_get_interactions("STRING:9606.ENSP00000269305", required_score=900)
```

**TP53 High-Confidence Interactors** (score > 0.99):

| Partner | Score | Evidence Source |
|---------|-------|-----------------|
| SIRT1 | 0.999 | Co-expression, text-mining |
| MDM2 | 0.999 | (via network) |
| MDM4 | 0.999 | Co-expression, database |
| USP7 | 0.999 | Experimental, text-mining |
| EP300 | 0.999 | Experimental, text-mining |
| ATM | 0.995 | Database, text-mining |
| DAXX | 0.995 | Experimental |
| RPA1 | 0.999 | Experimental, text-mining |

---

## Phase 4: Drug-Target Edge

### Nutlin-3 Activity vs MDM2

```bash
curl "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL191334"
```

| Target ChEMBL | Target Name | Metric | Value | Units |
|---------------|-------------|--------|-------|-------|
| CHEMBL5023 | E3 ubiquitin-protein ligase Mdm2 | Ki | 36.0 | nM |
| CHEMBL5023 | E3 ubiquitin-protein ligase Mdm2 | IC50 | 1500.0 | nM |

---

## Validated Pathway Graph

```json
{
  "nodes": [
    {"id": "HGNC:11998", "name": "TP53", "type": "biolink:Gene", "role": "Tumor Suppressor"},
    {"id": "HGNC:6973", "name": "MDM2", "type": "biolink:Gene", "role": "E3 Ligase/Oncogene"},
    {"id": "CHEMBL:5023", "name": "MDM2 Protein", "type": "biolink:Protein"},
    {"id": "CHEMBL:191334", "name": "Nutlin-3", "type": "biolink:SmallMolecule"},
    {"id": "HGNC:6974", "name": "MDM4", "type": "biolink:Gene", "role": "TP53 Regulator"},
    {"id": "HGNC:882", "name": "ATM", "type": "biolink:Gene", "role": "DNA Damage Sensor"},
    {"id": "HGNC:11106", "name": "SIRT1", "type": "biolink:Gene", "role": "Deacetylase"}
  ],
  "edges": [
    {"source": "HGNC:6973", "target": "HGNC:11998", "type": "NEGATIVELY_REGULATES", "mechanism": "Ubiquitination/Degradation"},
    {"source": "CHEMBL:191334", "target": "CHEMBL:5023", "type": "INHIBITOR", "Ki": "36nM"},
    {"source": "HGNC:882", "target": "HGNC:11998", "type": "PHOSPHORYLATES", "effect": "Stabilization"},
    {"source": "HGNC:6974", "target": "HGNC:6973", "type": "INTERACTS_WITH", "score": 0.999},
    {"source": "HGNC:11106", "target": "HGNC:11998", "type": "DEACETYLATES", "effect": "Inactivation"}
  ]
}
```

---

## Therapeutic Axis Explained

1. **Normal State**: MDM2 binds p53 and marks it for proteasomal degradation via ubiquitination
2. **Cancer State**: MDM2 overexpression or amplification leads to excessive p53 degradation → loss of tumor suppression
3. **Therapeutic Strategy**: Nutlin-3 disrupts MDM2-p53 binding (Ki: 36 nM) → p53 stabilization → apoptosis in cancer cells

---

## Network Visualization

STRING provides a network image:
```
https://string-db.org/api/highres_image/network?identifiers=9606.ENSP00000269305&species=9606&add_nodes=15
```

---

## Tools Used

| Phase | Tool | Purpose |
|-------|------|---------|
| 1 | `hgnc_search_genes("TP53")` | Gene resolution |
| 1 | `hgnc_search_genes("MDM2")` | Gene resolution |
| 1 | `chembl_search_compounds("Nutlin")` | Drug resolution |
| 2 | `string_search_proteins("TP53")` | Protein annotation |
| 2 | `chembl_get_compound()` | Drug enrichment |
| 3 | `string_get_interactions()` | Network expansion |
| 4 | curl ChEMBL /activity | Drug-target binding |

---

## Key Finding

The p53-MDM2-Nutlin axis is fully resolvable using the MCP tools:
- **Gene resolution**: HGNC provides canonical identifiers
- **Protein interaction**: STRING shows MDM2-TP53 as highest-confidence interactor (score 0.999)
- **Drug mechanism**: ChEMBL activity data confirms Nutlin-3 as MDM2 inhibitor (Ki: 36 nM)
- **Network context**: Additional regulators (ATM, SIRT1, MDM4) provide therapeutic context

This validates the full Fuzzy-to-Fact protocol for oncology pathway construction.
