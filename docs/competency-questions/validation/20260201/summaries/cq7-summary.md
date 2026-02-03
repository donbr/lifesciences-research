## CQ-7: NGLY1 Deficiency Multi-Hop Drug Repurposing

**Question**: For NGLY1 deficiency, what are the associated genes, and what existing drugs target proteins in those pathways?
**Date**: 2026-02-01
**Status**: VALIDATED
**group_id**: `cq7-ngly1-drug-repurposing`

### Key Entities

| Entity | CURIE | Type | Role |
|--------|-------|------|------|
| NGLY1 deficiency | MONDO:0800044 | Disease | Congenital disorder of deglycosylation 1 |
| NGLY1 | HGNC:17646 | Gene | N-glycanase 1 (3p24.2), causal gene |
| DERL1 | HGNC:28454 | Gene | Derlin 1, ERAD membrane component |
| VCP | HGNC:12666 | Gene | Valosin containing protein, AAA-ATPase |
| NFE2L1 | HGNC:7781 | Gene | NRF1 transcription factor |
| Bortezomib | CHEMBL:325041 | Drug | Proteasome inhibitor (AVOID) |

### Key Findings

- Causal gene: NGLY1 (HGNC:17646) removes N-glycans from misfolded glycoproteins in ERAD pathway
- Key interactors: DERL1 (STRING score 0.905), VCP (STRING score 0.999), NFE2L1/NRF1
- Therapeutic strategy: Enhance autophagy to compensate for ERAD defects
- Repurposing candidates: Rapamycin (mTOR inhibitor), Carbamazepine (autophagy inducer), Sulforaphane (NRF2 activator)
- Drugs to AVOID: Proteasome inhibitors (Bortezomib) would exacerbate protein degradation defects

### Graph Summary

- **Nodes**: 5
- **Edges**: 3

### Provenance

| Source | Tools Used | Evidence |
|--------|------------|----------|
| HGNC | hgnc_search_genes, hgnc_get_gene | HGNC:17646 (NGLY1), HGNC:28454 (DERL1), HGNC:12666 (VCP), HGNC:7781 (NFE2L1) |
| STRING | string_search_proteins, string_get_interactions | STRING:9606.ENSP00000280700, scores: DERL1=0.905, VCP=0.999 |
| Open Targets | opentargets_get_associations | ENSG00000151092 associations |
| ChEMBL | chembl_search_compounds, chembl_get_compound | CHEMBL:325041 (Bortezomib) |

### Mechanism/Path

`HGNC:17646 (NGLY1)` --[INTERACTS]--> `HGNC:28454 (DERL1)` (ERAD pathway)

`HGNC:17646 (NGLY1)` --[INTERACTS]--> `HGNC:12666 (VCP)` (ERAD pathway)

`HGNC:17646 (NGLY1)` --[ACTIVATES]--> `HGNC:7781 (NFE2L1)` (NGLY1 processes NRF1)
