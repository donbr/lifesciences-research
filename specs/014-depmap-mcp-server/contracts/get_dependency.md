# Tool Contract: get_dependency

**Type**: Strict Lookup
**Protocol Phase**: Phase 2
**Returns**: DependencyRecord | ErrorEnvelope
**Satisfies**: FR-005, FR-008

## Purpose

Report how essential one gene is in one cell model, from a cached gene-effect release.

## Parameters

```python
{
    "gene": str,                              # HGNC symbol
    "model_id": str,                          # "SIDM:#####" CURIE
    "data_source": DataSource = "broad_24q2",
}
```

## Behaviour

**Values are never fetched live.** No provider serves gene effect over a query API: Sanger exposes
`crispr_ko_available` as a flag only, and probes to `/datasets/crispr` and `/datasets/crispr_ko`
return empty, because the matrix is a Project Score or Data Miner file (research.md R3). Values come
from a cached, checksum-pinned release.

If the configured release is not present on disk, return `UPSTREAM_ERROR` whose recovery hint says
which release is missing and how to obtain it. Never return a zero or a null as if it were a
measurement.

Free text in `model_id` is refused with `UNRESOLVED_ENTITY` naming `search_models`.

## Responses

```json
{
  "gene": "AURKB",
  "model_id": "SIDM:00903",
  "gene_effect": -0.42,
  "data_source": "broad_24q2"
}
```

More negative means more essential.

## Acceptance

| Given | Then |
|---|---|
| a gene and model present in the cached release | the value, labelled with its release |
| a model with no measurement for that gene | the value key is omitted, not zero |
| no cached release available | `UPSTREAM_ERROR` naming the missing release |
