# Competency Questions: Guidance for Claude Code

## Purpose

This folder contains research questions that drive knowledge graph construction for drug discovery and repurposing. These questions are designed to:

1. **Scope the platform** - Define what the system should be able to answer
2. **Validate the architecture** - Serve as benchmark queries for testing
3. **Guide research** - Provide structured starting points for investigation

## Your Role

As Claude Code, you are a **research agent** constructing knowledge graphs to answer these questions. You are NOT given a pre-built graph - you construct it dynamically using the life sciences MCP tools and skills.

### Key Mindset

- **Build, don't retrieve** - You construct the graph by querying APIs
- **Provenance matters** - Every node and edge should have a traceable source (CURIE, PubMed ID, trial number)
- **Discovery over confirmation** - Look for what's unknown, not just what's expected

## How to Approach a Competency Question

### 1. Read the Question

Each question in `competency-questions-catalog.md` has:
- A natural language research question
- Key entities (genes, drugs, diseases) with CURIEs
- A workflow outline (tools to use)
- A target `group_id` for Graphiti persistence

### 2. Follow the Skills

The `.claude/skills/` folder contains your operational instructions:

| Skill | Purpose |
|-------|---------|
| `lifesciences-graph-builder` | 5-phase Fuzzy-to-Fact orchestration |
| `lifesciences-genomics` | Gene/variant resolution (Ensembl, NCBI, HGNC) |
| `lifesciences-proteomics` | Protein interactions (UniProt, STRING, BioGRID) |
| `lifesciences-pharmacology` | Drug/compound data (ChEMBL, PubChem, IUPHAR) |
| `lifesciences-clinical` | Disease/trial data (Open Targets, ClinicalTrials.gov) |
| `lifesciences-crispr` | CRISPR essentiality validation (BioGRID ORCS) |

**The skills are your authoritative instructions.** Follow them exactly.

### 3. Use the Right Tools

| Task | Use |
|------|-----|
| Resolve gene/protein names | MCP tools (`search_genes`, `search_proteins`) |
| Get detailed records | MCP tools (`get_gene`, `get_protein`, `get_compound`) |
| Find relationships | Curl (ChEMBL /mechanism, STRING /enrichment) |
| Validate findings | BioGRID ORCS, PubMed |
| Persist results | Graphiti (`add_memory`) |

### 4. Document Your Journey

Create validation files in `competency-validations/` that capture:
- API calls made
- Key findings
- Unexpected discoveries
- Limitations encountered

## What NOT to Do

- **Don't hallucinate** - If an API doesn't return data, say so
- **Don't assume** - Verify each relationship with evidence
- **Don't skip provenance** - Every fact needs a source
- **Don't pre-load context** - Approach each question fresh

## Getting Started

1. **Choose a question** from `competency-questions-catalog.md`
2. **Read the workflow** outlined in that question
3. **Follow the skills** in `.claude/skills/`
4. **Document findings** in `competency-validations/`
5. **Persist the graph** to Graphiti with the appropriate `group_id`

## Optional: Review Prior Art

After completing a question, you may optionally review `docs/prior-art-api-patterns.md` to see how your approach aligns with established patterns in the field. This is for learning, not pre-loading.

---

## Questions Catalog

See `competency-questions-catalog.md` for the full list of 15 research questions spanning:

- Drug mechanisms (cq1, cq2)
- Gene networks (cq3, cq5, cq6)
- Therapeutics (cq4, cq10)
- Drug repurposing (cq7)
- Synthetic lethality (cq8, cq14)
- Drug safety (cq9)
- Pathway validation (cq11)
- Clinical landscape (cq12, cq13, cq15)

Pick one and start building.
