---
name: lifesciences-proteomics
description: "Queries protein databases (UniProt, STRING, BioGRID) via curl for protein lookups, protein-protein interactions, functional enrichment analysis, and cross-database ID mapping. This skill should be used when the user asks to \"find protein interactions\", \"analyze interaction networks\", \"perform GO enrichment\", \"map protein IDs\", or mentions PPI networks, UniProt accessions, STRING scores, BioGRID interactions, or protein ID conversion between databases."
---

# Proteomics API Skills

Query protein databases directly via curl. These endpoints complement the Life Sciences MCPs.

## Quick Reference

| Task | API | Endpoint |
|------|-----|----------|
| Search proteins | UniProt | `/uniprotkb/search` |
| Get protein details | UniProt | `/uniprotkb/{accession}` |
| Batch ID mapping | UniProt | `/idmapping/run` |
| Protein interactions | STRING | `/network` |
| Functional enrichment | STRING | `/enrichment` |
| Genetic/physical interactions | BioGRID | `/interactions` |

## Curl Examples

### UniProt: Protein Search & Retrieval

```bash
# Search for protein by gene name
curl -s "https://rest.uniprot.org/uniprotkb/search?query=gene:TP53+AND+organism_id:9606&format=json&size=3" \
  | jq '.results[:1][] | {accession: .primaryAccession, name: .proteinDescription.recommendedName.fullName.value}'

# Get protein by accession
curl -s "https://rest.uniprot.org/uniprotkb/P04637.json" \
  | jq '{accession: .primaryAccession, gene: .genes[0].geneName.value, function: .comments[] | select(.commentType=="FUNCTION") | .texts[0].value}'

# Get protein sequence (FASTA)
curl -s "https://rest.uniprot.org/uniprotkb/P04637.fasta"

# Search with field queries
curl -s "https://rest.uniprot.org/uniprotkb/search?query=reviewed:true+AND+organism_id:9606+AND+keyword:Apoptosis&format=json&size=5" \
  | jq '.results[] | {accession: .primaryAccession, gene: .genes[0].geneName.value}'
```

### UniProt: Batch ID Mapping (Async)

```bash
# Submit ID mapping job
JOB_ID=$(curl -s "https://rest.uniprot.org/idmapping/run" \
  --form 'ids=P04637,P38398,P51587' \
  --form 'from=UniProtKB_AC-ID' \
  --form 'to=Ensembl' | jq -r '.jobId')

# Check job status
curl -s "https://rest.uniprot.org/idmapping/status/$JOB_ID"

# Get results (when complete)
curl -s "https://rest.uniprot.org/idmapping/results/$JOB_ID" | jq '.results'
```

### STRING: Protein-Protein Interactions

```bash
# Get interaction network for proteins
curl -s "https://string-db.org/api/json/network?identifiers=TP53&species=9606&required_score=700&limit=10" \
  | jq '.[] | {proteinA: .preferredName_A, proteinB: .preferredName_B, score}'

# Network for multiple proteins
curl -s "https://string-db.org/api/json/network?identifiers=TP53%0dMDM2%0dATM&species=9606" \
  | jq '.[] | {A: .preferredName_A, B: .preferredName_B, score}'

# Get evidence scores breakdown
curl -s "https://string-db.org/api/json/network?identifiers=TP53&species=9606&required_score=900&limit=5" \
  | jq '.[] | {A: .preferredName_A, B: .preferredName_B, experimental: .escore, database: .dscore, textmining: .tscore}'
```

### STRING: Functional Enrichment

```bash
# GO/KEGG/Reactome enrichment for protein set
curl -s "https://string-db.org/api/json/enrichment?identifiers=9606.ENSP00000269305%0d9606.ENSP00000258149%0d9606.ENSP00000278616&species=9606" \
  | jq '.[:5][] | {category, term, description, fdr}'

# Enrichment with gene symbols (need to resolve first)
curl -s "https://string-db.org/api/json/get_string_ids?identifiers=TP53%0dMDM2%0dATM&species=9606" \
  | jq '.[].stringId' # Use these IDs for enrichment
```

### STRING: Network Visualization

```bash
# Get network image URL
echo "https://string-db.org/api/highres_image/network?identifiers=TP53%0dMDM2%0dATM&species=9606&network_flavor=confidence"

# Get SVG
curl -s "https://string-db.org/api/svg/network?identifiers=TP53&species=9606&add_nodes=5" > network.svg
```

### BioGRID: Genetic & Physical Interactions

```bash
# Get interactions for gene (requires API key)
curl -s "https://webservice.thebiogrid.org/interactions?geneList=TP53&taxId=9606&format=json&accesskey=${BIOGRID_API_KEY}" \
  | jq 'to_entries[:5][] | .value | {geneA: .OFFICIAL_SYMBOL_A, geneB: .OFFICIAL_SYMBOL_B, system: .EXPERIMENTAL_SYSTEM}'

# Filter by experimental method
curl -s "https://webservice.thebiogrid.org/interactions?geneList=TP53&taxId=9606&evidenceList=Two-hybrid&format=json&accesskey=${BIOGRID_API_KEY}"

# Low-throughput only (higher confidence)
curl -s "https://webservice.thebiogrid.org/interactions?geneList=TP53&taxId=9606&throughputTag=low&format=json&accesskey=${BIOGRID_API_KEY}"
```

## ID Resolution Patterns

```bash
# Gene symbol → STRING ID
curl -s "https://string-db.org/api/json/get_string_ids?identifiers=TP53&species=9606" \
  | jq '.[0].stringId'
# Output: "9606.ENSP00000269305"

# STRING ID → UniProt
curl -s "https://rest.ensembl.org/xrefs/id/ENSP00000269305?content-type=application/json" \
  | jq '.[] | select(.dbname=="Uniprot/SWISSPROT") | .primary_id'
```

## Rate Limits

| API | Limit | Auth Required |
|-----|-------|---------------|
| UniProt | 100 req/s | No |
| STRING | 1 req/s | No |
| BioGRID | 10 req/s | Yes (API key) |
