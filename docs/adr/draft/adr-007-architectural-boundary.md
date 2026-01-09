# ADR-007: Architectural Boundary - Stateless Tool Provider (Draft)

## Status
Draft

## Context
As the project ecosystem expands to include "Agentic" capabilities (reasoning loops, long-running workflows, memory), there is a risk of "Scope Creep" where agent logic bleeds into the tool layer. This coupling makes tools harder to test, reuse, and reason about.

We must explicitly define the boundary between "This Repository" (Life Sciences MCP) and the external "Agentic Systems" that consume it.

## Decision
We adopt a strict **Stateless Tool Provider** boundary for this repository.

### 1. The Boundary
*   **IN SCOPE**: 
    *   Deterministic Tools (Input -> Output)
    *   Stateless API Wrappers
    *   Atomic Business Logic (e.g., "Search Gene", "Get Protein")
*   **OUT OF SCOPE**: 
    *   Agentic Loops ("Reasoning")
    *   State Management (Memory, Checkpoints)
    *   Durable Workflows (Retries over days, Sagas)
    *   Orchestration Logic ("Deciding which tool to call next")

### 2. Consumer Contract
This repository guarantees that all exposed MCP tools are:
1.  **Stateless**: A call to a tool does not change the internal state of the server in a way that affects subsequent calls (caches are permitted but must be transparent).
2.  **Deterministic**: The same input (mostly) yields the same output, barring external API changes.
3.  **Agent-Agnostic**: Tools do not know *who* is calling them (LangGraph, AutoGen, Script, Human).

## Consequences
*   **Positive**: This repository remains lightweight, testable, and highly portable. It can be "plugged in" to any agent frameworks.
*   **Negative**: Complex multi-step logic (e.g., "Find gene, then get sequence, then map variants") must be implemented by the *caller*, not the tool. We do not provide "Macro Tools" that hide these decisions.
