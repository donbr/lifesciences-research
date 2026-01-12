# Draft X Posts for Life Sciences MCP

## Strategy
Focus on the **"Bridge"** capability: Linking the rigid world of biological databases (ChEMBL, Ensembl) with the flexible reasoning of Agents (Claude/Gemini).

**Key Themes from `prior-art-api-patterns.md`:**
1.  **Strict vs. Fuzzy**: The "Fuzzy-to-Fact" protocol.
2.  **Federation**: Connecting silos (Genomics -> Pharma -> Clinical) without a massive warehouse.
3.  **Token Efficiency**: The `slim` parameter importance.

## 1. The Main Post (The Hook)
**Goal**: highlight the "Self-Healing" and "Federated" nature.

**Text**:
Building "Agentic" tools for Life Sciences isn't just about wrapping APIs. It's about solving the *Knowledge Gap* between LLMs and rigid databases. 🧬🤖

Introducing `lifesciences-mcp`: A formalized Model Context Protocol server that turns OpenTargets, ChEMBL, and ClinicalTrials.gov into a **Federated, Self-Healing Knowledge Graph**.

Key innovation: The **"Fuzzy-to-Fact" Protocol**.
1️⃣ Agent "guesses" a gene (e.g., "NGLY1").
2️⃣ Tool resolves it to `HGNC:17646` or `ENSG...`.
3️⃣ Agent locks onto the ID for all downstream queries.

No more hallucinations. Just verifiable biology.

[Link to Repo]
#biotech #AI #LLM #Agentic #MCP

**Showcase Image**:
A screenshot of the `docs/agentic-architectural-patterns.md` mermaid diagram ("The Durable Specialist"), or a snippet of the "Self-Healing" validation log from CQ7 where it fixed the MONDO ID.

## 2. Follow-Up Post (The Deep Dive)
**Goal**: Explain *why* this matters (The "Prior Art" context).

**Text**:
Why build this? Most bio-APIs (TRAPI, BioLink) are designed for machines, not Agents. They return 5MB of JSON when the LLM only needs 5 lines.

We implemented **Token Budgeting** directly into the tools:
✅ `slim=True` for efficient reasoning.
✅ "Retrieval-Optimized" schemas that respect context windows.
✅ Explicit error recovery hints (e.g., "ID Obsolete, try searching web").

It's not just an API wrapper; it's an **Agent-Native Interface** for biology.

#bioinformatics #DeepAgents #PydanticAI

## 3. The "Platform Engineering" Angle (The Philosophy)
**Goal**: Appeal to the engineers/architects. Frame reliability as an architectural choice.

**Text**:
"AI without guardrails creates chaos faster than humans can verify." 📉

We applied **Platform Engineering** principles (Team Topologies) to biological AI.
Instead of letting the agent "wing it", we built a "Thick Platform" of 12+ MCP servers with strict schemas.

Core Pillars:
1️⃣ **Golden Paths**: Standardized `/scaffold` patterns for every tool.
2️⃣ **Spec-Driven**: `/speckit` ensures Agents plan before they code.
3️⃣ **Agentic Biolink**: One schema to rule 12+ databases.

Result? A researcher asks a question, and the platform handles the plumbing.

Read the rationale: `docs/platform-engineering-rationale.md`
#PlatformEngineering #TeamTopologies #DataEngineering

## 4. The "Standing on Shoulders" Angle (The Context)
**Goal**: Show humility and deep understanding. "Repurposing > Reinventing".

**Text**:
In tech, we obsess over "New". In Science, we build on what works. 🏛️

This project isn't a random invention. It's a formalization of 20 years of bioinformatics wisdom from STRING, STITCH, and NCATS Translator.
We didn't invent the patterns; we just taught them to the Agents.

Success means **Aligning** with the ecosystem, not replacing it.

Alignment is a feature. Read the history: `docs/prior-art-api-patterns.md`
#OpenScience #Bioinformatics #TRAPI #ResearchLegacy

## 5. The "Static Data Rot" Angle (The Silent Killer)
**Goal**: Highlight the specific "Self-Healing" value prop.

**Text**:
In software, "Rot" means code breaking. In Biology, the **Facts themselves rot**. 🦠

A disease ID from 2024 might be obsolete today (`MONDO:0014109` -> `MONDO:0800044`).
A "known" drug mechanism might be retracted or refined.

Standard Databases are Snapshots. They are wrong the moment they are published.
Agents are **Just-In-Time**.

Our Architecture doesn't trust the snapshot. It uses the database as a "Hint" and validates against the live "Fact".

Agents > Databases for dynamic science.
#DataRot #LivingScience #KnowledgeGraph
