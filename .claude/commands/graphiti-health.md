---
description: Display unified real-time health status for Neo4j Aura and Graphiti services
allowed-tools:
  - mcp__graphiti-aura__get_status
  - mcp__neo4j-aura-management__list_instances
  - mcp__neo4j-aura-management__get_instance_details
  - mcp__graphiti-docker__get_status
  - mcp__graphiti-docker__get_episodes
  - mcp__mcp-server-time__get_current_time
  - Bash(docker ps:*)
---

Display unified real-time health status for Neo4j Aura and Graphiti services.

## Instructions

Execute these health checks to provide a comprehensive system status report. Report results with color-coded indicators.

### Check 1: Graphiti Server Health

```python
mcp__graphiti-aura__get_status()
```

**Expected Response**:
```json
{
  "status": "ok",
  "message": "Graphiti MCP server is running and connected to neo4j database"
}
```

**Health Indicators**:
- ✅ `status == "ok"` - Server healthy and database connected
- ❌ Any other status or error - Server unavailable or database connection failed

### Check 2: Neo4j Aura Instance Health

```python
# First, get available instances
instances = mcp__neo4j-aura-management__list_instances()

# Then check health of primary instance (use instance ID from list)
mcp__neo4j-aura-management__get_instance_details(instance_ids=["cd339b4f"])
```

**Expected Response**:
```json
{
  "instances": [{
    "id": "cd339b4f",
    "name": "dwb",
    "status": "running",
    "memory": "1GB",
    "graph_nodes": 3284,
    "graph_relationships": 12614,
    "connection_url": "neo4j+s://cd339b4f.databases.neo4j.io",
    "cloud_provider": "gcp",
    "region": "us-central1"
  }]
}
```

**Health Indicators**:
- ✅ `status == "running"` AND nodes/relationships present - Database healthy and operational
- ⚠️ `status == "running"` AND memory == "1GB" AND nodes > 5000 - May need scaling
- ⚠️ `status == "paused"` - Instance paused (manual intervention needed)
- ❌ `status != "running"` OR connection errors - Database unavailable

### Check 3: Local Docker Development Environment (Optional)

```python
# Check if local Docker Neo4j is running
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | grep -E "(neo4j|7474|7687|graphiti)"

# Check graphiti-docker MCP server status
mcp__graphiti-docker__get_status()

# Query episodes in local instance
mcp__graphiti-docker__get_episodes(max_episodes=10)
```

**Expected Response**:
- Docker containers running and healthy
- `graphiti-docker` MCP server connected to local Neo4j
- Episodes list (may be empty for fresh dev environment)

**Health Indicators**:
- ✅ Containers healthy, MCP connected, ready for development
- ⚠️ Containers running but MCP connection failed - check docker-compose config
- ❌ No containers found - start with `docker compose -f docker/docker-compose-neo4j-local.yml up -d`
- 💡 Empty episodes is normal for dev environment

## Output Format

Format the health report with these sections:

### 1. Overall System Health

Show aggregate status at the top with clear visual indicator:
- ✅ **HEALTHY** - All services operational
- ⚠️ **DEGRADED** - Some services have warnings
- ❌ **UNHEALTHY** - Critical services down or failing

### 2. Graphiti Service Status

Display:
- Service status (running/error)
- Database connection status
- Server message

### 3. Neo4j Aura Database Status

Display:
- Instance name and ID
- Status (running/paused/stopped)
- Memory allocation
- Graph size (nodes and relationships)
- Connection URL
- Cloud provider and region
- Capacity warnings if applicable

### 4. Local Docker Development Environment (Optional)

Display:
- Docker container status (running/stopped/not found)
- graphiti-docker MCP connection status
- Episode count in local instance
- Note if containers aren't running (graceful degradation)

### 5. Recommendations

If warnings or errors detected, provide actionable next steps:
- Memory scaling recommendations
- Connection troubleshooting steps
- Service restart instructions

## Example Output

```
🏥 System Health Report
Generated: 2025-12-16 23:45 UTC

Overall Status: ✅ HEALTHY

=== Graphiti Service ===
Status: ✅ Running
Database: ✅ Connected to neo4j
Message: Graphiti MCP server is running and connected to neo4j database

=== Neo4j Aura Database ===
Instance: dwb (cd339b4f)
Status: ✅ Running
Memory: 1GB
Graph Size: 3,284 nodes, 12,614 relationships
Connection: neo4j+s://cd339b4f.databases.neo4j.io
Cloud: GCP us-central1
Capacity: ✅ Within limits (1GB instance, <5k nodes)

=== Local Docker Development ===
Containers: ✅ Running (neo4j, graphiti-mcp)
graphiti-docker MCP: ✅ Connected
Episodes: 0 (empty dev environment)

=== Summary ===
All services operational. No action required.

Execution time: 0.8 seconds
```

## Example Output with Warnings

```
🏥 System Health Report
Generated: 2025-12-16 23:45 UTC

Overall Status: ⚠️ DEGRADED

=== Graphiti Service ===
Status: ✅ Running
Database: ✅ Connected to neo4j
Message: Graphiti MCP server is running and connected to neo4j database

=== Neo4j Aura Database ===
Instance: dwb (cd339b4f)
Status: ✅ Running
Memory: 1GB
Graph Size: 8,432 nodes, 32,156 relationships
Connection: neo4j+s://cd339b4f.databases.neo4j.io
Cloud: GCP us-central1
Capacity: ⚠️ APPROACHING LIMIT (1GB instance with >5k nodes)

=== Local Docker Development ===
Containers: ✅ Running (neo4j, graphiti-mcp)
graphiti-docker MCP: ✅ Connected
Episodes: 125 (dev namespaces active)

=== Recommendations ===
⚠️ Neo4j Aura: Consider upgrading to 2GB instance for better performance
   - Current: 1GB with 8,432 nodes
   - Use /dba command to resize instance (when available)
   - Or visit: https://console.neo4j.io

Execution time: 0.9 seconds
```

## Example Output with Errors

```
🏥 System Health Report
Generated: 2025-12-16 23:45 UTC

Overall Status: ❌ UNHEALTHY

=== Graphiti Service ===
Status: ❌ Error
Database: ❌ Connection failed
Error: Failed to connect to neo4j database

=== Neo4j Aura Database ===
Status: ❌ Unable to retrieve instance details
Error: Authentication failed or instance unavailable

=== Local Docker Development ===
Status: 💡 Skipped (focus on production issues first)

=== Recommendations ===
❌ Graphiti Service: Check database connection
   - Verify NEO4J_URI in .env file
   - Run /graphiti-verify command for detailed diagnostics
   - Check Neo4j Aura instance status

❌ Neo4j Aura: Check MCP server and credentials
   - Ensure neo4j-aura-management MCP server is running:
     docker compose -f docker/docker-compose-neo4j-mcp.yml --env-file .env up -d
   - Verify NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET in .env
   - Check https://console.neo4j.io for instance status

Execution time: 1.2 seconds
```

## Performance Notes

- **Target execution time**: < 3 seconds (with Docker checks)
- All checks are read-only (no writes)
- Checks run sequentially (not parallel)
- Graceful degradation:
  - If Neo4j Aura MCP unavailable, show Graphiti status only
  - If Docker containers not running, skip local development section

## Troubleshooting

**Neo4j Aura MCP not available**:
- **Symptom**: Tool `mcp__neo4j-aura-management__get_instance_details` not found
- **Solution**: Start Neo4j Aura MCP server:
  ```bash
  docker compose -f docker/docker-compose-neo4j-mcp.yml --env-file .env up -d
  ```
- **Graceful degradation**: Show Graphiti health only, skip Neo4j Aura section

**Graphiti server not responding**:
- **Symptom**: `mcp__graphiti-aura__get_status` returns error or timeout
- **Solution**:
  - Check if Graphiti MCP server is running
  - Verify server is configured in .mcp.json
  - Check logs for errors

**Instance ID not found**:
- **Symptom**: `list_instances` returns empty or different instances
- **Solution**:
  - Update instance ID in health check to match your primary instance
  - Use `list_instances` to find correct instance ID
  - If no instances, create one at https://console.neo4j.io

**Timeout errors**:
- **Symptom**: Checks take > 3 seconds or timeout
- **Solutions**:
  - Check network connectivity to Neo4j Aura
  - Verify firewall allows HTTPS to Aura API endpoints
  - Check if Aura instance is in correct region (latency)

**Docker containers not found**:
- **Symptom**: `docker ps` returns no matching containers
- **Solution**: Start local Docker environment:
  ```bash
  docker compose -f docker/docker-compose-neo4j-local.yml up -d
  ```
- **Graceful degradation**: Health check skips Docker section if containers not running

**graphiti-docker MCP connection failed**:
- **Symptom**: Containers running but `mcp__graphiti-docker__get_status()` fails
- **Solutions**:
  - Check MCP server logs: `docker logs docker-graphiti-mcp-1`
  - Verify port 8002 is accessible: `curl http://localhost:8002/health`
  - Restart containers: `docker compose -f docker/docker-compose-neo4j-local.yml restart`

## Related Commands

- `/graphiti-verify` - Comprehensive environment validation (includes health checks)
- `/graphiti-aura-stats` - Production graph analytics and capacity planning
- `/graphiti-docker-stats` - Development environment analytics and cleanup
- `/dba` - Database administration operations (when available)

## Notes

- This command provides **real-time** health status (not cached)
- Covers both production (Neo4j Aura) and development (Docker) environments
- Color-coded indicators (✅⚠️❌) require emoji support in terminal
- Instance ID `cd339b4f` is example - replace with your actual instance ID
- Capacity thresholds:
  - ✅ < 5,000 nodes on 1GB instance
  - ⚠️ 5,000-10,000 nodes on 1GB instance
  - ❌ > 10,000 nodes on 1GB instance (requires upgrade)
- Docker checks are optional - gracefully skipped if containers not running
