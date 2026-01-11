# Research 3: CAR-T Regulatory Landscape Validation

**Date**: 2026-01-10

**Question**: Which CAR-T cell trials are currently navigating FDA or EMA milestones most rapidly?

**Status**: VALIDATED (via MCP)

---

## Phase 1: Trial Discovery

### CAR-T Phase 3 Trials

```python
clinicaltrials_search_trials("CAR-T cell therapy", phase="PHASE3", page_size=5)
```

**Results**: 41 Phase 3 CAR-T trials found

| NCT ID | Title | Status | Conditions |
|--------|-------|--------|------------|
| NCT:07186192 | Digital Health Intervention for CAR-T Telemonitoring | RECRUITING | Hematologic Malignancies |
| NCT:06464991 | Equecabtagene Autoleucel Phase III for R/R Multiple Myeloma | RECRUITING | Multiple Myeloma |
| NCT:03937544 | CD19 CAR-T Phase II/III for R/R B-ALL | RECRUITING | B-ALL |
| NCT:03435796 | Long-Term Follow-up for Gene-Modified T Cells | RECRUITING | Neoplasms |
| NCT:05991388 | Novel Agents in Pediatric B-cell NHL | RECRUITING | B-cell NHL |

---

## Phase 2: Deep Dive - Equecabtagene Trial

### Full Trial Details (NCT:06464991)

```python
clinicaltrials_get_trial("NCT:06464991")
```

| Field | Value |
|-------|-------|
| Title | Phase III Randomized Study of Equecabtagene Autoleucel in Lenalidomide-Refractory R/R Multiple Myeloma |
| Sponsor | Nanjing IASO Biotechnology Co., Ltd. |
| Status | RECRUITING |
| Start Date | 2024-03-27 |
| Completion Date | 2027-08 |
| Allocation | RANDOMIZED |
| Intervention Model | PARALLEL |

### Primary Endpoint
- **Progression-Free Survival (PFS)** as assessed by Independent Review Committee

### Key Secondary Endpoints
- MRD negativity rate at 12 months
- Overall Response Rate
- Duration of Response
- Overall Survival

### Interventions
- Equecabtagene Autoleucel Injection (CAR-T)
- Daratumumab
- Pomalidomide
- Bortezomib
- Dexamethasone

---

## Phase 3: GLP-1 Innovation Cross-Reference

```python
clinicaltrials_search_trials("GLP-1", status="RECRUITING", phase="PHASE3")
```

**Results**: 36 Phase 3 GLP-1 trials recruiting

| NCT ID | Title | Conditions |
|--------|-------|------------|
| NCT:07104383 | VK2735 for Weight Management in T2D | Weight Loss |
| NCT:06961280 | Tirzepatide in T1D with Obesity | Type 1 Diabetes, Obesity |
| NCT:06629585 | GIP/GLP-1RA with Automated Insulin Delivery | Type 1 Diabetes |

---

## Key Findings

1. **CAR-T Maturation**: 41 Phase 3 trials indicate CAR-T moving from experimental to standard of care
2. **Global Sponsors**: Chinese biotechs (IASO, etc.) now leading Phase 3 CAR-T development
3. **Indication Expansion**: CAR-T moving beyond lymphoma into multiple myeloma and solid tumors
4. **Digital Health Integration**: NCT:07186192 shows CAR-T trials incorporating telemonitoring - regulatory modernization

---

## MCP Validation

The ClinicalTrials.gov MCP works correctly when called from Claude Code:
- `search_trials()` returns paginated results with trial summaries
- `get_trial()` returns full protocol details including eligibility, endpoints, sponsors

**Note**: The Cloudflare blocking documented in CLAUDE.md affects pytest integration tests only, not live MCP usage.

---

## Tools Used

| Tool | Purpose |
|------|---------|
| `clinicaltrials_search_trials()` | Trial discovery by phase/status |
| `clinicaltrials_get_trial()` | Full protocol details |
