# Deployment Architecture Diagrams

> **Analysis Date:** 2026-01-05
> **Project:** Life Sciences MCP
> **Deployment Model:** Client-side MCP + Optional Cloud Gateway

## Overview

This document provides visual representations of the Life Sciences MCP deployment topology, resource relationships, and network architecture. The project supports two deployment modes:

1. **Local STDIO Mode** - Primary deployment for Claude Desktop integration
2. **HTTP Gateway Mode** - Optional cloud deployment via FastMCP Cloud

---

## Deployment Topology

### High-Level System Context

```mermaid
graph LR
    subgraph "User Layer"
        U1[Researchers]
        U2[AI Agents]
        U3[Applications]
    end

    subgraph "Interface Layer"
        CD[Claude Desktop<br/>STDIO]
        WA[Web Apps<br/>HTTP]
        API[API Clients<br/>JSON-RPC]
    end

    subgraph "MCP Layer"
        GW[Gateway Server<br/>39 Tools]
    end

    subgraph "Client Layer"
        CL[14 API Clients<br/>Async HTTP]
    end

    subgraph "External APIs"
        EA[12 Life Sciences<br/>Databases]
    end

    U1 & U2 & U3 --> CD & WA & API
    CD -->|STDIO| GW
    WA & API -->|HTTP| GW
    GW --> CL
    CL -->|HTTPS| EA

    classDef user fill:#e8eaf6,stroke:#3f51b5
    classDef interface fill:#e3f2fd,stroke:#1976d2
    classDef mcp fill:#c8e6c9,stroke:#2e7d32
    classDef client fill:#fff3e0,stroke:#f57c00
    classDef external fill:#fce4ec,stroke:#c2185b

    class U1,U2,U3 user
    class CD,WA,API interface
    class GW mcp
    class CL client
    class EA external
```

---

## Local Deployment Architecture

### STDIO Mode (Primary)

**What you're looking at:** Complete local deployment showing process boundaries and data flow.

```mermaid
graph TB
    subgraph "Host Machine"
        subgraph "Claude Desktop Process"
            CD[Claude Desktop]
        end

        subgraph "MCP Server Process"
            direction TB
            GW[Gateway Server<br/>gateway.py]

            subgraph "Gene Servers"
                HGNC[hgnc.py<br/>2 tools]
                ENS[ensembl.py<br/>3 tools]
                ENT[entrez.py<br/>3 tools]
            end

            subgraph "Protein Servers"
                UP[uniprot.py<br/>2 tools]
                STR[string.py<br/>3 tools]
                BG[biogrid.py<br/>2 tools]
            end

            subgraph "Compound Servers"
                CH[chembl.py<br/>3 tools]
                PC[pubchem.py<br/>2 tools]
            end

            subgraph "Drug Servers"
                IU[iuphar.py<br/>4 tools]
                DB[drugbank.py<br/>2 tools]
            end

            subgraph "Other Servers"
                OT[opentargets.py<br/>3 tools]
                WP[wikipathways.py<br/>4 tools]
                CT[clinicaltrials.py<br/>3 tools]
            end

            GW --> HGNC & ENS & ENT
            GW --> UP & STR & BG
            GW --> CH & PC
            GW --> IU & DB
            GW --> OT & WP & CT
        end

        CD <-->|STDIO<br/>JSON-RPC 2.0| GW
    end

    subgraph "Internet"
        API1[Gene APIs]
        API2[Protein APIs]
        API3[Compound APIs]
        API4[Drug APIs]
        API5[Other APIs]
    end

    HGNC & ENS & ENT -->|HTTPS| API1
    UP & STR & BG -->|HTTPS| API2
    CH & PC -->|HTTPS| API3
    IU & DB -->|HTTPS| API4
    OT & WP & CT -->|HTTPS| API5

    classDef desktop fill:#e8eaf6,stroke:#3f51b5
    classDef gateway fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef server fill:#e3f2fd,stroke:#1976d2
    classDef api fill:#fff3e0,stroke:#f57c00

    class CD desktop
    class GW gateway
    class HGNC,ENS,ENT,UP,STR,BG,CH,PC,IU,DB,OT,WP,CT server
    class API1,API2,API3,API4,API5 api
```

### Narrative

The local STDIO deployment runs as a single Python process spawned by Claude Desktop. The gateway server (`gateway.py`) acts as a facade, mounting all 12 domain servers with zero-overhead direct function calls (`as_proxy=False`). Communication uses JSON-RPC 2.0 over standard input/output streams.

**Key Characteristics:**
- **Single process** - All servers run in one Python interpreter
- **No network overhead** - Internal calls are direct function invocations
- **STDIO transport** - Bidirectional JSON-RPC over stdin/stdout
- **Async I/O** - `httpx` for concurrent external API calls

---

## Cloud Deployment Architecture

### HTTP Gateway Mode (Optional)

**What you're looking at:** FastMCP Cloud deployment with HTTP transport.

```mermaid
graph TB
    subgraph "Clients"
        C1[Claude Desktop]
        C2[Web Application]
        C3[Python Script]
        C4[Other MCP Client]
    end

    subgraph "Internet"
        LB[Load Balancer<br/>FastMCP Cloud]
    end

    subgraph "FastMCP Cloud Infrastructure"
        subgraph "Gateway Instance"
            GW[gateway.py:mcp<br/>HTTP Endpoint]

            subgraph "Mounted Servers"
                S1[hgnc_*]
                S2[uniprot_*]
                S3[chembl_*]
                S4[opentargets_*]
                S5[string_*]
                S6[biogrid_*]
                S7[ensembl_*]
                S8[entrez_*]
                S9[pubchem_*]
                S10[iuphar_*]
                S11[wikipathways_*]
                S12[clinicaltrials_*]
            end
        end

        ENV[Environment<br/>Variables]
        LOG[Logging<br/>Service]
    end

    subgraph "External APIs"
        EA1[rest.genenames.org]
        EA2[rest.uniprot.org]
        EA3[www.ebi.ac.uk/chembl]
        EA4[platform.opentargets.org]
        EA5[string-db.org]
        EA6[thebiogrid.org]
        EA7[rest.ensembl.org]
        EA8[eutils.ncbi.nlm.nih.gov]
        EA9[pubchem.ncbi.nlm.nih.gov]
        EA10[guidetopharmacology.org]
        EA11[wikipathways.org]
        EA12[clinicaltrials.gov]
    end

    C1 & C2 & C3 & C4 -->|HTTPS| LB
    LB --> GW
    GW --> S1 & S2 & S3 & S4 & S5 & S6
    GW --> S7 & S8 & S9 & S10 & S11 & S12
    GW -.-> ENV & LOG

    S1 --> EA1
    S2 --> EA2
    S3 --> EA3
    S4 --> EA4
    S5 --> EA5
    S6 --> EA6
    S7 --> EA7
    S8 --> EA8
    S9 --> EA9
    S10 --> EA10
    S11 --> EA11
    S12 --> EA12

    classDef client fill:#e8eaf6,stroke:#3f51b5
    classDef lb fill:#ffcdd2,stroke:#c62828
    classDef gateway fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef server fill:#e3f2fd,stroke:#1976d2
    classDef infra fill:#f5f5f5,stroke:#9e9e9e
    classDef api fill:#fff3e0,stroke:#f57c00

    class C1,C2,C3,C4 client
    class LB lb
    class GW gateway
    class S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12 server
    class ENV,LOG infra
    class EA1,EA2,EA3,EA4,EA5,EA6,EA7,EA8,EA9,EA10,EA11,EA12 api
```

### Narrative

The HTTP deployment mode uses FastMCP Cloud's managed infrastructure. The gateway server is deployed as an HTTP endpoint accessible via `https://lifesciences.fastmcp.app/mcp`. Multiple clients can connect simultaneously, sharing the same server instance.

**Key Characteristics:**
- **HTTP transport** - JSON-RPC over HTTPS
- **Managed infrastructure** - FastMCP Cloud handles scaling, SSL, logging
- **Multi-client** - Single endpoint serves multiple clients
- **Environment variables** - API keys injected at deployment

---

## Resource Relationships

### Server-Client-API Mapping

```mermaid
graph LR
    subgraph "MCP Servers"
        S1[hgnc.py]
        S2[uniprot.py]
        S3[chembl.py]
        S4[opentargets.py]
        S5[string.py]
        S6[biogrid.py]
        S7[ensembl.py]
        S8[entrez.py]
        S9[pubchem.py]
        S10[iuphar.py]
        S11[wikipathways.py]
        S12[clinicaltrials.py]
        S13[drugbank.py]
    end

    subgraph "API Clients"
        C1[HGNCClient]
        C2[UniProtClient]
        C3[ChEMBLClient]
        C4[OpenTargetsClient]
        C5[STRINGClient]
        C6[BioGridClient]
        C7[EnsemblClient]
        C8[EntrezClient]
        C9[PubChemClient]
        C10[IUPHARClient]
        C11[WikiPathwaysClient]
        C12[ClinicalTrialsClient]
        C13[DrugBankClient]
    end

    subgraph "External APIs"
        A1[rest.genenames.org]
        A2[rest.uniprot.org]
        A3[www.ebi.ac.uk/chembl]
        A4[api.platform.opentargets.org]
        A5[string-db.org]
        A6[webservice.thebiogrid.org]
        A7[rest.ensembl.org]
        A8[eutils.ncbi.nlm.nih.gov]
        A9[pubchem.ncbi.nlm.nih.gov]
        A10[www.guidetopharmacology.org]
        A11[webservice.wikipathways.org]
        A12[clinicaltrials.gov]
        A13[api.drugbank.com]
    end

    S1 --> C1 --> A1
    S2 --> C2 --> A2
    S3 --> C3 --> A3
    S4 --> C4 --> A4
    S5 --> C5 --> A5
    S6 --> C6 --> A6
    S7 --> C7 --> A7
    S8 --> C8 --> A8
    S9 --> C9 --> A9
    S10 --> C10 --> A10
    S11 --> C11 --> A11
    S12 --> C12 --> A12
    S13 --> C13 --> A13

    classDef server fill:#c8e6c9,stroke:#2e7d32
    classDef client fill:#e3f2fd,stroke:#1976d2
    classDef api fill:#fff3e0,stroke:#f57c00

    class S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13 server
    class C1,C2,C3,C4,C5,C6,C7,C8,C9,C10,C11,C12,C13 client
    class A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,A11,A12,A13 api
```

### Narrative

The architecture follows a strict **1:1:1 mapping**: each MCP server has exactly one API client, which communicates with exactly one external API. This pattern ensures:

- **Clear ownership** - Each server owns its domain
- **Independent scaling** - Servers can be deployed individually
- **Isolation** - API failures are contained to their domain

---

## Network Architecture

### Data Flow Diagram

```mermaid
sequenceDiagram
    participant User as User/Agent
    participant CD as Claude Desktop
    participant GW as Gateway Server
    participant CL as API Client
    participant API as External API

    User->>CD: Natural language query
    CD->>GW: JSON-RPC tool call<br/>(STDIO or HTTP)

    activate GW
    GW->>GW: Route to server<br/>by prefix

    GW->>CL: Call client method
    activate CL

    CL->>API: HTTPS request
    activate API
    API-->>CL: JSON response
    deactivate API

    CL->>CL: Parse response
    CL-->>GW: Domain model
    deactivate CL

    GW->>GW: Serialize to JSON
    GW-->>CD: JSON-RPC response
    deactivate GW

    CD-->>User: Formatted answer
```

### Port and Protocol Summary

| Component | Protocol | Port | Notes |
|-----------|----------|------|-------|
| Claude Desktop ↔ Gateway | STDIO | N/A | Process pipes |
| HTTP Clients ↔ Gateway | HTTP/2 | 443 | FastMCP Cloud |
| Gateway ↔ External APIs | HTTPS | 443 | REST/GraphQL |

---

## Deployment Configuration

### File Structure

```mermaid
graph TB
    subgraph "Project Root"
        PY[pyproject.toml<br/>Dependencies]
        FM[fastmcp.json<br/>Cloud config]
        ENV[.env.example<br/>API keys]
    end

    subgraph "Source Code"
        subgraph "src/lifesciences_mcp"
            INIT[__init__.py<br/>Exports]

            subgraph "servers/"
                GW[gateway.py<br/>Unified entry]
                S1[hgnc.py]
                S2[uniprot.py]
                S3[...12 more]
            end

            subgraph "clients/"
                CB[base.py<br/>Base client]
                C1[hgnc.py]
                C2[uniprot.py]
                C3[...12 more]
            end

            subgraph "models/"
                M1[envelopes.py]
                M2[genes.py]
                M3[proteins.py]
                M4[compounds.py]
                M5[xrefs.py]
            end
        end
    end

    PY --> INIT
    FM --> GW
    ENV --> GW
    GW --> S1 & S2 & S3
    S1 & S2 & S3 --> C1 & C2 & C3
    C1 & C2 & C3 --> CB
    S1 & S2 & S3 --> M1 & M2 & M3 & M4 & M5

    classDef config fill:#fff3e0,stroke:#f57c00
    classDef server fill:#c8e6c9,stroke:#2e7d32
    classDef client fill:#e3f2fd,stroke:#1976d2
    classDef model fill:#f3e5f5,stroke:#7b1fa2

    class PY,FM,ENV config
    class GW,S1,S2,S3 server
    class CB,C1,C2,C3 client
    class M1,M2,M3,M4,M5 model
```

---

## Scaling Architecture

### Horizontal Scaling (Future)

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Application<br/>Load Balancer]
    end

    subgraph "Gateway Instances"
        GW1[Gateway #1]
        GW2[Gateway #2]
        GW3[Gateway #3]
    end

    subgraph "Shared State"
        CACHE[Redis Cache<br/>Rate Limit State]
    end

    subgraph "External APIs"
        EA[12 Life Sciences<br/>Databases]
    end

    LB --> GW1 & GW2 & GW3
    GW1 & GW2 & GW3 --> CACHE
    GW1 & GW2 & GW3 --> EA

    classDef lb fill:#ffcdd2,stroke:#c62828
    classDef gw fill:#c8e6c9,stroke:#2e7d32
    classDef cache fill:#e1f5fe,stroke:#0288d1
    classDef api fill:#fff3e0,stroke:#f57c00

    class LB lb
    class GW1,GW2,GW3 gw
    class CACHE cache
    class EA api
```

### Narrative

For high-availability deployments, the gateway can be horizontally scaled behind a load balancer. The stateless architecture allows any instance to handle any request. A shared Redis cache would coordinate rate limiting across instances to avoid exceeding external API limits.

---

## Security Architecture

### Authentication & Authorization Flow

```mermaid
graph LR
    subgraph "Client"
        USER[User]
        APP[Application]
    end

    subgraph "Transport Security"
        TLS[TLS 1.3<br/>Encryption]
    end

    subgraph "Gateway"
        GW[MCP Gateway]
        AUTH[No Auth<br/>Required]
    end

    subgraph "API Keys"
        ENV[Environment<br/>Variables]
        K1[BIOGRID_API_KEY]
        K2[NCBI_API_KEY]
        K3[DRUGBANK_API_KEY]
    end

    subgraph "External APIs"
        API[External APIs]
    end

    USER --> APP
    APP -->|HTTPS| TLS --> GW
    GW --> AUTH
    AUTH -->|Read| ENV
    ENV --> K1 & K2 & K3
    GW -->|HTTPS + API Key| API

    classDef client fill:#e8eaf6,stroke:#3f51b5
    classDef security fill:#ffcdd2,stroke:#c62828
    classDef gateway fill:#c8e6c9,stroke:#2e7d32
    classDef key fill:#fff3e0,stroke:#f57c00
    classDef api fill:#e1f5fe,stroke:#0288d1

    class USER,APP client
    class TLS,AUTH security
    class GW gateway
    class ENV,K1,K2,K3 key
    class API api
```

### Security Considerations

| Layer | Protection | Implementation |
|-------|------------|----------------|
| **Transport** | TLS 1.3 | FastMCP Cloud / HTTPS |
| **Gateway** | No auth (open) | Rely on client-side security |
| **API Keys** | Environment variables | `.env` file, not in code |
| **Rate Limiting** | Client-side | Built into API clients |
| **Input Validation** | Pydantic models | Type enforcement |

---

## Monitoring & Observability

### Logging Architecture

```mermaid
graph LR
    subgraph "Application"
        GW[Gateway Server]
        CL[API Clients]
    end

    subgraph "FastMCP Logging"
        LOG[Structured Logs<br/>JSON Format]
    end

    subgraph "Metrics"
        M1[Request Count]
        M2[Response Time]
        M3[Error Rate]
        M4[API Latency]
    end

    subgraph "Alerting"
        ALERT[Alerts<br/>Rate Limit, Errors]
    end

    GW --> LOG
    CL --> LOG
    LOG --> M1 & M2 & M3 & M4
    M3 --> ALERT

    classDef app fill:#c8e6c9,stroke:#2e7d32
    classDef log fill:#e3f2fd,stroke:#1976d2
    classDef metric fill:#fff3e0,stroke:#f57c00
    classDef alert fill:#ffcdd2,stroke:#c62828

    class GW,CL app
    class LOG log
    class M1,M2,M3,M4 metric
    class ALERT alert
```

### Key Metrics

| Metric | Description | Threshold |
|--------|-------------|-----------|
| `request_count` | Total tool invocations | N/A |
| `response_time_ms` | End-to-end latency | < 5000ms |
| `error_rate` | Failed requests | < 5% |
| `api_latency_ms` | External API response time | < 3000ms |
| `rate_limit_hits` | Rate limit encounters | Log only |

---

## Summary Diagram

### Complete Architecture Overview

```mermaid
graph TB
    subgraph "Users"
        U[Researchers<br/>AI Agents]
    end

    subgraph "Interfaces"
        CD[Claude Desktop]
        WEB[Web Apps]
    end

    subgraph "Life Sciences MCP"
        GW[Gateway Server<br/>39 Tools]

        subgraph "Domain Servers"
            GENE[Gene<br/>8 tools]
            PROT[Protein<br/>5 tools]
            COMP[Compound<br/>5 tools]
            DRUG[Drug<br/>6 tools]
            TARG[Target<br/>3 tools]
            PATH[Pathway<br/>7 tools]
            CLIN[Clinical<br/>3 tools]
        end
    end

    subgraph "External APIs"
        EA[12 Life Sciences<br/>Databases]
    end

    U --> CD & WEB
    CD -->|STDIO| GW
    WEB -->|HTTP| GW
    GW --> GENE & PROT & COMP & DRUG & TARG & PATH & CLIN
    GENE & PROT & COMP & DRUG & TARG & PATH & CLIN -->|HTTPS| EA

    classDef user fill:#e8eaf6,stroke:#3f51b5
    classDef interface fill:#e3f2fd,stroke:#1976d2
    classDef gateway fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    classDef server fill:#fff3e0,stroke:#f57c00
    classDef api fill:#fce4ec,stroke:#c2185b

    class U user
    class CD,WEB interface
    class GW gateway
    class GENE,PROT,COMP,DRUG,TARG,PATH,CLIN server
    class EA api
```

---

## Deployment Checklist

### Local Deployment
- [ ] Clone repository
- [ ] Install uv package manager
- [ ] Run `uv sync` to install dependencies
- [ ] Configure `.env` with API keys (optional)
- [ ] Test with `uv run fastmcp run src/lifesciences_mcp/servers/gateway.py`
- [ ] Configure Claude Desktop `claude_desktop_config.json`

### Cloud Deployment
- [ ] Create `fastmcp.json` configuration (exists)
- [ ] Set environment variables in FastMCP Cloud
- [ ] Deploy with `fastmcp deploy`
- [ ] Verify endpoint accessibility
- [ ] Test with sample tool call

---

*Generated: 2026-01-05*
*Analysis Scope: Deployment topology, resource relationships, network architecture*
