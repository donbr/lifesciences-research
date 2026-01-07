# Feature Specification: BioGRID MCP Server

**Feature Branch**: `feature/006-string-007-biogrid`
**Created**: 2025-12-23
**Status**: Scaffolded (pending integration tests)
**Updated**: 2025-12-23
**Linear**: AGE-75
**Input**: User description: "Build the BioGRID MCP Server for genetic and protein interaction data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gene Symbol Search (Priority: P1)

As a genetics researcher, I need to validate gene symbols for BioGRID interaction queries so that I can identify genes with known genetic/protein interactions.

**Why this priority**: This is the entry point for BioGRID interaction queries. BioGRID uses gene symbols directly (not CURIEs), so validation is essential before querying interactions.

**Independent Test**: Can be fully tested by querying "TP53" and verifying the gene symbol is valid for human (taxid 9606). Delivers immediate value by enabling gene validation.

**Acceptance Scenarios**:

1. **Given** a researcher knows a gene symbol, **When** they search for "TP53", **Then** the system returns a validated candidate with organism information
2. **Given** a researcher enters a partial symbol, **When** they search with minimum 2 characters, **Then** the system validates the symbol format
3. **Given** a researcher wants human genes only, **When** they specify organism=9606, **Then** results are filtered to Homo sapiens
4. **Given** a researcher provides invalid input, **When** they search with 1 character, **Then** the system returns error code AMBIGUOUS_QUERY with recovery hint

---

### User Story 2 - Genetic/Protein Interactions (Priority: P2)

As a genetics researcher, once I have validated a gene symbol, I need to retrieve genetic and protein interactions with experimental evidence types so that I can analyze functional relationships with supporting experimental data.

**Why this priority**: This is the core functionality of BioGRID - providing experimentally validated interactions. The distinction between physical (protein-protein) and genetic (synthetic lethality, epistasis) interactions is essential for understanding functional relationships.

**Independent Test**: Can be tested by querying "TP53" and verifying interactions with MDM2, ATM including experimental system types (Affinity Capture-Western, Two-hybrid, Synthetic Lethality). Delivers value by providing curated experimental evidence.

**Acceptance Scenarios**:

1. **Given** a researcher has a validated gene symbol, **When** they request interactions for "TP53", **Then** the system returns genetic and protein interactions with partners
2. **Given** a researcher needs experimental evidence, **When** they retrieve interactions, **Then** each interaction includes experimental_system (e.g., "Affinity Capture-Western", "Two-hybrid", "Synthetic Lethality")
3. **Given** a researcher needs to distinguish interaction types, **When** they retrieve interactions, **Then** each includes experimental_system_type ("physical" or "genetic")
4. **Given** a researcher needs literature references, **When** they retrieve interactions, **Then** each includes pubmed_id for the supporting publication
5. **Given** a researcher wants to limit results, **When** they set max_results=100, **Then** only the specified number of interactions are returned
6. **Given** a researcher provides an invalid gene symbol, **When** they query a non-existent gene, **Then** the system returns error code ENTITY_NOT_FOUND

---

### User Story 3 - Cross-Database Integration (Priority: P3)

As a genetics researcher, I need BioGRID interaction records to include cross-references to Entrez Gene IDs so that I can integrate with other gene databases.

**Why this priority**: While BioGRID primarily uses gene symbols, cross-references to Entrez enable integration with NCBI resources.

**Independent Test**: Can be tested by retrieving interactions for TP53 and verifying that cross_references contains Entrez Gene ID for the query gene.

**Acceptance Scenarios**:

1. **Given** a researcher retrieves interactions, **When** they access the cross_references field, **Then** it contains Entrez Gene ID from BioGRID response
2. **Given** a gene has no Entrez cross-reference, **When** retrieving the record, **Then** the entrez key is omitted from cross_references (never null)

---

### User Story 4 - Error Recovery and Resilience (Priority: P4)

As a genetics researcher, when I encounter errors during BioGRID queries (rate limits, invalid API key, invalid input), I need clear error messages with actionable recovery hints.

**Why this priority**: Good error handling enables self-service resolution, especially for API key configuration issues.

**Acceptance Scenarios**:

1. **Given** a researcher hasn't configured an API key, **When** they attempt any query, **Then** the system returns error code UPSTREAM_ERROR with recovery hint to obtain a free key at https://webservice.thebiogrid.org/
2. **Given** a researcher has an invalid API key, **When** they attempt a query, **Then** the system returns error code UPSTREAM_ERROR with message about invalid key
3. **Given** a researcher sends too many requests, **When** they exceed rate limits, **Then** the system returns error code RATE_LIMITED with backoff hint
4. **Given** the BioGRID API is temporarily unavailable, **When** a query fails, **Then** the system returns error code UPSTREAM_ERROR with recovery hint

---

### Edge Cases

- What happens when a gene has thousands of interactions (exceeding max_results)?
- How does the system handle genes from non-model organisms with sparse data?
- What happens when BioGRID API returns interactions without PubMed IDs?
- How does the system distinguish between high-throughput and low-throughput studies?

## Requirements *(mandatory)*

### Functional Requirements

**Architecture & Integration**

- **FR-001**: System MUST implement BioGridClient as a subclass of LifeSciencesClient to inherit connection pooling, rate limiting, and error handling patterns (ADR-001 Section 2)
- **FR-002**: All HTTP calls MUST use httpx async client with native asyncio (ADR-001 Section 2)
- **FR-003**: Client MUST implement context manager protocol for proper resource cleanup
- **FR-004**: System MUST require BIOGRID_API_KEY environment variable (free registration)

**Fuzzy-to-Fact Protocol**

- **FR-005**: System MUST implement `search_genes(query)` tool validating gene symbols for BioGRID (ADR-001 Section 3)
- **FR-006**: System MUST implement `get_interactions(gene_symbol)` tool accepting validated gene symbols (ADR-001 Section 3)
- **FR-007**: Gene symbols are case-insensitive and normalized to uppercase

**Interaction Data**

- **FR-008**: All interactions MUST include:
  - biogrid_interaction_id: Unique BioGRID identifier
  - symbol_a, symbol_b: Gene symbols for interacting partners
  - experimental_system: Experimental method (e.g., "Affinity Capture-Western")
  - experimental_system_type: "physical" or "genetic"
  - pubmed_id: Literature reference (optional)
  - throughput: "High Throughput" or "Low Throughput" (optional)
- **FR-009**: Response MUST include counts of physical vs genetic interactions

**Envelopes & Schema**

- **FR-010**: Fuzzy search MUST return results wrapped in PaginationEnvelope (ADR-001 Section 8)
- **FR-011**: All errors MUST use ErrorEnvelope with code, message, recovery_hint, and invalid_input fields (ADR-001 Section 8)
- **FR-012**: Interaction results MUST include cross_references with Entrez Gene ID where available

### Non-Functional Requirements

- **NFR-001**: Authentication: Requires free API key from https://webservice.thebiogrid.org/
- **NFR-002**: Rate limit: 2 requests per second (conservative estimate)
- **NFR-003**: Max interactions per request: 10,000
- **NFR-004**: Response time: P95 < 3 seconds for interaction queries

## Technical Implementation

### API Details

- **Base URL**: `https://webservice.thebiogrid.org`
- **Protocol**: REST (JSON output)
- **Authentication**: API key via `accesskey` query parameter
- **Rate Limit**: 2 req/sec (conservative estimate)

### Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `/interactions` | Get genetic/protein interactions for gene(s) |

### Models Implemented

- `BioGridSearchCandidate`: Gene symbol validation result
- `GeneticInteraction`: Single interaction with experimental evidence
- `BioGridCrossReferences`: Cross-database links (Entrez)
- `InteractionResult`: Complete response with interaction list and counts

### Experimental System Types

**Physical Interactions:**
- Affinity Capture-Western
- Two-hybrid
- Reconstituted Complex
- Co-fractionation
- Co-purification
- Far Western

**Genetic Interactions:**
- Synthetic Lethality
- Dosage Rescue
- Phenotypic Enhancement
- Phenotypic Suppression
- Negative Genetic

## Test Coverage

| Test | Status | Description |
|------|--------|-------------|
| test_search_genes_tp53 | PENDING | Gene symbol validation |
| test_search_genes_validation | PENDING | Query validation errors |
| test_get_interactions_tp53 | PENDING | Interactions for TP53 |
| test_get_interactions_evidence | PENDING | Experimental system types |
| test_get_interactions_counts | PENDING | Physical vs genetic counts |
| test_get_interactions_limit | PENDING | max_results parameter |
| test_get_interactions_validation | PENDING | Gene symbol validation |
| test_api_key_missing | PENDING | Missing API key error |
| test_api_key_invalid | PENDING | Invalid API key error |
| test_error_recovery | PENDING | Error envelope format |

**Total: 0/10 integration tests (scaffolded, pending BIOGRID_API_KEY configuration)**

## Dependencies

- **BIOGRID_API_KEY**: Required environment variable
  - Free registration: https://webservice.thebiogrid.org/
  - Set in .env file or environment

## Cross-References

- **ADR-001**: Architecture Decision Record for Life Sciences MCP
- **Constitution**: Principles I (Async-First), II (Fuzzy-to-Fact), III (Schema Determinism)
- **Linear Issue**: AGE-75 (BioGRID Tier 1)
