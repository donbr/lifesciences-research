# Scenario 5: Synthetic Lethality Walkthrough Script

**Target Length:** 7-10 minutes
**Perspective:** Clinical Researcher
**Source:** Feng et al., *Sci. Adv.* 8, eabm6638 (2022) - PMC35559673
**Dataset:** [dwb2023/sl_gene_pairs](https://huggingface.co/datasets/dwb2023/sl_gene_pairs)

---

## The Story: A Researcher's Journey to Find Treatment Options

**Setting:** You are a cancer researcher studying TP53-mutant tumors. TP53 is mutated in 50% of all cancers - it's the most commonly altered tumor suppressor. Your patient has a TP53-deficient cancer. What treatment options exist?

**The Challenge:** You can't restore TP53 function directly. But synthetic lethality offers an alternative: find genes that TP53-deficient cells depend on, and target those instead.

---

## Act 1: The Challenge (1-2 min)

### Opening: Acknowledge Prior Art and Set Context

> "Today we're going to walk through a real research scenario. Imagine you're studying TP53-mutant cancers - the most common tumor suppressor mutation, found in 50% of all cancers."

> "We stand on the shoulders of giants - STRING, ChEMBL, BioGRID - databases with 20+ years of curation. Our contribution isn't recreating them; it's teaching AI agents how to navigate them without hallucinating."

### The Research Question

> "Our question is: **What synthetic lethal partners of TP53 could be therapeutic targets?**"

> "We have a starting point: Feng et al. 2022 - a Science Advances paper that systematically screened 12 tumor suppressors including TP53. But that paper is from 2022. Has anything changed? Are there additional papers confirming these findings? What drugs exist for the partners they identified?"

**Key Context:**
- TP53 is mutated in 50% of cancers (Vogelstein et al.)
- You can't drug TP53 directly - it's a tumor suppressor
- Synthetic lethality: target what TP53-deficient cells depend on
- Feng et al. identified TYMS, MCM9, BRIP1 as TP53 synthetic lethal partners

---

## Act 2: The Resolution Journey (2 min)

### From Fuzzy Names to Precise Identifiers

> "First, we need to resolve gene names to canonical identifiers. This prevents hallucination - every step is verifiable."

**Demo: Resolve TP53**

```python
# Step 1: Resolve the tumor suppressor
hgnc_search_genes("TP53")
# Expected: HGNC:11998, name: "tumor protein p53"
# Entrez ID: 7157
```

**Demo: Find TP53's Synthetic Lethal Partners from Feng Dataset**

From [dwb2023/sl_gene_pairs](https://huggingface.co/datasets/dwb2023/sl_gene_pairs):

| SL_GENE | TS_GENE |
|---------|---------|
| TYMS | TP53 |
| MCM9 | TP53 |
| BRIP1 | TP53 |

> "The Feng paper found these three genes are synthetic lethal with TP53. Let's resolve their identifiers."

```python
# Resolve each partner
hgnc_search_genes("TYMS")   # → HGNC:12441, Entrez: 7298
hgnc_search_genes("MCM9")   # → HGNC:21484, Entrez: 254394
hgnc_search_genes("BRIP1")  # → HGNC:20473, Entrez: 83990
```

**Key Message:**
> "No hallucination. Database facts. Each gene has a canonical CURIE that's verifiable across databases."

---

## Act 3: The Validation (2 min)

### Is This Finding Reproducible?

> "The Feng paper is one source. But science requires reproducibility. Has anyone else found these same synthetic lethal relationships?"

> "BioGRID ORCS aggregates CRISPR screen data from hundreds of studies. Let's check if TYMS essentiality in TP53-deficient cells is confirmed by independent labs."

**Demo: Query BioGRID ORCS**

```bash
# Query BioGRID ORCS for TYMS essentiality across all screens
curl -s "https://orcsws.thebiogrid.org/gene/7298?accesskey=${BIOGRID_API_KEY}" | wc -l
# Expected: ~1400+ screen results

# Filter for screens with negative scores (essential genes)
# Look for multiple PubMed IDs
```

**What to Show:**
1. **Screen count**: TYMS appears in 1400+ CRISPR screens - heavily studied
2. **Essentiality scores**: Negative scores = gene knockout kills cells
3. **Multiple PubMed IDs**: Independent papers confirming the finding

> "Look - there are multiple PubMed IDs. The Feng paper is PMC35559673, but we also see [PMID1], [PMID2]. Independent labs, same finding. This is reproducibility in action."

---

## Act 4: The Translation (2 min)

### From Research to Treatment Options

> "We've validated that TYMS is synthetic lethal with TP53. Now the clinical question: **Can we target TYMS? What drugs exist?**"

**Demo: Search for TYMS Inhibitors**

```python
# Search ChEMBL for TYMS-targeting compounds
chembl_search_compounds("TYMS inhibitor")
# Expected:
# - 5-fluorouracil (CHEMBL185) - Approved, widely used
# - Pemetrexed (CHEMBL502) - Approved for lung cancer
# - Raltitrexed (CHEMBL536) - Approved for colorectal cancer
```

> "TYMS is not just druggable - it's already targeted by approved chemotherapies. This isn't theoretical drug discovery; it's drug repurposing."

**Demo: Check Clinical Trials**

```python
# Search for trials combining TYMS-targeting drugs with TP53-based selection
clinicaltrials_search_trials("TP53 pemetrexed")
# Expected: Phase 2/3 trials exploring TP53 as biomarker

# Check if synthetic lethality angle is being explored
clinicaltrials_search_trials("synthetic lethality TP53")
```

**Key Questions Answered:**
1. **Is the partner druggable?** Yes - TYMS has multiple approved inhibitors
2. **Are there clinical trials?** Check trial landscape
3. **What's changed since 2022?** New trials, new compounds?

---

## Act 5: The Record (1 min)

### Persisting Knowledge for Future Queries

> "We've built a validated subgraph: TP53 → TYMS synthetic lethality, confirmed by multiple papers, druggable with approved compounds. Let's persist this for future queries."

**Demo: Save to Research Memory**

```python
graphiti_add_memory(
    name="TP53-TYMS Synthetic Lethality Validation",
    group_id="cq14-feng-synthetic-lethality",
    source="json",
    episode_body=json.dumps({
        "research_question": "What are synthetic lethal partners of TP53?",
        "tumor_suppressor": {
            "curie": "HGNC:11998",
            "name": "TP53",
            "mutation_frequency": "50% of cancers"
        },
        "synthetic_lethal_partner": {
            "curie": "HGNC:12441",
            "name": "TYMS",
            "entrez_id": "7298"
        },
        "evidence": {
            "primary_paper": "PMC35559673",
            "biogrid_screens": 1446,
            "confirming_pubmeds": ["PMID_1", "PMID_2"]
        },
        "druggability": {
            "approved_inhibitors": [
                {"name": "5-fluorouracil", "chembl": "CHEMBL185"},
                {"name": "pemetrexed", "chembl": "CHEMBL502"}
            ]
        }
    })
)
```

**Closing:**
> "From a clinical research question to validated, actionable knowledge. Every step has provenance - the paper, the confirming studies, the drug IDs, the trial numbers. This is how we operationalize research."

---

## Summary: The Researcher's Journey

| Step | Question | Tool | Output |
|------|----------|------|--------|
| 1 | What gene is mutated? | HGNC | TP53 → HGNC:11998 |
| 2 | What are its SL partners? | Feng Dataset | TYMS, MCM9, BRIP1 |
| 3 | Is this reproducible? | BioGRID ORCS | Multiple PubMed IDs |
| 4 | Can we target the partner? | ChEMBL | Approved drugs exist |
| 5 | Any clinical trials? | ClinicalTrials | Active studies |
| 6 | Save for future | Graphiti | Persistent subgraph |

---

## Alternative Entry Points

### The Pharma Perspective (Alternate Walkthrough)

> "I have a TYMS inhibitor (pemetrexed). It's approved for lung cancer. What other cancers might benefit?"

| Step | Question | Tool | Output |
|------|----------|------|--------|
| 1 | What does my drug target? | ChEMBL | TYMS |
| 2 | What TSGs pair with TYMS? | Feng Dataset | TP53, LKB1, NF1, NF2, PBRM1, PTEN, TP53BP1 |
| 3 | Which cancers have these? | Open Targets | Cancer-TSG associations |
| 4 | Any trials in these? | ClinicalTrials | Expansion opportunities |

---

## Technical Requirements

- `BIOGRID_API_KEY` from https://webservice.thebiogrid.org/
- MCP servers: HGNC, Entrez, ChEMBL, Open Targets, ClinicalTrials
- Graphiti Docker for persistence

---

## References

1. Feng et al. (2022). Genome-scale CRISPR screens identify synthetic lethal vulnerabilities in tumor suppressor-deficient cancers. *Science Advances*, 8, eabm6638. [PMC35559673](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9098673/)

2. Dataset: [dwb2023/pmc_35559673_table_s6_sl_gene_detail](https://huggingface.co/datasets/dwb2023/pmc_35559673_table_s6_sl_gene_detail)

3. Prior work: `docs/my-prior-work.md` - NSCLC pathway analysis including TP53
