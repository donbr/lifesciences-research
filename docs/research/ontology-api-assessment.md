# Ontology API Integration Assessment

**Date:** 2026-01-26
**Status:** Research Complete
**Decision:** Defer to Q2 2026 (after validation infrastructure)

---

## Executive Summary

This document assesses OLS (Ontology Lookup Service) and Monarch Initiative for potential MCP integration, contextualized within the platform's existing research priorities.

| API | Score | Unique Value | Integration Priority |
|-----|-------|--------------|---------------------|
| **Monarch Initiative** | **7/10** | Phenotype-gene associations (HPO), rare disease focus | Q2 2026 |
| **OLS** | **6.5/10** | Disease hierarchy traversal, 266 ontologies | Q2 2026 |

**Key Finding:** Neither API is mentioned in existing research documents as a priority gap. Current disease handling (Open Targets + MONDO) is functional for all existing competency questions.

---

## Consolidated Priority Ranking

Based on review of all 6 research documents in `docs/research/`, here is the platform's priority stack:

### Tier 1: Foundation (Jan-Feb 2026)

| Priority | Task | Source | Impact |
|----------|------|--------|--------|
| **1** | DrugMechDB Integration | benchmark-datasets-analysis.md | 4,583 curated drug-disease paths; foundational validation benchmark |
| **2** | Gene Ontology Keys | industry-standards-alignment.md | Missing from 22-key registry; blocks functional enrichment |
| **3** | TRAPI Deviation Docs | industry-standards-alignment.md | Clarifies 85% compliance with intentional simplifications |

### Tier 2: Validation Infrastructure (Mar-Apr 2026)

| Priority | Task | Source | Impact |
|----------|------|--------|--------|
| **4** | Multi-evaluator Scoring | prior-art-validation-patterns.md | GPT-4 + BERTScore + ROUGE; required for ANY new API validation |
| **5** | Graph Quality Metrics | validation-strategy-recommendations.md | Completeness ≥90%, Precision ≥95%, Coherence ≥80%, Provenance ≥95% |
| **6** | BioKGBench Adoption | benchmark-datasets-analysis.md | 698 KGQA + 1,385 SCV tasks for agent-based validation |

### Tier 3: CQ Expansion (Apr-May 2026)

| Priority | Task | Source | Impact |
|----------|------|--------|--------|
| **7** | Tier 3 CQ Implementation | competency-question-gaps.md | cq12-cq15 landscape questions under-represented |
| **8** | ChEMBL Mechanism API | just-in-time-graph-construction.md | Drug→Target edges not exposed via MCP |

### Tier 4: Strategic APIs (Q2 2026)

| Priority | Task | Source | Impact |
|----------|------|--------|--------|
| **9** | Monarch Initiative | this document | Phenotype-driven discovery (HPO) |
| **10** | OLS | this document | Hierarchical ontology reasoning |

---

## Why Monarch/OLS Are Deferred

### Current Disease Handling is Sufficient

| Capability | Current Solution | Gap? |
|------------|------------------|------|
| Gene-disease associations | Open Targets | No |
| MONDO ontology | Open Targets cross-references | No |
| Pathway analysis | WikiPathways | No |
| Phenotype mapping (HPO) | Not implemented | **Yes (future)** |
| Disease hierarchy | Not implemented | **Yes (future)** |

### No CQs Currently Blocked

All 15 existing competency questions can be executed with current servers:
- **Tier 1 (3 CQs)**: Simple lookups - fully supported
- **Tier 2 (9 CQs)**: Multi-hop queries - fully supported
- **Tier 3 (3 CQs)**: Landscape analysis - partially supported (need stress tests)

### Prerequisites for New API Integration

Before adding Monarch/OLS, the platform needs:

1. **Validation benchmarks** (DrugMechDB) - How do we measure if the new API improves accuracy?
2. **Quality metrics** (Completeness, Precision) - How do we compare before/after?
3. **Multi-evaluator scoring** - How do we validate LLM-generated answers?

---

## Monarch Initiative Research

### Unique Capabilities

1. **Phenotype-Driven Discovery (HPO)**
   - 16,000+ HPO terms integrated
   - 1.4M genotype-phenotype associations
   - Enables: "Patient has tremor + cognitive decline → which genes?"

2. **Rare Disease Expertise**
   - MONDO + Orphanet + OMIM harmonization
   - NORD/GARD integration
   - Cross-species evidence (mouse, fly, worm models)

3. **Biolink-Compatible Schema**
   - Native CURIE support (MONDO, HP, HGNC, ENSG)
   - Fits platform architecture

### API Details

| Aspect | Details |
|--------|---------|
| Base URL | `https://api-v3.monarchinitiative.org/v3` |
| Auth | None required |
| Documentation | https://api-v3.monarchinitiative.org/v3/docs |
| Response | JSON, Biolink-compatible |

### Key Endpoints

```bash
# Search diseases
curl "https://api-v3.monarchinitiative.org/v3/api/search/entities?q=alzheimer&entity_type=disease&limit=5"

# Get disease-gene associations
curl "https://api-v3.monarchinitiative.org/v3/api/entity/MONDO:0004975/biolink:DiseaseToGeneAssociation"

# Get phenotypes for disease
curl "https://api-v3.monarchinitiative.org/v3/api/entity/MONDO:0004975/biolink:DiseaseToPhenotypicFeatureAssociation"

# Phenotype-to-gene (UNIQUE capability)
curl "https://api-v3.monarchinitiative.org/v3/api/entity/HP:0001337/biolink:PhenotypicFeatureToGeneAssociation"
```

### Proposed MCP Tools

```python
@mcp.tool()
async def search_entities(query: str, entity_type: Optional[str] = None, limit: int = 50):
    """Fuzzy search diseases, genes, phenotypes"""

@mcp.tool()
async def get_entity(entity_id: str, slim: bool = False):
    """Retrieve entity details by CURIE"""

@mcp.tool()
async def get_associations(entity_id: str, association_type: str, limit: int = 50):
    """Query associations (disease-gene, gene-phenotype, etc.)"""

@mcp.tool()
async def get_phenotype_genes(hp_id: str, limit: int = 50):
    """Get genes associated with phenotype (enables phenotype-driven discovery)"""
```

### CQs Enhanced by Monarch

| Existing CQ | Enhancement |
|-------------|-------------|
| CQ3 (AD networks) | Add HPO phenotype context |
| CQ7 (NGLY1 repurposing) | Phenotype-to-gene mapping |
| CQ10 (Huntington's) | Phenotype-based target prioritization |
| CQ14 (TP53 SL) | Cross-species SL validation |

**New CQs Enabled:**
- CQ16: Phenotype-driven diagnosis
- CQ17: Rare disease patient matching
- CQ18: Cross-species model selection

---

## OLS Research

### Unique Capabilities

1. **Unified Ontology Access**
   - 266 ontologies, 8.6M+ classes
   - Single endpoint for MONDO, HPO, GO, DOID, OMIM

2. **Hierarchical Reasoning**
   - Neo4j backend for ancestor/descendant queries
   - Enables: "All subtypes of Alzheimer's disease"

3. **Disease Harmonization**
   - Bridges MONDO ↔ OMIM ↔ Orphanet ↔ DOID
   - Precise semantic mappings

### API Details

| Aspect | Details |
|--------|---------|
| Base URL | `https://www.ebi.ac.uk/ols4/api/` |
| Auth | None required |
| Documentation | https://www.ebi.ac.uk/ols4/api/ |
| Coverage | 266 ontologies, 8.6M classes |

### Key Endpoints

```bash
# Get disease term
curl "https://www.ebi.ac.uk/ols4/api/terms?short_form=MONDO:0007606"

# Get all ancestors (disease hierarchy)
curl "https://www.ebi.ac.uk/ols4/api/ontologies/mondo/ancestors?id=MONDO:0004975"

# Get all descendants (disease subtypes)
curl "https://www.ebi.ac.uk/ols4/api/ontologies/mondo/descendants?id=MONDO:0005559"

# Cross-ontology search
curl "https://www.ebi.ac.uk/ols4/api/search?q=Alzheimer&ontology=mondo&size=20"
```

### Proposed MCP Tools

```python
@mcp.tool()
async def search_ontologies(query: str):
    """Fuzzy search across 266 ontologies"""

@mcp.tool()
async def search_terms(query: str, ontology: str):
    """Search terms within a specific ontology"""

@mcp.tool()
async def get_term(ontology: str, term_id: str):
    """Resolve term by short form (MONDO:0007606)"""

@mcp.tool()
async def get_ancestors(ontology: str, term_id: str):
    """Retrieve all parent terms (hierarchical)"""

@mcp.tool()
async def get_descendants(ontology: str, term_id: str):
    """Retrieve all child terms"""
```

### Token Budget Risk

**Warning**: Large hierarchies can return 1000+ items
- Example: "All descendants of cancer" = very large response
- **Mitigation**: Implement `limit` parameter, use `slim=True`

---

## Comparison: Monarch vs. Open Targets

| Feature | Monarch | Open Targets |
|---------|---------|--------------|
| Disease-gene associations | 78,000+ | 50,000+ |
| Evidence scoring | No | 1-10 scale |
| Phenotype integration | Primary focus | Minimal |
| Rare disease focus | Yes | No |
| Tractability assessment | No | Yes |
| Druggability ranking | No | Yes |

**Verdict**: Complementary, not redundant. Use Monarch for phenotype discovery, Open Targets for drug prioritization.

---

## Pros & Cons Summary

### Monarch Initiative

| Pros | Cons |
|------|------|
| Unique HPO phenotype capabilities | 50-60% overlap with Open Targets |
| Rare disease expertise | No evidence scoring |
| No auth required | No druggability data |
| Biolink-compatible | Large association lists |
| Enables 3 new CQs | |

### OLS

| Pros | Cons |
|------|------|
| 266 ontologies, single endpoint | Only ~20 ontologies relevant |
| Hierarchical reasoning | Token budget risk (large hierarchies) |
| No auth required | No drug/gene connections |
| Peer-reviewed (Bioinformatics 2025) | Requires custom model (~200 LOC) |
| ELIXIR infrastructure | |

---

## Implementation Roadmap

| Phase | Timeline | Scope | Status |
|-------|----------|-------|--------|
| **Phase 1** | Jan-Feb 2026 | DrugMechDB + GO keys + TRAPI docs | **PRIORITY** |
| **Phase 2** | Mar-Apr 2026 | Multi-evaluator scoring + Quality metrics | **PRIORITY** |
| **Phase 3** | Apr-May 2026 | Tier 3 CQs (cq12-cq15) | Strategic |
| **Phase 4** | Q2 2026 | Monarch + OLS integration | Deferred |

---

## References

### Monarch Initiative
- API Documentation: https://api-v3.monarchinitiative.org/v3/docs
- NAR Publication (2024): "The Monarch Initiative in 2024"
- GitHub: https://github.com/monarch-initiative/monarch-app

### OLS
- API Documentation: https://www.ebi.ac.uk/ols4/api/
- Bioinformatics Publication (May 2025)
- GitHub: https://github.com/EBISPOT/ols4

### Existing Research Documents
- `docs/research/benchmark-datasets-analysis.md`
- `docs/research/prior-art-validation-patterns.md`
- `docs/research/competency-question-gaps.md`
- `docs/research/industry-standards-alignment.md`
- `docs/research/validation-strategy-recommendations.md`
- `docs/research/just-in-time-graph-construction.md`
