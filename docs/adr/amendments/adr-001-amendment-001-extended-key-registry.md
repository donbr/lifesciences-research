# ADR-001 Amendment 001: Extended Cross-Reference Key Registry

**Status:** Proposed
**Date:** 2025-12-21
**Amends:** ADR-001 v1.1, Appendix A (Cross-Reference Key Registry)
**Reason:** Alignment with Discovery Issue AGE-65 API coverage

---

## Context

The Discovery Issue (AGE-65) identified APIs across 5 tiers for MCP wrapper development. ADR-001 v1.1 Appendix A defines cross-reference keys for only a subset of these APIs.

To ensure the Triangulation Protocol (Section 6) can verify assertions across ALL planned data sources, the Cross-Reference Key Registry must be extended.

---

## Amendment

### Extended Cross-Reference Key Registry (Appendix A)

Replace the existing Appendix A with this extended registry:

#### Core Identifiers (Original)

| Key Name | ID Type | Format Regex | Cardinality | Notes |
|----------|---------|--------------|-------------|-------|
| `ensembl_gene` | Ensembl Gene | `^ENSG\d{11}$` | String | Primary Gene ID |
| `ensembl_transcript` | Ensembl Transcript | `^ENST\d{11}$` | List[String] | Alternates |
| `uniprot` | UniProt Accession | `^[A-Z0-9]{6,10}$` | List[String] | Handles isoforms |
| `entrez` | NCBI Gene ID | `^\d+$` | String | NCBI Entrez |
| `chembl` | ChEMBL ID | `^CHEMBL\d+$` | String | Targets, drugs, assays |
| `pdb` | PDB Structure ID | `^[0-9][A-Z0-9]{3}$` | List[String] | Protein structures |

#### Tier 0: Drug Discovery Core (New)

| Key Name | ID Type | Format Regex | Cardinality | Notes |
|----------|---------|--------------|-------------|-------|
| `drugbank` | DrugBank ID | `^DB\d{5}$` | String | Drug information |
| `opentargets` | Open Targets ID | `^ENSG\d{11}$` | String | Uses Ensembl gene IDs |

#### Tier 1-2: Interaction Networks (New)

| Key Name | ID Type | Format Regex | Cardinality | Notes |
|----------|---------|--------------|-------------|-------|
| `string` | STRING ID | `^\d+\.[A-Za-z0-9]+$` | String | Protein-protein interactions |
| `biogrid` | BioGRID ID | `^\d+$` | String | Genetic interactions |
| `stitch` | STITCH ID | `^(CID[sm])?\d+$` | String | Chemical-protein interactions |
| `iuphar` | GtoPdb Target ID | `^\d+$` | String | Pharmacological targets |

#### Tier 3: Pathways & Disease (New)

| Key Name | ID Type | Format Regex | Cardinality | Notes |
|----------|---------|--------------|-------------|-------|
| `kegg` | KEGG Gene ID | `^[a-z]{3,4}:\d+$` | String | e.g., `hsa:672` |
| `kegg_pathway` | KEGG Pathway ID | `^[a-z]{3,4}\d{5}$` | List[String] | e.g., `hsa05224` |
| `omim` | OMIM ID | `^\d{6}$` | String | Genetic disorders |
| `orphanet` | Orphanet ID | `^ORPHA:\d+$` | String | Rare diseases |
| `mondo` | MONDO ID | `^MONDO:\d{7}$` | String | Disease ontology |
| `efo` | EFO ID | `^EFO:\d{7}$` | String | Experimental Factor Ontology |

#### Tier 4: Additional Genomics (New)

| Key Name | ID Type | Format Regex | Cardinality | Notes |
|----------|---------|--------------|-------------|-------|
| `hgnc` | HGNC ID | `^HGNC:\d+$` | String | Gene nomenclature |
| `refseq` | RefSeq Accession | `^[NX][MR]_\d+$` | List[String] | NCBI sequences |
| `pubchem_compound` | PubChem CID | `^\d+$` | String | Chemical compounds |
| `pubchem_substance` | PubChem SID | `^\d+$` | String | Substance records |

---

## Implementation Notes

### Cardinality Rules

1. **String (Single):** Most IDs are 1:1 mappings
2. **List[String] (Multiple):** Use for:
   - Isoforms (UniProt)
   - Transcript variants (Ensembl)
   - Multiple structures (PDB)
   - Pathway memberships (KEGG)
   - Sequence versions (RefSeq)

### Null Handling

- If a cross-reference doesn't exist for an entity, **omit the key entirely**
- Do NOT set to `null` or empty string
- This keeps payloads minimal and avoids null-checking logic

### Validation

All keys should be validated against the regex pattern before inclusion. Invalid IDs should trigger an `INVALID_CROSS_REFERENCE` error (add to Error Code Registry).

---

## Error Code Registry Addition

Add to Appendix B:

| Code | Meaning | Agent Action |
|------|---------|--------------|
| `INVALID_CROSS_REFERENCE` | Cross-reference ID failed regex validation | Report data quality issue |

---

## Rationale

This extension ensures:

1. **Full Discovery Alignment:** All APIs from AGE-65 Tiers 0-4 have corresponding keys
2. **Future-Proofing:** Disease ontologies (MONDO, EFO) included for Open Targets compatibility
3. **Chemical Coverage:** PubChem IDs for compound/substance disambiguation
4. **Triangulation Completeness:** Agents can verify across ANY source pair

---

## Approval

**Proposed By:** Lead Architect (Claude Code)
**Date:** 2025-12-21
**Requires:** Enterprise Architect sign-off before merge to v1.2
