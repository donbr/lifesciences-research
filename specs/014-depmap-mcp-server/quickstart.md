# Quickstart: DepMap Genotype-Selective Dependency MCP Server

**Feature**: 014-depmap-mcp-server

## Run the server

```bash
uv sync --extra dev
uv run fastmcp dev src/lifesciences_mcp/servers/depmap.py
```

Or through the gateway, alongside the other twelve servers:

```bash
uv run fastmcp dev src/lifesciences_mcp/servers/gateway.py
```

Gateway tools are prefixed: `depmap_search_models`, `depmap_get_model`,
`depmap_models_with_mutation`, `depmap_get_dependency`, `depmap_genotype_contrast_by_gene`.

## The Fuzzy-to-Fact walkthrough

```python
# Phase 1, fuzzy: type the name the way a paper writes it
result = await client.call_tool("search_models", {"query": "a549"})
model_id = result["items"][0]["id"]        # "SIDM:00903"

# Phase 2, strict: only a resolved identifier is accepted
model = await client.call_tool("get_model", {"model_id": model_id})

# Free text here is refused, not guessed at
await client.call_tool("get_model", {"model_id": "A549"})
# -> UNRESOLVED_ENTITY, recovery hint names search_models
```

## The capability this server exists for

```python
contrast = await client.call_tool("genotype_contrast_by_gene", {
    "target_gene": "AURKB",
    "genotype_gene": "RB1",
    "mutation_type": "deletion",
})
```

Read `tested` before anything else. When it is false the statistics are absent by design and the
note says why. That is the guard against reporting an underpowered cohort as a finding.

Read `data_source` next. Broad 24Q2 and Sanger Project Score are different screens, and their
numbers are not comparable.

## Choosing a mutation type

The value `mutation` means any variant. For RB1 it returns 2185 of 2266 models, which would put
almost the whole catalogue in the mutant arm. Use a damaging class:

| mutation_type | RB1 models |
|---|---|
| mutation | 2185 |
| deletion | 501 |
| splice_variant | 60 |
| frameshift | 27 |

Accepted values: `frameshift`, `snp`, `insertion`, `deletion`, `splice_variant`, `mutation`.

## Tests

```bash
uv run pytest -m depmap -v                    # unit and integration for this server
uv run pytest -m "unit and depmap" -v         # no network
uv run pytest -m "integration and depmap" -v  # live Sanger calls
```

## Data access terms

Cell Model Passports data is non-commercial, and third-party application use requires prior
permission from depmap@sanger.ac.uk. Gene-effect matrices are not served by any API and must be
obtained as a checksum-pinned release file.
