---
name: lifesciences-clinical
description: "Queries clinical databases (Open Targets, ClinicalTrials.gov) via curl for target-disease associations, target tractability assessment, and clinical trial discovery. This skill should be used when the user asks to \"validate drug targets\", \"find clinical trials\", \"assess target tractability\", \"discover disease associations\", or mentions Open Targets scores, NCT identifiers, target-disease evidence, druggability assessment, or translational research workflows."
---

# Clinical & Translational API Skills

Query clinical databases directly via curl. These endpoints complement the Life Sciences MCPs.

## Quick Reference

| Task | API | Endpoint |
|------|-----|----------|
| Target-disease associations | Open Targets | GraphQL `/graphql` |
| Target tractability | Open Targets | GraphQL `tractability` |
| Known drugs for target | Open Targets | GraphQL `knownDrugs` |
| Search clinical trials | ClinicalTrials.gov | `/studies` |
| Get trial details | ClinicalTrials.gov | `/studies/{NCT}` |

## Open Targets GraphQL

Open Targets uses GraphQL - construct queries to get exactly what you need in one call.

### Basic Target-Disease Associations

```bash
# Get diseases associated with target (TP53)
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000141510\") { approvedSymbol associatedDiseases(page: {index: 0, size: 5}) { rows { disease { id name } score } } } }"}' \
  | jq '.data.target.associatedDiseases.rows[] | {disease: .disease.name, score}'
```

### Target Details with Tractability

```bash
# Get target with druggability assessment
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000141510\") { approvedSymbol biotype tractability { label modality value } } }"}' \
  | jq '.data.target | {symbol: .approvedSymbol, tractability}'
```

### Known Drugs for Target

```bash
# Get approved drugs targeting a protein
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000171791\") { approvedSymbol knownDrugs(page: {size: 5}) { rows { drug { name } phase mechanismOfAction } } } }"}' \
  | jq '.data.target.knownDrugs.rows[] | {drug: .drug.name, phase, mechanism: .mechanismOfAction}'
```

### Nested Query: All-in-One

```bash
# Get target + diseases + drugs + tractability in single call
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{
      target(ensemblId: \"ENSG00000141510\") {
        approvedSymbol
        biotype
        tractability { label value }
        knownDrugs(page: {size: 3}) {
          rows { drug { name } phase }
        }
        associatedDiseases(page: {size: 3}) {
          rows { disease { name } score }
        }
      }
    }"
  }' | jq '.data.target'
```

### Disease-Centric Queries

```bash
# Get targets associated with disease (breast cancer = EFO_0000305)
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ disease(efoId: \"EFO_0000305\") { name associatedTargets(page: {size: 5}) { rows { target { approvedSymbol } score } } } }"}' \
  | jq '.data.disease.associatedTargets.rows[] | {target: .target.approvedSymbol, score}'

# Search for disease by name
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ search(queryString: \"breast cancer\", entityNames: [\"disease\"]) { hits { id name } } }"}' \
  | jq '.data.search.hits[:3]'
```

### Evidence Breakdown

```bash
# Get association with evidence type scores
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ disease(efoId: \"MONDO_0018875\") { name associatedTargets(page: {size: 3}) { rows { target { approvedSymbol } score datatypeScores { id score } } } } }"}' \
  | jq '.data.disease.associatedTargets.rows[] | {target: .target.approvedSymbol, overall: .score, evidence: .datatypeScores}'
```

## ClinicalTrials.gov API v2

### Search Clinical Trials

```bash
# Search by condition
curl -s "https://clinicaltrials.gov/api/v2/studies?query.cond=breast+cancer&pageSize=3&format=json" \
  | jq '.studies[] | {nct: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, status: .protocolSection.statusModule.overallStatus}'

# Search by intervention (drug)
curl -s "https://clinicaltrials.gov/api/v2/studies?query.intr=venetoclax&pageSize=3&format=json" \
  | jq '.studies[] | {nct: .protocolSection.identificationModule.nctId, phase: .protocolSection.designModule.phases, status: .protocolSection.statusModule.overallStatus}'

# Filter by status
curl -s "https://clinicaltrials.gov/api/v2/studies?filter.overallStatus=RECRUITING&query.cond=leukemia&pageSize=3&format=json" \
  | jq '.studies[] | {nct: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle}'

# Filter by phase
curl -s "https://clinicaltrials.gov/api/v2/studies?filter.advanced=AREA[Phase]PHASE3&query.cond=cancer&pageSize=3&format=json" \
  | jq '.studies[] | {nct: .protocolSection.identificationModule.nctId, phases: .protocolSection.designModule.phases}'
```

### Get Trial Details

```bash
# Get full trial by NCT ID
curl -s "https://clinicaltrials.gov/api/v2/studies/NCT00461032?format=json" \
  | jq '{
    nct: .protocolSection.identificationModule.nctId,
    title: .protocolSection.identificationModule.briefTitle,
    status: .protocolSection.statusModule.overallStatus,
    phase: .protocolSection.designModule.phases,
    conditions: .protocolSection.conditionsModule.conditions,
    interventions: [.protocolSection.armsInterventionsModule.interventions[]?.name]
  }'

# Get eligibility criteria
curl -s "https://clinicaltrials.gov/api/v2/studies/NCT00461032?format=json" \
  | jq '.protocolSection.eligibilityModule | {criteria: .eligibilityCriteria, minAge, maxAge, sex}'
```

### Pagination

```bash
# Get page token for next page
RESPONSE=$(curl -s "https://clinicaltrials.gov/api/v2/studies?query.cond=cancer&pageSize=10&format=json")
NEXT_TOKEN=$(echo $RESPONSE | jq -r '.nextPageToken')

# Get next page
curl -s "https://clinicaltrials.gov/api/v2/studies?query.cond=cancer&pageSize=10&pageToken=$NEXT_TOKEN&format=json"
```

## Common Workflows

### Drug Target Validation Pipeline

```bash
# 1. Get target-disease association score
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000171791\") { approvedSymbol associatedDiseases(page: {size: 1}) { rows { disease { id name } score } } } }"}' \
  | jq '.data.target'

# 2. Check tractability
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000171791\") { tractability { label modality value } } }"}' \
  | jq '.data.target.tractability'

# 3. Find clinical trials for the target
curl -s "https://clinicaltrials.gov/api/v2/studies?query.intr=BCL2&filter.overallStatus=RECRUITING&pageSize=5&format=json" \
  | jq '.studies[] | {nct: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle}'
```

### Disease → Targets → Drugs → Trials

```bash
# 1. Find top targets for disease
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ disease(efoId: \"EFO_0000574\") { name associatedTargets(page: {size: 3}) { rows { target { approvedSymbol } score } } } }"}' \
  | jq '.data.disease'

# 2. Get drugs for top target
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ target(ensemblId: \"ENSG00000171791\") { knownDrugs(page: {size: 5}) { rows { drug { name id } phase } } } }"}' \
  | jq '.data.target.knownDrugs.rows'

# 3. Find trials for drug
curl -s "https://clinicaltrials.gov/api/v2/studies?query.intr=venetoclax&filter.overallStatus=RECRUITING&pageSize=3&format=json" \
  | jq '.studies[] | {nct: .protocolSection.identificationModule.nctId, condition: .protocolSection.conditionsModule.conditions[0]}'
```

## Rate Limits

| API | Limit | Notes |
|-----|-------|-------|
| Open Targets | 100 req/s | No auth required |
| ClinicalTrials.gov | Varies | May block automated clients |

## Notes

- **ClinicalTrials.gov** uses Cloudflare protection that may block Python httpx clients. Use curl for reliable access.
- **Open Targets** requires Ensembl Gene IDs (ENSG*) for target queries; use EFO IDs for disease queries.

## Query Best Practices

### Clinical Trials
- **Default status=RECRUITING** for active research landscape
- Use phase filter only for specific analysis:
  - **PHASE3+**: Commercialization/late-stage pipeline analysis
  - **PHASE1/2**: Early pipeline, first-in-human studies
  - **No filter**: Full landscape view (all phases)
- Don't assume phase filter is always needed

### Open Targets
- Requires Ensembl Gene IDs (ENSG*) for target queries
- Use EFO IDs for disease queries (search first to resolve)
- Use nested GraphQL queries to minimize API calls

### Common Pitfalls
- Don't filter by PHASE3+ for general drug discovery
- Recruiting trials are most relevant for collaboration opportunities
- Completed trials provide outcome data but may be outdated

## See Also

- [references/opentargets-schema.md](references/opentargets-schema.md) - GraphQL schema reference
- [references/clinicaltrials-fields.md](references/clinicaltrials-fields.md) - Study field reference
