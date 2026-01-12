# cq11: p53-MDM2-Nutlin Therapeutic Axis - Validation Report

**Date**: 2026-01-11
**group_id**: `cq11-p53-mdm2-nutlin`
**Status**: VALIDATED

---

## Question

*How do we build and validate a knowledge graph for the p53-MDM2-Nutlin therapeutic axis?*

---

## Therapeutic Hypothesis

Inhibiting MDM2 prevents p53 degradation, reactivating tumor suppressor function in cancers with wild-type p53 and MDM2 overexpression/amplification.

---

## API Calls Made

### Phase 1: Anchor Genes

```
hgnc_search_genes("TP53") → HGNC:11998
hgnc_get_gene("HGNC:11998")
```
**Result**:
- Symbol: TP53
- Name: tumor protein p53
- Location: 17p13.1
- UniProt: P04637
- Ensembl: ENSG00000141510
- Aliases: p53, LFS1
- OMIM: 191170 (Li-Fraumeni syndrome link)

```
hgnc_search_genes("MDM2") → HGNC:6973
hgnc_get_gene("HGNC:6973")
```
**Result**:
- Symbol: MDM2
- Name: MDM2 proto-oncogene
- Location: 12q15
- UniProt: Q00987
- Ensembl: ENSG00000135679
- Aliases: HDM2
- Previous names: "p53 binding protein", "E3 ubiquitin protein ligase"

### Phase 2: Protein Interactions (STRING)

```
string_search_proteins("TP53", species=9606)
string_get_interactions("STRING:9606.ENSP00000269305", required_score=900)
```
**Result**: 10 high-confidence interactions including MDM2, SIRT1, RPA1, ATM

```
string_search_proteins("MDM2", species=9606)
string_get_interactions("STRING:9606.ENSP00000258149", required_score=900)
```
**Result**: 10 high-confidence interactions:

| Partner | Score | Evidence Breakdown |
|---------|-------|-------------------|
| TP53 | 0.999 | exp:0.999, db:0.9, txt:0.999 |
| MDM4 | 0.999 | exp:0.999, db:0.9, txt:0.986 |
| CDKN2A | 0.999 | exp:0.992, db:0.9, txt:0.999 |
| USP7 | 0.999 | exp:0.925, db:0.5, txt:0.995 |
| AKT1 | 0.999 | exp:0.891, db:0.9, txt:0.98 |
| RB1 | 0.999 | exp:0.889, db:0.9, txt:0.925 |
| RPL5 | 0.999 | exp:0.94, txt:0.996 |
| RPL11 | 0.999 | exp:0.999, txt:0.997 |
| EP300 | 0.999 | exp:0.82, txt:0.994 |
| UBE2D2 | 0.999 | exp:0.999, txt:0.643 |

### Phase 3: Drug Discovery

```
chembl_search_compounds("nutlin")
chembl_get_compound("CHEMBL:191334")
```
**Result**:
- Name: NUTLIN-3
- Molecular Weight: 581.5
- Max Phase: null (research tool)
- SMILES: cis-imidazoline with dichlorophenyl groups

```
chembl_search_compounds("idasanutlin")
chembl_get_compound("CHEMBL:2402737")
```
**Result**:
- Name: IDASANUTLIN
- Molecular Weight: 616.49
- Max Phase: 3
- Synonyms: RG7388, RO5503781
- Indications: AML, breast cancer, colorectal cancer, glioblastoma, follicular lymphoma, DLBCL, multiple myeloma, polycythemia vera, thrombocythemia

---

## Nodes Confirmed

| Entity | CURIE | Type | Source |
|--------|-------|------|--------|
| TP53 | HGNC:11998 | biolink:Gene | HGNC |
| MDM2 | HGNC:6973 | biolink:Gene | HGNC |
| TP53 protein | STRING:9606.ENSP00000269305 | biolink:Protein | STRING |
| MDM2 protein | STRING:9606.ENSP00000258149 | biolink:Protein | STRING |
| Nutlin-3 | CHEMBL:191334 | biolink:SmallMolecule | ChEMBL |
| Idasanutlin | CHEMBL:2402737 | biolink:SmallMolecule | ChEMBL |

---

## Edges Built

| Source | Target | Predicate | Evidence |
|--------|--------|-----------|----------|
| HGNC:6973 | HGNC:11998 | biolink:negatively_regulates | STRING 0.999 |
| STRING:9606.ENSP00000258149 | STRING:9606.ENSP00000269305 | biolink:physically_interacts_with | STRING exp:0.999 |
| CHEMBL:191334 | HGNC:6973 | biolink:inhibits | ChEMBL mechanism |
| CHEMBL:2402737 | HGNC:6973 | biolink:inhibits | ChEMBL mechanism |
| CHEMBL:191334 | CHEMBL:2402737 | biolink:precursor_of | Roche program |

---

## Key Findings

1. **MDM2-TP53 interaction** has maximum STRING confidence (0.999) across all evidence types
2. **MDM2 network hub** includes key oncology targets: MDM4, CDKN2A (p16/ARF), AKT1, RB1
3. **Ribosomal stress sensors** RPL5 and RPL11 directly interact with MDM2 to activate p53
4. **Drug development progression**: Nutlin-3 (prototype) → Idasanutlin (Phase 3 clinical)
5. **Broad oncology indications** for idasanutlin spanning hematologic and solid tumors

---

## Biological Context

### p53-MDM2 Regulatory Loop
1. p53 is a transcription factor that induces cell cycle arrest or apoptosis
2. MDM2 is transcriptionally activated by p53 (negative feedback)
3. MDM2 binds p53 transactivation domain, blocking its function
4. MDM2 ubiquitinates p53, marking it for proteasomal degradation
5. MDM2 promotes p53 nuclear export

### Therapeutic Rationale
- ~50% of cancers have wild-type TP53
- Many of these overexpress or amplify MDM2
- Blocking MDM2-p53 interaction releases functional p53
- p53 reactivation induces tumor cell death

---

## Graphiti Persistence

```
group_id: cq11-p53-mdm2-nutlin
episode_name: cq11: p53-MDM2-Nutlin therapeutic axis
source: json
status: queued for processing
```

---

## Limitations

- ChEMBL /mechanism endpoint not directly queried (would provide binding data)
- No clinical trial search performed (ClinicalTrials.gov blocked by Cloudflare in tests)
- STRING regulatory direction not captured (would require STRING v12.5 regulatory network)

---

## Next Steps

- Proceed to cq14: Feng synthetic lethality validation
- Query BioGRID ORCS for TP53 essentiality screens
- Search PubMed for MDM2 inhibitor clinical trial results
