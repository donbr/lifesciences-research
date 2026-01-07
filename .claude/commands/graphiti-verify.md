---
description: Run Day 1 verification sequence to confirm environment is working
allowed-tools:
  - mcp__graphiti-aura__get_status
  - mcp__neo4j-aura-cypher__read_neo4j_cypher
  - mcp__graphiti-aura__search_nodes
  - mcp__neo4j-aura-management__list_instances
  - mcp__neo4j-aura-management__get_instance_details
  - mcp__graphiti-docker__get_status
  - mcp__graphiti-docker__get_episodes
  - Bash(docker ps:*)
  - TodoWrite
---

Run the Day 1 verification sequence to confirm the environment is working.

## Instructions

Execute these checks in order. Report results but do NOT attempt fixes without user approval.

**Environments checked:**
- Production: Neo4j Aura via `graphiti-aura` MCP (Checks 1-4)
- Development: Docker Neo4j via `graphiti-docker` MCP (Check 5)

### Check 1: Server Health
```python
mcp__graphiti-aura__get_status()
```
**Expected:** Status OK with database connection confirmed.

### Check 2: Query Available Groups
```python
mcp__neo4j-aura-cypher__read_neo4j_cypher(
    query="MATCH (e:Episodic) RETURN DISTINCT e.group_id AS group_id, count(*) AS episodes ORDER BY episodes DESC"
)
```
**Expected:** List of group_ids with episode counts. Primary groups are `graphiti_meta_knowledge` and `graphiti_reference_docs`.

**Note:** This check requires the neo4j-aura-cypher MCP server running. If unavailable, start it with:
```bash
docker compose -f docker/docker-compose-neo4j-mcp.yml --env-file .env up -d
```

### Check 3: Test Semantic Search
```python
mcp__graphiti-aura__search_nodes(
    query="graphiti best practices",
    group_ids=["graphiti_meta_knowledge"],
    max_nodes=5
)
```
**Expected:** Returns relevant entity nodes.

### Check 4: Neo4j Aura Health (Optional)
```python
# First, get available instances
mcp__neo4j-aura-management__list_instances()

# Then check health of your instance (replace with your instance ID)
mcp__neo4j-aura-management__get_instance_details(instance_ids=["your-instance-id"])
```
**Expected:**
- Instance status: "running"
- Memory allocation appropriate for workload
- Graph size metrics (nodes/relationships) reported
- Connection URL accessible

**Health Indicators:**
- ✅ Status "running" with graph nodes/relationships counts
- ⚠️ Warn if memory is 1GB and graph has >5000 nodes (may need scaling)
- ❌ Status not "running" or connection errors

**Note:** This check requires the neo4j-aura-management MCP server running. If unavailable, start it with:
```bash
docker compose -f docker/docker-compose-neo4j-mcp.yml --env-file .env up -d
```

### Check 5: Local Docker Neo4j (Optional)
```python
# Check if local Docker Neo4j is running
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | grep -E "(neo4j|7474|7687|graphiti)"

# Check graphiti-docker MCP server status
mcp__graphiti-docker__get_status()

# Query episodes in local instance
mcp__graphiti-docker__get_episodes(max_episodes=10)
```
**Expected:**
- Docker containers running and healthy
- `graphiti-docker` MCP server connected to local Neo4j
- Episodes list (may be empty for fresh dev environment)

**Health Indicators:**
- ✅ Containers healthy, MCP connected, ready for development
- ⚠️ Containers running but MCP connection failed - check docker-compose config
- ❌ No containers found - start with `docker compose -f docker/docker-compose-neo4j-local.yml up -d`
- 💡 Empty episodes is normal for dev environment

**Environment Distinction:**
| MCP Server | Database | Purpose |
|------------|----------|---------|
| `graphiti-aura` | Neo4j Aura (cloud) | Production data |
| `graphiti-docker` | Docker Neo4j (localhost:7687) | Local development |

## After Running

Report your findings to the user:
- ✅ All checks passed - environment is healthy
- ⚠️ Some checks failed - describe what you found, ASK before fixing
- ❌ Connection errors - report error, do NOT attempt destructive fixes
- 💡 Checks 4-5 skipped if respective MCP servers unavailable (non-critical, graceful degradation)

## Remember

- Empty results usually mean wrong `group_ids` parameter, NOT a broken system
- NEVER run `clear_graph` or delete commands without explicit user request
- When in doubt, ASK THE USER
