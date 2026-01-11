# Scenario 3: Huntington's Disease Novel Targets

**Question**: What novel therapeutic targets exist for Huntington's Disease that are not covered by current Phase 3 interventions?

**Validation Date**: 2025-01-10

---

## Phase 1: Anchor Node (HTT Gene)

### Gene Resolution
```
Tool: hgnc_get_gene("HGNC:4851")
```

| Field | Value |
|-------|-------|
| **CURIE** | HGNC:4851 |
| **Symbol** | HTT |
| **Name** | huntingtin |
| **Location** | 4p16.3 |
| **Aliases** | IT15, HD |
| **UniProt** | P42858 |
| **Ensembl** | ENSG00000197386 |
| **OMIM** | 613004 |
| **Orphanet** | ORPHA:122387 |

---

## Phase 2: Expand Edges (HTT Interactome)

### STRING Interactions (score > 0.98)
```
Tool: string_get_interactions("STRING:9606.ENSP00000347184", required_score=700)
```

| Interactor | Score | Function | Target Status |
|------------|-------|----------|---------------|
| **HAP1** | 0.999 | Huntingtin-associated protein 1 | Novel |
| **TP53** | 0.998 | Tumor suppressor | Established (cancer) |
| **CREBBP** | 0.997 | CREB binding protein, transcription | Novel for HD |
| **ITPR1** | 0.995 | IP3 receptor, calcium signaling | Novel |
| **TAF4** | 0.994 | TATA-box binding protein factor | Novel |
| **REST** | 0.991 | RE1 silencing TF, neuronal genes | Novel |
| **SNCA** | 0.989 | Alpha-synuclein (PD link) | Established (PD) |
| **AP2A2** | 0.989 | Endocytosis adaptor | Novel |
| **PRPF40A** | 0.989 | Pre-mRNA processing | Novel |
| **HYPK** | 0.986 | Huntingtin interacting protein K | Novel |
| **HIP1** | 0.985 | Huntingtin interacting protein 1 | Novel |

### Network Visualization
![HTT Network](https://string-db.org/api/highres_image/network?identifiers=9606.ENSP00000347184&species=9606&add_nodes=15)

---

## Phase 3: Current Drug Landscape (VMAT2 Inhibitors)

### Approved HD Drugs
```
Tools: chembl_get_compound()
```

| Drug | CHEMBL | Max Phase | Target | Indication |
|------|--------|-----------|--------|------------|
| **Tetrabenazine** | CHEMBL:117785 | 4 (Approved) | VMAT2 | HD Chorea |
| **Valbenazine** | CHEMBL:2364639 | 4 (Approved) | VMAT2 | Movement Disorders |
| **Deutetrabenazine** | CHEMBL:3137326 | 4 (Approved) | VMAT2 | HD Chorea |

### Investigational Drugs
| Drug | CHEMBL | Max Phase | Target | Mechanism |
|------|--------|-----------|--------|-----------|
| **Pridopidine** | CHEMBL:596802 | 3 | Sigma-1R | Neuroprotection |

### VMAT2 Target Details
```
Tool: iuphar_get_target("IUPHAR:1012")
```

| Field | Value |
|-------|-------|
| **CURIE** | IUPHAR:1012 |
| **Name** | Vesicular monoamine transporter 2 |
| **Gene** | SLC18A2 |
| **ChEMBL Target** | CHEMBL:1893 |
| **Ensembl** | ENSG00000165646 |

---

## Phase 4: Disease Associations (Open Targets)

```
Tool: opentargets_get_associations("ENSG00000197386")
```

| Disease | MONDO/EFO | Score | Evidence |
|---------|-----------|-------|----------|
| Huntington disease | MONDO_0007739 | 0.708 | Primary |
| Lopes-Maciel-Rodan syndrome | EFO_0009904 | 0.652 | Rare variant |
| Neurodegenerative disease | EFO_0005772 | 0.507 | Class |
| Major depressive disorder | MONDO_0002009 | 0.427 | Comorbidity |
| Juvenile Huntington disease | MONDO_0016621 | 0.383 | Variant |

---

## Phase 5: Pathway Context (ERK Pathway in HD)

### WikiPathways HD Pathways
```
Tool: wikipathways_search_pathways("Huntington")
```

| Pathway | ID | Genes | Description |
|---------|-----|-------|-------------|
| **ERK pathway in HD** | WP:WP3853 | 17 | MAPK/ERK signaling in neurodegeneration |
| **Omega-3 PUFA in HD** | WP:WP5470 | - | Nutritional intervention pathway |

### WP3853 Key Pathway Members
```
Tool: wikipathways_get_pathway("WP:WP3853")
```

**Signaling Cascade**:
- EGFR → RAF1 → MAP2K1/2 → MAPK1/3 (ERK1/2)
- NTRK2 (TrkB) → BDNF signaling
- ELK1, CREB1 → Transcriptional outputs

**Genes**: HTT, BDNF, NTRK2, EGFR, RAF1, MAP2K1, MAP2K2, MAPK1, MAPK3, ELK1, CREB1, CASP3, CASP7, EGF, GRM1, RPS6KA5

---

## Novel Target Opportunities (Gap Analysis)

Based on STRING interactome vs. current drug coverage:

| Novel Target | Function | Druggability | Rationale |
|--------------|----------|--------------|-----------|
| **REST** | RE1-silencing TF | Transcription factor | Regulates neuronal gene expression in HD |
| **CREBBP** | Histone acetyltransferase | HDAC modulation | Epigenetic regulation disrupted in HD |
| **ITPR1** | IP3 receptor | Ion channel | Calcium dysregulation in HD neurons |
| **HAP1** | HTT-associated protein | Protein-protein | Direct HTT interactor, vesicle transport |
| **BDNF/NTRK2** | Neurotrophic signaling | Receptor kinase | Neuroprotection pathway |

### Currently Covered Mechanism
- **VMAT2 inhibition**: Tetrabenazine, Valbenazine, Deutetrabenazine (symptomatic chorea)
- **Sigma-1R agonism**: Pridopidine (neuroprotection, Phase 3)

### Uncovered Mechanisms
1. **Epigenetic modulation** (CREBBP pathway)
2. **Calcium homeostasis** (ITPR1)
3. **Neurotrophin signaling** (BDNF/TrkB)
4. **Transcriptional regulation** (REST)
5. **Vesicle trafficking** (HAP1, HIP1)

---

## Knowledge Graph Structure (BioLink)

```json
{
  "nodes": [
    {"id": "HGNC:4851", "name": "HTT", "type": "biolink:Gene"},
    {"id": "UniProtKB:P42858", "name": "Huntingtin", "type": "biolink:Protein"},
    {"id": "MONDO:0007739", "name": "Huntington disease", "type": "biolink:Disease"},
    {"id": "CHEMBL:117785", "name": "Tetrabenazine", "type": "biolink:SmallMolecule"},
    {"id": "CHEMBL:2364639", "name": "Valbenazine", "type": "biolink:SmallMolecule"},
    {"id": "CHEMBL:596802", "name": "Pridopidine", "type": "biolink:SmallMolecule"},
    {"id": "IUPHAR:1012", "name": "VMAT2", "type": "biolink:Protein"},
    {"id": "WP:WP3853", "name": "ERK pathway in HD", "type": "biolink:Pathway"},
    {"id": "HGNC:9936", "name": "REST", "type": "biolink:Gene"},
    {"id": "HGNC:2348", "name": "CREBBP", "type": "biolink:Gene"},
    {"id": "HGNC:6180", "name": "ITPR1", "type": "biolink:Gene"}
  ],
  "edges": [
    {"source": "HGNC:4851", "target": "MONDO:0007739", "type": "biolink:causes"},
    {"source": "CHEMBL:117785", "target": "IUPHAR:1012", "type": "biolink:inhibits"},
    {"source": "CHEMBL:2364639", "target": "IUPHAR:1012", "type": "biolink:inhibits"},
    {"source": "HGNC:4851", "target": "HGNC:9936", "type": "biolink:interacts_with"},
    {"source": "HGNC:4851", "target": "HGNC:2348", "type": "biolink:interacts_with"},
    {"source": "HGNC:4851", "target": "HGNC:6180", "type": "biolink:interacts_with"},
    {"source": "HGNC:4851", "target": "WP:WP3853", "type": "biolink:participates_in"}
  ]
}
```

---

## Summary

**Validated Finding**: Current HD therapeutics focus on **VMAT2 inhibition** for symptomatic chorea treatment. Novel target opportunities exist in:
1. **REST** - Transcriptional dysregulation
2. **CREBBP** - Epigenetic mechanisms
3. **ITPR1** - Calcium signaling
4. **BDNF/NTRK2** - Neuroprotection

**MCP Tools Used**:
- `hgnc_get_gene` - Gene resolution
- `string_get_interactions` - Protein interactome
- `chembl_get_compound` - Drug information
- `iuphar_get_target` - Pharmacological target
- `opentargets_get_associations` - Disease associations
- `wikipathways_get_pathway` - Pathway context
