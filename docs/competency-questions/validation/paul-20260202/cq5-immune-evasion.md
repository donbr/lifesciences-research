# CQ5: Immune Evasion Mechanisms - Validation Report

**Status**: VALIDATED

**Question**: How does the tumor hijack the immune system to create an evasion mechanism, and what specific factors does it secrete to inhibit immune response or stimulate its own growth?

**Validation Date**: 2026-02-02

---

## Executive Summary

Tumors evade immune surveillance through two primary mechanisms:
1. **Immune Checkpoint Upregulation**: Tumor cells upregulate inhibitory ligands (PD-L1/CD274) that bind to checkpoint receptors (PD-1, CTLA-4, LAG-3) on T-cells, causing T-cell exhaustion and anergy.
2. **Immunosuppressive Factor Secretion**: Tumors secrete cytokines (TGF-beta1, IL-10) and growth factors (VEGF-A) that inhibit immune cell function and promote tumor growth.

---

## CURIEs Resolved

### Immune Checkpoint Genes (Inhibitory Receptors/Ligands)
| Symbol | HGNC ID | UniProtKB | Entrez | Role |
|--------|---------|-----------|--------|------|
| CD274 (PD-L1) | HGNC:17635 | UniProtKB:Q9NZQ7 | 29126 | Ligand on tumor cells |
| PDCD1 (PD-1) | HGNC:8760 | UniProtKB:Q15116 | 5133 | Receptor on T-cells |
| CTLA4 | HGNC:2505 | UniProtKB:P16410 | 1493 | Receptor on T-cells |
| IDO1 | HGNC:6059 | UniProtKB:P14902 | 3620 | Enzyme in tumor cells |
| LAG3 | HGNC:6476 | UniProtKB:P18627 | 3902 | Receptor on T-cells |

### Immunosuppressive Secreted Factors
| Symbol | HGNC ID | UniProtKB | Entrez | Function |
|--------|---------|-----------|--------|----------|
| TGFB1 | HGNC:11766 | UniProtKB:P01137 | 7040 | Immunosuppressive cytokine |
| IL10 | HGNC:5962 | UniProtKB:P22301 | 3586 | Anti-inflammatory cytokine |
| VEGFA | HGNC:12680 | UniProtKB:P15692 | 7422 | Angiogenic growth factor |

---

## Key Findings

### 1. PD-1/PD-L1 Axis (Primary Checkpoint)
**CD274/PD-L1** (UniProtKB:Q9NZQ7):
- "Plays a critical role in induction and maintenance of immune tolerance to self"
- "As a ligand for the inhibitory receptor PDCD1/PD-1, modulates the activation threshold of T-cells and limits T-cell effector response"
- Located at 9p24.1 - frequently amplified in tumors

**PDCD1/PD-1** (UniProtKB:Q15116):
- "Inhibitory receptor on antigen activated T-cells"
- "Delivers inhibitory signals upon binding to ligands CD274/PDCD1L1 and CD273/PDCD1LG2"
- "Suppresses T-cell activation through the recruitment of PTPN11/SHP-2"
- Mechanism: Phosphorylation of ITSM motif -> PTPN11/SHP-2 recruitment -> Dephosphorylation of ZAP70, PRKCQ, CD247

### 2. CTLA-4 Checkpoint
**CTLA4** (UniProtKB:P16410):
- "Inhibitory receptor acting as a major negative regulator of T-cell responses"
- "Acts as a decoy receptor: the affinity of CTLA4 for its natural B7 family ligands, CD80 and CD86, is considerably stronger than the affinity of their cognate stimulatory coreceptor CD28"
- Outcompetes CD28 for B7 binding -> Prevents T-cell costimulation

### 3. IDO1 Metabolic Checkpoint
**IDO1** (UniProtKB:P14902):
- "Catalyzes the first and rate limiting step of the catabolism of the essential amino acid tryptophan along the kynurenine pathway"
- "Tryptophan shortage inhibits T lymphocytes division and accumulation of tryptophan catabolites induces T-cell apoptosis and differentiation of regulatory T-cells"
- "Acts as a suppressor of anti-tumor immunity"

### 4. LAG-3 Checkpoint
**LAG3** (UniProtKB:P18627):
- "Inhibitory receptor on antigen activated T-cells"
- "Delivers inhibitory signals upon binding to ligands, such as MHC class II, its main ligand present at the surface of APCs, and FGL1, which is secreted by hepatocytes and certain types of tumor cells"
- "May inhibit antigen-specific T-cell activation in synergy with PDCD1/PD-1"

---

## STRING Interaction Network

### CD274/PD-L1 Network (High Confidence >0.7)
| Partner | Score | Evidence Type |
|---------|-------|---------------|
| CD8A | 0.999 | Database, Text-mining |
| CD28 | 0.971 | Text-mining |
| PDCD1 | 0.960 | Database, Text-mining |
| CD86 | 0.958 | Text-mining |
| CD80 | 0.958 | Experiments, Text-mining |
| CTLA4 | 0.955 | Experiments, Text-mining |
| PDCD1LG2 | 0.945 | Database, Text-mining |
| LAG3 | 0.914 | Text-mining |
| ICOS | 0.929 | Text-mining |
| HAVCR2 (TIM-3) | 0.833 | Text-mining |
| TIGIT | 0.757 | Text-mining |
| PTPN11 (SHP-2) | 0.783 | Database, Experiments |

### Key Signaling Partners
- **PTPN11/SHP-2**: Phosphatase recruited by PD-1 to dephosphorylate TCR signaling components
- **PTPN6/SHP-1**: Alternative phosphatase in immune inhibition
- **STAT3**: Transcription factor activated in immune evasion

---

## WikiPathways Evidence

### WP4585: Cancer Immunotherapy by PD-1 Blockade
- **Components**: 26 genes, 85 proteins
- **Key pathway members**: CD274, PDCD1, PDCD1LG2, CD8A, ZAP70, LCK, NFATC1, STAT3, JUN
- **URL**: https://classic.wikipathways.org/index.php/Pathway:WP4585

### WP4582: Cancer Immunotherapy by CTLA4 Blockade
- **Components**: 16 genes, 60 proteins
- **Key pathway members**: CTLA4, CD80, CD86, CD28, PTPN6, PTPN11, PIK3CA, PIK3R1
- **URL**: https://classic.wikipathways.org/index.php/Pathway:WP4582

---

## Provenance Table

| Tool | Query | Result Count | Key CURIEs |
|------|-------|--------------|------------|
| hgnc_search_genes | CD274 | 1 | HGNC:17635 |
| hgnc_search_genes | PDCD1 | 2 | HGNC:8760 |
| hgnc_search_genes | CTLA4 | 1 | HGNC:2505 |
| hgnc_search_genes | IDO1 | 1 | HGNC:6059 |
| hgnc_search_genes | LAG3 | 1 | HGNC:6476 |
| hgnc_search_genes | TGFB1 | 2 | HGNC:11766 |
| hgnc_search_genes | IL10 | 1 | HGNC:5962 |
| hgnc_search_genes | VEGFA | 1 | HGNC:12680 |
| uniprot_get_protein | UniProtKB:Q9NZQ7 | 1 | CD274/PD-L1 |
| uniprot_get_protein | UniProtKB:Q15116 | 1 | PDCD1/PD-1 |
| uniprot_get_protein | UniProtKB:P16410 | 1 | CTLA4 |
| uniprot_get_protein | UniProtKB:P14902 | 1 | IDO1 |
| uniprot_get_protein | UniProtKB:P18627 | 1 | LAG3 |
| string_get_interactions | STRING:9606.ENSP00000370989 | 15 | CD274 network |
| string_get_interactions | STRING:9606.ENSP00000335062 | 15 | PDCD1 network |
| wikipathways_search_pathways | immune checkpoint | 10 | WP4582, WP4585 |
| wikipathways_get_pathway | WP:WP4585 | 1 | PD-1 blockade |
| wikipathways_get_pathway | WP:WP4582 | 1 | CTLA4 blockade |
| entrez_get_pubmed_links | NCBIGene:29126 | 5 | CD274 literature |
| entrez_get_pubmed_links | NCBIGene:5133 | 5 | PDCD1 literature |

---

## Graph Payload

```json
{
  "nodes": [
    {
      "id": "HGNC:17635",
      "symbol": "CD274",
      "name": "CD274 molecule",
      "aliases": ["PD-L1", "B7-H1"],
      "type": "gene",
      "role": "immune_checkpoint_ligand",
      "location": "9p24.1",
      "cross_references": {
        "uniprot": "Q9NZQ7",
        "entrez": "29126",
        "ensembl": "ENSG00000120217"
      }
    },
    {
      "id": "HGNC:8760",
      "symbol": "PDCD1",
      "name": "programmed cell death 1",
      "aliases": ["PD-1", "CD279"],
      "type": "gene",
      "role": "immune_checkpoint_receptor",
      "location": "2q37.3",
      "cross_references": {
        "uniprot": "Q15116",
        "entrez": "5133",
        "ensembl": "ENSG00000188389"
      }
    },
    {
      "id": "HGNC:2505",
      "symbol": "CTLA4",
      "name": "cytotoxic T-lymphocyte associated protein 4",
      "aliases": ["CD152"],
      "type": "gene",
      "role": "immune_checkpoint_receptor",
      "location": "2q33.2",
      "cross_references": {
        "uniprot": "P16410",
        "entrez": "1493",
        "ensembl": "ENSG00000163599"
      }
    },
    {
      "id": "HGNC:6059",
      "symbol": "IDO1",
      "name": "indoleamine 2,3-dioxygenase 1",
      "type": "gene",
      "role": "metabolic_checkpoint",
      "location": "8p11.21",
      "cross_references": {
        "uniprot": "P14902",
        "entrez": "3620",
        "ensembl": "ENSG00000131203"
      }
    },
    {
      "id": "HGNC:6476",
      "symbol": "LAG3",
      "name": "lymphocyte activating 3",
      "aliases": ["CD223"],
      "type": "gene",
      "role": "immune_checkpoint_receptor",
      "location": "12p13.31",
      "cross_references": {
        "uniprot": "P18627",
        "entrez": "3902",
        "ensembl": "ENSG00000089692"
      }
    },
    {
      "id": "HGNC:11766",
      "symbol": "TGFB1",
      "name": "transforming growth factor beta 1",
      "type": "gene",
      "role": "immunosuppressive_cytokine",
      "location": "19q13.2",
      "cross_references": {
        "uniprot": "P01137",
        "entrez": "7040",
        "ensembl": "ENSG00000105329"
      }
    },
    {
      "id": "HGNC:5962",
      "symbol": "IL10",
      "name": "interleukin 10",
      "type": "gene",
      "role": "immunosuppressive_cytokine",
      "location": "1q32.1",
      "cross_references": {
        "uniprot": "P22301",
        "entrez": "3586",
        "ensembl": "ENSG00000136634"
      }
    },
    {
      "id": "HGNC:12680",
      "symbol": "VEGFA",
      "name": "vascular endothelial growth factor A",
      "type": "gene",
      "role": "tumor_growth_factor",
      "location": "6p21.1",
      "cross_references": {
        "uniprot": "P15692",
        "entrez": "7422",
        "ensembl": "ENSG00000112715"
      }
    },
    {
      "id": "WP:WP4585",
      "name": "Cancer immunotherapy by PD-1 blockade",
      "type": "pathway",
      "source": "WikiPathways"
    },
    {
      "id": "WP:WP4582",
      "name": "Cancer immunotherapy by CTLA4 blockade",
      "type": "pathway",
      "source": "WikiPathways"
    }
  ],
  "edges": [
    {
      "source": "HGNC:17635",
      "target": "HGNC:8760",
      "relationship": "BINDS",
      "mechanism": "inhibitory_ligand_receptor",
      "confidence": 0.96,
      "evidence": "STRING interaction, UniProt function"
    },
    {
      "source": "HGNC:8760",
      "target": "T_CELL_ACTIVATION",
      "relationship": "INHIBITS",
      "mechanism": "SHP-2_recruitment_dephosphorylation",
      "evidence": "UniProt: PTPN11/SHP-2 recruitment -> dephosphorylation of ZAP70, PRKCQ, CD247"
    },
    {
      "source": "HGNC:2505",
      "target": "CD28_COSTIMULATION",
      "relationship": "INHIBITS",
      "mechanism": "competitive_binding_B7",
      "evidence": "UniProt: Decoy receptor outcompetes CD28 for CD80/CD86 binding"
    },
    {
      "source": "HGNC:6059",
      "target": "T_CELL_PROLIFERATION",
      "relationship": "INHIBITS",
      "mechanism": "tryptophan_depletion_kynurenine",
      "evidence": "UniProt: Tryptophan shortage inhibits T lymphocytes division"
    },
    {
      "source": "HGNC:6476",
      "target": "T_CELL_ACTIVATION",
      "relationship": "INHIBITS",
      "mechanism": "TCR_disruption",
      "evidence": "UniProt: Forms condensates with CD3E, disrupting LCK association"
    },
    {
      "source": "HGNC:6476",
      "target": "HGNC:8760",
      "relationship": "SYNERGIZES_WITH",
      "mechanism": "dual_checkpoint_inhibition",
      "evidence": "UniProt: May inhibit T-cell activation in synergy with PDCD1/PD-1"
    },
    {
      "source": "TUMOR",
      "target": "HGNC:17635",
      "relationship": "UPREGULATES",
      "mechanism": "immune_evasion",
      "evidence": "Gene amplification at 9p24.1 common in tumors"
    },
    {
      "source": "TUMOR",
      "target": "HGNC:6059",
      "relationship": "UPREGULATES",
      "mechanism": "metabolic_immune_suppression",
      "evidence": "UniProt: Acts as a suppressor of anti-tumor immunity"
    },
    {
      "source": "TUMOR",
      "target": "HGNC:11766",
      "relationship": "SECRETES",
      "mechanism": "immunosuppression",
      "evidence": "TGF-beta1 inhibits immune cell function"
    },
    {
      "source": "TUMOR",
      "target": "HGNC:5962",
      "relationship": "SECRETES",
      "mechanism": "immunosuppression",
      "evidence": "IL-10 suppresses inflammatory responses"
    },
    {
      "source": "TUMOR",
      "target": "HGNC:12680",
      "relationship": "SECRETES",
      "mechanism": "angiogenesis_growth",
      "evidence": "VEGF-A promotes tumor vascularization and growth"
    }
  ]
}
```

---

## Literature References

### PubMed IDs for CD274/PD-L1
- PMID:32699939
- PMID:28409437
- PMID:28404915
- PMID:32671898
- PMID:32672060

### PubMed IDs for PDCD1/PD-1
- PMID:32084010
- PMID:25427199
- PMID:32202617
- PMID:25499323
- PMID:25510412

---

## ChEMBL Therapeutic Validation

### Checkpoint Inhibitors (Resolved via ChEMBL)

| Drug | ChEMBL ID | Max Phase | Mechanism | Key Synonyms |
|------|-----------|-----------|-----------|--------------|
| Pembrolizumab | CHEMBL:3137343 | 4 (Approved) | Anti-PD-1 mAb | Keytruda, MK-3475, Lambrolizumab |
| Nivolumab | CHEMBL:2108738 | 4 (Approved) | Anti-PD-1 mAb | Opdivo, BMS-936558, MDX-1106 |

**Pembrolizumab Indications** (sample): Melanoma, Non-Small Cell Lung Carcinoma, Renal Cell Carcinoma, Hodgkin Disease, Head and Neck Neoplasms, Breast Neoplasms, Colorectal Neoplasms, Hepatocellular Carcinoma, Gastric Adenocarcinoma, Esophageal Neoplasms, and 100+ additional oncology indications.

**Nivolumab Indications** (sample): Melanoma, Non-Small Cell Lung Carcinoma, Renal Cell Carcinoma, Hodgkin Disease, Urothelial Carcinoma, Colorectal Neoplasms, Hepatocellular Carcinoma, and similar broad oncology coverage.

---

## Clinical Implications

The immune checkpoint axis represents validated therapeutic targets:
- **Anti-PD-1**: Pembrolizumab (Keytruda), Nivolumab (Opdivo)
- **Anti-PD-L1**: Atezolizumab (Tecentriq), Durvalumab (Imfinzi)
- **Anti-CTLA-4**: Ipilimumab (Yervoy)
- **Anti-LAG-3**: Relatlimab (in combination therapy)
- **IDO1 inhibitors**: Epacadostat (clinical trials)

These findings confirm that tumor immune evasion is mediated by checkpoint upregulation (PD-L1, IDO1) and secretion of immunosuppressive factors (TGF-beta1, IL-10, VEGF-A), providing mechanistic basis for checkpoint blockade immunotherapy.
