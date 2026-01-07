---
description: Generate development environment statistics for Docker Neo4j namespace management
allowed-tools:
  - mcp__neo4j-docker-cypher__read_neo4j_cypher
  - mcp__mcp-server-time__get_current_time
---

Generate development environment statistics for Docker Neo4j namespace management and cleanup.

## Instructions

Execute these queries sequentially to build a development environment report. Report results to the user in a formatted summary.

**Purpose**: Namespace cleanup, development progress tracking, and quick sanity checks.

### Query 1: Namespace Overview

```python
mcp__neo4j-docker-cypher__read_neo4j_cypher(
    query="""
    MATCH (e:Episodic)
    RETURN e.group_id AS namespace,
           count(*) AS episodes,
           min(e.created_at) AS first_episode,
           max(e.created_at) AS last_episode
    ORDER BY episodes DESC
    """
)
```

**Purpose**: Shows all namespaces with episode counts and identifies cleanup candidates.

### Query 2: Development Namespace Breakdown

```python
mcp__neo4j-docker-cypher__read_neo4j_cypher(
    query="""
    MATCH (e:Episodic)
    WHERE e.group_id STARTS WITH 'dev_'
       OR e.group_id STARTS WITH 'test_'
       OR e.group_id STARTS WITH 'experimental_'
       OR e.group_id STARTS WITH 'scratch_'
       OR e.group_id STARTS WITH 'demo_'
    RETURN e.group_id AS namespace,
           count(*) AS episodes,
           max(e.created_at) AS last_activity
    ORDER BY last_activity DESC
    """
)
```

**Purpose**: Identifies development namespaces with activity timestamps for cleanup decisions.

### Query 3: Total Graph Size

```python
mcp__neo4j-docker-cypher__read_neo4j_cypher(
    query="""
    MATCH (n:Entity)
    WITH count(n) AS entity_count
    MATCH ()-[r]->()
    RETURN entity_count,
           count(r) AS relationship_count
    """
)
```

**Purpose**: Simple counts for development environment capacity check.

### Query 4: Recent Activity (Last 7 Days)

```python
mcp__neo4j-docker-cypher__read_neo4j_cypher(
    query="""
    MATCH (e:Episodic)
    WHERE e.created_at > datetime() - duration('P7D')
    RETURN e.group_id AS namespace,
           count(*) AS recent_episodes,
           max(e.created_at) AS last_episode
    ORDER BY recent_episodes DESC
    """
)
```

**Purpose**: Shows active development areas in the last week.

### Query 5: Cleanup Candidates

```python
mcp__neo4j-docker-cypher__read_neo4j_cypher(
    query="""
    MATCH (e:Episodic)
    WHERE (e.group_id STARTS WITH 'test_' OR e.group_id STARTS WITH 'scratch_')
      AND e.created_at < datetime() - duration('P7D')
    RETURN e.group_id AS namespace,
           count(*) AS episodes,
           max(e.created_at) AS last_activity,
           duration.between(max(e.created_at), datetime()).days AS days_inactive
    ORDER BY days_inactive DESC
    """
)
```

**Purpose**: Identifies stale test/scratch namespaces older than 7 days for cleanup.

## Output Format

Format the results as a development environment report with these sections:

### 1. Namespace Summary

- Total namespaces in development environment
- Breakdown by prefix (dev_*, test_*, experimental_*, scratch_*, demo_*)
- Highlight empty namespaces

### 2. Graph Size

- Total entities
- Total relationships
- Compare with production if needed

### 3. Recent Activity

- Active namespaces (last 7 days)
- Number of episodes added per namespace
- Current development focus areas

### 4. Cleanup Recommendations

- Stale test/scratch namespaces (>7 days old)
- Empty namespaces
- Suggested cleanup commands

## Example Output

```
🧪 Development Environment Statistics
Generated: 2025-12-19 15:30 UTC

=== Namespace Overview ===
Total namespaces: 12

By prefix:
  dev_*: 5 namespaces, 89 episodes
  test_*: 4 namespaces, 23 episodes
  experimental_*: 2 namespaces, 15 episodes
  scratch_*: 1 namespace, 3 episodes

Top namespaces:
  1. dev_agent_coordination:     34 episodes (2025-12-15 to 2025-12-19)
  2. dev_namespace_registry:     28 episodes (2025-12-16 to 2025-12-19)
  3. dev_context_formatting:     27 episodes (2025-12-14 to 2025-12-18)

=== Graph Size ===
Entities: 412
Relationships: 1,847

=== Recent Activity (Last 7 Days) ===
Active development:
  1. dev_agent_coordination:     15 episodes (last: 2 hours ago)
  2. dev_namespace_registry:     12 episodes (last: 4 hours ago)
  3. test_integration_suite:     8 episodes (last: 1 day ago)

=== Cleanup Recommendations ===
Stale namespaces (>7 days inactive):
  ⚠️ test_old_feature:          5 episodes (14 days inactive)
  ⚠️ scratch_temp_experiment:   3 episodes (10 days inactive)
  ⚠️ test_migration_validation: 2 episodes (9 days inactive)

Suggested cleanup:
  # Review and delete if no longer needed
  # Use graphiti-docker MCP to clear specific namespaces

Performance: Queries executed in 0.8 seconds
```

## Performance Notes

- **Target execution time**: < 2 seconds (simpler queries than production)
- All queries are read-only (no writes)
- Designed for frequent use during development
- Lightweight compared to production analytics

## Troubleshooting

**Empty results**:
- **Cause**: No data in development environment (expected for fresh instances)
- **Solution**:
  - This is normal - development environment may be empty
  - Create test data with dev_*, test_*, or experimental_* namespaces

**MCP server not available**:
- **Symptom**: Tool `mcp__neo4j-docker-cypher__read_neo4j_cypher` not found
- **Solution**: Start Docker Neo4j environment:
  ```bash
  docker compose -f docker/docker-compose-neo4j-local.yml up -d
  ```
- **Verify**: Check containers are running: `docker ps | grep neo4j`

**Connection errors**:
- **Symptom**: "Failed to connect" errors
- **Solutions**:
  - Verify Docker containers are running
  - Check Neo4j is accessible at `bolt://localhost:7687`
  - Verify MCP server containers: `docker ps | grep graphiti`
  - Check logs: `docker logs docker-graphiti-mcp-1`

**Slow queries (>2s)**:
- **Cause**: Development environment unexpectedly large
- **Solutions**:
  - Check graph size with Query 3
  - Consider cleaning up stale namespaces
  - Large dev environments (>10k nodes) should be cleaned

## Related Commands

- `/graphiti-aura-stats` - Production analytics and capacity planning
- `/graphiti-health` - System health including development environment
- `/graphiti-verify` - Comprehensive environment validation

## Notes

- This command is for **development environment only** (Docker Neo4j)
- Complements `/graphiti-aura-stats` which focuses on production
- Optimized for frequent use during active development
- Cleanup recommendations based on namespace naming conventions from `docs/NAMESPACE_POLICY.md`
- Safe to run multiple times per day
