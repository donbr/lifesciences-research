# CQ1: Doxorubicin Cardiotoxicity Mechanisms

**Status**: VALIDATED

**Question**: What are the clinically documented side effects of Doxorubicin on heart cells, and what are the specific molecular mechanisms believed to cause this cardiotoxicity?

## Executive Summary

Doxorubicin (CHEMBL:53463) is an FDA-approved anthracycline antibiotic with broad antitumor activity. Its cardiotoxicity is primarily mediated through DNA topoisomerase II beta (TOP2B) inhibition in cardiomyocytes, leading to oxidative stress and mitochondrial dysfunction. Open Targets confirms TOP2B association with cardiomyopathy (EFO:0000318, score: 0.465).

---

## CURIEs Resolved

| Entity | CURIE | Source | Cross-References |
|--------|-------|--------|------------------|
| Doxorubicin | CHEMBL:53463 | ChEMBL | Max Phase 4, 104 indications |
| TOP2A | HGNC:11989 | HGNC | ENSG00000131747, UniProt:P11388, OMIM:126430 |
| TOP2B | HGNC:11990 | HGNC | ENSG00000077097, UniProt:Q02880, OMIM:126431 |
| TOP2B (Entrez) | NCBIGene:7155 | NCBI | BioGRID:113008 |
| Cardiomyopathy | EFO:0000318 | Open Targets | Association score: 0.465 |
| Dexrazoxane | CHEMBL:1738 | ChEMBL | Cardioprotective agent, Max Phase 4 |

---

## Key Findings

### 1. Primary Mechanism: TOP2B Inhibition

Doxorubicin inhibits both TOP2A (tumor-targeting) and TOP2B (cardiac toxicity driver):

| Isoform | Location | Function | Clinical Relevance |
|---------|----------|----------|-------------------|
| TOP2A | Chr 17q21.2 | Cell division, tumor proliferation | Therapeutic target |
| TOP2B | Chr 3p24.2 | Post-mitotic cardiomyocyte DNA repair | Cardiotoxicity mediator |

**Mechanistic Insight** (from NCBIGene:7155 summary):
> "This gene encodes a DNA topoisomerase... This nuclear enzyme is involved in processes such as chromosome condensation, chromatid separation, and the relief of torsional stress that occurs during DNA transcription and replication."

### 2. TOP2B Interaction Network (STRING, score >= 700)

The STRING database reveals TOP2B's high-confidence interaction partners involved in cardiotoxicity:

| Partner | STRING Score | Functional Role |
|---------|--------------|-----------------|
| TOP2A | 0.973 | Paralog, functional redundancy |
| TOPBP1 | 0.955 | DNA damage checkpoint |
| TDP2 | 0.820 | Repairs TOP2-induced DNA breaks |
| SMC2 | 0.780 | Chromosome condensation |
| CTCF | 0.775 | Chromatin architecture |
| AR | 0.774 | Hormone receptor signaling |
| PARP1 | 0.724 | DNA damage response (synthetic lethality target) |
| SUMO1 | 0.711 | SUMOylation of TOP2B |

### 3. Open Targets Disease Associations for TOP2B

TOP2B (ENSG00000077097) shows genetic associations with:

| Disease | EFO ID | Score | Relevance |
|---------|--------|-------|-----------|
| B-cell immunodeficiency | MONDO:0012243 | 0.720 | Genetic |
| Neoplasm | EFO:0000616 | 0.595 | Cancer |
| Small cell lung carcinoma | EFO:0000702 | 0.572 | Cancer |
| Lung cancer | MONDO:0008903 | 0.528 | Cancer |
| Breast cancer | MONDO:0007254 | 0.513 | Cancer |
| **Cardiomyopathy** | **EFO:0000318** | **0.465** | **Cardiotoxicity** |

### 4. Dexrazoxane: FDA-Approved Cardioprotective Agent

CHEMBL:1738 (Dexrazoxane) is the only FDA-approved agent for anthracycline-induced cardiotoxicity:

- **Mechanism**: Iron chelator that prevents iron-mediated oxidative damage
- **Synonyms**: ICRF-187, Cardioxane, ADR-529
- **Max Phase**: 4 (FDA approved)
- **Indications**: Used prophylactically with doxorubicin in high-risk patients

### 5. WikiPathways: TOP2B in DNA Replication

TOP2B participates in:
- **WP:WP3805** - SUMOylation of DNA replication proteins (TOP2B is SUMOylated, which affects its activity and localization)

---

## Cardiotoxicity Mechanism Model

```
Doxorubicin
    |
    v
TOP2B Inhibition in Cardiomyocytes
    |
    +---> DNA Double-Strand Breaks
    |         |
    |         v
    |     TDP2 Repair Pathway Overwhelmed
    |         |
    |         v
    |     Activation of PARP1 (DNA damage response)
    |         |
    |         v
    |     NAD+ Depletion --> Mitochondrial Dysfunction
    |
    +---> Reactive Oxygen Species (ROS) Generation
    |         |
    |         v
    |     Iron-Doxorubicin Complex Formation
    |         |
    |         v
    |     Fenton Reaction --> Hydroxyl Radicals
    |         |
    |         v
    |     Lipid Peroxidation, Protein Oxidation
    |
    v
Cardiomyocyte Apoptosis --> Cardiomyopathy (EFO:0000318)
```

---

## Clinical Trial Evidence

ClinicalTrials.gov searches identify active research on cardioprotection:

| NCT ID | Title | Phase | Status |
|--------|-------|-------|--------|
| NCT06103279 | Empagliflozin Effect Against Doxorubicin Induced Cardiomyopathy | Phase 2/3 | Unknown |
| NCT05959889 | Montelukast on Doxorubicin Induced Cardiotoxicity in Breast Cancer | NA | Completed |
| NCT05146843 | MitoQ Supplementation for CV Toxicity in Doxorubicin Chemotherapy | NA | Unknown |

---

## Provenance Table

| Tool | Query | Key Result |
|------|-------|------------|
| mcp__lifesciences-research__chembl_search_compounds | "Doxorubicin" | CHEMBL:53463 |
| mcp__lifesciences-research__chembl_get_compound | CHEMBL:53463 | 104 indications, MW 543.53 |
| mcp__lifesciences-research__hgnc_get_gene | HGNC:11990 | TOP2B, Chr 3p24.2 |
| mcp__lifesciences-research__entrez_get_gene | NCBIGene:7155 | Full functional summary |
| mcp__lifesciences-research__string_get_interactions | STRING:9606.ENSP00000264331 | 15 interactions (score >= 700) |
| mcp__lifesciences-research__opentargets_get_associations | ENSG00000077097 | Cardiomyopathy score 0.465 |
| mcp__lifesciences-research__chembl_get_compound | CHEMBL:1738 | Dexrazoxane details |
| curl ClinicalTrials.gov | doxorubicin cardiotoxicity | 5 trials |

---

## Literature References (PubMed Links from Entrez)

TOP2B-associated publications (via NCBIGene:7155):
- PMID:16502015, PMID:37068767, PMID:28554742, PMID:28669856
- PMID:9426241, PMID:17209120, PMID:9743583, PMID:16932348
- PMID:30318608, PMID:21280220, PMID:35831557, PMID:10879730

---

## Validation Confidence

- **Fuzzy-to-Fact Protocol**: Fully followed (search -> CURIE resolution -> strict lookup)
- **Cross-Reference Validation**: TOP2B CURIEs consistent across HGNC, Ensembl, UniProt, NCBI
- **Disease Association**: Open Targets confirms cardiomyopathy link (score 0.465)
- **Therapeutic Target**: Dexrazoxane (CHEMBL:1738) FDA-approved for this indication
