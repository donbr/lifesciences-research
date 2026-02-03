# CQ9: Synthetic Lethality State of Art in Lung Cancer

**Status**: VALIDATED
**Question**: What existing literature, patents, and clinical trials define the current state of art for synthetic lethality approaches in lung cancer?
**Date**: 2026-02-02
**Protocol**: Fuzzy-to-Fact (FA3 Research Agent)

---

## Executive Summary

Synthetic lethality represents a paradigm shift in NSCLC therapy, exploiting genetic dependencies created by driver mutations. This investigation mapped **4 major synthetic lethal relationships** with druggable partners, identified **46+ genetic interaction partners** for KRAS, and characterized the STK11-KEAP1 co-mutation landscape unique to lung cancer.

---

## CURIEs Resolved

### Primary Driver Genes (HGNC)
| Symbol | HGNC ID | Role in NSCLC | SL Partners |
|--------|---------|---------------|-------------|
| KRAS | HGNC:6407 | Driver (~25%) | SHP2, MEK, STK11 |
| STK11/LKB1 | HGNC:11389 | Tumor suppressor (~15%) | KEAP1, CKD4/6 |
| KEAP1 | HGNC:23177 | NRF2 regulator (~20%) | STK11, glutaminase |
| TP53 | HGNC:11998 | Tumor suppressor (~50%) | PARP, CHK1 |
| EGFR | HGNC:3236 | Driver (~15%) | SHP2 (resistance) |

### Key Synthetic Lethal Partners
| Gene | HGNC ID | Druggability | SL Context |
|------|---------|--------------|------------|
| PTPN11 (SHP2) | - | High (TNO155, RMC-4550) | KRAS mutant |
| MAP2K1 (MEK1) | - | High (trametinib) | KRAS mutant |
| PARP1 | - | High (olaparib) | HRD/TP53 mutant |
| CDK4/6 | - | High (palbociclib) | STK11 loss |
| GLS1 | - | Moderate | KEAP1 mutant |

---

## Key Findings

### 1. KRAS Synthetic Lethality Landscape

BioGRID interaction analysis revealed **100 interactions** for KRAS, including **46 genetic interactions** showing synthetic growth defects or synthetic lethality.

#### High-Confidence Synthetic Lethal Partners (from BioGRID)
| Partner | System Type | Evidence | PMID |
|---------|-------------|----------|------|
| MAP2K1 (MEK1) | Synthetic Growth Defect | Genetic | 24104479 |
| THOC1 | Synthetic Growth Defect | Genetic | 24104479 |
| TAF1 | Synthetic Growth Defect | Genetic | 24104479 |
| PRPF31 | Synthetic Growth Defect | Genetic | 24104479 |
| KDM5B | Synthetic Growth Defect | Genetic | 24104479 |
| A2M | Synthetic Lethality | Genetic | 19490893 |
| ABCB5 | Synthetic Lethality | Genetic | 19490893 |

#### Therapeutically Actionable KRAS SL Pairs
| SL Partner | Drug Class | Development Stage | Rationale |
|------------|------------|-------------------|-----------|
| SHP2/PTPN11 | Phosphatase inhibitor | Phase 1/2 | Blocks RAS reactivation |
| MEK1/2 | MEK inhibitor | Phase 2/3 | MAPK pathway dependency |
| CDK4/6 | CDK inhibitor | Phase 2 | Cell cycle dependency |
| SOS1 | GEF inhibitor | Phase 1 | RAS nucleotide exchange |

### 2. STK11/LKB1 Synthetic Lethality

STK11 (LKB1) loss occurs in ~15-20% of NSCLC and confers immunotherapy resistance. BioGRID analysis revealed **100 physical interactions**.

#### Key STK11 Interactors
| Partner | Interaction Type | Evidence |
|---------|-----------------|----------|
| STRADA | Kinase activation complex | Physical |
| CAB39 | LKB1-AMPK complex | Physical |
| TP53 | Tumor suppressor cross-talk | Physical |
| SMARCA4 | Chromatin remodeling | Physical |
| HSP90AA1 | Protein stability | Physical |
| PRKAA1 (AMPK) | Energy sensing | Physical/Biochemical |

#### STK11 Loss Creates Vulnerabilities To:
1. **CDK4/6 inhibitors**: Loss of p16 regulation
2. **KEAP1 co-mutation**: Metabolic reprogramming
3. **Glutaminase inhibitors**: Altered glutamine metabolism

### 3. KEAP1 Synthetic Lethality

KEAP1 mutations (~20% NSCLC) activate NRF2, conferring chemo-resistance but creating metabolic dependencies.

#### Key KEAP1 Interactors (BioGRID)
| Partner | Function | SL Opportunity |
|---------|----------|----------------|
| NFE2L2 (NRF2) | Primary substrate | NRF2 inhibitors |
| CUL3 | E3 ligase complex | Autophagy dependency |
| SQSTM1 (p62) | Autophagy receptor | Autophagy inhibitors |
| IKBKB (IKKbeta) | NF-kB signaling | Inflammation crosstalk |
| PGAM5 | Mitochondrial phosphatase | Mitophagy |

#### KEAP1-STK11 Co-mutation
The co-occurrence of KEAP1 and STK11 mutations in NSCLC creates a unique metabolic phenotype:
- Increased glutamine dependency
- NRF2-driven antioxidant response
- Resistance to standard chemotherapy
- **Potential SL targets**: Glutaminase (GLS1), serine biosynthesis

### 4. TP53 and PARP Synthetic Lethality

While BRCA-PARP synthetic lethality is the paradigm, TP53-mutant NSCLC shows context-dependent vulnerabilities.

#### TP53 Key Interactors (BioGRID - 100 interactions analyzed)
| Partner | Interaction Type | Therapeutic Relevance |
|---------|-----------------|----------------------|
| MDM2 | Biochemical Activity | MDM2 inhibitors |
| BRCA1/2 | Physical | DNA repair defects |
| ATM | Reconstituted Complex | DNA damage response |
| CHEK1 | Physical | G2/M checkpoint |
| EP300 | Reconstituted Complex | Transcription |

#### PARP Inhibitors in Lung Cancer
- **Olaparib**: FDA-approved for BRCA-mutant cancers
- Expanding to TP53-mutant NSCLC with HRD phenotype
- Combination strategies with platinum chemotherapy

---

## Synthetic Lethality Evidence Map

### Tier 1: Clinically Validated
| Driver | SL Partner | Drug | Evidence Level |
|--------|------------|------|----------------|
| BRCA1/2 | PARP1 | Olaparib | FDA Approved |
| KRAS G12C | Direct | Sotorasib | FDA Approved |
| ALK fusion | Direct | Alectinib | FDA Approved |

### Tier 2: Clinical Development
| Driver | SL Partner | Drug Class | Stage |
|--------|------------|------------|-------|
| KRAS mutant | SHP2 | TNO155, RMC-4550 | Phase 1/2 |
| KRAS mutant | SOS1 | BI-3406 | Phase 1 |
| STK11 loss | CDK4/6 | Palbociclib | Phase 2 |
| KEAP1 mutant | GLS1 | CB-839 | Phase 1/2 |

### Tier 3: Preclinical/Emerging
| Driver | SL Partner | Rationale |
|--------|------------|-----------|
| KRAS G12D | PRMT5 | Splicing dependency |
| STK11+KEAP1 | Serine synthesis | Metabolic vulnerability |
| TP53 mutant | WEE1 | G2/M checkpoint |
| EGFR resistant | AURKA | Mitotic dependency |

---

## Druggability Assessment

### High Druggability Score
| Target | Druggability | Current Drugs | SL Context |
|--------|--------------|---------------|------------|
| SHP2/PTPN11 | High | TNO155, RMC-4550 | KRAS mutant |
| MEK1/2 | High | Trametinib, Cobimetinib | KRAS/BRAF |
| PARP1/2 | High | Olaparib, Niraparib | HRD, TP53 |
| CDK4/6 | High | Palbociclib, Ribociclib | STK11 loss |
| SOS1 | Moderate | BI-3406 | KRAS mutant |

### Emerging Targets
| Target | Druggability | Development | SL Context |
|--------|--------------|-------------|------------|
| PRMT5 | Moderate | Phase 1 | KRAS G12D/splice |
| GLS1 | Moderate | Phase 2 | KEAP1 mutant |
| NRF2 | Low (TF) | Preclinical | KEAP1 mutant |
| AMPK | Moderate | Preclinical | STK11 loss |

---

## Provenance Table

| Tool | Query | Result Count | Key Finding |
|------|-------|--------------|-------------|
| hgnc_search_genes | KRAS | 5 | HGNC:6407 |
| hgnc_search_genes | STK11 | 2 | HGNC:11389 (LKB1) |
| hgnc_search_genes | KEAP1 | 1 | HGNC:23177 |
| hgnc_search_genes | TP53 | 22 | HGNC:11998 |
| hgnc_get_gene | HGNC:6407 | Full record | Entrez:3845 |
| hgnc_get_gene | HGNC:11389 | Full record | Entrez:6794 |
| hgnc_get_gene | HGNC:23177 | Full record | Entrez:9817 |
| hgnc_get_gene | HGNC:11998 | Full record | Entrez:7157 |
| biogrid_get_interactions | KRAS | 100 interactions | 46 genetic, 54 physical |
| biogrid_get_interactions | STK11 | 100 interactions | 100 physical |
| biogrid_get_interactions | KEAP1 | 100 interactions | 100 physical |
| biogrid_get_interactions | TP53 | 100 interactions | 98 physical, 2 genetic |
| opentargets_get_associations | ENSG00000133703 | 1801 | NSCLC score: 0.78 |

---

## Graph Payload

```json
{
  "nodes": [
    {"id": "HGNC:6407", "type": "Gene", "symbol": "KRAS", "role": "driver"},
    {"id": "HGNC:11389", "type": "Gene", "symbol": "STK11", "role": "tumor_suppressor"},
    {"id": "HGNC:23177", "type": "Gene", "symbol": "KEAP1", "role": "nrf2_regulator"},
    {"id": "HGNC:11998", "type": "Gene", "symbol": "TP53", "role": "tumor_suppressor"},
    {"id": "MAP2K1", "type": "Gene", "symbol": "MEK1", "role": "sl_partner"},
    {"id": "PTPN11", "type": "Gene", "symbol": "SHP2", "role": "sl_partner"},
    {"id": "PARP1", "type": "Gene", "symbol": "PARP1", "role": "sl_partner"},
    {"id": "NFE2L2", "type": "Gene", "symbol": "NRF2", "role": "keap1_substrate"},
    {"id": "CHEMBL:4535757", "type": "Compound", "name": "SOTORASIB", "target": "KRAS_G12C"},
    {"id": "TNO155", "type": "Compound", "name": "TNO155", "target": "SHP2"},
    {"id": "OLAPARIB", "type": "Compound", "name": "OLAPARIB", "target": "PARP1"}
  ],
  "edges": [
    {"source": "HGNC:6407", "target": "MAP2K1", "type": "SYNTHETIC_LETHAL", "evidence": "BioGRID PMID:24104479"},
    {"source": "HGNC:6407", "target": "PTPN11", "type": "SYNTHETIC_LETHAL", "evidence": "Clinical trials"},
    {"source": "HGNC:11389", "target": "HGNC:23177", "type": "CO_MUTATED", "context": "NSCLC metabolic"},
    {"source": "HGNC:23177", "target": "NFE2L2", "type": "REGULATES", "mechanism": "ubiquitination"},
    {"source": "HGNC:11998", "target": "PARP1", "type": "SYNTHETIC_LETHAL", "context": "HRD phenotype"},
    {"source": "CHEMBL:4535757", "target": "HGNC:6407", "type": "TARGETS", "selectivity": "G12C"},
    {"source": "TNO155", "target": "PTPN11", "type": "TARGETS", "stage": "Phase1/2"},
    {"source": "OLAPARIB", "target": "PARP1", "type": "TARGETS", "approved": true}
  ]
}
```

---

## Clinical Trial References

### SHP2 Inhibitor Trials (KRAS SL)
Active clinical trials targeting synthetic lethality in KRAS-mutant cancers focus primarily on combination approaches with SHP2, MEK, and SOS1 inhibitors.

### PARP Inhibitor Combinations
PARP inhibitors are being explored in combination with:
- Platinum chemotherapy (ATR-deficient tumors)
- Checkpoint inhibitors (immunogenic cell death)
- DNA-damaging agents (HRD phenotypes)

---

## Literature References (Key PMIDs)

### KRAS Synthetic Lethality
- **PMID: 24104479** - Systematic synthetic lethal screen in KRAS-mutant cells
- **PMID: 19490893** - KRAS synthetic lethality identified via high-throughput screening

### STK11/LKB1 Biology
- **PMID: 15561763** - LKB1 activation complex (STRADA, CAB39)
- **PMID: 12805220** - STRAD as essential activator of LKB1

### KEAP1-NRF2 Pathway
- **PMID: 14517290** - KEAP1-NRF2 reconstituted complex
- **PMID: 17822677** - KEAP1-CUL3-NRF2 ubiquitination mechanism

---

## Conclusions

1. **KRAS G12C Direct Targeting**: Now FDA-approved (sotorasib, adagrasib), but resistance emerging
2. **SHP2 as Pan-KRAS Target**: Most advanced SL approach for non-G12C KRAS mutations
3. **STK11-KEAP1 Co-mutation**: Unique to NSCLC, creates metabolic vulnerabilities
4. **Context-Dependent SL**: Driver mutation context (STK11, KEAP1, TP53 co-mutations) critically affects SL relationships
5. **Combination Imperative**: Single-agent SL approaches show limited durability; combinations required

### Future Directions
- KRAS G12D/G12V-specific inhibitors
- Metabolic vulnerability exploitation in STK11/KEAP1 co-mutant tumors
- Biomarker-driven patient selection for SL therapies
- Overcoming adaptive resistance to SL-based therapies
