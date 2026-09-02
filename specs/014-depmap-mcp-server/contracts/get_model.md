# Tool Contract: get_model

**Type**: Strict Lookup
**Protocol Phase**: Phase 2 (Fuzzy-to-Fact)
**Returns**: CellModel | ErrorEnvelope
**Satisfies**: FR-008, FR-013

## Purpose

Return the full record for a cell model whose identifier has already been resolved.

## Parameters

```python
{"model_id": str}   # "SIDM:#####" CURIE, e.g. "SIDM:00903"
```

### model_id (required)

- **Format**: `SIDM:#####`, regex `^SIDM:\d{5}$`
- Valid: `"SIDM:00903"`
- Normalised, not rejected: `"SIDM00903"`, the raw upstream form
- Invalid: `"A549"` (free text), `"sidm:00903"` (lower case)

## Behaviour

Free text is refused **before any network call** with `UNRESOLVED_ENTITY` and a recovery hint naming
`search_models`. The current code strips whitespace and calls the API, returning `ENTITY_NOT_FOUND`,
which tells the agent the cell line does not exist when in fact it was never resolved.

A well-formed identifier the upstream does not hold returns `ENTITY_NOT_FOUND`.

## Responses

```json
{
  "id": "SIDM:00903",
  "name": "A549",
  "aliases": ["A549", "NCI-A549", "A549/ATCC", "hA549"],
  "lineage": "Lung",
  "model_type": "Cell Line",
  "data_available": ["mutations", "cnv", "expression", "rnaseq"],
  "data_source": "sanger_project_score",
  "cross_references": {"ccle": "A549_LUNG", "cosmic": "905949"}
}
```

Keys with no value are **omitted**, never null.

## Acceptance

| Given | Then |
|---|---|
| `"SIDM:00903"` | full record for A549 |
| `"A549"` | `UNRESOLVED_ENTITY`, hint names `search_models`, no request made |
| `"SIDM:99999"` | `ENTITY_NOT_FOUND` |
