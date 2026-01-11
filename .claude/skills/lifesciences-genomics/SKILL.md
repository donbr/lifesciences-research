---
name: lifesciences-genomics
description: "Queries genomic databases (Ensembl, NCBI, HGNC) via curl for gene lookup, variant annotation, orthology, and cross-database ID resolution. This skill should be used when the user asks to \"annotate variants\", \"find orthologs\", \"map gene IDs\", \"analyze linkage disequilibrium\", or mentions gene symbols, ENSG IDs, HGNC identifiers, VEP annotation, LD analysis, HGVS notation, or DNA sequences."
---

# Genomics API Skills

Query genomic databases directly via curl. These endpoints complement the Life Sciences MCPs.

## Quick Reference

| Task | API | Endpoint |
|------|-----|----------|
| Resolve gene symbol | HGNC | `/search/{symbol}` |
| Get gene metadata | Ensembl | `/lookup/id/{ENSG}` |
| Annotate variant | Ensembl VEP | `/vep/:species/hgvs` |
| Find orthologs | Ensembl | `/homology/id/:species/:id` |
| Cross-reference IDs | Ensembl | `/xrefs/id/{ENSG}` |
| Search NCBI Gene | E-utilities | `/esearch.fcgi?db=gene` |
| Link gene→PubMed | E-utilities | `/elink.fcgi?dbfrom=gene&db=pubmed` |

## Curl Examples

### HGNC: Resolve Gene Symbol

```bash
# Search for gene by symbol
curl -s "https://rest.genenames.org/search/symbol/TP53" \
  -H "Accept: application/json" | jq '.response.docs[0] | {hgnc_id, symbol, name}'

# Fetch by HGNC ID
curl -s "https://rest.genenames.org/fetch/hgnc_id/11998" \
  -H "Accept: application/json" | jq '.response.docs[0]'
```

### Ensembl: Gene Lookup & Metadata

```bash
# Lookup gene by Ensembl ID
curl -s "https://rest.ensembl.org/lookup/id/ENSG00000141510?expand=1&content-type=application/json" \
  | jq '{id, display_name, biotype, description, seq_region_name, start, end}'

# Resolve symbol to Ensembl ID
curl -s "https://rest.ensembl.org/lookup/symbol/homo_sapiens/TP53?content-type=application/json" \
  | jq '{id, display_name}'

# Get sequence
curl -s "https://rest.ensembl.org/sequence/id/ENSG00000141510?type=genomic&content-type=application/json" \
  | jq '.seq[:100]'
```

### Ensembl VEP: Variant Annotation

```bash
# Annotate variant by rsID
curl -s "https://rest.ensembl.org/vep/human/id/rs56116432?content-type=application/json" \
  | jq '.[0] | {most_severe_consequence, transcript_consequences: .transcript_consequences[:2]}'

# Annotate by HGVS notation (POST for batch)
curl -s -X POST "https://rest.ensembl.org/vep/human/hgvs" \
  -H "Content-Type: application/json" \
  -d '{"hgvs_notations": ["ENST00000366667:c.803C>T"]}' \
  | jq '.[0].transcript_consequences[0] | {consequence_terms, sift_prediction, polyphen_prediction}'
```

### Ensembl: Orthology

```bash
# Find orthologs for TP53
curl -s "https://rest.ensembl.org/homology/id/human/ENSG00000141510?type=orthologues&content-type=application/json" \
  | jq '.data[0].homologies[:5][] | {species: .target.species, gene_id: .target.id, perc_id: .target.perc_id}'
```

### Ensembl: Cross-References

```bash
# Get all cross-references for gene
curl -s "https://rest.ensembl.org/xrefs/id/ENSG00000141510?content-type=application/json" \
  | jq '.[] | select(.dbname | test("HGNC|UniProt|OMIM|RefSeq")) | {db: .dbname, id: .primary_id}'
```

### Ensembl: Linkage Disequilibrium

```bash
# LD between two variants
curl -s "https://rest.ensembl.org/ld/human/pairwise/rs56116432/rs1042522?population_name=1000GENOMES:phase_3:EUR&content-type=application/json" \
  | jq '.[0] | {r2, d_prime}'

# LD in genomic region
curl -s "https://rest.ensembl.org/ld/human/region/17:7668421..7687490/1000GENOMES:phase_3:EUR?content-type=application/json" \
  | jq '.[:3]'
```

### NCBI E-utilities: Gene Search & Links

```bash
# Search for gene
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term=TP53[sym]+AND+human[orgn]&retmode=json" \
  | jq '.esearchresult | {count, idlist}'

# Get gene summary
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id=7157&retmode=json" \
  | jq '.result["7157"] | {name: .name, description: .description, chromosome: .chromosome}'

# Link gene to PubMed articles
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=gene&db=pubmed&id=7157&retmode=json" \
  | jq '.linksets[0].linksetdbs[] | select(.dbto=="pubmed") | {db: .dbto, count: (.links | length)}'
```

## Rate Limits

| API | Limit | Notes |
|-----|-------|-------|
| HGNC | 10 req/s | No auth required |
| Ensembl | 15 req/s | No auth required |
| NCBI | 3 req/s | 10 req/s with NCBI_API_KEY |

## Query Best Practices

### Human-Centric Defaults
- **Filter to human by default** unless performing comparative genomics
- Use `human[orgn]` in NCBI searches, `homo_sapiens` for Ensembl
- Only omit organism filter when explicitly comparing across species (e.g., ortholog analysis)

### Efficient Querying
- Use `page_size=10` for exploration
- Use cross-reference endpoints to resolve IDs rather than multiple searches
- Prefer Ensembl IDs (ENSG*) for programmatic access

## See Also

- [references/ensembl-endpoints.md](references/ensembl-endpoints.md) - Full endpoint reference
- [references/ncbi-eutils.md](references/ncbi-eutils.md) - E-utilities pipeline patterns
