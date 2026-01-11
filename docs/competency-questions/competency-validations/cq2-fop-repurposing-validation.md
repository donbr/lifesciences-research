# CQ-2: FOP Drug Repurposing Validation

**Date**: 2026-01-10

**Question**: What other drugs targeting the BMP Signaling Pathway could be repurposed for FOP?

**Status**: VALIDATED

---

## Phase 1: Anchor Node

| Entity | Query | Resolved CURIE |
|--------|-------|----------------|
| Target Gene | ACVR1 | HGNC:171 |
| Pathway Partner | SMAD1 | HGNC:6767 |
| Pathway Partner | BMPR1A | HGNC:1076 |

---

## Phase 2: Pathway Discovery

### BMP Signaling Pathway (WikiPathways)

```python
wikipathways_search_pathways("BMP signaling", organism="Homo sapiens")
```

**Top Pathways**:
| Pathway ID | Title | Score |
|------------|-------|-------|
| WP:WP2760 | Signaling by BMP | 0.74 |
| WP:WP3927 | BMP signaling in eyelid development | 0.70 |
| WP:WP1425 | Bone morphogenic protein signaling | 0.59 |

### Pathway Components (WP:WP2760)

**Key Genes**: BMPR1A, BMPR1B, BMPR2, SMAD1, SMAD4, SMAD5, ACVR2A, ACVR2B

---

## Phase 3: Drug Discovery

### Direct ACVR1 Inhibitors (ChEMBL target CHEMBL2148)

```bash
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?target_chembl_id=CHEMBL2148&format=json"
```

**Candidates**:
| Drug CURIE | Name | Max Phase | Action |
|------------|------|-----------|--------|
| CHEMBL:405130 | WHI-P131 (JANEX-1) | 1 | INHIBITOR |
| CHEMBL:495727 | AT-9283 | 2 | INHIBITOR |
| CHEMBL:2106468 | TRICETAMIDE | 1 | INHIBITOR |
| CHEMBL:4116008 | - | - | INHIBITOR |
| CHEMBL:5314384 | - | - | INHIBITOR |

### Lead Candidate: AT-9283

| Property | Value |
|----------|-------|
| CHEMBL ID | CHEMBL:495727 |
| Name | AT-9283 |
| Molecular Weight | 381.44 |
| Max Phase | 2 |
| Mechanism | ACVR1 inhibitor |

---

## Validated Repurposing Graph

```json
{
  "nodes": [
    {"id": "MONDO:0007621", "name": "FOP", "type": "biolink:Disease"},
    {"id": "HGNC:171", "name": "ACVR1", "type": "biolink:Gene"},
    {"id": "WP:WP2760", "name": "Signaling by BMP", "type": "biolink:Pathway"},
    {"id": "CHEMBL:405130", "name": "WHI-P131", "type": "biolink:SmallMolecule"},
    {"id": "CHEMBL:495727", "name": "AT-9283", "type": "biolink:SmallMolecule"},
    {"id": "CHEMBL:2105648", "name": "Palovarotene", "type": "biolink:SmallMolecule"}
  ],
  "edges": [
    {"source": "HGNC:171", "target": "MONDO:0007621", "type": "biolink:gene_associated_with_condition"},
    {"source": "HGNC:171", "target": "WP:WP2760", "type": "biolink:participates_in"},
    {"source": "CHEMBL:405130", "target": "HGNC:171", "type": "biolink:inhibits"},
    {"source": "CHEMBL:495727", "target": "HGNC:171", "type": "biolink:inhibits"},
    {"source": "CHEMBL:2105648", "target": "MONDO:0007621", "type": "biolink:treats", "note": "FDA approved"}
  ]
}
```

---

## Reasoning Chain

1. **Identify Target**: ACVR1 (HGNC:171) is the causal gene for FOP
2. **Identify Pathway**: ACVR1 participates in BMP Signaling (WP:WP2760)
3. **Find Pathway Members**: SMAD1, SMAD5, BMPR1A, BMPR1B, BMPR2
4. **Find Inhibitors**: AT-9283, WHI-P131, TRICETAMIDE target ACVR1 directly
5. **Repurposing Hypothesis**: These inhibitors could treat FOP by reducing BMP signaling

---

## Key Finding

**AT-9283** (CHEMBL:495727) is a Phase 2 ACVR1 inhibitor that could be repurposed for FOP. Unlike Palovarotene (an RAR-gamma agonist that indirectly modulates BMP signaling), AT-9283 directly inhibits ACVR1 kinase activity.

---

## Tools Used

| Phase | Tool/Command | Purpose |
|-------|--------------|---------|
| 1 | `hgnc_search_genes("ACVR1")` | Anchor gene resolution |
| 2 | `wikipathways_search_pathways("BMP signaling")` | Pathway discovery |
| 2 | `wikipathways_get_pathway_components("WP:WP2760")` | Pathway member extraction |
| 3 | curl ChEMBL /mechanism | Drug->Target edges |
| 3 | `chembl_get_compounds_batch()` | Drug enrichment |
