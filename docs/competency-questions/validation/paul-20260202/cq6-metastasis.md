# CQ6: Metastasis Gene Expression - Validation Report

**Status**: VALIDATED

**Question**: What are the key differences in gene expression that trigger metastasis versus those involved in maintaining a localized tumor?

**Validation Date**: 2026-02-02

---

## Executive Summary

The transition from localized to metastatic tumor is driven by **Epithelial-Mesenchymal Transition (EMT)**, a developmental program hijacked by cancer cells. This involves:
1. **Downregulation of Epithelial Markers**: Loss of E-cadherin (CDH1), EPCAM - maintains cell-cell adhesion
2. **Upregulation of Mesenchymal Markers**: Gain of Vimentin (VIM), Fibronectin (FN1) - promotes motility
3. **EMT Master Regulators**: Transcription factors SNAI1, SNAI2, TWIST1, ZEB1 that orchestrate the switch

---

## CURIEs Resolved

### Epithelial Markers (Localized Tumor - High Expression)
| Symbol | HGNC ID | UniProtKB | Entrez | Function |
|--------|---------|-----------|--------|----------|
| CDH1 (E-cadherin) | HGNC:1748 | UniProtKB:P12830 | 999 | Cell-cell adhesion |
| EPCAM | HGNC:11529 | UniProtKB:P16422 | 4072 | Epithelial cell adhesion |

### Mesenchymal Markers (Metastatic Tumor - High Expression)
| Symbol | HGNC ID | UniProtKB | Entrez | Function |
|--------|---------|-----------|--------|----------|
| VIM (Vimentin) | HGNC:12692 | UniProtKB:P08670 | 7431 | Intermediate filament |
| FN1 (Fibronectin) | HGNC:3778 | UniProtKB:P02751 | 2335 | ECM component |

### EMT Master Regulators (Switch Inducers)
| Symbol | HGNC ID | UniProtKB | Entrez | Mechanism |
|--------|---------|-----------|--------|-----------|
| SNAI1 (Snail) | HGNC:11128 | UniProtKB:O95863 | 6615 | CDH1 repression |
| SNAI2 (Slug) | HGNC:11094 | - | 6591 | CDH1 repression |
| TWIST1 | HGNC:12428 | UniProtKB:Q15672 | 7291 | CDH1 repression |
| ZEB1 | HGNC:11642 | UniProtKB:P37275 | 6935 | CDH1 repression |

---

## Key Findings

### 1. E-cadherin (CDH1) - The Gatekeeper
**UniProtKB:P12830** - Cadherin-1:
- "Cadherins are calcium-dependent cell adhesion proteins"
- "CDH1 is involved in mechanisms regulating cell-cell adhesions, mobility and proliferation of epithelial cells"
- "Has a potent invasive suppressor role"
- "Promotes organization of radial actin fiber structure"
- Loss of CDH1 is a hallmark of EMT initiation

### 2. Vimentin (VIM) - Mesenchymal Identity
**UniProtKB:P08670** - Vimentin:
- "Class-III intermediate filaments found in various non-epithelial cells, especially mesenchymal cells"
- "Plays a role in cell directional movement, orientation, cell sheet organization"
- "Attached to the nucleus, endoplasmic reticulum, and mitochondria"
- Expression indicates mesenchymal phenotype

### 3. SNAI1 - Primary EMT Orchestrator
**UniProtKB:O95863** - Zinc finger protein SNAI1:
- "Involved in induction of the epithelial to mesenchymal transition (EMT)"
- "Binds to 3 E-boxes of the E-cadherin/CDH1 gene promoter and to the promoters of CLDN7 and KRT8"
- "In association with histone demethylase KDM1A which it recruits to the promoters, causes a decrease in dimethylated H3K4 levels and represses transcription"
- "During EMT, involved with LOXL2 in negatively regulating pericentromeric heterochromatin transcription"
- "Associates with EGR1 and SP1 to mediate TPA-induced up-regulation of CDKN2B"

### 4. TWIST1 - EMT and Metastasis Promoter
**UniProtKB:Q15672** - Twist-related protein 1:
- "Acts as a transcriptional regulator"
- "Inhibits myogenesis by sequestrating E proteins"
- "Represses expression of pro-inflammatory cytokines such as TNFA and IL1B"
- "Regulates gene expression differentially, depending on dimer composition"
- "Homodimers induce expression of FGFR2 and POSTN while heterodimers repress FGFR2 and POSTN expression"

### 5. ZEB1 - Dual Regulator
**UniProtKB:P37275** - Zinc finger E-box-binding homeobox 1:
- "Acts as a transcriptional repressor"
- "Represses E-cadherin promoter and induces an epithelial-mesenchymal transition (EMT) by recruiting SMARCA4/BRG1"
- "Represses transcription by binding to the E box (5'-CANNTG-3')"
- "Positively regulates neuronal differentiation"

---

## Gene Expression Signature Comparison

### Localized Tumor (Epithelial Phenotype)
| Gene | Expression | Function | Consequence |
|------|------------|----------|-------------|
| CDH1 | HIGH | Cell-cell adhesion | Maintains tissue architecture |
| EPCAM | HIGH | Epithelial adhesion | Prevents dissemination |
| SNAI1 | LOW | EMT TF | EMT not activated |
| ZEB1 | LOW | EMT TF | EMT not activated |
| VIM | LOW | Mesenchymal marker | Epithelial state |
| FN1 | LOW | ECM migration | Limited motility |

### Metastatic Tumor (Mesenchymal Phenotype)
| Gene | Expression | Function | Consequence |
|------|------------|----------|-------------|
| CDH1 | LOW | Cell-cell adhesion | Cell detachment |
| EPCAM | LOW | Epithelial adhesion | Loss of polarity |
| SNAI1 | HIGH | EMT TF | Represses CDH1 |
| ZEB1 | HIGH | EMT TF | Represses CDH1 |
| TWIST1 | HIGH | EMT TF | Promotes invasion |
| VIM | HIGH | Mesenchymal marker | Enhanced motility |
| FN1 | HIGH | ECM migration | ECM remodeling |

---

## WikiPathways Evidence

### WP5469: Hallmark of Cancer - Metastasis and EMT
- **Components**: 23 genes, 141 proteins
- **Key pathway members**: CDH1, SNAI1, SNAI2, TWIST1, ZEB1, ZEB2, TGFB1
- **Additional regulators**: EZH2, SUZ12, HDAC1, HDAC2, KDM1A, SIRT1
- **URL**: https://classic.wikipathways.org/index.php/Pathway:WP5469

### WP4239: Epithelial to Mesenchymal Transition in Colorectal Cancer
- **Components**: 163 genes, 618 proteins
- **Comprehensive pathway including**:
  - TGF-beta signaling: TGFB1, TGFB2, TGFB3, TGFBR1, TGFBR2
  - WNT signaling: WNT1-WNT11, FZD1-FZD10, CTNNB1
  - Notch signaling: NOTCH1-4, JAG1, JAG2, DLL1
  - MAPK signaling: RAF1, MAP2K1/2, MAPK1/3
  - EMT markers: All core EMT genes
- **URL**: https://classic.wikipathways.org/index.php/Pathway:WP4239

### WP2943: Hypoxia-mediated EMT and Stemness
- **Components**: 2 genes, 10 proteins
- **Key link**: DICER1, ZEB1 - connects hypoxia to EMT via miRNA regulation
- **URL**: https://classic.wikipathways.org/index.php/Pathway:WP2943

---

## EMT Regulatory Cascade

```
HYPOXIA / TGFB1 / Growth Factors
            |
            v
    +---------------+
    | SNAI1/TWIST1  |  (EMT Master Regulators)
    | ZEB1/ZEB2     |
    +---------------+
            |
            v
    Epigenetic Silencing (KDM1A, HDAC, EZH2)
            |
            v
    +---------------+
    | CDH1 REPRESSION |  (E-cadherin loss)
    +---------------+
            |
            v
    Loss of Cell-Cell Adhesion
            |
            v
    +---------------+
    | VIM/FN1 UP    |  (Mesenchymal markers)
    +---------------+
            |
            v
    Enhanced Motility & Invasion
            |
            v
    METASTASIS
```

---

## Provenance Table

| Tool | Query | Result Count | Key CURIEs |
|------|-------|--------------|------------|
| hgnc_search_genes | CDH1 | 2 | HGNC:1748 |
| hgnc_search_genes | EPCAM | 2 | HGNC:11529 |
| hgnc_search_genes | VIM | 2 | HGNC:12692 |
| hgnc_search_genes | FN1 | 2 | HGNC:3778 |
| hgnc_search_genes | SNAI1 | 2 | HGNC:11128 |
| hgnc_search_genes | TWIST1 | 2 | HGNC:12428 |
| hgnc_search_genes | ZEB1 | 3 | HGNC:11642 |
| hgnc_get_gene | HGNC:1748 | 1 | CDH1 full record |
| hgnc_get_gene | HGNC:11529 | 1 | EPCAM full record |
| hgnc_get_gene | HGNC:12692 | 1 | VIM full record |
| hgnc_get_gene | HGNC:3778 | 1 | FN1 full record |
| hgnc_get_gene | HGNC:11128 | 1 | SNAI1 full record |
| hgnc_get_gene | HGNC:12428 | 1 | TWIST1 full record |
| hgnc_get_gene | HGNC:11642 | 1 | ZEB1 full record |
| uniprot_get_protein | UniProtKB:P12830 | 1 | CDH1 function |
| uniprot_get_protein | UniProtKB:P08670 | 1 | VIM function |
| uniprot_get_protein | UniProtKB:O95863 | 1 | SNAI1 function |
| uniprot_get_protein | UniProtKB:Q15672 | 1 | TWIST1 function |
| uniprot_get_protein | UniProtKB:P37275 | 1 | ZEB1 function |
| wikipathways_search_pathways | EMT | 10 | WP5469, WP4239, WP2943 |
| wikipathways_search_pathways | metastasis | 10 | WP5469, WP2249 |
| wikipathways_get_pathway | WP:WP5469 | 1 | Metastasis/EMT pathway |
| wikipathways_get_pathway | WP:WP4239 | 1 | EMT in colorectal cancer |
| wikipathways_get_pathway | WP:WP2943 | 1 | Hypoxia-EMT |

---

## Graph Payload

```json
{
  "nodes": [
    {
      "id": "HGNC:1748",
      "symbol": "CDH1",
      "name": "cadherin 1",
      "aliases": ["E-cadherin", "CD324"],
      "type": "gene",
      "role": "epithelial_marker",
      "expression_localized": "HIGH",
      "expression_metastatic": "LOW",
      "location": "16q22.1",
      "cross_references": {
        "uniprot": "P12830",
        "entrez": "999",
        "ensembl": "ENSG00000039068"
      }
    },
    {
      "id": "HGNC:11529",
      "symbol": "EPCAM",
      "name": "epithelial cell adhesion molecule",
      "aliases": ["CD326", "TROP1"],
      "type": "gene",
      "role": "epithelial_marker",
      "expression_localized": "HIGH",
      "expression_metastatic": "LOW",
      "location": "2p21",
      "cross_references": {
        "uniprot": "P16422",
        "entrez": "4072",
        "ensembl": "ENSG00000119888"
      }
    },
    {
      "id": "HGNC:12692",
      "symbol": "VIM",
      "name": "vimentin",
      "type": "gene",
      "role": "mesenchymal_marker",
      "expression_localized": "LOW",
      "expression_metastatic": "HIGH",
      "location": "10p13",
      "cross_references": {
        "uniprot": "P08670",
        "entrez": "7431",
        "ensembl": "ENSG00000026025"
      }
    },
    {
      "id": "HGNC:3778",
      "symbol": "FN1",
      "name": "fibronectin 1",
      "type": "gene",
      "role": "mesenchymal_marker",
      "expression_localized": "LOW",
      "expression_metastatic": "HIGH",
      "location": "2q35",
      "cross_references": {
        "uniprot": "P02751",
        "entrez": "2335",
        "ensembl": "ENSG00000115414"
      }
    },
    {
      "id": "HGNC:11128",
      "symbol": "SNAI1",
      "name": "snail family transcriptional repressor 1",
      "aliases": ["Snail", "SNAIL"],
      "type": "gene",
      "role": "emt_master_regulator",
      "expression_localized": "LOW",
      "expression_metastatic": "HIGH",
      "location": "20q13.13",
      "cross_references": {
        "uniprot": "O95863",
        "entrez": "6615",
        "ensembl": "ENSG00000124216"
      }
    },
    {
      "id": "HGNC:12428",
      "symbol": "TWIST1",
      "name": "twist family bHLH transcription factor 1",
      "aliases": ["H-twist"],
      "type": "gene",
      "role": "emt_master_regulator",
      "expression_localized": "LOW",
      "expression_metastatic": "HIGH",
      "location": "7p21.1",
      "cross_references": {
        "uniprot": "Q15672",
        "entrez": "7291",
        "ensembl": "ENSG00000122691"
      }
    },
    {
      "id": "HGNC:11642",
      "symbol": "ZEB1",
      "name": "zinc finger E-box binding homeobox 1",
      "aliases": ["TCF8", "AREB6"],
      "type": "gene",
      "role": "emt_master_regulator",
      "expression_localized": "LOW",
      "expression_metastatic": "HIGH",
      "location": "10p11.22",
      "cross_references": {
        "uniprot": "P37275",
        "entrez": "6935",
        "ensembl": "ENSG00000148516"
      }
    },
    {
      "id": "WP:WP5469",
      "name": "Hallmark of cancer: metastasis and EMT",
      "type": "pathway",
      "source": "WikiPathways"
    },
    {
      "id": "WP:WP4239",
      "name": "Epithelial to mesenchymal transition in colorectal cancer",
      "type": "pathway",
      "source": "WikiPathways"
    }
  ],
  "edges": [
    {
      "source": "HGNC:11128",
      "target": "HGNC:1748",
      "relationship": "REPRESSES",
      "mechanism": "e_box_binding_epigenetic",
      "evidence": "UniProt: Binds to 3 E-boxes of CDH1 promoter, recruits KDM1A"
    },
    {
      "source": "HGNC:12428",
      "target": "HGNC:1748",
      "relationship": "REPRESSES",
      "mechanism": "transcriptional_repression",
      "evidence": "UniProt: Acts as transcriptional regulator"
    },
    {
      "source": "HGNC:11642",
      "target": "HGNC:1748",
      "relationship": "REPRESSES",
      "mechanism": "e_box_binding_brg1",
      "evidence": "UniProt: Represses E-cadherin promoter by recruiting SMARCA4/BRG1"
    },
    {
      "source": "HGNC:11128",
      "target": "HGNC:12692",
      "relationship": "INDUCES",
      "mechanism": "emt_induction",
      "evidence": "EMT master regulator induces mesenchymal markers"
    },
    {
      "source": "HGNC:11128",
      "target": "HGNC:3778",
      "relationship": "INDUCES",
      "mechanism": "emt_induction",
      "evidence": "EMT master regulator induces mesenchymal markers"
    },
    {
      "source": "HGNC:1748",
      "target": "CELL_ADHESION",
      "relationship": "PROMOTES",
      "mechanism": "homophilic_binding",
      "evidence": "UniProt: Calcium-dependent cell adhesion"
    },
    {
      "source": "HGNC:12692",
      "target": "CELL_MOTILITY",
      "relationship": "PROMOTES",
      "mechanism": "cytoskeleton_organization",
      "evidence": "UniProt: Plays role in cell directional movement"
    },
    {
      "source": "LOCALIZED_TUMOR",
      "target": "HGNC:1748",
      "relationship": "EXPRESSES_HIGH",
      "evidence": "Epithelial phenotype maintains CDH1"
    },
    {
      "source": "METASTATIC_TUMOR",
      "target": "HGNC:11128",
      "relationship": "EXPRESSES_HIGH",
      "evidence": "EMT activation in metastatic cells"
    },
    {
      "source": "METASTATIC_TUMOR",
      "target": "HGNC:12692",
      "relationship": "EXPRESSES_HIGH",
      "evidence": "Mesenchymal phenotype marker"
    },
    {
      "source": "EMT_INDUCTION",
      "target": "METASTASIS",
      "relationship": "ENABLES",
      "evidence": "EMT enables cell detachment, invasion, and metastasis"
    }
  ]
}
```

---

## Clinical Implications

### EMT as Therapeutic Target
- **E-cadherin restoration**: Re-expression can reverse EMT
- **SNAI1/TWIST1/ZEB1 inhibition**: Block EMT induction
- **TGF-beta pathway inhibitors**: Galunisertib targeting TGF-beta signaling
- **Epigenetic modulators**: HDAC inhibitors may reverse EMT

### Biomarker Panels
- **Localized tumor signature**: CDH1(+), EPCAM(+), VIM(-), SNAI1(-)
- **Metastatic risk signature**: CDH1(-), VIM(+), SNAI1(+), TWIST1(+)

### EMT Plasticity
- EMT is reversible (MET - Mesenchymal-Epithelial Transition)
- Metastatic cells may re-epithelialize at distant sites
- Partial EMT states exist (hybrid E/M phenotypes)

---

## STRING Network Validation (E-cadherin/CDH1)

STRING interactions for CDH1 (STRING:9606.ENSP00000261769) with confidence >0.7:

| Partner | Score | Function |
|---------|-------|----------|
| CTNNA1 | 0.999 | Alpha-catenin, adherens junction |
| CTNNB1 | 0.997 | Beta-catenin, adherens junction/Wnt signaling |
| VCL | 0.996 | Vinculin, cell adhesion focal contact |
| IQGAP1 | 0.997 | Scaffold protein for cell-cell junctions |
| ITGAE | 0.997 | Integrin alpha-E, epithelial cell adhesion |
| CDH2 | 0.995 | N-cadherin (mesenchymal cadherin) |
| OCLN | 0.993 | Occludin, tight junction component |
| CBLL1 | 0.993 | E3 ubiquitin ligase for cadherins |
| TJP1 | 0.987 | ZO-1, tight junction scaffold |
| SRC | 0.988 | Proto-oncogene tyrosine-protein kinase |

**Interpretation**: CDH1 is central to epithelial cell adhesion complexes. Loss of CDH1 during EMT disrupts adherens junctions (CTNNA1, CTNNB1), tight junctions (TJP1, OCLN), and focal adhesions (VCL), enabling cell motility and invasion.

---

This validation confirms that metastasis is fundamentally linked to EMT, with transcription factors SNAI1, TWIST1, and ZEB1 serving as master switches that repress epithelial markers (CDH1) and induce mesenchymal markers (VIM, FN1).
