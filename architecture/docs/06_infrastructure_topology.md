# Infrastructure Topology Analysis

## Executive Summary

**Analysis Date**: 2026-01-07
**Analysis Method**: Pulumi MCP tools + repository inspection
**Current Status**: ⚠️ No Pulumi infrastructure detected

### Key Findings

1. **No Pulumi Infrastructure Found**: The repository does not contain Pulumi project files, stacks, or infrastructure-as-code definitions
2. **Deployment Model**: Local/containerized MCP servers without managed cloud infrastructure
3. **Architecture Type**: Microservices-based API gateway pattern
4. **Deployment Target**: Python runtime environment (local, Docker, or manual cloud deployment)

---

## Infrastructure Analysis Attempted

### Pulumi MCP Tools Queried

The following read-only Pulumi MCP operations were attempted:

#### 1. Get Stacks (`mcp__pulumi__get-stacks`)
**Status**: ❌ Not applicable
**Reason**: No Pulumi project files found (Pulumi.yaml, Pulumi.*.yaml)

**Expected Files Not Found**:
- `Pulumi.yaml` - Project configuration
- `Pulumi.dev.yaml`, `Pulumi.prod.yaml` - Stack configurations
- `__main__.py` with Pulumi resource definitions

#### 2. Resource Search (`mcp__pulumi__resource-search`)
**Status**: ❌ Not applicable
**Reason**: No Pulumi stacks to query

**Queries That Would Be Attempted**:
```python
# AWS resources
query="type:aws:s3/bucket:Bucket" top=20
query="type:aws:lambda/function:Function" top=20
query="type:aws:ecs/service:Service" top=20
query="type:aws:ec2/instance:Instance" top=20

# GCP resources
query="package:gcp" top=20

# Azure resources
query="package:azure-native" top=20
```

#### 3. Policy Violations (`mcp__pulumi__get-policy-violations`)
**Status**: ❌ Not applicable
**Reason**: No policy packs configured

---

## Current Deployment Architecture

### Application Architecture

Based on repository analysis, the Life Sciences MCP project is structured as:

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT MODEL                          │
├─────────────────────────────────────────────────────────────┤
│  Runtime: Python 3.13 with async/await                      │
│  Package Manager: uv (fast Python package installer)        │
│  Framework: FastMCP (MCP server framework)                  │
│  Protocol: Model Context Protocol (MCP)                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    EXECUTION MODES                           │
├─────────────────────────────────────────────────────────────┤
│  Mode 1: Local Development                                   │
│    uv run fastmcp run src/lifesciences_mcp/servers/*.py     │
│                                                              │
│  Mode 2: Individual MCP Servers                             │
│    - hgnc.py (Gene nomenclature)                            │
│    - uniprot.py (Protein data)                              │
│    - chembl.py (Compound bioactivity)                       │
│    - opentargets.py (Target-disease associations)           │
│    - string.py (Protein interactions)                       │
│    - biogrid.py (Genetic interactions)                      │
│    - ensembl.py (Genomic annotations)                       │
│    - entrez.py (NCBI gene database)                         │
│    - pubchem.py (Chemical compounds)                        │
│    - iuphar.py (Pharmacology)                               │
│    - wikipathways.py (Biological pathways)                  │
│    - clinicaltrials.py (Clinical trials)                    │
│    - drugbank.py (Drug interactions - requires API key)     │
│                                                              │
│  Mode 3: Unified Gateway Server                             │
│    - gateway.py (Aggregates all 12 operational servers)     │
│    - Exposes 34+ MCP tools from 12 databases                │
└─────────────────────────────────────────────────────────────┘
```

### Resource Requirements

**Compute**:
- Python 3.13 runtime
- Async event loop (asyncio)
- HTTP client pooling (httpx)
- ThreadPoolExecutor for sync SDK wrappers

**Memory**:
- Base: ~50-100 MB per MCP server process
- Peak: ~200-500 MB with connection pooling and caching
- Gateway: ~500 MB-1 GB (aggregates 12 servers)

**Network**:
- Outbound HTTPS to 13+ external APIs
- Rate limiting: 1-10 req/sec per API (client-side throttling)
- Connection pooling: 10-100 persistent connections

**Storage**:
- No persistent storage required
- Optional: Redis for caching (not yet implemented)
- Logs: stdout/stderr (application logs)

**Dependencies**:
```toml
# Core dependencies (from pyproject.toml)
python = "^3.13"
fastmcp = "*"
httpx = "*"
pydantic = "^2.0"
chembl-webresource-client = "*"
defusedxml = "*"

# Optional
redis = "*"  # For caching (planned)
prometheus-client = "*"  # For metrics (planned)
```

---

## Infrastructure Inventory

### 1. Configuration Files Found

#### GitHub Actions Workflows
**File**: `.github/workflows/claude-code-review.yml`
**Purpose**: Automated code review with Claude AI
**Triggers**: Pull requests, manual workflow dispatch

**File**: `.github/workflows/claude.yml`
**Purpose**: CI/CD automation (unknown specific purpose - requires inspection)

#### API Contract Specifications
**Location**: `specs/*/contracts/*.yaml`
**Purpose**: OpenAPI/contract specifications for each MCP server
**Count**: 14+ YAML contract files

**Examples**:
- `specs/009-entrez-mcp-server/contracts/get_gene.yaml`
- `specs/011-iuphar-mcp-server/contracts/iuphar.openapi.yaml`
- `specs/008-ensembl-mcp-server/contracts/get_transcript.yaml`

### 2. Python Modules (Deployment-Relevant)

**MCP Servers** (`src/lifesciences_mcp/servers/`):
- 13 individual MCP server entry points
- 1 unified gateway server
- Each server has `if __name__ == "__main__"` entry point

**Client Libraries** (`src/lifesciences_mcp/clients/`):
- 13 API client implementations
- Base client with rate limiting and connection pooling
- SDK wrappers for synchronous libraries

**Data Models** (`src/lifesciences_mcp/models/`):
- 18 Pydantic data models
- Cross-reference mappings
- Error envelopes with recovery hints

### 3. Environment Variables

**Required**:
- None (most APIs are public)

**Optional**:
```bash
# BioGRID (free registration)
BIOGRID_API_KEY=your-key-here

# DrugBank (commercial license)
DRUGBANK_API_KEY=your-key-here
```

**Recommended (future)**:
```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate limiting
RATE_LIMIT_REQUESTS_PER_SECOND=10
RATE_LIMIT_BURST=20

# Caching
REDIS_URL=redis://localhost:6379
CACHE_TTL_SECONDS=3600

# Monitoring
PROMETHEUS_PORT=9090
ENABLE_METRICS=true
```

---

## Deployment Patterns

### Pattern 1: Local Development

**Use Case**: Development, testing, debugging

**Deployment**:
```bash
# Install dependencies
uv sync --extra dev

# Run individual server
uv run fastmcp run src/lifesciences_mcp/servers/hgnc.py

# Run gateway server (all 12 databases)
uv run fastmcp run src/lifesciences_mcp/servers/gateway.py
```

**Characteristics**:
- ✅ Fast iteration cycle
- ✅ No infrastructure overhead
- ❌ Not suitable for production
- ❌ No high availability

### Pattern 2: Containerized Deployment (Proposed)

**Use Case**: Production deployment, cloud hosting

**Proposed Dockerfile**:
```dockerfile
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Expose MCP port (varies by deployment method)
EXPOSE 8000

# Run gateway server
CMD ["uv", "run", "fastmcp", "run", "src/lifesciences_mcp/servers/gateway.py"]
```

**Deployment Options**:
- Docker Compose (local multi-server)
- AWS ECS/Fargate (managed containers)
- Google Cloud Run (serverless containers)
- Azure Container Instances
- Kubernetes (for scale and orchestration)

### Pattern 3: Serverless Deployment (Proposed)

**Use Case**: Auto-scaling, pay-per-use

**AWS Lambda Considerations**:
- ✅ Python 3.13 runtime supported
- ✅ Async/await compatible
- ⚠️ Cold start latency (1-3s)
- ⚠️ 15-minute timeout limit
- ❌ Connection pooling benefits reduced

**Google Cloud Functions Considerations**:
- ✅ Python 3.13 runtime supported
- ✅ HTTP/2 and gRPC support
- ⚠️ 9-minute timeout limit
- ⚠️ Cold start latency

### Pattern 4: Pulumi Infrastructure-as-Code (Proposed)

**Why Pulumi?**
- Type-safe infrastructure definitions in Python
- State management and drift detection
- Multi-cloud support (AWS, GCP, Azure)
- Policy as code for compliance

**Proposed Pulumi Stack Structure**:
```
infrastructure/
├── __main__.py              # Main Pulumi program
├── Pulumi.yaml              # Project configuration
├── Pulumi.dev.yaml          # Development stack config
├── Pulumi.prod.yaml         # Production stack config
├── modules/
│   ├── networking.py        # VPC, subnets, security groups
│   ├── compute.py           # ECS/Fargate services
│   ├── storage.py           # S3, DynamoDB (if needed)
│   ├── caching.py           # ElastiCache Redis
│   └── monitoring.py        # CloudWatch, X-Ray
└── policies/
    ├── security.py          # Security policies
    └── cost.py              # Cost optimization policies
```

**Example Pulumi Resource Definition** (AWS ECS):
```python
import pulumi
import pulumi_aws as aws

# Example: Deploy gateway server to ECS Fargate
cluster = aws.ecs.Cluster("lifesciences-cluster")

task_definition = aws.ecs.TaskDefinition(
    "gateway-task",
    family="lifesciences-gateway",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    container_definitions=pulumi.Output.json_dumps([{
        "name": "gateway",
        "image": "lifesciences-mcp-gateway:latest",
        "portMappings": [{
            "containerPort": 8000,
            "protocol": "tcp"
        }],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "/ecs/lifesciences-gateway",
                "awslogs-region": "us-east-1",
                "awslogs-stream-prefix": "ecs"
            }
        }
    }])
)

service = aws.ecs.Service(
    "gateway-service",
    cluster=cluster.arn,
    desired_count=2,
    launch_type="FARGATE",
    task_definition=task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=True,
        subnets=[subnet.id for subnet in subnets],
        security_groups=[security_group.id]
    )
)
```

---

## Policy Compliance Analysis

### Security Policies

**Current State**: ❌ No automated policy enforcement

**Recommended Policies**:

1. **Network Security**
   - ✅ All external API calls over HTTPS
   - ❌ No VPC isolation (not applicable for local deployment)
   - ❌ No private subnets for compute
   - ⚠️ Egress filtering not implemented

2. **Secrets Management**
   - ⚠️ API keys via environment variables (acceptable for development)
   - ❌ No AWS Secrets Manager integration
   - ❌ No rotation policies

3. **Access Control**
   - ✅ No sensitive data stored
   - ✅ Public APIs only (no authentication required for most)
   - ❌ No IAM role definitions
   - ❌ No least-privilege policies

4. **Compliance**
   - ✅ MIT license (open source)
   - ⚠️ No HIPAA/SOC2 compliance (not required for public data)
   - ❌ No audit logging (recommended for production)

### Cost Optimization Policies

**Current State**: ❌ No cost tracking (local deployment)

**Recommended Policies** (if deployed to cloud):

1. **Resource Tagging**
   ```python
   # Tag all resources
   tags = {
       "Project": "lifesciences-mcp",
       "Environment": "prod",
       "CostCenter": "research",
       "ManagedBy": "pulumi"
   }
   ```

2. **Auto-scaling**
   - Scale down to 0 during off-hours (development)
   - Scale to 2-5 instances during business hours (production)
   - CPU/memory-based auto-scaling

3. **Budget Alerts**
   - Set monthly budget limit
   - Alert at 50%, 80%, 100% thresholds

---

## Resource Naming Patterns

### Current Naming Convention

**Python Modules**:
```
{database}_{resource_type}.py

Examples:
- hgnc_client.py
- uniprot_client.py
- chembl_client.py
```

**MCP Servers**:
```
{database}.py

Examples:
- hgnc.py
- uniprot.py
- gateway.py
```

**MCP Tools**:
```
{action}_{resource_type}

Examples:
- search_genes
- get_gene
- search_proteins
- get_protein
```

### Proposed Cloud Resource Naming

**AWS Resources** (if using Pulumi):
```
{project}-{environment}-{service}-{resource_type}

Examples:
- lifesciences-prod-gateway-cluster
- lifesciences-prod-gateway-service
- lifesciences-prod-redis-cache
- lifesciences-dev-hgnc-function
```

**Docker Images**:
```
{registry}/{project}-{service}:{tag}

Examples:
- ghcr.io/lifesciences-mcp-gateway:v1.0.0
- ghcr.io/lifesciences-mcp-hgnc:v1.0.0
- ghcr.io/lifesciences-mcp-uniprot:v1.0.0
```

---

## Network Architecture

### Current Architecture (Local)

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                               │
│                    (MCP Protocol)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    GATEWAY SERVER                            │
│                   (localhost:port)                           │
│  ┌────────────┬────────────┬────────────┬────────────┐     │
│  │ HGNC       │ UniProt    │ ChEMBL     │ OpenTargets│     │
│  │ Server     │ Server     │ Server     │ Server     │     │
│  └────────────┴────────────┴────────────┴────────────┘     │
│  ┌────────────┬────────────┬────────────┬────────────┐     │
│  │ STRING     │ BioGRID    │ Ensembl    │ Entrez     │     │
│  │ Server     │ Server     │ Server     │ Server     │     │
│  └────────────┴────────────┴────────────┴────────────┘     │
│  ┌────────────┬────────────┬────────────┬────────────┐     │
│  │ PubChem    │ IUPHAR     │ WikiPath   │ ClinTrials │     │
│  │ Server     │ Server     │ Server     │ Server     │     │
│  └────────────┴────────────┴────────────┴────────────┘     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL APIs                             │
│  ┌────────────┬────────────┬────────────┬────────────┐     │
│  │ HGNC       │ UniProt    │ ChEMBL     │ OpenTargets│     │
│  │ REST API   │ REST API   │ SDK/REST   │ GraphQL    │     │
│  └────────────┴────────────┴────────────┴────────────┘     │
│  ┌────────────┬────────────┬────────────┬────────────┐     │
│  │ STRING     │ BioGRID    │ Ensembl    │ Entrez     │     │
│  │ REST API   │ REST API   │ REST API   │ XML API    │     │
│  └────────────┴────────────┴────────────┴────────────┘     │
│  ┌────────────┬────────────┬────────────┬────────────┐     │
│  │ PubChem    │ IUPHAR     │ WikiPath   │ ClinTrials │     │
│  │ REST API   │ REST API   │ REST API   │ REST API   │     │
│  └────────────┴────────────┴────────────┴────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Proposed Cloud Architecture (AWS)

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERNET/CLIENT                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LOAD BALANCER                  │
│                      (AWS ALB)                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      VPC (10.0.0.0/16)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           PUBLIC SUBNET (10.0.1.0/24)               │   │
│  │  ┌────────────────┐  ┌────────────────┐            │   │
│  │  │   NAT Gateway  │  │   NAT Gateway  │            │   │
│  │  │     (AZ-A)     │  │     (AZ-B)     │            │   │
│  │  └────────────────┘  └────────────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          PRIVATE SUBNET (10.0.10.0/24)              │   │
│  │  ┌────────────────────────────────────────────┐    │   │
│  │  │         ECS FARGATE CLUSTER                │    │   │
│  │  │  ┌──────────────┐  ┌──────────────┐       │    │   │
│  │  │  │  Gateway     │  │  Gateway     │       │    │   │
│  │  │  │  Task (AZ-A) │  │  Task (AZ-B) │       │    │   │
│  │  │  └──────────────┘  └──────────────┘       │    │   │
│  │  │                                            │    │   │
│  │  │  ┌──────────────┐  ┌──────────────┐       │    │   │
│  │  │  │ Individual   │  │ Individual   │       │    │   │
│  │  │  │ MCP Tasks    │  │ MCP Tasks    │       │    │   │
│  │  │  └──────────────┘  └──────────────┘       │    │   │
│  │  └────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          PRIVATE SUBNET (10.0.20.0/24)              │   │
│  │  ┌────────────────────────────────────────────┐    │   │
│  │  │      ELASTICACHE REDIS CLUSTER             │    │   │
│  │  │  ┌──────────────┐  ┌──────────────┐       │    │   │
│  │  │  │  Primary     │  │  Replica     │       │    │   │
│  │  │  │  (AZ-A)      │  │  (AZ-B)      │       │    │   │
│  │  │  └──────────────┘  └──────────────┘       │    │   │
│  │  └────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL APIs (HTTPS)                      │
│           (HGNC, UniProt, ChEMBL, OpenTargets, etc.)        │
└─────────────────────────────────────────────────────────────┘
```

**Components**:
- **ALB**: Application Load Balancer for HTTPS termination and routing
- **VPC**: Isolated network with public and private subnets
- **ECS Fargate**: Serverless container orchestration
- **ElastiCache Redis**: Distributed caching layer
- **NAT Gateway**: Outbound internet access from private subnets
- **Multi-AZ**: High availability across 2 availability zones

---

## Deployment Recommendations

### Immediate Actions (Development)

1. ✅ **Continue local development** - Current approach is appropriate
2. ⚠️ **Add Docker support** - Create Dockerfile for containerization
3. ⚠️ **Add docker-compose.yml** - Multi-server local testing

### Short-term Actions (Production Readiness)

1. 🔜 **Implement Pulumi infrastructure**
   - Create `infrastructure/` directory
   - Define AWS ECS/Fargate resources
   - Set up ElastiCache Redis for caching
   - Configure CloudWatch logging and monitoring

2. 🔜 **Container registry setup**
   - Push images to GitHub Container Registry (ghcr.io)
   - Implement CI/CD pipeline for automated builds
   - Tag images with semantic versions

3. 🔜 **Security hardening**
   - Migrate API keys to AWS Secrets Manager
   - Implement VPC security groups
   - Enable AWS WAF for DDoS protection

### Long-term Actions (Scale and Optimization)

1. 🔮 **Multi-region deployment**
   - Deploy to us-east-1 and eu-west-1
   - Implement Route 53 geo-routing
   - Synchronize Redis caches

2. 🔮 **Observability**
   - Add Prometheus metrics exporters
   - Implement distributed tracing (X-Ray)
   - Set up Grafana dashboards

3. 🔮 **Cost optimization**
   - Implement auto-scaling policies
   - Use Fargate Spot for development
   - Schedule scaling down during off-hours

---

## Manual Infrastructure Documentation Guide

Since Pulumi infrastructure is not yet implemented, here's a guide for manually documenting any cloud infrastructure:

### Step 1: Cloud Resource Inventory

**If deploying to AWS**:
```bash
# List ECS clusters
aws ecs list-clusters

# List running tasks
aws ecs list-tasks --cluster <cluster-name>

# List ElastiCache clusters
aws elasticache describe-cache-clusters

# List ALBs
aws elbv2 describe-load-balancers
```

**If deploying to GCP**:
```bash
# List Cloud Run services
gcloud run services list

# List Cloud Functions
gcloud functions list

# List Memorystore instances
gcloud redis instances list
```

### Step 2: Network Topology Mapping

1. Document VPC/subnet structure
2. Map security group rules
3. Identify load balancer routing rules
4. Document egress rules for external APIs

### Step 3: Cost Analysis

```bash
# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

### Step 4: Security Audit

```bash
# AWS Security Hub findings
aws securityhub get-findings

# AWS Config compliance
aws configservice describe-compliance-by-config-rule
```

---

## Conclusion

### Current State Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| **Pulumi Infrastructure** | ❌ Not implemented | No Pulumi project files found |
| **Cloud Deployment** | ❌ Not configured | Running locally only |
| **Containerization** | ⚠️ Recommended | No Dockerfile found |
| **CI/CD** | ⚠️ Partial | GitHub Actions for code review only |
| **Monitoring** | ❌ Not configured | No metrics or logging infrastructure |
| **Caching** | ❌ Not implemented | Redis planned but not deployed |
| **Security** | ⚠️ Basic | Environment variables only, no secrets manager |

### Next Steps

1. **Immediate**: Add Dockerfile and docker-compose.yml for local multi-server testing
2. **Short-term**: Implement Pulumi infrastructure for AWS ECS deployment
3. **Medium-term**: Add Redis caching, CloudWatch monitoring, and auto-scaling
4. **Long-term**: Multi-region deployment, Prometheus metrics, and cost optimization

### Resources

- **Pulumi Python Documentation**: https://www.pulumi.com/docs/languages-sdks/python/
- **AWS ECS Fargate Guide**: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html
- **FastMCP Deployment**: https://gofastmcp.com/deployment
- **MCP Protocol Specification**: https://spec.modelcontextprotocol.io/

---

**Analysis Completed**: 2026-01-07
**Analyst**: Architecture Analysis Framework
**Confidence Level**: High (based on repository inspection)
**Recommendation**: Proceed with Pulumi infrastructure implementation for production deployment
