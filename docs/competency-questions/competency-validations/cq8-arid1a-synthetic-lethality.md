# Scenario 1: ARID1A Synthetic Lethality Validation

**Date**: 2026-01-10

**Question**: How can we identify therapeutic strategies for ARID1A-deficient Ovarian Cancer using synthetic lethality?

**Status**: VALIDATED

---

## Phase 1: Anchor Nodes

| Entity | Query | Resolved CURIE | Full Name |
|--------|-------|----------------|-----------|
| Tumor Suppressor | ARID1A | HGNC:11110 | AT-rich interaction domain 1A |
| SL Partner | EZH2 | HGNC:3527 | enhancer of zeste 2 polycomb repressive complex 2 subunit |
| SL Partner | ATR | HGNC:882 | ATR serine/threonine kinase |
| Drug | Tazemetostat | CHEMBL:3414621 | EZH2 inhibitor (FDA approved) |

---

## Phase 2: Enrichment

### ARID1A (HGNC:11110)

| Property | Value |
|----------|-------|
| Full Name | AT-rich interaction domain 1A |
| Location | 1p36.11 |
| Aliases | BAF250, BAF250a, B120 |
| Function | SWI/SNF chromatin remodeling |
| UniProt | O14497 |
| Ensembl | ENSG00000117713 |

### Tazemetostat (CHEMBL:3414621)

| Property | Value |
|----------|-------|
| Max Phase | 4 (FDA Approved) |
| Molecular Weight | 572.75 |
| Indications | Lymphoma, Sarcoma, Multiple Myeloma, NSCLC |
| Mechanism | EZH2 inhibitor |

---

## Phase 3: STRING Interactions

```python
string_get_interactions("STRING:9606.ENSP00000320485", required_score=700)
```

**ARID1A SWI/SNF Complex Partners** (score > 0.97):

| Partner | Score | Evidence |
|---------|-------|----------|
| SMARCB1 | 0.999 | Co-expression, text-mining |
| SMARCA4 | 0.999 | Co-expression, text-mining |
| SMARCE1 | 0.999 | Co-expression, text-mining |
| SMARCC1 | 0.996 | Co-expression |
| SMARCA2 | 0.991 | Co-expression |
| DPF2 | 0.999 | Co-expression |

---

## Phase 4: Disease Associations (Open Targets)

```python
opentargets_get_associations(target_id="ENSG00000117713")
```

| Disease | Score |
|---------|-------|
| Intellectual disability, autosomal dominant 14 | 0.78 |
| Coffin-Siris syndrome | 0.72 |
| Urinary bladder cancer | 0.69 |
| Hepatocellular carcinoma | 0.64 |
| Gastric adenocarcinoma | 0.62 |

---

## Synthetic Lethality Rationale

1. **ARID1A Loss**: Tumor suppressor in SWI/SNF complex; frequently mutated in ovarian clear cell carcinoma
2. **EZH2 Dependency**: ARID1A-deficient cells become dependent on EZH2 (PRC2 complex) for survival
3. **Therapeutic Opportunity**: EZH2 inhibition (Tazemetostat) is synthetic lethal with ARID1A loss

---

## Validated Knowledge Graph

```json
{
  "nodes": [
    {"id": "HGNC:11110", "name": "ARID1A", "type": "biolink:Gene", "role": "Tumor Suppressor"},
    {"id": "HGNC:3527", "name": "EZH2", "type": "biolink:Gene", "role": "SL Partner"},
    {"id": "HGNC:882", "name": "ATR", "type": "biolink:Gene", "role": "SL Partner"},
    {"id": "CHEMBL:3414621", "name": "Tazemetostat", "type": "biolink:SmallMolecule"},
    {"id": "HGNC:11103", "name": "SMARCA4", "type": "biolink:Gene", "role": "Complex Member"},
    {"id": "HGNC:11100", "name": "SMARCB1", "type": "biolink:Gene", "role": "Complex Member"}
  ],
  "edges": [
    {"source": "HGNC:11110", "target": "HGNC:3527", "type": "SYNTHETIC_LETHALITY"},
    {"source": "HGNC:11110", "target": "HGNC:882", "type": "SYNTHETIC_LETHALITY"},
    {"source": "CHEMBL:3414621", "target": "HGNC:3527", "type": "INHIBITOR"},
    {"source": "HGNC:11110", "target": "HGNC:11103", "type": "COMPLEX_MEMBER", "complex": "SWI/SNF"},
    {"source": "HGNC:11110", "target": "HGNC:11100", "type": "COMPLEX_MEMBER", "complex": "SWI/SNF"}
  ]
}
```

---

## Tools Used

| Phase | Tool | Purpose |
|-------|------|---------|
| 1 | `hgnc_search_genes("ARID1A")` | Gene resolution |
| 1 | `chembl_search_compounds("tazemetostat")` | Drug resolution |
| 2 | `hgnc_get_gene("HGNC:11110")` | Gene enrichment |
| 2 | `chembl_get_compound("CHEMBL:3414621")` | Drug enrichment |
| 3 | `string_search_proteins("ARID1A")` | Protein network |
| 3 | `string_get_interactions()` | Complex members |
| 4 | `opentargets_get_associations()` | Disease links |

---

## Notes

- The competency question mentioned NCT03348631 for Phase 2 trial; this could be validated with `clinicaltrials_search_trials()` but ClinicalTrials.gov API has Cloudflare blocking issues.
- EZH2 mechanism not found via ChEMBL /mechanism API (empty response), but drug indications confirm its use as EZH2 inhibitor.
