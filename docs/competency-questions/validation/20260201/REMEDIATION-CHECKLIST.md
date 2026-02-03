# Remediation Checklist: CQ Validation Gaps
## Quick Reference for Gap Resolution

**Last Updated**: 2026-02-01
**Target Completion**: 2026-02-08
**Owner**: Development Team

---

## Critical - Block CQ14 Completion

### ☐ Task 1: Obtain BioGRID ORCS API Key
**Effort**: 15 minutes | **Impact**: Unblocks CQ14 full validation

```bash
# Step 1: Register at https://webservice.thebiogrid.org/
# (Requires valid email, free account)

# Step 2: Retrieve API key from account settings

# Step 3: Store in environment
export BIOGRID_API_KEY="<your_key>"

# Step 4: Verify access
curl "https://webservice.thebiogrid.org/v3/genes/search?geneSymbol=TYMS&accesskey=$BIOGRID_API_KEY&format=json"
# Expected: Returns TYMS gene record with ID 7298

# Step 5: Update .env.example (NO KEYS IN .env!)
echo 'BIOGRID_API_KEY=...' >> .env.example

# Step 6: Run CQ14 validation with BioGRID client
uv run python -m src.lifesciences_mcp.clients.biogrid
# Should now retrieve CRISPR screen data

# Step 7: Re-generate CQ14 summary with complete graph
```

**Verification Checklist**:
- [ ] API key obtained
- [ ] curl query returns TYMS (7298)
- [ ] CQ14 client updated to use BioGRID
- [ ] CQ14 summary regenerated
- [ ] Edge count updated in master summary
- [ ] Status changed to "VALIDATED (Full)"

---

## High Priority - Incomplete Graph Coverage

### ☐ Task 2: Enumerate Missing Edges for CQ10, CQ14, CQ15
**Effort**: 30-45 min per CQ | **Impact**: Enables complete graph analysis

```bash
# For each CQ (CQ10, CQ14, CQ15):

# Step 1: Query Graphiti for all nodes/edges
# Example for CQ10:
GRAPHITI_GROUP_ID="cq10-huntingtons-novel-targets"

# (Via Python or Cypher):
# MATCH (g:Gene)-[r]->(t:Gene) WHERE g.cq_group = $group_id
# RETURN TYPE(r), COUNT(*) as count

# Step 2: Categorize edges by type
# Expected for CQ10:
# - INTERACTS (HTT ↔ various targets)
# - DYSREGULATES (HTT mutant → ITPR1, REST, BDNF)
# - STRING_INTERACTION (protein-level connections)

# Step 3: Update master summary
# | CQ10 | ... | 8 | 12 | ... |  (was: "8 | - |")

# Step 4: Document any MISSING edge types that should exist
```

**Checklist per CQ**:

#### CQ10 (Huntington's Targets)
- [ ] Query Graphiti: `cq10-huntingtons-novel-targets`
- [ ] Count INTERACTS edges (HTT ↔ targets)
- [ ] Count DYSREGULATES edges (mHTT → dysfunction)
- [ ] Count STRING_INTERACTION edges (protein network)
- [ ] Identify missing edge types (e.g., MODULATES, TARGETS_DRUG)
- [ ] Update master summary: Edges column
- [ ] Document in "Validation Gaps" section

#### CQ14 (Feng Synthetic Lethality)
- [ ] Query Graphiti: `cq14-feng-synthetic-lethality`
- [ ] Count SYNTHETIC_LETHAL edges (TP53 ↔ TYMS)
- [ ] Count INHIBITS edges (TYMS ← 5-FU, Pemetrexed)
- [ ] Verify BioGRID ORCS data (post-Task 1)
- [ ] Update master summary: Edges column
- [ ] Document confirmed CRISPR screen hits

#### CQ15 (CAR-T Regulatory)
- [ ] Query Graphiti: `cq15-car-t-regulatory`
- [ ] Count TARGETS edges (CAR-T → CD19/BCMA)
- [ ] Count TREATS edges (CAR-T → disease)
- [ ] Count APPROVED_BY edges (FDA/EMA milestones)
- [ ] Identify missing: regulatory pathway edges (BREAKTHROUGH, PRIORITY, etc.)
- [ ] Update master summary: Edges column
- [ ] Document regulatory timeline

---

### ☐ Task 3: Validate ClinicalTrials.gov Data with Curl
**Effort**: 10 minutes | **Impact**: Confirms data quality despite Cloudflare blocking

```bash
# Test 1: Simple search (verify API accepts parameters)
curl -s "https://clinicaltrials.gov/api/v2/studies?query.term=cancer&pageSize=1&format=json" \
  | jq '.studies[0].protocolSection.identificationModule.nctId'
# Expected: Returns NCT ID (e.g., "NCT00963261")

# Test 2: Status filter (verify filter.overallStatus works)
curl -s "https://clinicaltrials.gov/api/v2/studies?filter.overallStatus=RECRUITING&pageSize=1&format=json" \
  | jq '.studies[0].protocolSection.statusModule.overallStatus'
# Expected: "RECRUITING"

# Test 3: Phase filter (verify AREA[Phase] syntax works)
curl -s "https://clinicaltrials.gov/api/v2/studies?filter.advanced=AREA[Phase]PHASE3&pageSize=1&format=json" \
  | jq '.studies[0].protocolSection.designModule.phases[0]'
# Expected: "PHASE3"

# Test 4: Verify NCTs from CQ12, CQ13, CQ15 still exist
for nct in NCT:06463861 NCT:05548231 NCT:05882045; do
  curl -s "https://clinicaltrials.gov/api/v2/studies/$nct?format=json" \
    | jq -r '.protocolSection.identificationModule.nctId' | grep -q "$nct" && echo "✓ $nct" || echo "✗ $nct"
done
# Expected: All NCTs found and accessible
```

**Checklist**:
- [ ] Test 1: Simple search returns NCT ID ✓
- [ ] Test 2: Status filter works ✓
- [ ] Test 3: Phase filter works ✓
- [ ] Test 4: Sample NCTs from CQ12, CQ13, CQ15 verified ✓
- [ ] Document curl-based validation in test report
- [ ] Mark Python integration tests as @pytest.mark.skip (document Cloudflare reason)

---

## Medium Priority - Mechanistic Depth

### ☐ Task 4: Add Mechanistic Details for CQ10 Novel Targets
**Effort**: 2-3 hours (literature research) | **Impact**: Answers "why underexplored?"

```bash
# For each target (ITPR1, REST, BDNF, CREBBP, HAP1):

# Step 1: Literature search
# Google Scholar: "ITPR1 huntingtin" "HTT IP3 receptor calcium"
# PubMed: Query for 2-3 key papers on mechanism

# Step 2: Document in CQ10 summary:
# | Target | Current Mechanism | Gap | Potential Therapy |
# | ITPR1 | Calcium signaling dysregulation | Missing: HTT-ITPR1 direct interaction studies | IP3R modulators? |

# Step 3: Identify potential trials
# Query ClinicalTrials.gov: "ITPR1" OR "IP3 receptor" + "Huntington"

# Step 4: Persist to Graphiti with MODULATES/DYSREGULATES edges
# HTT-mutant --[DYSREGULATES_CALCIUM]--> ITPR1
# HTT-mutant --[TRAPS_TRANSCRIPTION_FACTOR]--> REST
# HTT-mutant --[IMPAIRS_AXONAL_TRANSPORT]--> BDNF
```

**Checklist**:
- [ ] Research mechanism for ITPR1 (calcium signaling)
  - [ ] 2-3 papers identified
  - [ ] Specific HTT-ITPR1 interaction documented
  - [ ] Potential rescue pathways identified
- [ ] Research mechanism for REST (transcription)
  - [ ] Cytoplasmic sequestration mechanism confirmed
  - [ ] Downstream transcriptional targets identified
- [ ] Research mechanism for BDNF (transport)
  - [ ] Axonal transport impairment documented
  - [ ] BDNF signaling pathway dependencies mapped
- [ ] Research mechanism for CREBBP (histone acetylation)
  - [ ] HAT activity dysregulation confirmed
  - [ ] CREBBP-HTT-EP300 pathway documented
- [ ] Research mechanism for HAP1 (vesicle trafficking)
  - [ ] Trafficking defects documented
  - [ ] HAP1-HTT interaction specificity confirmed
- [ ] Update CQ10 summary with mechanism table
- [ ] Persist MODULATES/DYSREGULATES edges to Graphiti
- [ ] Document missing trial coverage

---

### ☐ Task 5: Complete CQ14 with Full Feng et al. Synthetic Lethal Pairs
**Effort**: 2-3 hours | **Impact**: Demonstrates systematic synthetic lethality discovery

```bash
# Step 1: Obtain Feng et al. (2022) supplementary table
# (Citation: Feng et al. Systematic identification of synthetic lethal interactions in TP53-mutant cancers)
# Look for: Supplementary Table with TP53 synthetic lethal partners

# Step 2: For EACH TP53 partner identified:
# Example loop for TYMS, ATM, RPA1, etc.:

partners=("TYMS" "ATM" "RPA1" "CHEK2" "TP53BP1" ...)

for partner in "${partners[@]}"; do
  echo "=== Processing $partner ==="

  # 2a: Get HGNC data
  curl "https://rest.genenames.org/search/$partner" | jq '.response.docs[0] | {hgnc_id, symbol, name}'

  # 2b: Query ChEMBL for drugs targeting $partner
  # (via ChEMBL API or search_compounds)

  # 2c: Query BioGRID ORCS for CRISPR screen hits
  curl "https://webservice.thebiogrid.org/v3/genes/search?geneSymbol=$partner&accesskey=$BIOGRID_API_KEY&format=json"

  # 2d: Persist to Graphiti:
  # TP53 --[SYNTHETIC_LETHAL_WITH]--> $partner
  # $partner --[INHIBITED_BY]--> [drug1, drug2, drug3...]
done

# Step 3: Create matrix summary
# | TP53 Partner | CRISPR Score | Druggable? | Approved Drugs | Phase Drugs |
# | TYMS | 5.2 | YES | 5-FU, Pemetrexed | LY2405672 |
# | ATM | 4.8 | YES | M6620, M3814 | AZD0156 |
```

**Checklist**:
- [ ] Feng et al. (2022) supplementary table obtained
- [ ] For each TP53 partner:
  - [ ] HGNC gene record retrieved
  - [ ] ChEMBL drugs targeting partner identified
  - [ ] BioGRID ORCS CRISPR screen data retrieved
  - [ ] Clinical trials found (if available)
  - [ ] Persisted to Graphiti with SYNTHETIC_LETHAL edges
- [ ] Create TP53 synthetic lethal matrix (>3 partners)
- [ ] Update CQ14 summary with complete dataset
- [ ] Status changed to "VALIDATED (Full)" with multiple partners documented
- [ ] Demonstrate reusable synthetic lethality workflow

---

### ☐ Task 6: Complete CAR-T Regulatory Pathway (CQ15)
**Effort**: 1-2 hours | **Impact**: Enables timeline analysis

```bash
# Step 1: Build CAR-T regulatory milestone matrix

# | CAR-T Therapy | FDA Approved | EMA Approved | Pathway | Breakthrough? | Priority? |
# | Tisagenlecleucel (Kymriah) | 2017-08 | 2018 | Standard | YES | YES |
# | Axicabtagene ciloleucel (Yescarta) | 2017-10 | 2018 | Standard | YES | YES |
# | Brexucabtagene autoleucel (Tecartus) | 2020-07 | 2021 | Accelerated | NO | YES |
# | Lisocabtagene maraleucel (Breyanzi) | 2021-02 | 2022 | Accelerated | NO | YES |
# | Idecabtagene vicleucel (Abecma) | 2021-03 | 2021 | Accelerated | NO | YES |
# | Carvykti (releme-cel) | 2023-12 | 2024 | Conditional | NO | NO |

# Step 2: Document edge types needed:
# - BREAKTHROUGH_THERAPY_DESIGNATED (e.g., Kymriah)
# - PRIORITY_REVIEW (FDA expedited)
# - ACCELERATED_APPROVAL (FDA accelerated)
# - RMAT_ELIGIBLE (FDA regenerative medicine)
# - PRIME_DESIGNATED (EMA advanced therapy)
# - CONDITIONAL_APPROVAL (EMA conditional authorization)

# Step 3: Persist temporal edges
# CHEMBL:3301574 (Kymriah) --[FDA_APPROVED_2017]--> FDA
# CHEMBL:3301574 (Kymriah) --[BREAKTHROUGH_THERAPY]--> BT_DESIGNATION
# CHEMBL:3301574 (Kymriah) --[EMA_APPROVED_2018]--> EMA

# Step 4: Update CQ15 summary
# Add "Regulatory Timeline" section showing approval progression
# 2017: Kymriah, Yescarta (simultaneous breakthrough approvals)
# 2020-2021: Second generation (Tecartus, Breyanzi, Abecma)
# 2023+: Third generation (Carvykti - allogeneic)
```

**Checklist**:
- [ ] CAR-T regulatory milestone matrix built
- [ ] FDA approval dates verified for all 6 approved therapies
- [ ] EMA approval dates verified
- [ ] Regulatory pathway type identified (Breakthrough, Accelerated, Standard, Conditional)
- [ ] Edge types created: BREAKTHROUGH, PRIORITY_REVIEW, ACCELERATED, RMAT, PRIME, CONDITIONAL
- [ ] Temporal edges persisted to Graphiti (APPROVED_2017, APPROVED_2020, etc.)
- [ ] CQ15 summary updated with regulatory timeline
- [ ] Graph enables time-series analysis of CAR-T approval acceleration
- [ ] Edges enumerated and counted in master summary

---

## Quick Status Dashboard

| Task | CQ | Priority | Status | ETA | Owner |
|------|-----|----------|--------|-----|-------|
| 1. BioGRID API Key | CQ14 | 🔴 Critical | ☐ Not Started | 15 min | - |
| 2a. Edge Count CQ10 | CQ10 | 🟠 High | ☐ Not Started | 30 min | - |
| 2b. Edge Count CQ14 | CQ14 | 🟠 High | ☐ Not Started | 45 min | - |
| 2c. Edge Count CQ15 | CQ15 | 🟠 High | ☐ Not Started | 45 min | - |
| 3. ClinicalTrials.gov Curl Validation | All | 🟡 Medium | ☐ Not Started | 10 min | - |
| 4. CQ10 Mechanistic Depth | CQ10 | 🟡 Medium | ☐ Not Started | 2-3 hrs | - |
| 5. CQ14 Full Synthetic Lethal | CQ14 | 🟡 Medium | ☐ Not Started | 2-3 hrs | - |
| 6. CQ15 Regulatory Pathway | CQ15 | 🟡 Medium | ☐ Not Started | 1-2 hrs | - |

**Total Effort**: 5-7 hours for complete validation
**Critical Path**: Task 1 (BioGRID) → Task 2b (CQ14 edges) → Task 5 (Full CQ14)

---

## Progress Tracking

### Week 1 Target (2026-02-01 to 2026-02-05)
- [ ] Task 1: BioGRID API (15 min)
- [ ] Task 2: Edge enumeration (2 hrs)
- [ ] Task 3: ClinicalTrials curl validation (10 min)
- **Subtotal**: 2.5 hours

**Expected Outcome**: CQ14 unblocked, CQ10/CQ14/CQ15 edge counts complete

### Week 2 Target (2026-02-05 to 2026-02-08)
- [ ] Task 4: CQ10 mechanistic depth (2-3 hrs)
- [ ] Task 5: CQ14 full synthetic lethal dataset (2-3 hrs)
- [ ] Task 6: CQ15 regulatory pathway (1-2 hrs)
- **Subtotal**: 5-8 hours

**Expected Outcome**: All CQs at "Fully Validated" with complete mechanistic depth

---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Gap Analyzer | Claude Code | 2026-02-01 | Generated ✓ |
| Dev Lead | - | - | [ ] Assigned |
| QA | - | - | [ ] Verified |

---

**Last Updated**: 2026-02-01 by Gap Analyzer Agent
**Next Review**: Post-remediation (estimated 2026-02-08)
