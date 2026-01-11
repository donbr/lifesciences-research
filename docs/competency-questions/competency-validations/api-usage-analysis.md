# API Usage Analysis: Rate Limits and Query Optimization

**Analysis Date**: 2025-01-10

---

## API Rate Limits by Provider

All clients implement `_rate_limited_get` with built-in throttling. Here's the documented limit for each:

| API | Rate Limit | Limit Type | Our Implementation |
|-----|------------|------------|-------------------|
| **NCBI/Entrez** | 3 req/s (no key) / 10 req/s (with key) | Per-IP | `rate_limit_delay = 0.333s` or `0.1s` |
| **PubChem** | 5 req/s / 400 req/min | Per-IP | Built-in delay |
| **BioGRID** | 2 req/s | Per-IP | `_rate_limit_lock` with 0.5s delay |
| **STRING** | ~10 req/s | Per-IP (soft) | Built-in delay |
| **WikiPathways** | 10 req/s | Per-IP | `_enforce_rate_limit` |
| **ChEMBL** | No explicit limit | Fair use | SDK handles throttling |
| **Open Targets** | No explicit limit | Fair use | GraphQL batching |
| **HGNC** | No explicit limit | Fair use | Built-in delay |
| **UniProt** | 200 req/s | Per-IP | Built-in delay |
| **Ensembl** | 15 req/s / 55,000/day | Per-IP | Built-in delay |
| **ClinicalTrials** | Reasonable use | Cloudflare protected | Built-in delay |
| **IUPHAR/GtoPdb** | No explicit limit | Fair use | Built-in delay with retry |

---

## Estimated API Calls This Session

### By Scenario

| Scenario | HGNC | STRING | ChEMBL | WikiPathways | ClinicalTrials | OpenTargets | Total |
|----------|------|--------|--------|--------------|----------------|-------------|-------|
| CQ-3 (Alzheimer's) | 4 | 1 | 0 | 2 | 0 | 1 | 8 |
| CQ-4 (AD Therapeutics) | 1 | 0 | 4 | 0 | 1 | 0 | 6 |
| CQ-5 (MAPK) | 3 | 1 | 0 | 1 | 0 | 0 | 5 |
| CQ-6 (BRCA1) | 1 | 1 | 0 | 0 | 0 | 0 | 2 |
| CQ-7 (NGLY1) | 1 | 1 | 0 | 2 | 1 | 0 | 5 |
| Scenario 3 (Huntington) | 3 | 2 | 4 | 2 | 1 | 1 | 13 |
| Scenario 4 (p53-MDM2) | 2 | 2 | 2 | 1 | 0 | 0 | 7 |
| Scenario 5 (Emergencies) | 0 | 0 | 0 | 0 | 7 | 0 | 7 |
| Scenario 6 (Commercial) | 0 | 0 | 4 | 0 | 6 | 0 | 10 |
| **Total** | **15** | **8** | **14** | **8** | **16** | **2** | **~63** |

### Session Summary

| Metric | Value |
|--------|-------|
| **Total API calls** | ~63 |
| **Session duration** | ~30 minutes |
| **Avg calls/minute** | ~2 |
| **Peak burst** | 4 parallel calls |

---

## Are We Annoying Anyone?

### Risk Assessment by Provider

| Provider | Risk Level | Reasoning |
|----------|------------|-----------|
| **NCBI/Entrez** | LOW | We have API key (10 req/s), used ~3 calls total |
| **PubChem** | VERY LOW | Not used in this session |
| **BioGRID** | LOW | We have API key, 2 calls only |
| **STRING** | VERY LOW | 8 calls over 30 min = 0.27 req/min |
| **WikiPathways** | VERY LOW | 8 calls, well under limit |
| **ChEMBL** | LOW | SDK manages throttling, 14 calls |
| **Open Targets** | VERY LOW | GraphQL batching, 2 calls |
| **ClinicalTrials** | LOW | 16 calls, but spaced over time |
| **HGNC** | VERY LOW | 15 lightweight calls |

### Conclusion: **No Risk of Annoying Providers**

Our current usage pattern is:
- **~2 calls/minute average** across all APIs
- **Well under 1% of any rate limit**
- **Built-in throttling** prevents bursts
- **Parallel calls** are limited to 3-4 independent APIs

---

## Query Optimization Analysis

### Current Approach: Is It Right?

#### What We're Doing Well

1. **Fuzzy-to-Fact Protocol**
   ```
   search_genes("BRCA1") → HGNC:1100 → get_gene("HGNC:1100")
   ```
   - Resolves ambiguity upfront
   - Single strict call instead of multiple retries

2. **Parallel Independent Searches**
   ```
   # Good: 3 independent searches in one turn
   hgnc_get_gene("HGNC:4851")     # HTT
   string_search_proteins("HTT")   # STRING lookup
   chembl_search_compounds("tetrabenazine")  # Drug lookup
   ```

3. **Filtered Clinical Trial Searches**
   ```python
   # We used filters consistently
   clinicaltrials_search_trials(
       query="Huntington",
       phase="PHASE3",        # ← Reduces 21K to ~50
       status="RECRUITING"    # ← Further reduces
   )
   ```

#### What Could Be Improved

1. **Broad Searches Without Filters**
   ```python
   # BAD: This returns 21,619 results
   clinicaltrials_search_trials("cancer")

   # BETTER: Add disease ontology term
   clinicaltrials_search_trials(
       condition="breast cancer",  # Uses structured condition field
       phase="PHASE3",
       page_size=10
   )
   ```

2. **ChEMBL Name Sensitivity**
   ```python
   # FAILED: Exact compound search
   chembl_search_compounds("nutlin-3")  # No results

   # WORKED: Partial name
   chembl_search_compounds("nutlin")     # 12 results
   ```

3. **Large Pathway Enumeration**
   ```python
   # PROBLEMATIC: 1000+ genes
   wikipathways_get_pathway_components("WP:WP1785")  # 153K chars!

   # BETTER: Check size first
   pathway = wikipathways_get_pathway("WP:WP1785")
   if pathway.gene_count < 100:
       components = get_pathway_components(...)
   ```

---

## Recommended Query Patterns

### Pattern 1: Gene-Centric Discovery

```python
# Step 1: Resolve gene (1 call)
gene = hgnc_search_genes("BRCA1")  # → HGNC:1100

# Step 2: Get full gene record (1 call)
gene_data = hgnc_get_gene("HGNC:1100")

# Step 3: Get protein interactions (1 call)
# Use Ensembl ID from cross_references
interactions = string_get_interactions(
    f"STRING:9606.{gene_data.cross_references.ensembl_gene}",
    required_score=700,  # High confidence only
    limit=10             # Cap the results
)
```
**Total: 3 calls, minimal token usage**

### Pattern 2: Drug Discovery Pipeline

```python
# Step 1: Find compound (1 call)
compounds = chembl_search_compounds("ibuprofen", slim=True)

# Step 2: Get mechanism (1 call)
compound = chembl_get_compound(compounds[0].id)

# Step 3: Find trials (1 call with filters)
trials = clinicaltrials_search_trials(
    query=compound.name,
    phase="PHASE3",
    status="RECRUITING",
    page_size=10
)
```
**Total: 3 calls, targeted results**

### Pattern 3: Disease Landscape (Optimized)

```python
# BAD: Broad search
clinicaltrials_search_trials("cancer")  # 21,619 results

# GOOD: Specific disease + modality
clinicaltrials_search_trials(
    condition="triple negative breast cancer",
    intervention="sacituzumab",
    phase="PHASE3",
    page_size=20
)  # ~5 targeted results
```

---

## Summary Recommendations

### 1. Always Use Filters First

| Parameter | When to Use |
|-----------|-------------|
| `phase` | Drug discovery workflows |
| `status` | Active research landscape |
| `condition` | Specific disease focus |
| `page_size` | Keep ≤20 for exploration, 50 for analysis |
| `slim=True` | Batch operations, broad searches |

### 2. Check Before Enumerating

```python
# Check pathway size before getting components
pathway = get_pathway(id)
if pathway.gene_count > 100:
    # Use get_pathways_for_gene instead for targeted extraction
```

### 3. Use Batch Operations

```python
# Instead of 10 sequential calls
chembl_get_compounds_batch(["CHEMBL:25", "CHEMBL:941", ...], slim=True)
```

### 4. Parallel Independent Calls

Group independent lookups in single messages to reduce round-trips while respecting rate limits.

---

## Sensible Defaults Analysis

### Current Defaults by Tool

| Tool | Organism Default | Status |
|------|------------------|--------|
| **STRING** | `species=9606` (Human) | Good |
| **BioGRID** | `organism=9606` (Human) | Good |
| **Ensembl** | `species="homo_sapiens"` | Good |
| **Entrez** | `organism=None` (all) | Should default to human |
| **WikiPathways** | `organism=None` (all) | Should default to human |
| **UniProt** | No filter | Consider adding |
| **HGNC** | Human-only by definition | N/A |
| **ChEMBL** | No organism concept | N/A |
| **ClinicalTrials** | Human-only by definition | N/A |
| **Open Targets** | Human-focused | N/A |

### Recommended Default Filters

For drug discovery research (99% of use cases are human-centric):

```python
# Default query parameters
DEFAULTS = {
    "organism": 9606,              # Human
    "species": "homo_sapiens",
    "page_size": 20,               # Reasonable for exploration
    "slim": False,                 # Full data for single lookups
    "required_score": 700,         # High confidence for interactions
}
```

### Essential Filters by Workflow

| Workflow | Must-Have Filters |
|----------|-------------------|
| **Gene Discovery** | species=9606, page_size=10 |
| **Drug Discovery** | max_phase≥2, page_size=20 |
| **Clinical Landscape** | status=RECRUITING, phase=PHASE3 |
| **Pathway Analysis** | organism="Homo sapiens" |
| **Literature Search** | species=human, limit=10 |

### Implementation Recommendation

Add organism defaults to tools that currently lack them:

```python
# entrez server - add default
async def search_genes(
    query: str,
    organism: str = "human",  # ← Change from None
    ...
)

# wikipathways server - add default
async def search_pathways(
    query: str,
    organism: str = "Homo sapiens",  # ← Add default
    ...
)
```

This would reduce noise and improve result relevance for the vast majority of life sciences research queries.

---

## Metrics for Future Monitoring

Consider adding these metrics to track API health:

```python
# Suggested metrics per session
{
    "api_calls_by_source": {"hgnc": 15, "string": 8, ...},
    "avg_response_time_ms": {"hgnc": 120, "string": 450, ...},
    "rate_limit_hits": 0,
    "retry_count": 0,
    "total_tokens_returned": 45000
}
```

This would help identify if any API is becoming a bottleneck.
