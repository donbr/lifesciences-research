# ADR source documents

The two research reports that `docs/adr/archive/master-adr-v0.1.md` names as its sources:

> **Sources:** Synthesized from "Technical Standards & Implementation Guide" (Hardware/OS) and "Agentic Data Strategy" (Cognitive/UX).

They are the earliest surviving statement of the project's intent, written on 2025-12-21, the same day as master ADR v0.1, and they carry the prior-art citations behind the original decisions (Biolink Model documentation and paper, TRAPI, BioThings Explorer, Bioregistry, the MCP specification, and the upstream API documentation).

| File | Title cited in ADR v0.1 | Sources cited |
|---|---|---|
| `technical-standards-implementation-guide-2025-12-21.md` | "Technical Standards & Implementation Guide" | 38 |
| `agentic-data-strategy-2025-12-21.md` | "Agentic Data Strategy" | 33 |

## Provenance

Copied unchanged from the predecessor repository `donbr/lifesciences-mcp`, commit `64dc057bd5d867e44d560f864a5faea2b2215837` (2025-12-24):

| This file | Original path |
|---|---|
| `technical-standards-implementation-guide-2025-12-21.md` | `docs/archived-research/Technical_Life_Sciences_MCP_Strategy.md` |
| `agentic-data-strategy-2025-12-21.md` | `docs/archived-research/Agentic_Data_Strategy_for_Life_Sciences.md` |

Both reports were first committed in `452aeea` (2025-12-21). The 2025-12-24 commit only removed Markdown escape characters and whitespace; the text is otherwise identical.

## Reading them

These are AI deep-research reports. Their citations mix primary standards and official API documentation with forum posts, blogs and videos, and some footnotes are attached to the wrong claim. Treat a citation as a lead to verify against the primary source, not as evidence on its own.

Where they bear on ADR-001:

- **Biolink Model.** Technical guide §7.1 makes Biolink "the mandated interoperability standard" and §7.2 requires every tool to re-map its output to the Biolink schema, in TRAPI message form. Master ADR v0.1 kept the Biolink vocabulary but rejected the TRAPI nesting for context efficiency. See `../critique/adr-001-agentic-biolink-decision-record-2026-09-02.md`.
- **CURIEs.** Technical guide §5.2 sets the CURIE table, including the `CHEMBL:` prefix the code uses today.
- **Cognitive Hooks and triangulation.** Agentic Data Strategy §6 and §7.
