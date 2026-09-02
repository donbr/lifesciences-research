# Tool Contract: search_models

**Type**: Fuzzy Search
**Protocol Phase**: Phase 1 (Fuzzy-to-Fact)
**Returns**: PaginationEnvelope[CellModel] | ErrorEnvelope
**Satisfies**: FR-006, FR-007, FR-011, FR-012

## Purpose

Resolve a cell-line name as a researcher would write it into stable `SIDM:#####` identifiers. This
is the only entry point to every strict tool in this server.

## Parameters

```python
{
    "query": str,             # free text, e.g. "a549", "MCF-7", "HeLa"
    "slim": bool = False,     # reduced output, ~20 tokens per candidate
    "cursor": str | None = None,
    "page_size": int = 50,    # 1-100
}
```

## Behaviour

Matching is performed against a locally built, normalised alias index, **not** by delegating to the
upstream filter. The upstream names filter is exact and case-sensitive, and `any` is the only
operator it accepts. Measured: `a549`, `MCF-7` and `hela` all return zero hits upstream, while
`A549` and `HeLa` return one each (research.md R4). Upper-casing the query is not a fix, because it
rescues `a549` and breaks `HeLa`.

Normalisation is case-fold plus removal of whitespace and punctuation. Ranking is exact alias match,
then normalised match, then prefix match.

## Responses

Success, `slim=False`:

```json
{
  "items": [
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
  ],
  "pagination": {"cursor": null, "total_count": 1, "page_size": 50}
}
```

Success, `slim=True`: `id`, `name` and `data_source` only.

**No match is not an error.** An unmatched query returns an empty items list with a total count of
zero (FR-007). Returning `ENTITY_NOT_FOUND` here, as the current code does, makes an ordinary
negative answer indistinguishable from a failure.

## Acceptance

| Given | Then |
|---|---|
| `"a549"` | resolves to `SIDM:00903` |
| `"A549"` | resolves to `SIDM:00903` |
| `"MCF-7"` and `"MCF7"` | resolve to the same model |
| `"HeLa"` and `"hela"` | resolve to the same model |
| `"zzzznotacellline"` | empty envelope, not an error |
