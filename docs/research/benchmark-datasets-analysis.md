# Benchmark Datasets Analysis for Life Sciences Knowledge Graph Validation

**Purpose**: Research and document industry benchmark datasets used to validate biomedical knowledge graph systems.

**Created**: 2026-01-24
**Status**: Complete

---

## Executive Summary

This document catalogs benchmark datasets available for validating biomedical knowledge graph systems. We identify 15+ datasets across three categories:

1. **Drug Mechanism Benchmarks** - Ground truth for drug-disease pathways
2. **Biomedical QA Benchmarks** - Question-answer pairs for evaluation
3. **Knowledge Graph Benchmarks** - Large-scale KGs for link prediction

**Primary Recommendation**: Integrate DrugMechDB for mechanism validation (aligns with cq1-cq2) and BioKGBench for agent-based KG validation (aligns with Fuzzy-to-Fact protocol).

---

## Benchmark Inventory

### Summary Table

| Benchmark | Source | Question/Entry Count | Access Method | Primary Use Case |
|-----------|--------|---------------------|---------------|------------------|
| **DrugMechDB** | Su Lab (UCSD) | 4,583 drug-disease pairs | GitHub YAML/JSON | Drug mechanism validation |
| **BioASQ-QA** | EU Challenge | ~3,700 questions | Registration required | Biomedical QA evaluation |
| **PubMedQA** | Duke/CMU | 273,500 total (1k expert) | GitHub | Yes/No/Maybe research QA |
| **BioKGBench** | Westlake AutoLab | 698 KGQA + 1,385 SCV | GitHub (MIT) | Agent-based KG validation |
| **Hetionet** | UPenn | 47,031 nodes | Neo4j server | Drug repurposing baselines |
| **PrimeKG** | Harvard/Zitnik Lab | 129,375 nodes | Harvard Dataverse | Precision medicine |
| **DRKG** | AWS/DGL | 97,238 entities | GitHub | COVID-19 drug repurposing |
| **PharmKG** | MindRank/SYSU | ~8,000 entities | Zenodo | KG embedding benchmarks |
| **TRAPI Test Suite** | NCATS Translator | Dynamic | GitHub | Protocol compliance |

---

## Detailed Benchmark Analysis

### 1. DrugMechDB

**Source**: [github.com/SuLab/DrugMechDB](https://github.com/SuLab/DrugMechDB)
**Publication**: Gonzalez-Cavazos et al., *Scientific Data* 10:632 (2023)

#### Overview

DrugMechDB is a curated database capturing mechanistic paths from drugs to diseases. Unlike simple target-disease pairs, it represents complete biological pathways using the Biolink Model.

#### Statistics

| Metric | Value |
|--------|-------|
| Drug-disease pairs | 4,583 |
| Unique drugs | 1,580 |
| Unique diseases | 744 |
| Total relationships | 32,249 |
| Biological scales | 14 types |
| Unique path types | 297 |
| Most common sequence | Drug-Protein-BiologicalProcess-Disease (12.27%) |

#### Entity Distribution

| Concept Type | Percentage |
|--------------|------------|
| BiologicalProcess | 24.55% |
| Protein | 21.53% |
| Drug | (anchor nodes) |
| Disease | (terminal nodes) |

#### Data Format

```yaml
# Example from indication_paths.yaml
- drug: Palovarotene
  drug_mesh: D000077268
  disease: Fibrodysplasia ossificans progressiva
  disease_mesh: D009221
  drugbank: DB12490
  nodes:
    - id: DrugBank:DB12490
      label: Palovarotene
      type: Drug
    - id: UniProt:P13631
      label: RARG
      type: Protein
  links:
    - source: DrugBank:DB12490
      target: UniProt:P13631
      key: agonist
```

#### Access Methods

| Method | URL |
|--------|-----|
| Web Interface | https://sulab.github.io/DrugMechDB/ |
| YAML Data | `indication_paths.yaml` in repository |
| JSON Data | `indication_paths.json` in repository |
| RDF/Semantic Web | `dmdb_void.ttl` |
| Grouped Data | `dmdb_indications_grouped.zip` |

#### Alignment with CQ Framework

| CQ | Alignment | Notes |
|----|-----------|-------|
| cq1 | **High** | FOP mechanism matches DrugMechDB path format |
| cq2 | **High** | Drug repurposing via pathway expansion |
| cq9 | **Medium** | Drug safety could extend mechanism paths |

#### Validation Methodology

DrugMechDB uses bootstrapping analysis comparing against MechRepoNet:
- 28.71% overlap of unique associations
- p-value < 0.001 for top association types
- Expert curation from DrugBank, Wikipedia, literature

---

### 2. BioASQ

**Source**: [bioasq.org](http://bioasq.org/)
**Challenge**: Annual since 2013 (13th edition in 2025)

#### Overview

BioASQ is a challenge on biomedical semantic indexing and question answering, featuring expert-constructed questions in multiple formats.

#### Question Types

| Type | Description | Answer Format |
|------|-------------|---------------|
| **Factoid** | Single entity answer | Named entity (e.g., "BRCA1") |
| **List** | Multiple entity answer | List of entities |
| **Yes/No** | Binary decision | "yes" or "no" |
| **Summary** | Explanation required | Free-text paragraph |

#### Dataset Scale

| Component | Count |
|-----------|-------|
| Total questions | ~3,700 (through 2024) |
| Annual new questions | ~500 test instances |
| Reference articles | Per-question relevant PMIDs |
| Gold snippets | Text spans from articles |
| RDF triples | Structured evidence |

#### Data Structure (JSON)

```json
{
  "body": "Which genes are implicated in Alzheimer's disease?",
  "type": "list",
  "documents": ["http://www.ncbi.nlm.nih.gov/pubmed/12345"],
  "snippets": [{"text": "APP, PSEN1, and PSEN2 mutations..."}],
  "concepts": ["http://www.disease-ontology.org/..."],
  "ideal_answer": "APP, PSEN1, PSEN2, and APOE are implicated...",
  "exact_answer": [["APP"], ["PSEN1"], ["PSEN2"], ["APOE"]]
}
```

#### Evaluation Metrics

| Task | Metrics |
|------|---------|
| Document Retrieval | MAP, GMAP, Precision |
| Snippet Retrieval | MRR, Precision |
| Exact Answer | Accuracy, F1, MRR (factoid), F1 (list) |
| Ideal Answer | ROUGE-2, ROUGE-SU4, Manual evaluation |

#### Access

- **Registration**: https://participants-area.bioasq.org/
- **License**: CC BY 2.5
- **Format**: JSON with articles, snippets, and answers

#### Alignment with CQ Framework

| CQ | Alignment | Notes |
|----|-----------|-------|
| cq3 | **High** | AD gene questions match BioASQ style |
| cq4 | **High** | AD therapeutics as list questions |
| cq12 | **Medium** | Health emergencies as summary questions |

---

### 3. PubMedQA

**Source**: [pubmedqa.github.io](https://pubmedqa.github.io/)
**Publication**: Jin et al., EMNLP 2019

#### Overview

PubMedQA tests whether research questions can be answered with Yes/No/Maybe from abstracts. It requires reasoning over quantitative biomedical content.

#### Dataset Components

| Component | Count | Description |
|-----------|-------|-------------|
| Expert-labeled | 1,000 | Gold standard with expert annotations |
| Unlabeled | 61,200 | For semi-supervised learning |
| Artificial | 211,300 | Programmatically generated |
| **Total** | 273,500 | All QA pairs |

#### Example

```
Question: Do preoperative statins reduce atrial fibrillation
          after coronary artery bypass grafting?

Context: [Abstract without conclusion]

Long Answer: [Conclusion paragraph]

Answer: yes/no/maybe
```

#### Leaderboard (2024)

| Model | Accuracy |
|-------|----------|
| GPT-4 (Medprompt) | 82.0% |
| Med-PaLM 2 | 81.8% |
| MEDITRON (70B) | 81.6% |
| Claude 3 | 79.7% |
| Human Performance | 78.0% |

#### Access

- **GitHub**: https://github.com/pubmedqa/pubmedqa
- **License**: Open
- **Format**: JSON with question, context, answer

---

### 4. BioKGBench

**Source**: [github.com/westlake-autolab/BioKGBench](https://arxiv.org/html/2407.00466v1)
**Focus**: Agent-based knowledge graph validation

#### Overview

BioKGBench evaluates AI agents from a "scientist's perspective" - testing tool usage and structured knowledge access rather than raw LLM capabilities.

#### Task Structure

| Task | Description | Size |
|------|-------------|------|
| **KGQA** | Knowledge Graph QA | 698 questions (60 dev, 638 test) |
| **SCV** | Scientific Claim Verification | 1,385 claims (120 dev, 1,265 test) |
| **KGCheck** | Combined fact-checking | 225 instances (20 dev, 205 test) |

#### Clinical Knowledge Graph

| Component | Count |
|-----------|-------|
| Entities | 484,955 (12 types) |
| Relationships | 18,959,943 (18 types) |
| External resources | 5,664 abstracts + 51 papers |

Entity types include: proteins, genes, diseases, pathways, tissues, drugs.

#### Evaluation Metrics

| Task | Metrics |
|------|---------|
| KGQA | F1 score, executability rate |
| SCV | Accuracy, quote alignment, error rate |
| KGCheck | Exact match accuracy, tool selection |

#### Access

- **GitHub**: MIT License
- **Format**: JSON + Neo4j knowledge graph

#### Alignment with CQ Framework

| CQ | Alignment | Notes |
|----|-----------|-------|
| cq8 | **High** | Synthetic lethality via KG traversal |
| cq11 | **High** | p53-MDM2 pathway verification |
| All | **High** | Fuzzy-to-Fact maps to KGQA |

---

### 5. NCATS Translator TRAPI

**Source**: [github.com/NCATSTranslator](https://github.com/NCATSTranslator/ReasonerAPI)
**Focus**: Protocol compliance and semantic validation

#### Overview

TRAPI (Translator Reasoner API) is a standard HTTP API for biomedical question-answering. The test suite validates compliance with TRAPI schema and Biolink Model.

#### Validation Components

| Validator | Purpose |
|-----------|---------|
| **reasoner-validator** | TRAPI schema + Biolink semantic validation |
| **graph-validation-test-runners** | One-hop query testing |
| **SRI_testing** | Full component integration testing |

#### Test Types

| Test | Description |
|------|-------------|
| **StandardsValidationTest** | TRAPI compliance + Biolink semantics |
| **OneHopTest** | Single-hop edge recovery validation |
| **Provenance** | Source CURIE verification |

#### TRAPI Message Structure

```json
{
  "message": {
    "query_graph": {
      "nodes": {"n0": {"categories": ["biolink:Gene"]}},
      "edges": {"e0": {"subject": "n0", "predicates": ["biolink:related_to"]}}
    },
    "knowledge_graph": {
      "nodes": {"HGNC:1100": {"name": "BRCA1", "categories": ["biolink:Gene"]}}
    },
    "results": [{"node_bindings": {"n0": [{"id": "HGNC:1100"}]}}]
  }
}
```

#### Access

- **Validator PyPI**: `pip install reasoner-validator`
- **Test Runners**: `pip install graph-validation-test-runners`
- **Web Service**: https://sri-testing.apps.renci.org

#### Alignment with CQ Framework

| CQ | Alignment | Notes |
|----|-----------|-------|
| All | **High** | TRAPI query format matches MCP tool patterns |
| cq1 | **High** | One-hop queries for mechanism validation |

---

### 6. Hetionet

**Source**: [github.com/hetio/hetionet](https://github.com/hetio/hetionet)
**Publication**: Himmelstein et al., eLife 2017

#### Overview

Hetionet integrates 29 public resources into a biomedical knowledge graph optimized for drug repurposing via link prediction.

#### Statistics

| Metric | Value |
|--------|-------|
| Nodes | 47,031 |
| Edges | 2,250,197 |
| Node types | 11 |
| Edge types | 29 |
| Data sources | 29 |

#### Benchmark Results (Drug Repurposing)

| Method | MRR | Hits@10 |
|--------|-----|---------|
| REx | 0.427 | - |
| DREAMwalk | - | 0.876 accuracy |
| ComplEx | - | 0.646 accuracy |

#### Access

- **Neo4j Server**: Public read-only
- **TSV Files**: GitHub release
- **Format**: NetworkX-compatible

---

### 7. PrimeKG

**Source**: [zitniklab.hms.harvard.edu/projects/PrimeKG](https://zitniklab.hms.harvard.edu/projects/PrimeKG/)
**Publication**: Chandak et al., *Scientific Data* 2023

#### Overview

Precision Medicine Knowledge Graph integrating 20 resources for disease-centric analyses.

#### Statistics

| Metric | Value |
|--------|-------|
| Nodes | ~129,375 |
| Edges | ~8,100,498 |
| Diseases | 17,080 |
| Relationships | 4,050,249 |
| Edge types | 29 |
| Data sources | 20 |

#### Data Sources

MONDO, OMIM, HPO, NCBI Gene, Bgee, DrugBank, DrugCentral, SIDER, Reactome, DisGeNET, UBERON, UMLS, Gene Ontology, CTD, and more.

#### Access Methods

| Method | Command/URL |
|--------|-------------|
| Therapeutics Data Commons | Python API |
| PyKEEN | Native integration |
| Harvard Dataverse | https://doi.org/10.7910/DVN/IXA7BM |
| Direct download | `wget -O kg.csv https://dataverse.harvard.edu/api/access/datafile/6180620` |

---

### 8. DRKG (Drug Repurposing Knowledge Graph)

**Source**: [github.com/gnn4dr/DRKG](https://github.com/gnn4dr/DRKG)
**Focus**: COVID-19 and general drug repurposing

#### Statistics

| Metric | Value |
|--------|-------|
| Entities | 97,238 |
| Triplets | 5,874,261 |
| Entity types | 13 |
| Edge types | 107 |
| Entity pair types | 17 |

#### Entity Composition

| Type | Count |
|------|-------|
| Compounds | 24,313 |
| Genes | 39,220 |
| Diseases | 5,103 |
| Side effects | 5,701 |
| Pathways | 1,822 |
| Biological processes | 11,381 |

#### Data Sources

DrugBank (19,911), Hetionet (45,279), GNBR (44,033), STRING (18,316), IntAct (16,474), DGIdb (8,899).

#### Access

- **Download**: GitHub compressed archive
- **Embeddings**: Pre-trained TransE (400-dim)
- **Format**: Triplet TSV files

---

### 9. PharmKG

**Source**: [github.com/MindRank-Biotech/PharmKG](https://github.com/MindRank-Biotech/PharmKG)
**Publication**: Zheng et al., *Briefings in Bioinformatics* 2021

#### Statistics (PharmKG-8K)

| Metric | Value |
|--------|-------|
| Entities | ~8,000 |
| Triplets | 500,000+ |
| Relation types | 29 |
| Training set | 400,788 |
| Test set | 49,536 |

#### Entity Types

| Type | Count |
|------|-------|
| Genes | 4,758 |
| Chemicals/Drugs | 1,497 |
| Diseases | 1,346 |

#### Benchmark Results

| Model | MRR | Hits@1 |
|-------|-----|--------|
| HRGAT | 0.154 | 0.075 |
| TransE | - | baseline |

#### Access

- **Raw Data**: Zenodo
- **Framework**: PyKEEN compatible

---

## Additional Biomedical QA Datasets

### Comprehensive List

| Dataset | Size | Type | Access |
|---------|------|------|--------|
| **MedQA** | 61k | Multi-choice (board exams) | GitHub |
| **MedMCQA** | 194k | Multi-choice (Indian exams) | MLR |
| **CliCR** | 100k | MRC (BMJ Case Reports) | GitHub |
| **emrQA** | 455k | MRC (clinical notes) | GitHub |
| **MEDHOP** | 2.5k | Multi-hop reasoning | UCL |
| **BioRead** | 16.4M | Cloze-style | AUEB |
| **PathVQA** | 32.8k | Visual QA (pathology) | UCSD |
| **TREC Genomics** | 64 | IR (full-text) | NIST |
| **COVID-QA** | 2k | MRC (COVID-19) | Deepset |

---

## Recommendations for CQ Framework Integration

### Tier 1: Immediate Integration

| Benchmark | CQ Alignment | Integration Approach |
|-----------|--------------|---------------------|
| **DrugMechDB** | cq1, cq2, cq9 | Import YAML paths as gold standard |
| **BioKGBench** | All (agent focus) | Adopt KGQA evaluation metrics |
| **TRAPI** | All (protocol) | Use reasoner-validator for output |

### Tier 2: Evaluation Baselines

| Benchmark | CQ Alignment | Integration Approach |
|-----------|--------------|---------------------|
| **PubMedQA** | cq3, cq4 | Yes/No questions for research claims |
| **BioASQ** | cq3, cq4, cq12 | Factoid/List questions as test cases |

### Tier 3: Knowledge Graph Baselines

| Benchmark | Use Case |
|-----------|----------|
| **PrimeKG** | Precision medicine coverage comparison |
| **Hetionet** | Drug repurposing method benchmarking |
| **DRKG** | Entity resolution validation |

### Implementation Actions

1. **DrugMechDB Integration**
   - Download `indication_paths.yaml`
   - Map to Biolink predicates used in CQ framework
   - Create validation script comparing CQ outputs to gold paths

2. **BioKGBench Adoption**
   - Fork repository for local testing
   - Adapt KGQA tasks to MCP tool patterns
   - Use F1 metrics for search accuracy

3. **TRAPI Compliance**
   - Install `reasoner-validator`
   - Validate MCP tool outputs against Biolink Model
   - Add CI/CD step for schema compliance

---

## References

### Drug Mechanism Benchmarks
- Gonzalez-Cavazos et al. (2023). [DrugMechDB: A Curated Database of Drug Mechanisms](https://www.nature.com/articles/s41597-023-02534-z). *Scientific Data*.

### Biomedical QA Benchmarks
- Krithara et al. (2023). [BioASQ-QA: A manually curated corpus for Biomedical Question Answering](https://www.nature.com/articles/s41597-023-02068-4). *Scientific Data*.
- Jin et al. (2019). [PubMedQA: A Dataset for Biomedical Research Question Answering](https://aclanthology.org/D19-1259/). EMNLP.

### Agent-Based Benchmarks
- Tian et al. (2024). [BioKGBench: A Knowledge Graph Checking Benchmark of AI Agent for Biomedical Science](https://arxiv.org/html/2407.00466v1). arXiv.

### Knowledge Graph Benchmarks
- Chandak et al. (2023). [Building a knowledge graph to enable precision medicine](https://www.nature.com/articles/s41597-023-01960-3). *Scientific Data*.
- Himmelstein et al. (2017). [Systematic integration of biomedical knowledge prioritizes drugs for repurposing](https://elifesciences.org/articles/26726). eLife.
- Zheng et al. (2021). [PharmKG: a dedicated knowledge graph benchmark for biomedical data mining](https://academic.oup.com/bib/article/22/4/bbaa344/6042240). *Briefings in Bioinformatics*.

### Protocol Standards
- NCATS Translator. [Translator Reasoner API (TRAPI)](https://github.com/NCATSTranslator/ReasonerAPI). GitHub.
- TranslatorSRI. [Graph Validation Test Runners](https://github.com/TranslatorSRI/graph-validation-test-runners). GitHub.

### Curated Dataset Collections
- [Biomedical Question Answering Datasets](https://github.com/Andy-jqa/biomedical-qa-datasets). GitHub.
- [DRKG: Drug Repurposing Knowledge Graph](https://github.com/gnn4dr/DRKG). GitHub.
