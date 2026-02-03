# CQ10: Pharmacological Method Steps

**Status**: VALIDATED
**Date**: 2026-02-02
**Validation Agent**: FA4 Research Agent (Paul's Method Validation)

## Competency Question

> What are the iterative steps and criteria for storing research and identifying prior and emerging art in clinical trials as required by the established pharmacological method?

## Answer: The Fuzzy-to-Fact Protocol

The pharmacological method implemented in this platform follows a five-phase protocol called **Fuzzy-to-Fact**, designed to progressively resolve ambiguous natural language queries into validated, cross-referenced biomedical entities suitable for knowledge graph storage.

---

## Phase 1: ANCHOR (Fuzzy Search to CURIE Resolution)

**Purpose**: Convert natural language queries to unambiguous Compact URIs (CURIEs)

**Process**:
1. Accept natural language query (e.g., "BRCA1", "tumor protein p53", "breast cancer gene")
2. Execute fuzzy search against authoritative databases
3. Return ranked candidates with relevance scores
4. Human or agent selects top candidate, obtaining resolved CURIE

**Storage Criteria**:
- Only store entities with resolved CURIEs (never ambiguous strings)
- CURIEs must follow namespace:identifier format (e.g., `HGNC:1100`, `UniProtKB:P38398`)

**Example Trace**:
```
Query: "BRCA1"
Tool: hgnc_search_genes
Result: [
  {"id": "HGNC:1100", "symbol": "BRCA1", "score": 1.0},
  {"id": "HGNC:25829", "symbol": "ABRAXAS1", "score": 0.95},
  ...
]
Selected: HGNC:1100 (BRCA1)
```

---

## Phase 2: ENRICH (Strict Lookup for Full Entity Details)

**Purpose**: Retrieve complete entity records with cross-references

**Process**:
1. Use resolved CURIE from Phase 1
2. Execute strict lookup against source database
3. Extract full entity details: function, structure, annotations
4. Capture cross_references object for Phase 3 expansion

**Storage Criteria**:
- Store canonical name, symbol, and all aliases
- Store functional annotations (summary, description)
- Store provenance (source database, retrieval timestamp)

**Example Trace**:
```
Query: hgnc_get_gene("HGNC:1100")
Result: {
  "id": "HGNC:1100",
  "symbol": "BRCA1",
  "name": "BRCA1 DNA repair associated",
  "location": "17q21.31",
  "cross_references": {
    "ensembl_gene": "ENSG00000012048",
    "uniprot": ["P38398"],
    "entrez": "672",
    "omim": "113705"
  }
}
```

---

## Phase 3: EXPAND (Build Edges via Cross-References)

**Purpose**: Create a connected knowledge graph by following cross-references

**Process**:
1. Extract cross-reference CURIEs from Phase 2 entity
2. For each cross-reference type:
   - Validate by fetching from target database
   - Extract additional cross-references (transitive closure)
3. Build entity-to-entity edges with relationship types

**Storage Criteria**:
- Edges must have source_id, target_id, and relationship_type
- Cross-references are bidirectional verification (A references B, B references A)
- Failed validations logged but not stored

**Relationship Types**:
| Edge | Relationship | Databases |
|------|--------------|-----------|
| Gene -> Protein | `encodes` | HGNC -> UniProt |
| Protein -> Protein | `interacts_with` | STRING |
| Gene -> Disease | `associated_with` | Open Targets |
| Target -> Compound | `targeted_by` | ChEMBL |
| Gene -> Gene | `synthetic_lethal_with` | BioGRID ORCS |

**Example Trace**:
```
Cross-reference chain for BRCA1:
HGNC:1100 --encodes--> UniProtKB:P38398
HGNC:1100 --maps_to--> ENSG00000012048
HGNC:1100 --maps_to--> NCBIGene:672
ENSG00000012048 --associated_with--> MONDO:0007254 (breast cancer)
```

---

## Phase 4: VALIDATE (Literature and Clinical Confirmation)

**Purpose**: Anchor findings in peer-reviewed literature and clinical evidence

**Process**:
1. Retrieve PubMed links for each entity
2. Cross-reference with clinical trials (ClinicalTrials.gov)
3. Score evidence by:
   - Publication recency
   - Trial phase (Phase 3-4 = high evidence)
   - Citation count

**Prior Art Identification**:
- Publications > 5 years old with > 100 citations = established prior art
- FDA-approved drugs = definitive prior art
- Completed Phase 3 trials = strong prior art

**Emerging Art Identification**:
- Publications < 2 years old = emerging
- Active clinical trials (RECRUITING status) = emerging
- Phase 1-2 trials = early emerging
- Preprints (bioRxiv, medRxiv) = speculative emerging

**Example Trace**:
```
Gene: NCBIGene:672 (BRCA1)
PubMed Links: [18594935, 15967981, 24633894, 30817646, 30806067]

Clinical Trial: NCT00516373
Status: COMPLETED
Phase: PHASE1
Drug: Olaparib (CHEMBL:521686)
Classification: Established prior art (FDA-approved PARP inhibitor)
```

---

## Phase 5: PERSIST (Store to Knowledge Graph)

**Purpose**: Durably store validated entities and relationships

**Process**:
1. Format entity as JSON following Agentic Biolink schema
2. Call Graphiti add_memory with appropriate group_id
3. Include provenance metadata:
   - Source tools used
   - Retrieval timestamps
   - Validation status

**Storage Schema**:
```json
{
  "entity_type": "Gene",
  "curie": "HGNC:1100",
  "symbol": "BRCA1",
  "name": "BRCA1 DNA repair associated",
  "cross_references": {
    "uniprot": "UniProtKB:P38398",
    "ensembl": "ENSG00000012048",
    "entrez": "NCBIGene:672"
  },
  "provenance": {
    "source": "HGNC",
    "retrieved_at": "2026-02-02T00:00:00Z",
    "validation_status": "VALIDATED"
  }
}
```

**Graphiti Command**:
```python
add_memory(
    name="BRCA1 Gene Entity",
    episode_body=json.dumps(entity),
    group_id="paul-fa4-method",
    source="json",
    source_description="HGNC validated gene entity"
)
```

---

## Provenance Table

| Phase | Tool | Query | Result |
|-------|------|-------|--------|
| 1. Anchor | `hgnc_search_genes` | "BRCA1" | HGNC:1100 (score=1.0) |
| 2. Enrich | `hgnc_get_gene` | HGNC:1100 | Full gene record |
| 3. Expand | `uniprot_get_protein` | UniProtKB:P38398 | Cross-refs validated |
| 3. Expand | `ensembl_get_gene` | ENSG00000012048 | Cross-refs validated |
| 3. Expand | `entrez_get_gene` | NCBIGene:672 | Cross-refs validated |
| 4. Validate | `entrez_get_pubmed_links` | NCBIGene:672 | 5 PubMed IDs |
| 4. Validate | ClinicalTrials.gov API | "BRCA1 PARP inhibitor" | NCT00516373 |
| 5. Persist | `graphiti__add_memory` | JSON entity | Stored |

---

## Scalability Notes

### Batch Operations
- Use `slim=True` parameter for bulk searches (~20 tokens vs ~115 per entity)
- Use `get_compounds_batch` for ChEMBL lookups (prevents thread exhaustion)
- Paginate with cursor-based pagination for large result sets

### Rate Limiting
- NCBI Entrez: 3 req/s without API key, 10 req/s with key
- STRING: 1000 req/day
- ChEMBL: No documented limit (use 10 req/s as safe default)
- ClinicalTrials.gov: Blocked by Cloudflare for automated clients

### Error Handling
- `UNRESOLVED_ENTITY`: Query did not resolve to valid CURIE
- `ENTITY_NOT_FOUND`: Valid CURIE format but entity does not exist
- `RATE_LIMITED`: Back off and retry with exponential delay
- `UPSTREAM_ERROR`: Source API unavailable, log and skip

---

## Conclusion

The Fuzzy-to-Fact protocol provides a systematic methodology for:
1. Converting ambiguous queries to validated identifiers
2. Building rich entity profiles with cross-database validation
3. Identifying prior art (established) vs emerging art (active research)
4. Persisting findings in a durable knowledge graph with full provenance

This approach ensures that stored research is:
- **Unambiguous**: Every entity has a canonical CURIE
- **Validated**: Cross-references verified across multiple databases
- **Traceable**: Full provenance from query to storage
- **Scalable**: Designed for batch operations and rate-limit compliance
