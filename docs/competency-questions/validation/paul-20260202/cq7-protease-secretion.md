# CQ7: Protease Secretion for Invasion - Validation Report

**Status**: VALIDATED

**Question**: What is the pharmacological mechanism by which a tumor secretes proteases to break down the local environment and gain access to the blood?

**Validation Date**: 2026-02-02

---

## Executive Summary

Tumors secrete matrix metalloproteinases (MMPs) to degrade the extracellular matrix (ECM) and basement membrane, enabling invasion and intravasation. The key pathway is:

1. **ECM Degradation**: MMP2 and MMP9 (gelatinases) degrade type IV collagen in basement membranes
2. **MMP Activation**: MMP14 (membrane-bound) activates pro-MMP2 at the cell surface
3. **Ectodomain Shedding**: ADAM17 (TACE) releases growth factors and cytokines
4. **Intravasation**: ECM breach allows tumor cell entry into blood/lymphatic vessels

---

## CURIEs Resolved

### Matrix Metalloproteinases (MMPs)
| Symbol | HGNC ID | UniProtKB | Entrez | Substrate |
|--------|---------|-----------|--------|-----------|
| MMP2 | HGNC:7166 | UniProtKB:P08253 | 4313 | Type IV collagen, gelatin |
| MMP9 | HGNC:7176 | UniProtKB:P14780 | 4318 | Type IV/V collagen |
| MMP14 (MT1-MMP) | HGNC:7160 | UniProtKB:P50281 | 4323 | Collagen, pro-MMP2 |

### ADAM Metalloproteinases
| Symbol | HGNC ID | UniProtKB | Entrez | Function |
|--------|---------|-----------|--------|----------|
| ADAM17 (TACE) | HGNC:195 | UniProtKB:P78536 | 6868 | Ectodomain shedding |

---

## Key Findings

### 1. MMP2 (Gelatinase A) - ECM Degradation
**UniProtKB:P08253** - 72 kDa type IV collagenase:
- "Ubiquitous metalloproteinase involved in diverse functions such as remodeling of the vasculature, angiogenesis, tissue repair, tumor invasion, inflammation, and atherosclerotic plaque rupture"
- "Degrades extracellular matrix proteins"
- "Cleaves GSK3beta in vitro"
- "Involved in the formation of the fibrovascular tissues in association with MMP14"
- Substrate: Type IV collagen (basement membrane component)

### 2. MMP9 (Gelatinase B) - Matrix Remodeling
**UniProtKB:P14780** - Matrix metalloproteinase-9:
- "Plays an essential role in local proteolysis of the extracellular matrix and in leukocyte migration"
- "Could play a role in bone osteoclastic resorption"
- "Cleaves type IV and type V collagen into large C-terminal three quarter fragments and shorter N-terminal one quarter fragments"
- "Degrades fibronectin but not laminin"
- "Cleaves NINJ1 to generate the Secreted ninjurin-1 form"

### 3. MMP14 (MT1-MMP) - MMP Activator
**UniProtKB:P50281** - Matrix metalloproteinase-14:
- "Endopeptidase that degrades various components of the extracellular matrix such as collagen"
- "Essential for pericellular collagenolysis and modeling of skeletal and extraskeletal connective tissues during development"
- "Activates progelatinase A/MMP2, thereby acting as a positive regulator of cell growth and migration"
- "Involved in the formation of the fibrovascular tissues in association with pro-MMP2"
- "May be involved in actin cytoskeleton reorganization by cleaving PTK7"
- "Acts as a regulator of Notch signaling by mediating cleavage and inhibition of DLL1"

### 4. ADAM17 (TACE) - Ectodomain Sheddase
**UniProtKB:P78536** - ADAM metallopeptidase domain 17:
- "Transmembrane metalloprotease which mediates the ectodomain shedding of a myriad of transmembrane proteins including adhesion proteins, growth factor precursors and cytokines important for inflammation and immunity"
- "Cleaves the membrane-bound precursor of TNF to its mature soluble form"
- "Responsible for the proteolytic release of several other cell-surface proteins, including p75 TNF-receptor, interleukin 1 receptor type II, p55 TNF-receptor, transforming growth factor-alpha, L-selectin, growth hormone receptor, MUC1 and the amyloid precursor protein"
- "Acts as an activator of Notch pathway by mediating cleavage of Notch"
- "Plays a role in the proteolytic processing of ACE2"

---

## MMP Activation Cascade

```
Pro-MMP2 (inactive zymogen)
        |
        v
    +-------+
    | MMP14 |  (MT1-MMP, membrane-bound)
    +-------+
        |
        v (Proteolytic cleavage)
Active MMP2 (72 kDa gelatinase)
        |
        v
    +------------------------+
    | TYPE IV COLLAGEN       |
    | (Basement membrane)    |
    +------------------------+
        |
        v (Degradation)
    +------------------------+
    | BASEMENT MEMBRANE      |
    | BREACH                 |
    +------------------------+
        |
        v
    +------------------------+
    | MMP9 + MMP2            |
    | (ECM remodeling)       |
    +------------------------+
        |
        v
    +------------------------+
    | FIBRONECTIN            |
    | DEGRADATION            |
    +------------------------+
        |
        v
    INTRAVASATION
    (Entry to bloodstream)
```

---

## WikiPathways Evidence

### WP129: Matrix Metalloproteinases
- **Components**: 30 genes, 92 proteins
- **Key MMP family members**: MMP1-3, MMP7-17, MMP19-21, MMP23A/B, MMP24-28
- **TIMP inhibitors**: TIMP1-4 (tissue inhibitors of metalloproteinases)
- **Regulator**: BSG (Basigin/CD147) - induces MMP expression
- **URL**: https://classic.wikipathways.org/index.php/Pathway:WP129

### WP2769: Activation of Matrix Metalloproteinases
- **Components**: 33 genes, 118 proteins
- **Focus**: Pro-MMP to active MMP conversion mechanisms
- **URL**: https://classic.wikipathways.org/index.php/Pathway:WP2769

### WP2774: Degradation of the Extracellular Matrix
- **Components**: ECM substrates and proteases
- **URL**: https://classic.wikipathways.org/index.php/Pathway:WP2774

---

## ECM Degradation Pathway

### Phase 1: MMP Expression & Secretion
| Trigger | Effect |
|---------|--------|
| Hypoxia | HIF-1alpha induces MMP2/9 expression |
| TGF-beta | Induces MMP2 expression |
| Growth factors (EGF, VEGF) | Increase MMP secretion |
| Inflammatory cytokines (TNF, IL-1) | Induce MMP expression |

### Phase 2: MMP Activation
| Pro-enzyme | Activator | Mechanism |
|------------|-----------|-----------|
| Pro-MMP2 | MMP14 (MT1-MMP) | Cell surface proteolytic cleavage |
| Pro-MMP9 | MMP3 (Stromelysin) | Proteolytic cascade |
| Pro-MMP2 | TIMP2 paradox | TIMP2 bridges MMP14 and pro-MMP2 |

### Phase 3: ECM Degradation
| Substrate | Primary MMP | Result |
|-----------|-------------|--------|
| Type IV collagen | MMP2, MMP9 | Basement membrane breach |
| Type V collagen | MMP9 | ECM degradation |
| Fibronectin | MMP9 | Matrix remodeling |
| Gelatin | MMP2, MMP9 | Denatured collagen clearance |

### Phase 4: Intravasation
- Basement membrane breach enables tumor cell contact with endothelium
- ADAM17 sheds adhesion molecules facilitating transendothelial migration
- MMP14 cleaves receptors affecting cell-matrix interactions

---

## Pharmacological Intervention History

### Historical MMP Inhibitors (Failed Clinical Trials)
| Compound | Target | Outcome |
|----------|--------|---------|
| Marimastat | Broad MMP | Phase III failure |
| Batimastat | Broad MMP | Discontinued |
| Prinomastat | MMP2, MMP9, MMP13, MMP14 | Phase III failure |

### Failure Analysis
- Broad-spectrum inhibition caused musculoskeletal syndrome (MSS)
- MMPs have dual roles (pro- and anti-tumorigenic)
- Timing of intervention critical (early vs late stage)

### Current Approaches
- Selective MMP14 inhibitors in development
- ADAM17 inhibitors (more selective sheddase targeting)
- Antibody-based approaches targeting specific MMPs

### ChEMBL Drug Validation

| Drug | ChEMBL ID | Max Phase | Target | Outcome |
|------|-----------|-----------|--------|---------|
| Marimastat | CHEMBL:279785 | 3 | Broad MMP | Clinical failure (MSS side effects) |
| Batimastat | CHEMBL:279786 | 2 | Broad MMP | Discontinued |

**Marimastat (CHEMBL:279785)**:
- Synonyms: BB-2516, GI-5712, TA-2516
- SMILES: CNC(=O)[C@@H](NC(=O)[C@H](CC(C)C)[C@H](O)C(=O)NO)C(C)(C)C
- MW: 331.41 Da
- Indications (clinical trials): Breast Neoplasms, Lung Neoplasms

**Batimastat (CHEMBL:279786)**:
- Synonyms: BB-94
- SMILES: CNC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CC(C)C)[C@H](CSc1cccs1)C(=O)NO
- MW: 477.65 Da
- Mechanism: Hydroxamic acid-based MMP inhibitor

---

## Provenance Table

| Tool | Query | Result Count | Key CURIEs |
|------|-------|--------------|------------|
| hgnc_search_genes | MMP2 | 2 | HGNC:7166 |
| hgnc_search_genes | MMP9 | 2 | HGNC:7176 |
| hgnc_search_genes | MMP14 | 1 | HGNC:7160 |
| hgnc_search_genes | ADAM17 | 1 | HGNC:195 |
| hgnc_get_gene | HGNC:7166 | 1 | MMP2 full record |
| hgnc_get_gene | HGNC:7176 | 1 | MMP9 full record |
| hgnc_get_gene | HGNC:7160 | 1 | MMP14 full record |
| hgnc_get_gene | HGNC:195 | 1 | ADAM17 full record |
| uniprot_get_protein | UniProtKB:P08253 | 1 | MMP2 function |
| uniprot_get_protein | UniProtKB:P14780 | 1 | MMP9 function |
| uniprot_get_protein | UniProtKB:P50281 | 1 | MMP14 function |
| uniprot_get_protein | UniProtKB:P78536 | 1 | ADAM17 function |
| wikipathways_search_pathways | matrix metalloproteinase | 10 | WP129, WP2769 |
| wikipathways_search_pathways | extracellular matrix degradation | 10 | WP2774, WP2703 |
| wikipathways_get_pathway | WP:WP129 | 1 | MMP pathway |
| wikipathways_get_pathway | WP:WP2769 | 1 | MMP activation |

---

## Graph Payload

```json
{
  "nodes": [
    {
      "id": "HGNC:7166",
      "symbol": "MMP2",
      "name": "matrix metallopeptidase 2",
      "aliases": ["Gelatinase A", "72kDa type IV collagenase"],
      "type": "gene",
      "role": "ecm_protease",
      "substrate": ["type_IV_collagen", "gelatin", "fibronectin"],
      "location": "16q12.2",
      "cross_references": {
        "uniprot": "P08253",
        "entrez": "4313",
        "ensembl": "ENSG00000087245",
        "string": "9606.ENSP00000219070"
      }
    },
    {
      "id": "HGNC:7176",
      "symbol": "MMP9",
      "name": "matrix metallopeptidase 9",
      "aliases": ["Gelatinase B", "92kDa type IV collagenase"],
      "type": "gene",
      "role": "ecm_protease",
      "substrate": ["type_IV_collagen", "type_V_collagen", "fibronectin"],
      "location": "20q13.12",
      "cross_references": {
        "uniprot": "P14780",
        "entrez": "4318",
        "ensembl": "ENSG00000100985",
        "string": "9606.ENSP00000361405"
      }
    },
    {
      "id": "HGNC:7160",
      "symbol": "MMP14",
      "name": "matrix metallopeptidase 14",
      "aliases": ["MT1-MMP", "membrane type 1 MMP"],
      "type": "gene",
      "role": "mmp_activator",
      "substrate": ["collagen", "pro-MMP2"],
      "location": "14q11.2",
      "cross_references": {
        "uniprot": "P50281",
        "entrez": "4323",
        "ensembl": "ENSG00000157227",
        "string": "9606.ENSP00000308208"
      }
    },
    {
      "id": "HGNC:195",
      "symbol": "ADAM17",
      "name": "ADAM metallopeptidase domain 17",
      "aliases": ["TACE", "TNF-alpha convertase"],
      "type": "gene",
      "role": "ectodomain_sheddase",
      "substrate": ["TNF", "TGF-alpha", "L-selectin", "ACE2", "Notch"],
      "location": "2p25.1",
      "cross_references": {
        "uniprot": "P78536",
        "entrez": "6868",
        "ensembl": "ENSG00000151694",
        "string": "9606.ENSP00000309968"
      }
    },
    {
      "id": "ECM:TYPE_IV_COLLAGEN",
      "name": "Type IV Collagen",
      "type": "ecm_component",
      "role": "basement_membrane_component"
    },
    {
      "id": "ECM:FIBRONECTIN",
      "name": "Fibronectin",
      "type": "ecm_component",
      "role": "matrix_glycoprotein"
    },
    {
      "id": "WP:WP129",
      "name": "Matrix metalloproteinases",
      "type": "pathway",
      "source": "WikiPathways"
    },
    {
      "id": "WP:WP2769",
      "name": "Activation of Matrix Metalloproteinases",
      "type": "pathway",
      "source": "WikiPathways"
    }
  ],
  "edges": [
    {
      "source": "HGNC:7160",
      "target": "HGNC:7166",
      "relationship": "ACTIVATES",
      "mechanism": "proteolytic_cleavage",
      "evidence": "UniProt: Activates progelatinase A/MMP2"
    },
    {
      "source": "HGNC:7166",
      "target": "ECM:TYPE_IV_COLLAGEN",
      "relationship": "DEGRADES",
      "mechanism": "proteolysis",
      "evidence": "UniProt: 72 kDa type IV collagenase"
    },
    {
      "source": "HGNC:7176",
      "target": "ECM:TYPE_IV_COLLAGEN",
      "relationship": "DEGRADES",
      "mechanism": "proteolysis",
      "evidence": "UniProt: Cleaves type IV and type V collagen"
    },
    {
      "source": "HGNC:7176",
      "target": "ECM:FIBRONECTIN",
      "relationship": "DEGRADES",
      "mechanism": "proteolysis",
      "evidence": "UniProt: Degrades fibronectin"
    },
    {
      "source": "HGNC:7160",
      "target": "ECM:TYPE_IV_COLLAGEN",
      "relationship": "DEGRADES",
      "mechanism": "pericellular_collagenolysis",
      "evidence": "UniProt: Essential for pericellular collagenolysis"
    },
    {
      "source": "HGNC:195",
      "target": "TNF_PRECURSOR",
      "relationship": "CLEAVES",
      "mechanism": "ectodomain_shedding",
      "evidence": "UniProt: Cleaves membrane-bound TNF precursor"
    },
    {
      "source": "HGNC:195",
      "target": "GROWTH_FACTOR_RELEASE",
      "relationship": "ENABLES",
      "mechanism": "ectodomain_shedding",
      "evidence": "UniProt: Sheds TGF-alpha, growth hormone receptor"
    },
    {
      "source": "TUMOR",
      "target": "HGNC:7166",
      "relationship": "SECRETES",
      "mechanism": "hypoxia_tgfb_induction",
      "evidence": "HIF-1alpha and TGF-beta induce MMP2 expression"
    },
    {
      "source": "TUMOR",
      "target": "HGNC:7176",
      "relationship": "SECRETES",
      "mechanism": "inflammatory_induction",
      "evidence": "TNF, IL-1 induce MMP9 expression"
    },
    {
      "source": "ECM_DEGRADATION",
      "target": "BASEMENT_MEMBRANE_BREACH",
      "relationship": "ENABLES",
      "evidence": "Type IV collagen degradation breaches basement membrane"
    },
    {
      "source": "BASEMENT_MEMBRANE_BREACH",
      "target": "INTRAVASATION",
      "relationship": "ENABLES",
      "evidence": "Tumor cells access blood/lymphatic vessels"
    },
    {
      "source": "INTRAVASATION",
      "target": "METASTASIS",
      "relationship": "INITIATES",
      "evidence": "Circulating tumor cells can seed distant metastases"
    }
  ]
}
```

---

## Invasion Mechanism Summary

### Step-by-Step Process
1. **Tumor Growth**: Tumor mass expands, encounters basement membrane barrier
2. **MMP Induction**: Hypoxia, TGF-beta, inflammatory signals induce MMP expression
3. **MMP Activation**: MMP14 at cell surface activates pro-MMP2
4. **Matrix Degradation**: Active MMP2/MMP9 degrade type IV collagen (basement membrane)
5. **ECM Remodeling**: Fibronectin and other matrix proteins degraded
6. **Adhesion Remodeling**: ADAM17 sheds adhesion molecules
7. **Basement Membrane Breach**: Tumor cells cross into stroma
8. **Intravasation**: Tumor cells invade blood/lymphatic vessels
9. **Dissemination**: Circulating tumor cells spread to distant organs

### Key Pharmacological Targets
| Target | Rationale | Challenge |
|--------|-----------|-----------|
| MMP2 | Basement membrane degradation | Broad inhibition causes side effects |
| MMP9 | ECM remodeling | Dual pro/anti-tumor roles |
| MMP14 | MMP2 activation, invasion | Most promising selective target |
| ADAM17 | Growth factor/cytokine release | Multiple physiological roles |

---

## Clinical Implications

This validation confirms the molecular basis for tumor invasion:
1. **MMPs are essential for invasion** - Degrade basement membrane and ECM
2. **Activation cascade is targetable** - MMP14 activates MMP2
3. **Historical failures inform design** - Selectivity is critical
4. **ADAM17 provides alternative target** - Ectodomain shedding affects multiple pathways

The MMP/ADAM system represents a validated but challenging therapeutic target, requiring careful consideration of specificity, timing, and tumor stage for successful intervention.

---

## STRING Network Validation (MMP9)

STRING interactions for MMP9 (STRING:9606.ENSP00000361405) with confidence >0.7:

| Partner | Score | Function |
|---------|-------|----------|
| TIMP1 | 0.999 | Tissue inhibitor of MMP (direct inhibitor) |
| MMP1 | 0.999 | Interstitial collagenase (cascade partner) |
| ELANE | 0.999 | Neutrophil elastase (inflammatory cascade) |
| MPO | 0.999 | Myeloperoxidase (inflammatory cascade) |
| CTSG | 0.992 | Cathepsin G (serine protease, activator) |
| TGFB1 | 0.882 | TGF-beta1 (inducer of MMP expression) |
| LCN2 | 0.850 | Lipocalin-2 (forms complex with MMP9) |
| CD44 | 0.922 | Cell surface glycoprotein (localizes MMP9) |

**Interpretation**: MMP9 is regulated by TIMP1 and participates in inflammatory cascades (ELANE, MPO, CTSG). TGF-beta1 induces MMP9 expression, while LCN2 forms a stabilizing complex with MMP9. CD44 localizes MMP9 to the cell surface for pericellular matrix degradation.

---

## Open Targets Disease Associations (MMP9)

Target ID: ENSG00000100985

| Disease | EFO/MONDO ID | Association Score |
|---------|--------------|-------------------|
| Metaphyseal anadysplasia | MONDO_0015177 | 0.66 |
| Crohn's disease | EFO_0000384 | 0.38 |
| Lumbar disc degeneration | EFO_0004994 | 0.37 |
| Lung cancer | MONDO_0008903 | 0.36 |
| Breast cancer | MONDO_0007254 | 0.31 |
| Gastric adenocarcinoma | EFO_0000503 | 0.28 |
| Macular degeneration | EFO_0009606 | 0.25 |
| COVID-19 | MONDO_0100096 | 0.25 |
| COPD | EFO_0000341 | 0.14 |
| NSCLC | EFO_0003060 | 0.12 |
| Hepatocellular carcinoma | EFO_0000182 | 0.12 |

**Interpretation**: MMP9 shows significant associations with multiple cancer types (lung, breast, gastric, HCC), confirming its role in tumor invasion and metastasis. The association with inflammatory conditions (Crohn's, COPD) reflects MMP9's dual role in tissue remodeling and inflammation.
