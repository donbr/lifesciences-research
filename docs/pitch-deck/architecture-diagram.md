# Architecture Diagrams

This file contains Mermaid diagram sources for the Life Sciences MCP Platform pitch deck.

---

## 1. Three-Tier Architecture (MCP Nodes → curl Edges → Graphiti)

```mermaid
flowchart TB
    subgraph StreamAligned["STREAM-ALIGNED LAYER (Business Value)"]
        Q["'What therapeutic strategies exist for<br/>ARID1A-deficient cancers?'"]
        Users["Researchers · Domain Experts · Discovery Scientists"]
    end

    subgraph Specification["SPECIFICATION LAYER (Quality Gates)"]
        Spec["/speckit.specify"]
        Plan["/speckit.plan"]
        Impl["/speckit.implement"]
        Spec --> Plan --> Impl
    end

    subgraph Platform["PLATFORM LAYER (Encoded Expertise)"]
        subgraph Tier1["TIER 1: MCP NODES"]
            MCP["12 FastMCP Servers<br/>Canonical CURIEs + Cross-References"]
            HGNC["HGNC"]
            UniProt["UniProt"]
            ChEMBL["ChEMBL"]
            STRING["STRING"]
            More["...8 more"]
        end

        subgraph Tier2["TIER 2: CURL EDGES"]
            Skills["Platform Skills<br/>Bulk Edge Discovery"]
            Genomics["lifesciences-genomics"]
            Proteomics["lifesciences-proteomics"]
            Pharma["lifesciences-pharmacology"]
            Clinical["lifesciences-clinical"]
        end

        subgraph Tier3["TIER 3: GRAPHITI"]
            Graphiti["Research Memory<br/>Structured Episodes"]
        end
    end

    Q --> Specification
    Users --> Q
    Specification --> Platform

    MCP --> HGNC & UniProt & ChEMBL & STRING & More
    Skills --> Genomics & Proteomics & Pharma & Clinical

    Tier1 --> Tier2
    Tier2 --> Tier3

    style StreamAligned fill:#e3f2fd
    style Specification fill:#fff3e0
    style Platform fill:#e8f5e9
    style Tier1 fill:#c8e6c9
    style Tier2 fill:#a5d6a7
    style Tier3 fill:#81c784
```

---

## 2. Fuzzy-to-Fact Protocol Flow

```mermaid
sequenceDiagram
    participant Agent
    participant MCP as MCP Server
    participant API as Upstream API

    Note over Agent,API: Phase 1: Fuzzy Search
    Agent->>MCP: search_genes("BRCA1")
    MCP->>API: GET /search?q=BRCA1
    API-->>MCP: Raw results
    MCP-->>Agent: PaginationEnvelope<br/>[{id: "HGNC:1100", score: 1.0},<br/>{id: "HGNC:1101", score: 0.8}]

    Note over Agent: Agent selects top candidate

    Note over Agent,API: Phase 2: Strict Lookup
    Agent->>MCP: get_gene("HGNC:1100")
    MCP->>API: GET /fetch/hgnc_id/1100
    API-->>MCP: Complete record
    MCP-->>Agent: Gene{<br/>  id: "HGNC:1100",<br/>  symbol: "BRCA1",<br/>  cross_references: {<br/>    ensembl_gene: "ENSG00000012048",<br/>    uniprot: ["P38398"],<br/>    entrez: "672"<br/>  }<br/>}

    Note over Agent: Cross-references enable graph traversal
```

---

## 3. Cross-Reference Graph Traversal

```mermaid
graph LR
    subgraph HGNC["HGNC Server"]
        Gene["BRCA1<br/>HGNC:1100"]
    end

    subgraph UniProt["UniProt Server"]
        Protein["P38398<br/>UniProtKB:P38398"]
    end

    subgraph STRING["STRING Server"]
        Interaction["BRCA1-BARD1<br/>score: 0.999"]
    end

    subgraph ChEMBL["ChEMBL Server"]
        Drug["Olaparib<br/>CHEMBL:521686"]
    end

    subgraph ClinicalTrials["ClinicalTrials Server"]
        Trial["NCT:02489058<br/>Phase 3"]
    end

    Gene -->|"cross_ref.uniprot"| Protein
    Protein -->|"cross_ref.string"| Interaction
    Interaction -->|"target search"| Drug
    Drug -->|"trial search"| Trial

    style Gene fill:#e1f5fe
    style Protein fill:#fff3e0
    style Interaction fill:#e8f5e9
    style Drug fill:#f3e5f5
    style Trial fill:#fce4ec
```

---

## 4. Error Handling with Recovery Hints

```mermaid
flowchart TD
    A[Agent calls get_gene 'brca1'] --> B{CURIE Valid?}
    B -->|No| C[Return ErrorEnvelope]
    C --> D[error.code: UNRESOLVED_ENTITY]
    C --> E[error.recovery_hint:<br/>'Use search_genes first']
    B -->|Yes| F[Fetch from API]
    F --> G{API Response?}
    G -->|Success| H[Return Gene record]
    G -->|Not Found| I[Return ErrorEnvelope]
    I --> J[error.code: NOT_FOUND]
    I --> K[error.recovery_hint:<br/>'Check spelling or try broader search']
    G -->|Rate Limited| L[Return ErrorEnvelope]
    L --> M[error.code: RATE_LIMITED]
    L --> N[error.recovery_hint:<br/>'Retry after 60 seconds']

    E --> O[Agent self-corrects]
    O --> P[Agent calls search_genes 'brca1']
    P --> Q[Get ranked candidates]
    Q --> R[Agent calls get_gene 'HGNC:1100']
    R --> F

    style C fill:#ffcdd2
    style I fill:#ffcdd2
    style L fill:#ffcdd2
    style H fill:#c8e6c9
    style O fill:#fff9c4
```

---

## 5. ARID1A Synthetic Lethality Workflow

```mermaid
flowchart LR
    subgraph Step1["Step 1: Gene Resolution"]
        Q1["'ARID1A'"] --> S1["hgnc_search_genes"]
        S1 --> R1["HGNC:11110"]
    end

    subgraph Step2["Step 2: Cross-Reference"]
        R1 --> S2["get_gene"]
        S2 --> R2["ensembl_gene:<br/>ENSG00000117713"]
    end

    subgraph Step3["Step 3: Interactions"]
        R2 --> S3["string_get_interactions"]
        S3 --> R3["EZH2 (0.999)<br/>SMARCC1 (0.997)<br/>SMARCA4 (0.996)"]
    end

    subgraph Step4["Step 4: Drug Search"]
        R3 --> S4["chembl_search_compounds<br/>'EZH2 inhibitor'"]
        S4 --> R4["Tazemetostat<br/>CHEMBL:3414621"]
    end

    subgraph Step5["Step 5: Clinical Trials"]
        R4 --> S5["clinicaltrials_search_trials<br/>'Tazemetostat ARID1A'"]
        S5 --> R5["NCT:03348631<br/>Phase 2"]
    end

    subgraph Result["Knowledge Graph"]
        KG["Gene → Protein → Drug → Trial<br/>with full provenance"]
    end

    R5 --> KG

    style Step1 fill:#e1f5fe
    style Step2 fill:#e3f2fd
    style Step3 fill:#e8f5e9
    style Step4 fill:#f3e5f5
    style Step5 fill:#fce4ec
    style Result fill:#fff9c4
```

---

## 6. Platform Skills Layer

```mermaid
flowchart TB
    subgraph Agent["AI Agent"]
        Decision{"Choose<br/>Tool Type"}
    end

    subgraph MCP["MCP TOOLS<br/>(Verified Nodes)"]
        MCPTools["12 FastMCP Servers"]
        MCPBenefit["✓ CURIE validation<br/>✓ Error envelopes<br/>✓ Cross-references"]
    end

    subgraph Skills["PLATFORM SKILLS<br/>(Relationship Edges)"]
        SkillTools["curl-based workflows"]
        SkillBenefit["✓ Bulk operations<br/>✓ No protocol overhead<br/>✓ Direct API access"]
    end

    subgraph Memory["GRAPHITI<br/>(Research Memory)"]
        MemTools["add_memory / search_memory"]
        MemBenefit["✓ Persist findings<br/>✓ Structured episodes<br/>✓ Queryable journal"]
    end

    Decision -->|"Single entity lookup"| MCP
    Decision -->|"50+ edge discovery"| Skills
    Decision -->|"Store validated fact"| Memory

    MCPTools --> MCPBenefit
    SkillTools --> SkillBenefit
    MemTools --> MemBenefit

    style Agent fill:#e1f5fe
    style MCP fill:#c8e6c9
    style Skills fill:#a5d6a7
    style Memory fill:#81c784
```

---

## 7. Industry Standards Alignment

```mermaid
pie title Standards Compliance
    "TRAPI Compliant" : 85
    "TRAPI Deviated (Token Efficiency)" : 15
```

```mermaid
pie title Biolink Category Coverage
    "Covered (10 categories)" : 67
    "Missing GO/HPO/UBERON" : 33
```

---

## 8. Competency Question Complexity Distribution

```mermaid
pie title CQ Tier Distribution
    "Tier 1 (Simple)" : 3
    "Tier 2 (Medium)" : 9
    "Tier 3 (Complex)" : 3
```

---

## Usage Notes

### Rendering Mermaid Diagrams

These diagrams can be rendered:

1. **GitHub/GitLab**: Markdown preview renders Mermaid natively
2. **VS Code**: Install "Mermaid Preview" extension
3. **Online**: Use https://mermaid.live for interactive editing
4. **PDF Export**: Use Mermaid CLI (`mmdc`) or Slidev with Mermaid plugin

### Converting to Images

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Convert single diagram
mmdc -i architecture-diagram.md -o diagram.png -t neutral

# Convert with specific theme
mmdc -i architecture-diagram.md -o diagram.svg -t forest
```

### Recommended Themes

- **Presentation**: `neutral` or `default`
- **Print**: `neutral`
- **Dark mode**: `dark`

---

**Version:** 1.0
**Last Updated:** 2026-01-26
