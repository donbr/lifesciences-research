# Cypher Queries for Competency Question Visualization

Queries for exploring and visualizing knowledge graphs built using the `lifesciences-graph-builder` skill.

**Target**: Neo4j Browser or Bloom connected to `graphiti-docker` or `graphiti-aura`.

---

## 1. Overview: All Catalog Namespaces

Full graph view of all competency question data:

```cypher
MATCH (e:Episodic)-[:MENTIONS]->(n:Entity)
WHERE e.group_id IN [
  'scenario1-synthetic-lethality',
  'scenario2-safety-profile',
  'scenario3-huntington-sprint',
  'oncology-demo',
  'health-emergencies-2026',
  'high-commercialization-trials',
  'car-t-regulatory-landscape'
]
OPTIONAL MATCH (n)-[r:RELATES_TO]-(m:Entity)
RETURN e, n, r, m
LIMIT 200
```

---

## 2. Scenario 1: Synthetic Lethality Network

ARID1A-EZH2 synthetic lethality relationships:

```cypher
MATCH (e:Episodic {group_id: 'scenario1-synthetic-lethality'})-[:MENTIONS]->(n:Entity)
OPTIONAL MATCH (n)-[r:RELATES_TO]-(m:Entity)
WHERE e.group_id = 'scenario1-synthetic-lethality'
RETURN n, r, m
```

---

## 3. Scenario 2: Drug Safety Comparison

Dasatinib vs Imatinib safety profile:

```cypher
MATCH (e:Episodic {group_id: 'scenario2-safety-profile'})-[:MENTIONS]->(n:Entity)
OPTIONAL MATCH (n)-[r:RELATES_TO]-(m:Entity)
RETURN n, r, m
```

---

## 4. Scenario 4: p53-MDM2-Nutlin Pathway

Oncology pathway validation:

```cypher
MATCH (e:Episodic {group_id: 'oncology-demo'})-[:MENTIONS]->(n:Entity)
OPTIONAL MATCH (n)-[r:RELATES_TO]-(m:Entity)
RETURN n, r, m
```

---

## 5. Research Reports: Clinical Trials Landscape

Health emergencies and commercialization trials:

```cypher
MATCH (e:Episodic)-[:MENTIONS]->(n:Entity)
WHERE e.group_id IN [
  'health-emergencies-2026',
  'high-commercialization-trials',
  'car-t-regulatory-landscape'
]
OPTIONAL MATCH (n)-[r:RELATES_TO]-(m:Entity)
RETURN e.group_id AS research_area, n, r, m
LIMIT 150
```

---

## 6. Entity Type Distribution

What types of entities were extracted?

```cypher
MATCH (e:Episodic)-[:MENTIONS]->(n:Entity)
WHERE e.group_id IN [
  'scenario1-synthetic-lethality',
  'scenario2-safety-profile',
  'scenario3-huntington-sprint',
  'oncology-demo',
  'health-emergencies-2026',
  'high-commercialization-trials',
  'car-t-regulatory-landscape'
]
RETURN labels(n) AS entity_type, count(DISTINCT n) AS count
ORDER BY count DESC
```

---

## 7. Cross-Scenario Entity Overlap

Entities appearing in multiple scenarios:

```cypher
MATCH (e1:Episodic)-[:MENTIONS]->(n:Entity)<-[:MENTIONS]-(e2:Episodic)
WHERE e1.group_id <> e2.group_id
  AND e1.group_id IN [
    'scenario1-synthetic-lethality',
    'scenario2-safety-profile',
    'scenario3-huntington-sprint',
    'oncology-demo',
    'health-emergencies-2026',
    'high-commercialization-trials',
    'car-t-regulatory-landscape'
  ]
  AND e2.group_id IN [
    'scenario1-synthetic-lethality',
    'scenario2-safety-profile',
    'scenario3-huntington-sprint',
    'oncology-demo',
    'health-emergencies-2026',
    'high-commercialization-trials',
    'car-t-regulatory-landscape'
  ]
RETURN n.name AS shared_entity,
       collect(DISTINCT e1.group_id) AS scenarios,
       count(DISTINCT e1.group_id) AS scenario_count
ORDER BY scenario_count DESC
```

---

## 8. Relationship Types

What relationship types exist in the catalog data?

```cypher
MATCH (e:Episodic)-[:MENTIONS]->(n:Entity)-[r:RELATES_TO]-(m:Entity)
WHERE e.group_id IN [
  'scenario1-synthetic-lethality',
  'scenario2-safety-profile',
  'scenario3-huntington-sprint',
  'oncology-demo',
  'health-emergencies-2026',
  'high-commercialization-trials',
  'car-t-regulatory-landscape'
]
RETURN type(r) AS relationship_type,
       r.fact AS fact_description,
       count(*) AS count
ORDER BY count DESC
LIMIT 20
```

---

## 9. Episode Provenance View

Show episodes with their extracted entities:

```cypher
MATCH (e:Episodic)-[:MENTIONS]->(n:Entity)
WHERE e.group_id IN [
  'scenario1-synthetic-lethality',
  'scenario2-safety-profile',
  'scenario3-huntington-sprint',
  'oncology-demo',
  'health-emergencies-2026',
  'high-commercialization-trials',
  'car-t-regulatory-landscape'
]
RETURN e.group_id AS scenario,
       e.name AS episode_name,
       collect(n.name)[0..10] AS sample_entities,
       count(n) AS entity_count
ORDER BY scenario
```

---

## 10. Full Graph Export (for Neo4j Browser/Bloom)

Complete visualization-ready query:

```cypher
MATCH path = (e:Episodic)-[:MENTIONS]->(n:Entity)
WHERE e.group_id IN [
  'scenario1-synthetic-lethality',
  'scenario2-safety-profile',
  'scenario3-huntington-sprint',
  'oncology-demo',
  'health-emergencies-2026',
  'high-commercialization-trials',
  'car-t-regulatory-landscape'
]
OPTIONAL MATCH entity_path = (n)-[r:RELATES_TO]-(m:Entity)
RETURN path, entity_path
LIMIT 300
```

---

## Quick Test Query

Verify data exists:

```cypher
MATCH (e:Episodic)-[:MENTIONS]->(n:Entity)
WHERE e.group_id STARTS WITH 'scenario'
   OR e.group_id IN [
     'oncology-demo',
     'health-emergencies-2026',
     'high-commercialization-trials',
     'car-t-regulatory-landscape'
   ]
RETURN e.group_id AS namespace, count(DISTINCT n) AS entities
ORDER BY namespace
```

---

## Neo4j Browser Tips

1. **Open Neo4j Browser**: http://localhost:7474
2. **Connect**: `bolt://localhost:7687` (user: `neo4j`, password: from `.env`)
3. **Visualization**: Click the graph icon after running a query
4. **Styling**: Double-click node labels to customize colors by type
