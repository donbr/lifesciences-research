---
name: lifesciences-pharmacology
description: "Queries pharmacology databases (ChEMBL, PubChem, DrugBank, IUPHAR) via curl for drug mechanisms, target identification, bioactivity profiling, and indication discovery. This skill should be used when the user asks to \"find drug mechanisms\", \"identify drug targets\", \"analyze bioactivity data\", \"discover drug indications\", or mentions ChEMBL IDs, mechanisms of action, IC50/Ki values, drug-target relationships, or compound similarity searches."
---

# Pharmacology API Skills

Query pharmacology databases directly via curl. These endpoints complement the Life Sciences MCPs.

## Quick Reference

| Task | API | Endpoint |
|------|-----|----------|
| Search compounds | ChEMBL | `/molecule/search` |
| Drug mechanism | ChEMBL | `/mechanism` |
| Drug indications | ChEMBL | `/drug_indication` |
| Bioactivity data | ChEMBL | `/activity` |
| Compound properties | PubChem | `/compound/name/{name}/property` |
| Ligand-target | IUPHAR | `/interactions` |

## Curl Examples

### ChEMBL: Compound Search & Details

```bash
# Search compound by name
curl -s "https://www.ebi.ac.uk/chembl/api/data/molecule/search?q=venetoclax&format=json" \
  | jq '.molecules[:1][] | {chembl_id: .molecule_chembl_id, name: .pref_name, max_phase: .max_phase}'

# Get compound by ChEMBL ID
curl -s "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL3137309?format=json" \
  | jq '{id: .molecule_chembl_id, name: .pref_name, formula: .molecule_properties.full_molformula, mw: .molecule_properties.full_mwt}'

# Get SMILES structure
curl -s "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL3137309?format=json" \
  | jq '.molecule_structures.canonical_smiles'
```

### ChEMBL: Drug Mechanisms (Critical for Graph Edges!)

```bash
# Get mechanism for drug (Drug → Target edge)
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL3137309&format=json" \
  | jq '.mechanisms[] | {action: .action_type, mechanism: .mechanism_of_action, target_id: .target_chembl_id}'

# Reverse: Find all drugs for target (Target → Drugs edge)
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?target_chembl_id=CHEMBL4860&format=json" \
  | jq '.mechanisms[] | {drug_id: .molecule_chembl_id, action: .action_type, mechanism: .mechanism_of_action}'
```

### ChEMBL: Drug Indications

```bash
# Get indications for drug (Drug → Disease edge)
curl -s "https://www.ebi.ac.uk/chembl/api/data/drug_indication?molecule_chembl_id=CHEMBL3137309&format=json" \
  | jq '.drug_indications[:5][] | {disease: .mesh_heading, efo: .efo_term, phase: .max_phase_for_ind}'
```

### ChEMBL: Bioactivity Data (Potency Metrics)

```bash
# Get activity data (IC50, Ki, EC50)
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL3137309&format=json&limit=10" \
  | jq '.activities[] | {target: .target_pref_name, type: .standard_type, value: .standard_value, units: .standard_units}'

# Filter by activity type
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id=CHEMBL3137309&standard_type=Ki&format=json" \
  | jq '.activities[] | {target: .target_pref_name, Ki: .standard_value, units: .standard_units}'

# Get activities for target
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?target_chembl_id=CHEMBL4860&format=json&limit=10" \
  | jq '.activities[] | {compound: .molecule_chembl_id, type: .standard_type, value: .standard_value}'
```

### ChEMBL: Structure Search

```bash
# Similarity search (find analogs)
SMILES="CC1=CC=CC=C1"  # Example SMILES
curl -s "https://www.ebi.ac.uk/chembl/api/data/similarity/$SMILES/70?format=json" \
  | jq '.molecules[:3][] | {id: .molecule_chembl_id, name: .pref_name, similarity: .similarity}'

# Substructure search
curl -s "https://www.ebi.ac.uk/chembl/api/data/substructure/$SMILES?format=json&limit=5" \
  | jq '.molecules[] | {id: .molecule_chembl_id, name: .pref_name}'
```

### ChEMBL: Target Information

```bash
# Get target details
curl -s "https://www.ebi.ac.uk/chembl/api/data/target/CHEMBL4860?format=json" \
  | jq '{id: .target_chembl_id, name: .pref_name, type: .target_type, organism: .organism}'

# Search targets by gene
curl -s "https://www.ebi.ac.uk/chembl/api/data/target/search?q=BCL2&format=json" \
  | jq '.targets[:3][] | {id: .target_chembl_id, name: .pref_name, type: .target_type}'
```

### PubChem: Compound Data

```bash
# Get compound by name
curl -s "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/JSON" \
  | jq '.PC_Compounds[0] | {cid: .id.id.cid}'

# Get properties
curl -s "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/property/MolecularFormula,MolecularWeight,IUPACName/JSON" \
  | jq '.PropertyTable.Properties[0]'

# Get by CID
curl -s "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/property/MolecularFormula,CanonicalSMILES/JSON" \
  | jq '.PropertyTable.Properties[0]'

# Cross-references
curl -s "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/xrefs/RegistryID/JSON" \
  | jq '.InformationList.Information[0].RegistryID[:5]'
```

### IUPHAR/GtoPdb: Pharmacology

```bash
# Search ligands (drugs/compounds)
curl -s "https://www.guidetopharmacology.org/services/ligands?name=ibuprofen" \
  | jq '.[:1][] | {id: .ligandId, name, type, approved}'

# Get ligand details
curl -s "https://www.guidetopharmacology.org/services/ligands/2713" \
  | jq '{id: .ligandId, name, type, approved, synonyms}'

# Search targets
curl -s "https://www.guidetopharmacology.org/services/targets?name=dopamine" \
  | jq '.[:3][] | {id: .targetId, name, type: .type}'

# Get target-ligand interactions
curl -s "https://www.guidetopharmacology.org/services/ligands/2713/interactions" \
  | jq '.[:3][] | {target: .targetName, action: .action, affinity}'
```

### DrugBank: Drug Data (API Key Required)

```bash
# Search drugs (commercial API)
curl -s "https://api.drugbank.com/v1/drugs?q=venetoclax" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  | jq '.[:1][] | {drugbank_id, name, description}'
```

## Common Workflow: Drug Repurposing

```bash
# 1. Find target for known drug
TARGET=$(curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id=CHEMBL3137309&format=json" \
  | jq -r '.mechanisms[0].target_chembl_id')

# 2. Find other drugs for same target
curl -s "https://www.ebi.ac.uk/chembl/api/data/mechanism?target_chembl_id=$TARGET&format=json" \
  | jq '.mechanisms[] | {drug: .molecule_chembl_id, mechanism: .mechanism_of_action}'

# 3. Get indications for alternative drug
curl -s "https://www.ebi.ac.uk/chembl/api/data/drug_indication?molecule_chembl_id=CHEMBL2107358&format=json" \
  | jq '.drug_indications[:3][] | {disease: .mesh_heading, phase: .max_phase_for_ind}'
```

## Rate Limits

| API | Limit | Auth Required |
|-----|-------|---------------|
| ChEMBL | 100 req/s | No |
| PubChem | 5 req/s | No |
| DrugBank | Varies | Yes (commercial) |
| IUPHAR | 10 req/s | No |

## Query Best Practices

### Drug Discovery vs Repurposing
- **Drug repurposing**: Use `max_phase≥2` filter (want clinical validation, shorter approval path)
- **General discovery**: No phase filter (include preclinical tools, mechanism probes, research reagents)
- **Target validation**: No phase filter needed for mechanism studies

### Query Efficiency
- Check mechanisms (`/mechanism` endpoint) before bioactivity data
- Use `target_chembl_id` for reverse lookups (find drugs for target)
- Limit activity queries with `&limit=10` for exploration

### Common Pitfalls
- Don't filter by phase for mechanism discovery
- Don't assume approved drugs are the only useful compounds
- Preclinical tool compounds often have better selectivity data

## See Also

- [references/chembl-resources.md](references/chembl-resources.md) - ChEMBL resource endpoints
- [references/pubchem-pug.md](references/pubchem-pug.md) - PubChem PUG REST syntax
