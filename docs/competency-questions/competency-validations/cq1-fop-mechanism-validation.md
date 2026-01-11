# CQ-1: FOP Mechanism Validation

**Date**: 2026-01-10

**Question**: By what mechanism does Palovarotene treat Fibrodysplasia Ossificans Progressiva (FOP)?

**Status**: VALIDATED

---

## Phase 1: Anchor Node (Naming)

Resolved fuzzy inputs to canonical identifiers:

| Entity | Query | Resolved CURIE | Name |
|--------|-------|----------------|------|
| Drug | "Palovarotene" | CHEMBL:2105648 | PALOVAROTENE |
| Target Gene | "ACVR1" | HGNC:171 | activin A receptor type 1 |
| Receptor | "RARG" | HGNC:9866 | retinoic acid receptor gamma |

---

## Phase 2: Enrich Node (Functional)

### Palovarotene (CHEMBL:2105648)

| Property | Value |
|----------|-------|
| Molecular Weight | 414.55 |
| Max Phase | 4 (Approved) |
| Indications | Dry Eye Syndromes, Myositis Ossificans, Ossification Heterotopic |
| Trade Name | Sohonos |
| Synonyms | R-667, RG-667, IPN60120 |

### ACVR1 (HGNC:171)

| Property | Value |
|----------|-------|
| Full Name | activin A receptor type 1 |
| Aliases | ALK2, SKR1 |
| Location | 2q24.1 |
| UniProt | Q04771 |
| Ensembl | ENSG00000115170 |
| OMIM | 102576 |

### RARG (HGNC:9866)

| Property | Value |
|----------|-------|
| Full Name | retinoic acid receptor gamma |
| Aliases | RAR-gamma, NR1B3 |
| Location | 12q13.13 |
| UniProt | P13631 |
| Ensembl | ENSG00000172819 |

---

## Phase 3: Edge Discovery

### Mechanism of Action (ChEMBL)

```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL2105648&format=json"
```

**Result**:
| Action | Target ChEMBL | Target Name |
|--------|---------------|-------------|
| AGONIST | CHEMBL2003 | Retinoic acid receptor gamma |

### Gene-Disease Association (Open Targets)

```python
opentargets_get_associations(target_id="ENSG00000115170")
```

**Top Association**:
| Disease ID | Disease Name | Score |
|------------|--------------|-------|
| MONDO_0007606 | fibrodysplasia ossificans progressiva | 0.816 |

---

## Validated Mechanism Path

```
Drug(Palovarotene) --[AGONIST]--> Protein(RARG) --[regulates BMP signaling]--> Protein(ACVR1) --[causes]--> Disease(FOP)
```

### Structured Output (BioLink)

```json
{
  "nodes": [
    {"id": "CHEMBL:2105648", "name": "Palovarotene", "type": "biolink:SmallMolecule"},
    {"id": "HGNC:9866", "name": "RARG", "type": "biolink:Gene"},
    {"id": "CHEMBL:2003", "name": "Retinoic acid receptor gamma", "type": "biolink:Protein"},
    {"id": "HGNC:171", "name": "ACVR1", "type": "biolink:Gene"},
    {"id": "MONDO:0007606", "name": "FOP", "type": "biolink:Disease"}
  ],
  "edges": [
    {"source": "CHEMBL:2105648", "target": "CHEMBL:2003", "type": "biolink:agonist_of"},
    {"source": "CHEMBL:2003", "target": "HGNC:9866", "type": "biolink:gene_product_of"},
    {"source": "HGNC:9866", "target": "HGNC:171", "type": "biolink:regulates"},
    {"source": "HGNC:171", "target": "MONDO:0007606", "type": "biolink:gene_associated_with_condition"}
  ]
}
```

---

## Tools Used

| Phase | Tool/Command | Purpose |
|-------|--------------|---------|
| 1 | `chembl_search_compounds("Palovarotene")` | Fuzzy drug resolution |
| 1 | `hgnc_search_genes("ACVR1")` | Fuzzy gene resolution |
| 1 | `hgnc_search_genes("RARG")` | Fuzzy gene resolution |
| 2 | `chembl_get_compound("CHEMBL:2105648")` | Drug enrichment |
| 2 | `hgnc_get_gene("HGNC:171")` | Gene enrichment |
| 2 | `hgnc_get_gene("HGNC:9866")` | Gene enrichment |
| 3 | curl ChEMBL /mechanism | Drug->Target edge |
| 3 | `opentargets_get_associations()` | Gene->Disease edge |

---

## Notes

- The competency question document listed CHEMBL:2031034 for Palovarotene, but the actual resolved ID is CHEMBL:2105648. This is a minor data discrepancy.
- The document listed HGNC:17382 for RARG, but the actual resolved ID is HGNC:9866. This should be corrected in the catalog.
- The mechanism is indirect: Palovarotene activates RARG, which modulates BMP signaling. It does not directly inhibit ACVR1.
