---
name: lifesciences-crispr
description: "Validates synthetic lethality claims from CRISPR knockout screens using BioGRID ORCS 5-phase workflow. This skill should be used when the user asks to \"validate synthetic lethality\", \"query CRISPR essentiality data\", \"find gene dependencies\", \"compare cell line screens\", or mentions BioGRID ORCS, gene knockout data, essentiality scores (CERES, MAGeCK, BAGEL), or asks to validate claims from published CRISPR papers."
---

# CRISPR Essentiality & Synthetic Lethality Validation

Validate synthetic lethality hypotheses using BioGRID ORCS CRISPR screen data via curl.

## Quick Reference

| Task | Endpoint |
|------|----------|
| Get gene essentiality data | `/gene/{entrez_id}` |
| Find cell line screens | `/screens/?cellLine={name}` |
| List all screens | `/screens/` |

## BioGRID ORCS API

**IMPORTANT**: Use `orcsws.thebiogrid.org` (NOT `orcs.thebiogrid.org`)

- **Base URL**: `https://orcsws.thebiogrid.org`
- **Auth**: Requires `BIOGRID_API_KEY` (free: https://webservice.thebiogrid.org/)
- **Rate Limit**: ~10 req/s
- **Format**: Tab-delimited (NOT JSON - don't use `format=json` parameter)

### Data Format

Tab-delimited with key columns:
- Column 1: Screen ID
- Column 2: Entrez Gene ID
- Column 4: Gene Symbol
- Column 8: Essentiality Score (CERES/MAGeCK/etc.)
- Column 9: FDR (False Discovery Rate)

## 5-Phase Synthetic Lethality Validation Workflow

### Phase 1: Resolve Gene Identifiers

Use Life Sciences MCPs to get Entrez IDs:

```bash
# Using HGNC MCP: search_genes → get_gene
# Extract "entrez" from cross_references object
# Example: DHODH → {"cross_references": {"entrez": "1723"}}

# Using Entrez MCP: search_genes
# Top result format: "NCBIGene:1723"
# Extract numeric ID: 1723
```

### Phase 2: Query ORCS for Essentiality Data

```bash
# Get all CRISPR screens for gene (using Entrez ID)
curl -s "https://orcsws.thebiogrid.org/gene/1723?accesskey=${BIOGRID_API_KEY}" > gene_screens.tsv

# Count screens
wc -l gene_screens.tsv
# Output: ~1400 screens for popular genes like DHODH
```

### Phase 3: Identify Relevant Cell Line Screens

```bash
# Find screens for specific cell line
curl -s "https://orcsws.thebiogrid.org/screens/?cellLine=786-O&accesskey=${BIOGRID_API_KEY}" \
  | awk 'BEGIN{FS="\t"} {print "Screen " $1 ": " $25}'
# Output: Screen 213: 786-O

# Find screens for another cell line
curl -s "https://orcsws.thebiogrid.org/screens/?cellLine=Caki-1&accesskey=${BIOGRID_API_KEY}" \
  | awk 'BEGIN{FS="\t"} {print "Screen " $1 ": " $25}'
# Output: Screen 511: Caki-1
```

### Phase 4: Extract Dependency Scores

```bash
# Filter gene data by Screen ID
curl -s "https://orcsws.thebiogrid.org/gene/1723?accesskey=${BIOGRID_API_KEY}" | \
grep -E "^213\s|^511\s" | \
awk 'BEGIN{FS="\t"} {print "Screen " $1 ": score=" $8 ", FDR=" $9}'

# Output:
# Screen 213 (786-O): score=-0.377, FDR=0.0452   ✅ Significant
# Screen 511 (Caki-1): score=-0.556, FDR=0.036   ✅ Significant
```

**Interpretation:**
- **Negative score** = gene is essential (cell death upon knockout)
- **FDR < 0.05** = statistically significant dependency
- **CERES score**: Most common, corrects for copy number effects

### Phase 5: Compare Across Genetic Backgrounds

```bash
# Find all renal cancer cell line screens
curl -s "https://orcsws.thebiogrid.org/screens/?accesskey=${BIOGRID_API_KEY}" | \
grep -i "renal" | awk 'BEGIN{FS="\t"} {print $1 "\t" $25}' | sort -u

# Extract scores for all renal lines
curl -s "https://orcsws.thebiogrid.org/gene/1723?accesskey=${BIOGRID_API_KEY}" | \
grep -E "^213\s|^511\s|^512\s|^204\s|^205\s" | \
awk 'BEGIN{FS="\t"} {printf "%-10s  Score: %s  FDR: %s\n", $1, $8, $9}'
```

## Scoring Methods

| Method | Description | Interpretation |
|--------|-------------|----------------|
| **CERES** | Computational correction for copy number effects | Most common, negative = essential |
| **Kolmogorov-Smirnov** | Statistical enrichment test | Log p-value, higher = more significant |
| **MAGeCK** | Model-based Analysis of Genome-wide CRISPR | Negative = depletion = essential |
| **BAGEL** | Bayesian Analysis of Gene EssentiaLity | Bayes Factor, positive = essential |

## Common Pitfalls

1. **Wrong endpoint**: Use `orcsws.thebiogrid.org` (NOT `orcs.thebiogrid.org`)
2. **Missing API key**: Check `.env` file first: `grep BIOGRID_API_KEY .env`
3. **JSON format error**: Don't use `format=json` - API returns tab-delimited by default
4. **Gene identifiers**: Always use Entrez IDs (not gene symbols) for `/gene/{id}` endpoint
5. **Screen metadata**: Use `/screens/?cellLine={name}` to find Screen IDs before querying gene data
6. **Column numbers**: Score = column 8, FDR = column 9

## Complete Example

See [references/biogrid-orcs-validation.md](references/biogrid-orcs-validation.md) for a complete worked example validating DHODH/VHL synthetic lethality from a Science Advances paper.

**Result**: 2/4 VHL-mutant lines show significant DHODH dependency (context-dependent penetrance).

## Integration with Life Sciences MCPs

**Workflow:**
1. Use HGNC or Entrez MCP to resolve gene symbols to Entrez IDs
2. Query ORCS for essentiality data using Entrez IDs
3. Analyze dependency scores across cell lines
4. Validate synthetic lethality hypotheses

**Example:**
```python
# Phase 1: Use MCP to get Entrez ID
hgnc_result = await client.call_tool("hgnc_search_genes", {"query": "DHODH"})
gene = await client.call_tool("hgnc_get_gene", {"hgnc_id": hgnc_result["items"][0]["id"]})
entrez_id = gene["cross_references"]["entrez"]  # "1723"

# Phase 2-5: Use curl with ORCS (see workflow above)
```

## References

- **BioGRID ORCS**: https://orcs.thebiogrid.org/
- **API Key**: https://webservice.thebiogrid.org/
- **Meyers RM et al. 2017**: CERES methodology (PMID: 29083409)
- **Complete Example**: [references/biogrid-orcs-validation.md](references/biogrid-orcs-validation.md)
