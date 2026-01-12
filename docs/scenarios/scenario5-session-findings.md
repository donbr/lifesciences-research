# Scenario 5 Session Findings: Synthetic Lethality Walkthrough

**Date:** 2026-01-11
**Sessions:** 2 (Initial walkthrough + Follow-up research)
**Perspective:** Clinical Researcher with TP53-mutant cancer patient

---

## What Went Well

### 1. Fuzzy-to-Fact Protocol Validation

The protocol worked exactly as designed:
- **Phase 1 (Fuzzy):** HGNC `search_genes("TP53")` → ranked candidates with scores
- **Phase 2 (Strict):** `get_gene("HGNC:11998")` → authoritative record with cross-references

The cross-references object enabled seamless traversal: HGNC → Entrez ID → BioGRID ORCS → ChEMBL.

### 2. BioGRID ORCS as Independent Validation

The lifesciences-crispr skill proved its value:
- TYMS: 1,446 screens confirming essentiality
- MCM9: 1,438 screens
- BRIP1: 1,494 screens

This provides reproducibility beyond the single Feng et al. paper.

### 3. Druggability Gap Identification

The walkthrough revealed a concrete drug discovery opportunity:
- **TYMS:** Approved drugs (5-FU, pemetrexed)
- **MCM9:** No specific inhibitors (opportunity!)
- **BRIP1:** No specific inhibitors (opportunity!)

### 4. Multi-Database Triangulation

STRING and Open Targets added complementary context:
- STRING: TP53 network (MDM2, ATM, SIRT1) with evidence scores
- Open Targets: 3,277 disease associations with clinical relevance scores

### 5. Literature Discovery

PubMed search found papers beyond Feng et al. that validate the DNA repair SL theme:
- Patterson-Fortin 2022 (NHEJ/MMEJ)
- Chan 2019 (WRN helicase)
- Biayna 2021 (HMCES-APOBEC3A)

---

## Opportunities for Improvement

### 1. Human-Centric Default in CRISPR Skill

**Issue:** The lifesciences-crispr skill doesn't explicitly state to filter by human species.

**Recommendation:** Add to the skill:
```markdown
### Human-Centric Defaults
- Use human Entrez Gene IDs (NCBI Taxonomy 9606)
- Verify species column (9606 = Homo sapiens) in results
- Cell line names indicate human cancer context
```

### 2. PubMed ID Extraction from ORCS

**Issue:** BioGRID ORCS returns PubMed IDs in the TSV output, but we didn't extract them to cite specific supporting papers.

**Recommendation:** Add to lifesciences-crispr skill:
```bash
# Extract unique PubMed IDs from ORCS results
curl -s "https://orcsws.thebiogrid.org/gene/{ID}?accesskey=${BIOGRID_API_KEY}" | \
awk -F'\t' '{print $X}' | sort -u  # Column X contains PubMed ID
```

### 3. STRING Evidence Channel Utilization

**Issue:** We got interaction scores but didn't leverage STRING's 7-channel evidence breakdown.

**Per prior-art-api-patterns.md:**
> "STRING's 7-channel evidence model (nscore, fscore, pscore, ascore, escore, dscore, tscore) is essential for agent reasoning about confidence"

**Recommendation:** Update STRING interaction queries to include and interpret evidence breakdown.

### 4. BioThings Explorer Integration

**From prior-art-api-patterns.md:**
> "BTE-RAG shows 25 percentage point improvement (51% → 75.8%) with federated knowledge retrieval"

**Recommendation:** Consider BioThings Explorer as an alternative federation approach for complex multi-hop queries.

### 5. Competency Question Benchmark Alignment

**Current state:** cq14 follows the "Gene-centric mechanisms" pattern from BTE-RAG benchmarks.

**Recommendation:** Formalize validation metrics similar to BTE-RAG:
- Precision: Did we find known SL partners?
- Recall: Did we miss any documented SL partners?
- Drug coverage: What percentage of SL partners have approved drugs?

---

## Key Learnings

### 1. The Butterfly Effect in Synthetic Lethality

Some SL relationships are mechanistically obvious (BRCA1/PARP), while others emerge from complex network effects. Large-scale CRISPR screens find relationships that no one would predict from first principles.

### 2. Druggability ≠ Biological Validation

MCM9 has stronger ORCS validation than some drugged targets, but no drugs exist. This gap between biological validation and pharmaceutical investment is where opportunities lie.

### 3. DNA Repair Theme

Multiple TP53 SL partners involve DNA repair (TYMS, MCM9, BRIP1, WRN, NHEJ/MMEJ pathway). This suggests TP53-deficient cells are vulnerable to DNA synthesis/repair stress - a therapeutic theme to explore.

### 4. MDM2 as Alternative Strategy

STRING revealed MDM2 (score 0.999) as TP53's primary negative regulator. Instead of exploiting synthetic lethality, MDM2 inhibitors (Nutlin-3, idasanutlin) try to restore TP53 function by blocking degradation. This gives clinicians two strategies:
1. **Restore TP53** (MDM2 inhibitors)
2. **Exploit TP53 loss** (SL partner targeting)

---

## Recommendations for Next Steps

### Immediate

1. **Complete the execution checklist** - Persist expanded graph was marked complete
2. **Update lifesciences-crispr skill** with human-centric defaults and PubMed extraction
3. **Add STRING evidence channel documentation** to lifesciences-proteomics skill

### Near-Term

4. **Partner with domain expert** - Need biosciences researcher to validate findings and provide additional context
5. **Explore BioThings Explorer** - Consider as complementary federation approach
6. **Benchmark cq14** against BTE-RAG metrics for validation

### Future

7. **Investigate DNA repair SL cluster** - The theme across papers suggests systematic screening of DNA repair genes for TP53 SL
8. **MCM9/BRIP1 drug discovery analysis** - Deep dive into why no inhibitors exist and whether they're druggable targets

---

## Session Statistics

| Metric | Value |
|--------|-------|
| BioGRID ORCS API calls | 5 |
| HGNC MCP calls | 6 |
| ChEMBL MCP calls | 4 |
| STRING MCP calls | 2 |
| Open Targets MCP calls | 2 |
| PubMed searches | 2 |
| Graphiti persistence | 1 |
| Total tools invoked | ~40 |

---

## Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `docs/scenarios/scenario5-walkthrough-script.md` | Created | Recording script |
| `docs/scenarios/scenario5-synthetic-lethality-feng-walkthrough.md` | Created + Updated | Full walkthrough with outputs |
| `docs/competency-questions/competency-questions-catalog.md` | Updated | Added cq14 entry |
| `docs/my-prior-work.md` | Updated | Added SL extension section |
| `docs/scenarios/scenario5-session-findings.md` | Created | This document |

---

## Acknowledgments

This research builds on:
- Feng et al. (2022) - Primary synthetic lethality dataset
- BioGRID ORCS team - CRISPR screen aggregation
- STRING consortium - Protein interaction evidence
- Prior art documented in `docs/prior-art-api-patterns.md`
