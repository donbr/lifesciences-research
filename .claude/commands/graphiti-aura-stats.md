---
description: Generate production graph statistics for Neo4j Aura analytics and capacity planning
allowed-tools:
  - mcp__neo4j-aura-cypher__read_neo4j_cypher
  - mcp__mcp-server-time__get_current_time
---

Generate comprehensive production graph statistics for Neo4j Aura analytics and capacity planning.

## Instructions

Execute these queries sequentially to build a complete analytics report. Report results to the user in a formatted summary.

### Query 1: Episode Distribution by Namespace

```python
mcp__neo4j-aura-cypher__read_neo4j_cypher(
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

**Purpose**: Shows which namespaces contain data and identifies growth patterns.

### Query 2: Total Entity Count

```python
mcp__neo4j-aura-cypher__read_neo4j_cypher(
    query="""
    MATCH (n:Entity)
    RETURN count(n) AS total_entities
    """
)
```

**Purpose**: Get total entity count for summary statistics.

### Query 3: Entity Type Distribution

```python
mcp__neo4j-aura-cypher__read_neo4j_cypher(
    query="""
    MATCH (n:Entity)
    RETURN labels(n) AS entity_types,
           count(*) AS count
    ORDER BY count DESC
    LIMIT 15
    """
)
```

**Purpose**: Breakdown by entity labels (Person, Company, Concept, etc.). Helps validate extraction quality.

### Query 4: Relationship Type Frequency

```python
mcp__neo4j-aura-cypher__read_neo4j_cypher(
    query="""
    MATCH ()-[r]->()
    RETURN type(r) AS relationship_type,
           count(*) AS frequency,
           count(CASE WHEN r.invalid_at IS NOT NULL THEN 1 END) AS invalidated_count,
           round(100.0 * count(CASE WHEN r.invalid_at IS NOT NULL THEN 1 END) / count(*), 2) AS invalidation_rate_pct
    ORDER BY frequency DESC
    LIMIT 15
    """
)
```

**Purpose**: Most common relationship patterns and invalidation rates. Identifies schema usage and knowledge evolution velocity.

### Query 5: Temporal Invalidation Statistics

```python
mcp__neo4j-aura-cypher__read_neo4j_cypher(
    query="""
    MATCH ()-[r]->()
    WHERE r.invalid_at IS NOT NULL AND r.valid_at IS NOT NULL
    RETURN type(r) AS relationship_type,
           count(*) AS total_invalidated,
           round(avg(duration.between(
             datetime(r.valid_at),
             datetime(r.invalid_at)
           ).seconds) / 3600.0, 2) AS avg_lifetime_hours
    ORDER BY total_invalidated DESC
    LIMIT 10
    """
)
```

**Purpose**: Tracks knowledge evolution velocity - average fact lifetime and invalidation patterns.

## Output Format

Format the results as a comprehensive report with these sections:

### 1. Episode Distribution
- Table with: namespace, episode count, date range
- Highlight top 3 namespaces by volume

### 2. Entity Type Summary
- Total unique entity count
- Top entity types with counts
- Note any unusual patterns (e.g., too many generic "Entity" labels)

### 3. Relationship Analysis
- Total relationship count
- Top relationship types with frequency
- Overall invalidation rate percentage
- Highlight relationship types with >20% invalidation (indicates high knowledge churn)

### 4. Temporal Patterns
- If invalidations exist:
  - List top invalidated relationship types
  - Show average lifetime in hours
  - Interpret patterns (e.g., "CAUSES relationships average 0.98 hours - indicates rapid causal inference updates")
- If no invalidations: "No temporal invalidations found - all facts remain valid"

## Example Output

```
📊 Graph Statistics Report
Generated: 2025-12-16 23:15 UTC

=== Episode Distribution ===
Top namespaces:
  1. graphiti_meta_knowledge:    90 episodes (2025-12-12 to 2025-12-16)
  2. don_branson_resume_v3:      79 episodes (2025-12-12 to 2025-12-16)
  3. don_branson_career:         29 episodes (2025-12-12 to 2025-12-12)

Total: 19 namespaces, 318 episodes

=== Entity Type Distribution ===
Total entities: 3,284

Top entity types:
  1. Entity only:                 621 (18.9%)
  2. Entity,Requirement:          521 (15.9%)
  3. Entity,Topic:                518 (15.8%)
  4. Entity,Document:             416 (12.7%)
  5. Entity,Organization:         232 (7.1%)

=== Relationship Analysis ===
Total relationships: 12,614

Top relationship types:
  1. MENTIONS:     7,176 (0.0% invalidated)
  2. RELATES_TO:   5,438 (55.2% invalidated) ⚠️ High churn

Overall invalidation rate: 23.8%

=== Temporal Invalidation Patterns ===
RELATES_TO: 3,000 invalidated (avg lifetime: 0.98 hours)
→ Rapid relationship updates indicate active knowledge refinement

Performance: Queries executed in 1.2 seconds
```

## Performance Notes

- **Tested performance**: < 2 seconds for graphs with ~3,300 nodes and ~12,600 relationships
- **Expected scaling**: < 5 seconds for graphs up to 10k-50k nodes (extrapolated, not benchmarked)
- **Large graphs (>50k nodes)**: May require performance tuning or indexing
- All queries are read-only (no writes)
- Results are not cached - always shows current state
- If slow (>5s), recommend adding indexes on:
  - Episodic.group_id
  - Episodic.created_at
  - Relationship.invalid_at, Relationship.valid_at

## Troubleshooting

**Empty results**:
- **Cause**: No data in database or incorrect namespace
- **Solution**:
  - Check database connection with `/graphiti-verify`
  - Verify data exists: `MATCH (n) RETURN count(n)`
  - Empty results for specific queries are normal if graph is small

**MCP server not available**:
- **Symptom**: Tool `mcp__neo4j-aura-cypher__read_neo4j_cypher` not found
- **Solution**: Start Neo4j Cypher MCP server:
  ```bash
  docker compose -f docker/docker-compose-neo4j-mcp.yml --env-file .env up -d
  ```

**Slow queries (>5s)**:
- **Cause**: Large graph without proper indexes
- **Solutions**:
  - Check graph size: `MATCH (n) RETURN count(n)`
  - For large graphs (>50k nodes), add indexes
  - Run `mcp__neo4j-aura-cypher__get_neo4j_schema()` to verify indexes exist
  - Consider running queries individually rather than all at once

**Query timeout or connection loss**:
- **Symptom**: Query hangs or connection drops mid-execution
- **Solutions**:
  - Check Neo4j Aura instance status with `/graphiti-verify`
  - Verify stable network connection
  - For very large graphs, consider pagination or time-based filtering

**Connection errors**:
- **Symptom**: "Failed to connect" or authentication errors
- **Solutions**:
  - Verify Neo4j credentials in `.env` file
  - Check Neo4j Aura instance status with `/graphiti-verify`
  - Ensure firewall allows connections to Neo4j Aura (port 7687)
  - Verify MCP server containers are running: `docker ps | grep neo4j`

## Related Commands

- `/graphiti-docker-stats` - Development environment analytics and cleanup
- `/graphiti-health` - Real-time health status for both environments
- `/graphiti-verify` - Comprehensive environment validation

## Notes

- This command provides **production analytics** for Neo4j Aura only
- For development environment stats, use `/graphiti-docker-stats`
- Results are not cached - always shows current production state
- Designed for capacity planning and knowledge evolution tracking
