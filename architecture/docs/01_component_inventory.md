# Component Inventory

## Overview

This document provides a comprehensive inventory of all components in the Life Sciences MCP codebase, excluding analysis framework directories (ra_orchestrators, ra_agents, ra_tools, ra_output) and virtual environment (.venv).

**Total Code Statistics (Main Project)**:
- Client Layer: 8,162 lines across 14 client modules
- Model Layer: 3,403 lines across 18 model modules
- Server Layer: 2,191 lines across 13 server modules

---

## Public API

The Life Sciences MCP exposes a comprehensive public API through FastMCP servers and Python client libraries.

### 1. Main Package Interface

**File**: `src/lifesciences_mcp/__init__.py` (Lines 1-99)

**Purpose**: Primary public API entry point for the Life Sciences MCP package.

**Public Exports**:
- **Clients** (Lines 42-53):
  - `ChEMBLClient` - Compound and bioactivity data
  - `ClinicalTrialsClient` - Clinical trial search and details
  - `DrugBankClient` - Drug and drug target information
  - `HGNCClient` - Gene nomenclature and symbol resolution
  - `IUPHARClient` - Pharmacological ligands and targets
  - `LifeSciencesClient` - Base client class
  - `OpenTargetsClient` - Target-disease associations
  - `PubChemClient` - Chemical compound data
  - `UniProtClient` - Protein sequence and annotation
  - `WikiPathwaysClient` - Biological pathway database

- **Models** (Lines 54-70):
  - `Compound`, `CompoundSearchCandidate` - ChEMBL compound models
  - `CrossReferences` - Cross-database identifier registry
  - `ErrorEnvelope` - Standard error response wrapper
  - `Gene` - HGNC gene model with cross-references
  - `Ligand`, `LigandSearchCandidate` - IUPHAR ligand models
  - `PaginationEnvelope` - Standard pagination wrapper
  - `PharmacologicalTarget`, `PharmacologicalTargetSearchCandidate` - IUPHAR target models
  - `Protein`, `ProteinSearchCandidate` - UniProt protein models
  - `PubChemCompound`, `PubChemSearchCandidate` - PubChem compound models
  - `SearchCandidate` - Generic search result model

**Usage Pattern**:
```python
from lifesciences_mcp import HGNCClient, Gene, PaginationEnvelope

async with HGNCClient() as client:
    result = await client.search_genes("BRCA1")
```

---

### 2. Client Package (`lifesciences_mcp.clients`)

**File**: `src/lifesciences_mcp/clients/__init__.py` (Lines 1-55)

#### 2.1 Base Client

**File**: `src/lifesciences_mcp/clients/base.py` (Lines 1-66)

**Class**: `LifeSciencesClient` (Line 16)

**Purpose**: Base async HTTP client providing connection pooling and common HTTP functionality.

**Public Methods**:
- `__init__(base_url, timeout=30.0, max_connections=10)` (Lines 23-39) - Initialize client with connection settings
- `close()` (Lines 56-60) - Close HTTP client and cleanup resources
- `_get_client()` (Lines 41-54) - Get or create async HTTP client (internal but used by subclasses)
- `_get(path, **kwargs)` (Lines 62-65) - Make GET request (internal but used by subclasses)

**Design Pattern**: Connection pooling with httpx.AsyncClient

---

#### 2.2 HGNC Client (Gene Nomenclature)

**File**: `src/lifesciences_mcp/clients/hgnc.py` (Lines 1-353)

**Class**: `HGNCClient` (Line 29)

**Purpose**: HGNC REST API client implementing Fuzzy-to-Fact protocol for gene symbol resolution.

**Public Methods**:
- `__aenter__()` (Line 52) - Context manager entry
- `__aexit__()` (Line 56) - Context manager exit
- `search_genes(query, slim=False, cursor=None, page_size=50)` (Lines 110-248) - Fuzzy search for genes by name/symbol/alias
- `get_gene(hgnc_id)` (Lines 273-331) - Get complete gene record by HGNC CURIE

**Private Methods**:
- `_rate_limited_get(path)` (Lines 62-108) - Rate-limited GET with exponential backoff
- `_search_by_alias(query)` (Lines 255-271) - Search by alias_symbol field
- `_build_cross_references(doc)` (Lines 333-344) - Map HGNC response to CrossReferences model
- `_extract_omim(omim_value)` (Lines 346-352) - Extract OMIM ID from HGNC response

**Rate Limiting**: 10 requests/second with exponential backoff on 429/403/503

---

#### 2.3 UniProt Client (Protein Data)

**File**: `src/lifesciences_mcp/clients/uniprot.py` (Lines 1-400+)

**Class**: `UniProtClient` (Line 29)

**Purpose**: UniProt REST API client for protein sequence and annotation data.

**Public Methods**:
- `__aenter__()` (Line 55) - Context manager entry
- `__aexit__()` (Line 59) - Context manager exit
- `search_proteins(query, reviewed=None, organism=None, cursor=None, page_size=25)` (Lines 170-312) - Search proteins
- `get_protein(uniprot_id, slim=False)` (Lines 314-399) - Get complete protein record

**Private Methods**:
- `_rate_limited_get(path, **kwargs)` (Lines 65-168) - Rate-limited GET with retry logic

**Rate Limiting**: 1 request/second with exponential backoff

---

#### 2.4 ChEMBL Client (Compound Data)

**File**: `src/lifesciences_mcp/clients/chembl.py` (Lines 1-680)

**Class**: `ChEMBLClient` (Line 40)

**Purpose**: ChEMBL REST API client for compound and bioactivity data using ChEMBL Web Services SDK.

**Public Methods**:
- `search_compounds(query, slim=False, cursor=None, page_size=20)` (Lines 453-517) - Search compounds by name/synonym
- `get_compound(chembl_id, slim=False)` (Lines 519-586) - Get compound by ChEMBL ID
- `get_compounds_batch(chembl_ids, slim=False)` (Lines 588-673) - Batch fetch compounds
- `close()` (Lines 675-679) - Close client (no-op for SDK client)

**Private Methods**:
- `_rate_limited_sdk_call(sdk_func)` (Lines 94-123) - Rate-limited SDK call wrapper
- `_sdk_call_with_backoff(sdk_func)` (Lines 125-450) - SDK call with exponential backoff

**Rate Limiting**: 5 requests/second

---

#### 2.5 Open Targets Client (Target-Disease Associations)

**File**: `src/lifesciences_mcp/clients/opentargets.py` (Lines 1-730)

**Class**: `OpenTargetsClient` (Line 123)

**Purpose**: Open Targets Platform GraphQL API client for target-disease associations.

**Public Methods**:
- `__aenter__()` (Line 140) - Context manager entry
- `__aexit__()` (Line 144) - Context manager exit
- `search_targets(query, cursor=None, page_size=10)` (Lines 437-519) - Search targets by gene symbol/name
- `get_target(ensembl_id, slim=False)` (Lines 521-592) - Get target details by Ensembl ID
- `get_associations(ensembl_id, cursor=None, page_size=10)` (Lines 594-730) - Get disease associations for target

**Private Methods**:
- `_execute_graphql(query, variables)` (Lines 184-206) - Execute GraphQL query
- `_rate_limited_graphql(query, variables)` (Lines 208-434) - Rate-limited GraphQL with retry

**Rate Limiting**: 10 requests/second

---

#### 2.6 STRING Client (Protein Interactions)

**File**: `src/lifesciences_mcp/clients/string.py` (Lines 1-350+)

**Class**: `STRINGClient` (Line 36)

**Purpose**: STRING database client for protein-protein interaction networks.

**Public Methods**:
- `__aenter__()` (Line 65) - Context manager entry
- `__aexit__()` (Line 69) - Context manager exit
- `search_proteins(query, species=9606, limit=25)` (Lines 117-225) - Search proteins in STRING
- `get_interactions(string_ids, species=9606, required_score=400, limit=100)` (Lines 227-350) - Get protein interactions

**Private Methods**:
- `_rate_limited_get(path, params)` (Lines 75-115) - Rate-limited GET request

**Rate Limiting**: 1 request/second

---

#### 2.7 BioGRID Client (Genetic Interactions)

**File**: `src/lifesciences_mcp/clients/biogrid.py` (Lines 1-270)

**Class**: `BioGridClient` (Line 40)

**Purpose**: BioGRID REST API client for genetic and protein interaction data.

**Public Methods**:
- `search_genes(query, species="Homo sapiens", limit=25)` (Lines 120-173) - Search genes in BioGRID
- `get_interactions(gene_id, species="Homo sapiens", limit=100)` (Lines 175-270) - Get interactions for gene

**Private Methods**:
- `_rate_limited_get(url, params)` (Lines 70-118) - Rate-limited GET with API key

**Rate Limiting**: 5 requests/second with API key requirement

---

#### 2.8 Ensembl Client (Genomic Data)

**File**: `src/lifesciences_mcp/clients/ensembl.py` (Lines 1-600+)

**Class**: `EnsemblClient` (Line 57)

**Purpose**: Ensembl REST API client for genomic data (genes, transcripts).

**Public Methods**:
- `__aenter__()` (Line 79) - Context manager entry
- `__aexit__()` (Line 83) - Context manager exit
- `search_genes(query, species="human", cursor=None, page_size=25)` (Lines 223-366) - Search genes by symbol
- `get_gene(ensembl_id, slim=False)` (Lines 385-492) - Get gene details by Ensembl ID
- `get_transcript(transcript_id)` (Lines 494-600) - Get transcript details

**Private Methods**:
- `_rate_limited_get(path, params=None)` (Lines 101-221) - Rate-limited GET with retry
- `_get_gene_details(gene_id)` (Lines 368-383) - Fetch detailed gene information

**Rate Limiting**: 15 requests/second

---

#### 2.9 Entrez Client (NCBI Gene)

**File**: `src/lifesciences_mcp/clients/entrez.py` (Lines 1-730)

**Class**: `EntrezClient` (Line 40)

**Purpose**: NCBI Entrez E-utilities client for gene database access.

**Public Methods**:
- `__aenter__()` (Line 67) - Context manager entry
- `__aexit__()` (Line 71) - Context manager exit
- `search_genes(query, cursor=None, page_size=20)` (Lines 476-602) - Search genes in NCBI Gene
- `get_gene(entrez_id)` (Lines 604-691) - Get gene record by Entrez ID
- `get_pubmed_links(entrez_id, limit=10)` (Lines 693-730) - Get PubMed citations for gene

**Private Methods**:
- `_rate_limited_get(url, params)` (Lines 77-153) - Rate-limited GET
- `_esearch(query, retmax, retstart)` (Lines 155-199) - E-utilities search
- `_esummary(ids)` (Lines 201-218) - E-utilities summary
- `_efetch(gene_id)` (Lines 220-237) - E-utilities fetch
- `_elink(gene_id)` (Lines 239-474) - E-utilities link

**Rate Limiting**: 3 requests/second (NCBI guidelines)

---

#### 2.10 PubChem Client (Chemical Compounds)

**File**: `src/lifesciences_mcp/clients/pubchem.py` (Lines 1-800)

**Class**: `PubChemClient` (Line 31)

**Purpose**: PubChem PUG REST API client for chemical compound data.

**Public Methods**:
- `search_compounds(query, cursor=None, page_size=20)` (Lines 411-510) - Search compounds by name
- `get_compound(pubchem_id, slim=False)` (Lines 693-800) - Get compound by PubChem CID

**Private Methods**:
- `_rate_limited_get(url, **kwargs)` (Lines 65-113) - Rate-limited GET
- `_request_with_backoff(url, **kwargs)` (Lines 115-257) - Request with exponential backoff
- `_search_by_name(name)` (Lines 259-310) - Search compounds by name
- `_get_compound_properties(cids)` (Lines 312-409) - Get compound properties batch
- `_get_compound_synonyms(cid)` (Lines 512-565) - Get compound synonyms
- `_get_compound_xrefs(cid)` (Lines 567-691) - Get compound cross-references

**Rate Limiting**: 5 requests/second

---

#### 2.11 IUPHAR Client (Pharmacology)

**File**: `src/lifesciences_mcp/clients/iuphar.py` (Lines 1-720)

**Class**: `IUPHARClient` (Line 26)

**Purpose**: IUPHAR/GtoPdb REST API client for pharmacological ligands and targets.

**Public Methods**:
- `search_ligands(query, page_size=25)` (Lines 305-371) - Search ligands by name
- `get_ligand(iuphar_id)` (Lines 415-488) - Get ligand details by IUPHAR ID
- `search_targets(query, page_size=25)` (Lines 527-597) - Search pharmacological targets
- `get_target(iuphar_id)` (Lines 641-720) - Get target details by IUPHAR ID

**Private Methods**:
- `_rate_limited_get(path, retries=0, **kwargs)` (Lines 47-243) - Rate-limited GET with retry
- `_fetch_ligands(search_term)` (Lines 245-280) - Fetch ligands from API
- `_fetch_ligand_synonyms(ligand_id)` (Lines 282-303) - Fetch ligand synonyms
- `_fetch_ligand_detail(ligand_id)` (Lines 373-393) - Fetch ligand details
- `_fetch_ligand_db_links(ligand_id)` (Lines 395-413) - Fetch ligand database links
- `_fetch_targets(search_term)` (Lines 490-525) - Fetch targets from API
- `_fetch_target_detail(target_id)` (Lines 599-619) - Fetch target details
- `_fetch_target_db_links(target_id)` (Lines 621-639) - Fetch target database links

**Rate Limiting**: 10 requests/second

---

#### 2.12 WikiPathways Client (Biological Pathways)

**File**: `src/lifesciences_mcp/clients/wikipathways.py` (Lines 1-800)

**Class**: `WikiPathwaysClient` (Line 41)

**Purpose**: WikiPathways REST API client for biological pathway data.

**Public Methods**:
- `search_pathways(query, organism=None, cursor=None, page_size=25)` (Lines 278-407) - Search pathways
- `get_pathway(pathway_id)` (Lines 409-537) - Get pathway details by WikiPathways ID
- `get_pathways_for_gene(gene_symbol, organism=None, cursor=None, page_size=25)` (Lines 539-673) - Find pathways containing gene
- `get_pathway_components(pathway_id)` (Lines 675-800) - Get pathway components (data nodes, interactions)

**Private Methods**:
- `_enforce_rate_limit()` (Lines 68-88) - Enforce rate limit
- `_request_with_retry(method, url, retries=0, **kwargs)` (Lines 90-185) - Request with exponential backoff
- `_fetch_cross_references_bulk()` (Lines 187-276) - Bulk fetch cross-references

**Rate Limiting**: 10 requests/second

---

#### 2.13 ClinicalTrials Client (Clinical Trials)

**File**: `src/lifesciences_mcp/clients/clinicaltrials.py` (Lines 1-620)

**Class**: `ClinicalTrialsClient` (Line 28)

**Purpose**: ClinicalTrials.gov API v2 client for clinical trial data.

**Public Methods**:
- `search_trials(query, cursor=None, page_size=20)` (Lines 200-316) - Search clinical trials
- `get_trial(nct_id)` (Lines 318-514) - Get trial details by NCT ID
- `get_trial_locations(nct_id)` (Lines 516-620) - Get trial locations

**Private Methods**:
- `_rate_limited_request(method, url, **kwargs)` (Lines 99-198) - Rate-limited HTTP request

**Rate Limiting**: 10 requests/second

---

#### 2.14 DrugBank Client (Drug Data)

**File**: `src/lifesciences_mcp/clients/drugbank.py` (Lines 1-850)

**Class**: `DrugBankClient` (Line 55)

**Purpose**: DrugBank REST API client for drug and drug target information (requires commercial API key).

**Public Methods**:
- `__aenter__()` (Line 87) - Context manager entry
- `__aexit__()` (Line 91) - Context manager exit
- `search_drugs(query, slim=False, cursor=None, page_size=20)` (Lines 618-731) - Search drugs
- `get_drug(drugbank_id, slim=False)` (Lines 733-850) - Get drug by DrugBank ID

**Private Methods**:
- `_rate_limited_get(url, params=None)` (Lines 140-616) - Rate-limited GET with API key

**Rate Limiting**: 30 requests/second (commercial tier)

---

### 3. Model Package (`lifesciences_mcp.models`)

**File**: `src/lifesciences_mcp/models/__init__.py` (Lines 1-140)

All models follow Pydantic BaseModel with validation and serialization.

#### 3.1 Envelope Models (Standard Wrappers)

**File**: `src/lifesciences_mcp/models/envelopes.py` (Lines 1-145)

**Classes**:
- `ErrorCode` (Line 16) - Enum of standard error codes
- `ErrorDetail` (Line 27) - Error detail with recovery hints
- `ErrorEnvelope` (Line 36) - Standard error response wrapper
  - Factory methods: `unresolved_entity()`, `entity_not_found()`, `ambiguous_query()`, `rate_limited()`, `upstream_error()`
- `Pagination` (Line 111) - Pagination metadata
- `PaginationEnvelope[T]` (Line 119) - Generic pagination wrapper
  - Factory method: `create(items, cursor, total_count, page_size)`

**Purpose**: Canonical response envelopes per ADR-001 Section 8.

---

#### 3.2 Gene Models

**File**: `src/lifesciences_mcp/models/gene.py` (Lines 1-215)

**Classes**:
- `CrossReferences` (Line 27) - External database identifiers (22-key registry)
  - Fields: ensembl_gene, ensembl_transcript, uniprot, entrez, refseq, hgnc, omim, orphanet, mondo, efo, chembl, drugbank, pubchem_compound, pubchem_substance, kegg, kegg_pathway, string, biogrid, stitch, iuphar, pdb
- `SearchCandidate` (Line 145) - Lightweight gene search result
  - Fields: id (HGNC CURIE), symbol, name, score
- `Gene` (Line 166) - Complete gene record
  - Fields: id, symbol, name, status, locus_type, locus_group, location, alias_symbols, alias_names, prev_symbols, prev_names, cross_references

**Constants**:
- `HGNC_CURIE_PATTERN` (Line 12) - Regex for HGNC:NNNNN format

---

#### 3.3 Protein Models

**File**: `src/lifesciences_mcp/models/protein.py` (Lines 1-100)

**Classes**:
- `ProteinSearchCandidate` (Line 19) - Lightweight protein search result
  - Fields: id, name, organism, gene_name, score
- `Protein` (Line 44) - Complete protein record
  - Fields: id, name, organism, gene_name, sequence, length, function, subcellular_location, cross_references

---

#### 3.4 Compound Models

**File**: `src/lifesciences_mcp/models/compound.py` (Lines 1-150)

**Classes**:
- `CompoundSearchCandidate` (Line 19) - Lightweight compound search result
  - Fields: id, name, type, max_phase, score
- `Compound` (Line 73) - Complete compound record from ChEMBL
  - Fields: id, name, type, synonyms, smiles, inchi, inchi_key, molecular_formula, molecular_weight, max_phase, first_approval, indication_class, cross_references

---

#### 3.5 PubChem Compound Models

**File**: `src/lifesciences_mcp/models/pubchem_compound.py` (Lines 1-200)

**Classes**:
- `PubChemSearchCandidate` (Line 16) - Lightweight PubChem search result
  - Fields: id, title, score
- `PubChemCompound` (Line 79) - Complete PubChem compound record
  - Fields: id, title, iupac_name, smiles, inchi, inchi_key, molecular_formula, molecular_weight, synonyms, cross_references

**Constants**:
- `PUBCHEM_CURIE_PATTERN` (Line 16) - Regex for PubChem CID format

---

#### 3.6 Drug Models

**File**: `src/lifesciences_mcp/models/drug.py` (Lines 1-250)

**Classes**:
- `DrugCrossReferences` (Line 15) - Drug-specific cross-references
  - Fields: chembl, pubchem_compound, pubchem_substance, kegg_drug, pharmgkb, rxnorm, atc_codes
- `DrugSearchCandidate` (Line 72) - Lightweight drug search result
  - Fields: id, name, type, state, score
- `Drug` (Line 132) - Complete drug record from DrugBank
  - Fields: id, name, type, description, cas_number, state, indication, pharmacodynamics, mechanism, toxicity, metabolism, absorption, half_life, protein_binding, route_of_elimination, volume_distribution, clearance, cross_references

---

#### 3.7 Pharmacology Models (IUPHAR)

**File**: `src/lifesciences_mcp/models/pharmacology.py` (Lines 1-250)

**Classes**:
- `LigandSearchCandidate` (Line 33) - Lightweight ligand search result
  - Fields: id, name, type, species, score
- `Ligand` (Line 61) - Complete ligand record
  - Fields: id, name, abbreviation, type, iupac_name, inn, synonyms, species, radioactive, labelled, approved, withdrawn, approval_source, subunit_ids, complex_ids, prodrug_ids, active_ids, comments, cross_references
- `TargetSearchCandidate` (Line 141) - Lightweight target search result
  - Fields: id, name, type, family, score
- `Target` (Line 169) - Complete pharmacological target record
  - Fields: id, name, abbreviation, systematic_name, type, family, subunits, comments, cross_references

---

#### 3.8 Target Models (Open Targets)

**File**: `src/lifesciences_mcp/models/target.py` (Lines 1-250)

**Classes**:
- `TargetSearchCandidate` (Line 24) - Lightweight target search result
  - Fields: id, approved_symbol, approved_name, biotype, score
- `Target` (Line 76) - Complete target record from Open Targets
  - Fields: id, approved_symbol, approved_name, biotype, description, chromosome, tss, function_descriptions, subcellular_locations, pathways, protein_ids, cross_references
- `Association` (Line 164) - Target-disease association
  - Fields: disease_id, disease_name, therapeutic_areas, overall_score, genetic_association, somatic_mutation, known_drug, affected_pathway, literature, animal_model, rna_expression

---

#### 3.9 Interaction Models

**File**: `src/lifesciences_mcp/models/interaction.py` (Lines 1-300)

**Classes**:
- `InteractionSearchCandidate` (Line 25) - Lightweight interaction search result
  - Fields: id, name, organism, annotation, score
- `EvidenceScores` (Line 82) - STRING evidence scores
  - Fields: neighborhood, fusion, cooccurence, coexpression, experimental, database, textmining, combined_score
- `Interaction` (Line 154) - Protein-protein interaction
  - Fields: protein_a, protein_b, protein_a_name, protein_b_name, combined_score, evidence_scores
- `InteractionCrossReferences` (Line 212) - Interaction-specific cross-references
  - Fields: string, biogrid
- `InteractionNetwork` (Line 245) - Network of interactions
  - Fields: query_proteins, interactions, total_count, cross_references

---

#### 3.10 BioGRID Models

**File**: `src/lifesciences_mcp/models/biogrid.py` (Lines 1-100)

**Classes**:
- `BioGridSearchCandidate` (Line 17) - Lightweight gene search result
  - Fields: id, symbol, organism, score
- `GeneticInteraction` (Line 34) - Genetic or protein interaction
  - Fields: biogrid_id, gene_a, gene_b, gene_a_symbol, gene_b_symbol, experimental_system, pubmed_id, throughput, score
- `BioGridCrossReferences` (Line 62) - BioGRID-specific cross-references
  - Fields: entrez_gene_a, entrez_gene_b
- `InteractionResult` (Line 74) - Interaction query result
  - Fields: query_gene, interactions, total_count, cross_references

---

#### 3.11 Ensembl Models

**File**: `src/lifesciences_mcp/models/ensembl.py` (Lines 1-280)

**Classes**:
- `EnsemblCrossReferences` (Line 35) - Ensembl-specific cross-references
  - Fields: ensembl_gene, ensembl_transcript, hgnc, entrez, uniprot
- `GeneSearchCandidate` (Line 117) - Lightweight gene search result
  - Fields: id, display_name, description, biotype, species, score
- `EnsemblGene` (Line 149) - Complete Ensembl gene record
  - Fields: id, display_name, description, biotype, species, assembly_name, seq_region_name, start, end, strand, version, canonical_transcript, transcripts, cross_references
- `EnsemblTranscript` (Line 212) - Ensembl transcript record
  - Fields: id, display_name, biotype, species, assembly_name, seq_region_name, start, end, strand, version, parent_gene, is_canonical, translation_id, protein_sequence

---

#### 3.12 Entrez Models

**File**: `src/lifesciences_mcp/models/entrez.py` (Lines 1-250)

**Classes**:
- `GeneSearchCandidate` (Line 23) - Lightweight gene search result
  - Fields: id, symbol, description, organism, chromosome, map_location, gene_type, score
- `EntrezCrossReferences` (Line 96) - Entrez-specific cross-references
  - Fields: entrez, hgnc, ensembl_gene, uniprot, omim, mim
- `EntrezGene` (Line 177) - Complete Entrez gene record
  - Fields: id, symbol, description, organism, chromosome, map_location, gene_type, aliases, summary, nomenclature_symbol, nomenclature_name, nomenclature_status, cross_references

**Constants**:
- `NCBI_GENE_CURIE_PATTERN` (Line 23) - Regex for NCBIGene:NNNNN format

---

#### 3.13 Pathway Models

**File**: `src/lifesciences_mcp/models/pathway.py` (Lines 1-150)

**Classes**:
- `RevisionMetadata` (Line 16) - Pathway revision information
  - Fields: revision, last_edited, edited_by, description
- `ComponentCounts` (Line 27) - Pathway component statistics
  - Fields: data_nodes, interactions, graphical_lines, labels, shapes, groups
- `Pathway` (Line 40) - Complete pathway record
  - Fields: id, name, organism, description, url, last_edited, revision, authors, ontology_tags, component_counts
- `PathwaySearchCandidate` (Line 112) - Lightweight pathway search result
  - Fields: id, name, organism, revision, score

---

#### 3.14 Pathway Component Models

**File**: `src/lifesciences_mcp/models/pathway_components.py` (Lines 1-200)

**Classes**:
- `DataNode` (Line 19) - Pathway data node (gene, protein, metabolite, etc.)
  - Fields: id, text_label, type, xref_id, xref_datasource, graphics_center_x, graphics_center_y, graphics_width, graphics_height
- `Interaction` (Line 86) - Pathway interaction edge
  - Fields: id, type, source, target, arrow_head
- `PathwayComponents` (Line 125) - Complete pathway component data
  - Fields: pathway_id, data_nodes, interactions, total_data_nodes, total_interactions

---

#### 3.15 Trial Models

**File**: `src/lifesciences_mcp/models/trial.py` (Lines 1-180)

**Classes**:
- `TrialSearchCandidate` (Line 13) - Lightweight trial search result
  - Fields: nct_id, title, status, phase, enrollment, start_date, score
- `TrialProtocol` (Line 40) - Trial protocol information
  - Fields: brief_title, official_title, brief_summary, detailed_description, study_type, phases, enrollment, allocation, intervention_model, primary_purpose, masking
- `EligibilityCriteria` (Line 60) - Trial eligibility
  - Fields: sex, minimum_age, maximum_age, healthy_volunteers, criteria
- `Outcome` (Line 74) - Trial outcome measure
  - Fields: type, measure, time_frame, description
- `Sponsor` (Line 84) - Trial sponsor information
  - Fields: name, sponsor_class
- `Trial` (Line 91) - Complete clinical trial record
  - Fields: nct_id, protocol, conditions, interventions, start_date, completion_date, last_update_date, overall_status, eligibility, outcomes, sponsors

---

#### 3.16 Trial Location Models

**File**: `src/lifesciences_mcp/models/trial_location.py` (Lines 1-50)

**Classes**:
- `TrialLocation` (Line 10) - Clinical trial site location
  - Fields: facility, city, state, zip_code, country, status, contact_name, contact_phone, contact_email

---

#### 3.17 Provenance Models

**File**: `src/lifesciences_mcp/models/provenance.py` (Lines 1-180)

**Classes**:
- `Provenance` (Line 35) - Data provenance metadata
  - Fields: source, query, retrieved_at, version, upstream_id, cursor, method
- `MCPClaim` (Line 94) - MCP tool call claim
  - Fields: tool_name, parameters, provenance
- `BatchProvenance` (Line 137) - Batch operation provenance
  - Fields: source, retrieved_at, batch_size, successful_ids, failed_ids

---

### 4. Server Package (`lifesciences_mcp.servers`)

All servers use FastMCP framework and expose MCP tools via JSON-RPC.

**File**: `src/lifesciences_mcp/servers/__init__.py` (Lines 1-2)

#### 4.1 Gateway Server (Unified Access)

**File**: `src/lifesciences_mcp/servers/gateway.py` (Lines 1-116)

**Purpose**: Unified MCP server composing all 13 individual servers (excluding DrugBank).

**MCP Instance**: `mcp = FastMCP("Life Sciences MCP Gateway")` (Line 49)

**Mounted Servers** (Lines 52-109):
- `hgnc` - Tools: hgnc_search_genes, hgnc_get_gene
- `uniprot` - Tools: uniprot_search_proteins, uniprot_get_protein
- `chembl` - Tools: chembl_search_compounds, chembl_get_compound, chembl_get_compounds_batch
- `opentargets` - Tools: opentargets_search_targets, opentargets_get_target, opentargets_get_associations
- `string` - Tools: string_search_proteins, string_get_interactions, string_get_network_image_url
- `biogrid` - Tools: biogrid_search_genes, biogrid_get_interactions
- `ensembl` - Tools: ensembl_search_genes, ensembl_get_gene, ensembl_get_transcript
- `entrez` - Tools: entrez_search_genes, entrez_get_gene, entrez_get_pubmed_links
- `pubchem` - Tools: pubchem_search_compounds, pubchem_get_compound
- `iuphar` - Tools: iuphar_search_targets, iuphar_get_target, iuphar_search_ligands, iuphar_get_ligand
- `wikipathways` - Tools: wikipathways_search_pathways, wikipathways_get_pathway, wikipathways_get_pathways_for_gene, wikipathways_get_pathway_components
- `clinicaltrials` - Tools: clinicaltrials_search_trials, clinicaltrials_get_trial, clinicaltrials_get_trial_locations

**Usage**: `uv run fastmcp run src/lifesciences_mcp/servers/gateway.py`

**Cloud Deployment**: FastMCP Cloud endpoint at `https://lifesciences.fastmcp.app/mcp`

---

#### 4.2 Individual MCP Servers

Each server follows the same pattern:
1. Initialize FastMCP instance
2. Define shared client getter
3. Expose tools via `@mcp.tool` decorators

**HGNC Server**: `src/lifesciences_mcp/servers/hgnc.py` (Lines 1-86)
- Tools: `search_genes(query, slim, cursor, page_size)`, `get_gene(hgnc_id)`

**UniProt Server**: `src/lifesciences_mcp/servers/uniprot.py` (Lines 1-100)
- Tools: `search_proteins(query, reviewed, organism, cursor, page_size)`, `get_protein(uniprot_id, slim)`

**ChEMBL Server**: `src/lifesciences_mcp/servers/chembl.py` (Lines 1-130)
- Tools: `search_compounds(query, slim, cursor, page_size)`, `get_compound(chembl_id, slim)`, `get_compounds_batch(chembl_ids, slim)`

**Open Targets Server**: `src/lifesciences_mcp/servers/opentargets.py` (Lines 1-130)
- Tools: `search_targets(query, cursor, page_size)`, `get_target(ensembl_id, slim)`, `get_associations(ensembl_id, cursor, page_size)`

**STRING Server**: `src/lifesciences_mcp/servers/string.py` (Lines 1-150)
- Tools: `search_proteins(query, species, limit)`, `get_interactions(string_ids, species, required_score, limit)`, `get_network_image_url(string_ids, species)`

**BioGRID Server**: `src/lifesciences_mcp/servers/biogrid.py` (Lines 1-100)
- Tools: `search_genes(query, species, limit)`, `get_interactions(gene_id, species, limit)`

**Ensembl Server**: `src/lifesciences_mcp/servers/ensembl.py` (Lines 1-180)
- Tools: `search_genes(query, species, cursor, page_size)`, `get_gene(ensembl_id, slim)`, `get_transcript(transcript_id)`

**Entrez Server**: `src/lifesciences_mcp/servers/entrez.py` (Lines 1-160)
- Tools: `search_genes(query, cursor, page_size)`, `get_gene(entrez_id)`, `get_pubmed_links(entrez_id, limit)`

**PubChem Server**: `src/lifesciences_mcp/servers/pubchem.py` (Lines 1-150)
- Tools: `search_compounds(query, cursor, page_size)`, `get_compound(pubchem_id, slim)`

**IUPHAR Server**: `src/lifesciences_mcp/servers/iuphar.py` (Lines 1-400)
- Tools: `search_ligands(query, page_size)`, `get_ligand(iuphar_id)`, `search_targets(query, page_size)`, `get_target(iuphar_id)`

**WikiPathways Server**: `src/lifesciences_mcp/servers/wikipathways.py` (Lines 1-180)
- Tools: `search_pathways(query, organism, cursor, page_size)`, `get_pathway(pathway_id)`, `get_pathways_for_gene(gene_symbol, organism, cursor, page_size)`, `get_pathway_components(pathway_id)`

**ClinicalTrials Server**: `src/lifesciences_mcp/servers/clinicaltrials.py` (Lines 1-300)
- Tools: `search_trials(query, cursor, page_size)`, `get_trial(nct_id)`, `get_trial_locations(nct_id)`

**DrugBank Server**: `src/lifesciences_mcp/servers/drugbank.py` (Lines 1-100)
- Tools: `search_drugs(query, slim, cursor, page_size)`, `get_drug(drugbank_id, slim)`
- Note: Requires commercial API key

---

### 5. Experimental Agent Layer

**File**: `src/lifesciences_agent/__init__.py` (Line 1)

**Note**: This file is empty (1 line), indicating the agent layer is experimental/placeholder.

#### 5.1 Unified Search Aggregator

**File**: `src/lifesciences_agent/aggregator.py` (Lines 1-74)

**Classes**:
- `AggregatedResult` (Line 10) - Aggregated search results wrapper
  - Methods: `model_dump_json(exclude_none)`
- `UnifiedSearch` (Line 18) - Experimental multi-database search orchestrator

**Purpose**: Orchestrates queries across HGNC, UniProt, and Open Targets for improved entity grounding.

**Public Methods**:
- `__init__()` (Lines 25-28) - Initialize clients
- `search(query, limit=10)` (Lines 30-73) - Search and re-rank across databases

**Re-ranking Logic**: Exact symbol match > Known alias > Score (with boosting for common aliases like "p53" -> "TP53")

**Status**: Experimental prototype, not part of main API surface

---

## Internal Implementation

### 1. Tools Package

**File**: `src/lifesciences_mcp/tools/__init__.py` (Line 1)

**Status**: Empty file (1 line) - placeholder for future tooling

---

### 2. Test Infrastructure

#### 2.1 Test Configuration

**File**: `tests/conftest.py`

**Purpose**: Pytest configuration and shared fixtures

#### 2.2 Test Fixtures

**File**: `tests/fixtures/tier1_string_data.py`

**Purpose**: Fixture data for STRING database tests

#### 2.3 Test Suites

**Unit Tests** (`tests/unit/`):
- test_chembl_client.py - ChEMBL client unit tests
- test_chembl_models.py - ChEMBL model validation tests
- test_clinicaltrials_client.py - ClinicalTrials client unit tests
- test_drugbank_client.py - DrugBank client unit tests
- test_drugbank_models.py - DrugBank model validation tests
- test_ensembl_client.py - Ensembl client unit tests
- test_ensembl_models.py - Ensembl model validation tests
- test_entrez_client.py - Entrez client unit tests
- test_entrez_models.py - Entrez model validation tests
- test_error_envelopes.py - Error envelope tests
- test_iuphar_client.py - IUPHAR client unit tests
- test_models.py - Generic model tests
- test_pharmacology_models.py - Pharmacology model validation tests
- test_provenance_models.py - Provenance model tests
- test_pubchem_client.py - PubChem client unit tests
- test_pubchem_models.py - PubChem model validation tests
- test_trial_location_models.py - Trial location model tests
- test_trial_models.py - Trial model validation tests
- test_wikipathways_client.py - WikiPathways client unit tests
- test_wikipathways_models.py - WikiPathways model validation tests

**Integration Tests** (`tests/integration/`):
- test_biogrid_api.py - BioGRID API integration tests
- test_biogrid_performance.py - BioGRID performance tests
- test_chembl_api.py - ChEMBL API integration tests
- test_clinicaltrials_api.py - ClinicalTrials API integration tests
- test_competency_questions.py - Domain competency validation tests
- test_concurrency.py - Concurrent request handling tests
- test_drugbank_api.py - DrugBank API integration tests
- test_ensembl_api.py - Ensembl API integration tests
- test_entrez_api.py - Entrez API integration tests
- test_entrez_performance.py - Entrez performance tests
- test_error_recovery.py - Error handling and recovery tests
- test_gateway.py - Gateway server integration tests
- test_hgnc_api.py - HGNC API integration tests
- test_iuphar_api.py - IUPHAR API integration tests
- test_opentargets_api.py - Open Targets API integration tests
- test_performance.py - General performance tests
- test_pubchem_api.py - PubChem API integration tests
- test_string_api.py - STRING API integration tests
- test_string_performance.py - STRING performance tests
- test_uniprot_api.py - UniProt API integration tests
- test_wikipathways_api.py - WikiPathways API integration tests

**Gap Tests** (`tests/gaps/`):
- test_grounding_gap.py - Entity grounding improvement tests

**Manual Tests** (`tests/manual/`):
- test_ct_headers.py - ClinicalTrials HTTP header tests
- test_ct_headers2.py - ClinicalTrials HTTP header tests (variant)
- test_wikipathways_xref_format.py - WikiPathways cross-reference format tests
- verify_cloud_deployment.py - Cloud deployment verification

---

### 3. Scripts and Utilities

#### 3.1 Showcase Scripts

**File**: `scripts/showcase_nsclc.py`

**Purpose**: Original NSCLC (non-small cell lung cancer) use case demonstration

**File**: `scripts/showcase_nsclc_v2_fastmcp.py` (Lines 1-50+)

**Purpose**: Enhanced NSCLC showcase using FastMCP Cloud deployment via JSON-RPC

**Features**:
- KRAS targeting scenario
- EML4-ALK fusion scenario
- WikiPathways integration
- ClinicalTrials.gov integration
- MCP protocol (JSON-RPC 2.0) over HTTP

**MCP Endpoint**: `https://lifesciences.fastmcp.app/mcp`

**File**: `scripts/showcase_nsclc_v2_mcp.py`

**Purpose**: NSCLC showcase variant using MCP protocol

---

#### 3.2 Validation and Benchmark Scripts

**File**: `scripts/benchmark_value.py`

**Purpose**: Benchmark value and performance metrics

**File**: `scripts/validate_competency.py`

**Purpose**: Validate domain competency questions

**File**: `scripts/verify_chembl_v2.py`

**Purpose**: Verify ChEMBL v2 integration

**File**: `scripts/verify_swi_snf.py`

**Purpose**: Verify SWI/SNF complex pathway analysis

---

#### 3.3 Audit and Compliance

**File**: `docs/qa-audit-2026-01-03/audit_compliance.py`

**Purpose**: QA audit compliance checking

**File**: `tools/audit_compliance.py`

**Purpose**: Compliance audit tooling (duplicate/variant)

---

### 4. Claude Skills Integration

#### 4.1 Mermaid Diagram Optimizer Skill

**File**: `skills/mermaid-diagram-optimizer/skill.py` (Lines 1-50+)

**Purpose**: Reusable skill for optimizing Mermaid diagrams with progressive disclosure.

**Classes**:
- `DiagramSpec` (Line 14) - Diagram specification input
  - Fields: diagram_type, abstraction_level, entities, relationships, constraints, target_audience
- `DiagramResult` (Line 26) - Optimized diagram output
  - Fields: mermaid_code, narrative, metadata, next_steps
- `MermaidDiagramOptimizer` (Line 35) - Diagram optimization engine

**Methods**:
- `select_diagram_direction(diagram_type, abstraction_level)` (Lines 38-49) - Select optimal orientation

**Version**: 1.0.0

**Examples**: `skills/mermaid-diagram-optimizer/examples/`

---

#### 4.2 MCP Builder Skills

**File**: `.claude/.skills/mcp-builder/scripts/connections.py`

**Purpose**: MCP connection management utilities

**File**: `.claude/.skills/mcp-builder/scripts/evaluation.py`

**Purpose**: MCP evaluation and testing utilities

---

## Entry Points

### 1. Gateway Server (Primary Entry Point)

**File**: `src/lifesciences_mcp/servers/gateway.py`

**Entry Point**: Line 114-115
```python
if __name__ == "__main__":
    mcp.run()
```

**FastMCP Cloud Deployment**: `src/lifesciences_mcp/servers/gateway.py:mcp`

**Usage**:
```bash
# Local development
uv run fastmcp run src/lifesciences_mcp/servers/gateway.py

# Production endpoint
https://lifesciences.fastmcp.app/mcp
```

**Protocol**: JSON-RPC 2.0 over HTTP POST

**Available Tools**: 40+ tools across 13 data sources (see Section 4.1)

---

### 2. Individual Server Entry Points

Each server can be run independently:

**HGNC Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py
```

**UniProt Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/uniprot.py
```

**ChEMBL Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/chembl.py
```

**Open Targets Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/opentargets.py
```

**STRING Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/string.py
```

**BioGRID Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/biogrid.py
```

**Ensembl Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/ensembl.py
```

**Entrez Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/entrez.py
```

**PubChem Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/pubchem.py
```

**IUPHAR Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/iuphar.py
```

**WikiPathways Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/wikipathways.py
```

**ClinicalTrials Server**:
```bash
uv run fastmcp run src/lifesciences_mcp/servers/clinicaltrials.py
```

**DrugBank Server** (requires API key):
```bash
export DRUGBANK_API_KEY=your_key_here
uv run fastmcp run src/lifesciences_mcp/servers/drugbank.py
```

---

### 3. Python Client Library Entry Points

**Direct Client Usage** (without MCP server):

```python
# HGNC client example
from lifesciences_mcp import HGNCClient

async with HGNCClient() as client:
    # Fuzzy search
    results = await client.search_genes("BRCA1")

    # Strict lookup
    gene = await client.get_gene("HGNC:1100")
```

```python
# ChEMBL client example
from lifesciences_mcp import ChEMBLClient

async with ChEMBLClient() as client:
    # Search compounds
    results = await client.search_compounds("aspirin")

    # Get compound details
    compound = await client.get_compound("CHEMBL25")
```

```python
# Multi-client orchestration
from lifesciences_mcp import HGNCClient, UniProtClient, OpenTargetsClient

async with HGNCClient() as hgnc, \
           UniProtClient() as uniprot, \
           OpenTargetsClient() as ot:

    # Resolve gene
    gene_results = await hgnc.search_genes("TP53")
    hgnc_id = gene_results.items[0].id
    gene = await hgnc.get_gene(hgnc_id)

    # Get protein
    uniprot_id = gene.cross_references.uniprot[0]
    protein = await uniprot.get_protein(uniprot_id)

    # Get disease associations
    ensembl_id = gene.cross_references.ensembl_gene
    associations = await ot.get_associations(ensembl_id)
```

---

### 4. Showcase Script Entry Points

**NSCLC Showcase (FastMCP Cloud)**:

**File**: `scripts/showcase_nsclc_v2_fastmcp.py`

**Usage**:
```bash
# Point to cloud endpoint
export MCP_ENDPOINT=https://lifesciences.fastmcp.app/mcp
python scripts/showcase_nsclc_v2_fastmcp.py
```

**Scenarios Demonstrated**:
1. KRAS targeting in NSCLC
2. EML4-ALK fusion analysis
3. Pathway visualization (WikiPathways)
4. Clinical trial discovery (ClinicalTrials.gov)

---

## Architecture Patterns

### 1. Fuzzy-to-Fact Protocol

**Implementation**: All search/get tool pairs follow this pattern

**Phase 1 - Fuzzy Search**:
- Input: Natural language query or ambiguous term
- Output: `PaginationEnvelope[SearchCandidate]` with ranked results
- Example: `search_genes("p53")` returns candidates including "TP53"

**Phase 2 - Strict Lookup**:
- Input: Validated CURIE from Phase 1
- Output: Complete entity record with cross-references
- Example: `get_gene("HGNC:11998")` returns full TP53 gene record

**Enforcement**: CURIE validation in get_* methods returns `ErrorEnvelope` for invalid inputs

---

### 2. Canonical Envelopes (ADR-001 Section 8)

**Success Response**: `PaginationEnvelope[T]`
```json
{
  "items": [...],
  "pagination": {
    "cursor": "opaque_cursor_string",
    "total_count": 42,
    "page_size": 20
  }
}
```

**Error Response**: `ErrorEnvelope`
```json
{
  "success": false,
  "error": {
    "code": "UNRESOLVED_ENTITY",
    "message": "The input 'BRCA' is not a valid HGNC CURIE.",
    "recovery_hint": "Call search_genes to resolve the identifier first.",
    "invalid_input": "BRCA"
  }
}
```

---

### 3. Cross-Reference Registry (22-Key Registry)

**Implementation**: `CrossReferences` model (gene.py, Lines 27-143)

**Supported Databases**:
- Core: ensembl_gene, ensembl_transcript, uniprot, entrez, refseq, hgnc
- Disease: omim, orphanet, mondo, efo
- Compound: chembl, drugbank, pubchem_compound, pubchem_substance
- Pathway: kegg, kegg_pathway
- Interaction: string, biogrid, stitch, iuphar
- Structure: pdb

**Validation**: Regex patterns for each cross-reference type (gene.py, Lines 14-24)

**Omission Policy**: Keys with no value are omitted (never null or empty string)

---

### 4. Rate Limiting Strategy

Each client implements rate limiting appropriate to upstream API:

| Client | Rate Limit | Implementation |
|--------|------------|----------------|
| HGNC | 10 req/s | Exponential backoff on 429/403/503 |
| UniProt | 1 req/s | Lock-based rate limiting |
| ChEMBL | 5 req/s | SDK-based rate limiting |
| Open Targets | 10 req/s | GraphQL batching + rate limiting |
| STRING | 1 req/s | Lock-based rate limiting |
| BioGRID | 5 req/s | API key + rate limiting |
| Ensembl | 15 req/s | Exponential backoff |
| Entrez | 3 req/s | NCBI guidelines compliance |
| PubChem | 5 req/s | Exponential backoff |
| IUPHAR | 10 req/s | Retry with backoff |
| WikiPathways | 10 req/s | Lock-based rate limiting |
| ClinicalTrials | 10 req/s | Rate-limited requests |
| DrugBank | 30 req/s | Commercial tier rate limiting |

**Common Pattern**: `_rate_limited_get()` method in each client with async lock and backoff

---

### 5. Connection Pooling

**Implementation**: `LifeSciencesClient` base class (base.py, Lines 41-54)

**Features**:
- httpx.AsyncClient with connection pooling
- Configurable max_connections (default: 10)
- Keep-alive connection reuse
- Automatic cleanup on close()

**Usage**:
```python
async with HGNCClient() as client:
    # Client reuses connections across multiple requests
    result1 = await client.search_genes("BRCA1")
    result2 = await client.search_genes("TP53")
    # Connections automatically closed on context exit
```

---

## Component Dependencies

### External Dependencies

**HTTP Client**:
- httpx (async HTTP requests)

**Data Validation**:
- pydantic (model validation and serialization)

**MCP Framework**:
- fastmcp (MCP server implementation)

**ChEMBL SDK**:
- chembl_webresource_client (ChEMBL Web Services SDK)

**Environment**:
- python-dotenv (environment variable management)

### Internal Dependencies

**Dependency Graph**:
```
servers/
  └─> clients/ (async HTTP clients)
       └─> models/ (Pydantic models)
            └─> envelopes (canonical responses)

clients/
  └─> base.py (LifeSciencesClient)
       └─> httpx.AsyncClient

models/
  └─> pydantic.BaseModel
       └─> validation patterns
```

**Import Chain**:
1. Server imports client and models from package root
2. Client inherits from LifeSciencesClient base
3. Models inherit from Pydantic BaseModel
4. Package __init__.py re-exports public API

---

## File Organization Summary

### Source Code Structure

```
src/lifesciences_mcp/
├── __init__.py              # Public API exports
├── clients/                 # 14 API clients (8,162 lines)
│   ├── __init__.py
│   ├── base.py             # Base client (66 lines)
│   ├── hgnc.py             # HGNC client (353 lines)
│   ├── uniprot.py          # UniProt client (400+ lines)
│   ├── chembl.py           # ChEMBL client (680 lines)
│   ├── opentargets.py      # Open Targets client (730 lines)
│   ├── string.py           # STRING client (350+ lines)
│   ├── biogrid.py          # BioGRID client (270 lines)
│   ├── ensembl.py          # Ensembl client (600+ lines)
│   ├── entrez.py           # Entrez client (730 lines)
│   ├── pubchem.py          # PubChem client (800 lines)
│   ├── iuphar.py           # IUPHAR client (720 lines)
│   ├── wikipathways.py     # WikiPathways client (800 lines)
│   ├── clinicaltrials.py   # ClinicalTrials client (620 lines)
│   └── drugbank.py         # DrugBank client (850 lines)
├── models/                  # 18 model modules (3,403 lines)
│   ├── __init__.py
│   ├── envelopes.py        # Canonical envelopes (145 lines)
│   ├── gene.py             # Gene models (215 lines)
│   ├── protein.py          # Protein models (100 lines)
│   ├── compound.py         # Compound models (150 lines)
│   ├── pubchem_compound.py # PubChem models (200 lines)
│   ├── drug.py             # Drug models (250 lines)
│   ├── pharmacology.py     # IUPHAR models (250 lines)
│   ├── target.py           # Target models (250 lines)
│   ├── interaction.py      # Interaction models (300 lines)
│   ├── biogrid.py          # BioGRID models (100 lines)
│   ├── ensembl.py          # Ensembl models (280 lines)
│   ├── entrez.py           # Entrez models (250 lines)
│   ├── pathway.py          # Pathway models (150 lines)
│   ├── pathway_components.py # Pathway component models (200 lines)
│   ├── trial.py            # Trial models (180 lines)
│   ├── trial_location.py   # Trial location models (50 lines)
│   └── provenance.py       # Provenance models (180 lines)
├── servers/                 # 13 MCP servers (2,191 lines)
│   ├── __init__.py
│   ├── gateway.py          # Gateway server (116 lines)
│   ├── hgnc.py             # HGNC server (86 lines)
│   ├── uniprot.py          # UniProt server (100 lines)
│   ├── chembl.py           # ChEMBL server (130 lines)
│   ├── opentargets.py      # Open Targets server (130 lines)
│   ├── string.py           # STRING server (150 lines)
│   ├── biogrid.py          # BioGRID server (100 lines)
│   ├── ensembl.py          # Ensembl server (180 lines)
│   ├── entrez.py           # Entrez server (160 lines)
│   ├── pubchem.py          # PubChem server (150 lines)
│   ├── iuphar.py           # IUPHAR server (400 lines)
│   ├── wikipathways.py     # WikiPathways server (180 lines)
│   ├── clinicaltrials.py   # ClinicalTrials server (300 lines)
│   └── drugbank.py         # DrugBank server (100 lines)
└── tools/
    └── __init__.py          # Placeholder

src/lifesciences_agent/
├── __init__.py              # Empty (experimental)
└── aggregator.py            # Unified search (74 lines)
```

### Supporting Files

```
scripts/                     # Showcase and validation scripts
├── showcase_nsclc.py
├── showcase_nsclc_v2_fastmcp.py
├── showcase_nsclc_v2_mcp.py
├── benchmark_value.py
├── validate_competency.py
├── verify_chembl_v2.py
└── verify_swi_snf.py

skills/                      # Reusable Claude skills
└── mermaid-diagram-optimizer/
    ├── skill.py
    └── examples/

tests/                       # Comprehensive test suite
├── conftest.py
├── fixtures/
├── unit/                    # 20 unit test files
├── integration/             # 19 integration test files
├── gaps/                    # 1 gap test file
├── manual/                  # 4 manual test files
└── contract/                # Contract test placeholder
```

---

## Statistics Summary

**Total Components**:
- 14 Client classes
- 63 Model classes
- 13 MCP servers (12 active + 1 requires API key)
- 40+ MCP tools
- 44 test files
- 7 showcase/validation scripts
- 1 reusable skill

**Code Volume**:
- Client layer: 8,162 lines
- Model layer: 3,403 lines
- Server layer: 2,191 lines
- Total production code: ~13,756 lines

**API Coverage**:
- 13 external biological databases
- 22-key cross-reference registry
- Fuzzy-to-Fact protocol across all services
- Canonical envelope pattern (success/error)

---

## Key Design Principles

1. **Separation of Concerns**: Clear separation between clients (data access), models (validation), and servers (MCP tools)

2. **Fuzzy-to-Fact Protocol**: Two-phase resolution (search → validate → get) prevents hallucination

3. **Canonical Envelopes**: Standardized response format with pagination and error recovery hints

4. **Rate Limiting**: Respectful API usage with backoff strategies

5. **Cross-Reference Network**: 22-key registry enables cross-database navigation

6. **Connection Pooling**: Efficient resource usage with httpx.AsyncClient

7. **Validation by Default**: Pydantic models enforce data quality at runtime

8. **Context Managers**: Proper resource cleanup with async context managers

9. **Error Recovery**: Agent-actionable error messages with recovery hints

10. **Progressive Disclosure**: Slim mode for token efficiency, full mode for completeness

---

*End of Component Inventory*
