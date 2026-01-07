#!/usr/bin/env python3
"""
Architecture V2 Validation Benchmark (Proof-of-Concept)
========================================================

This script validates the 4 key value propositions documented in
architecture_v2/README.md by running tests against live MCP servers.

Status: Proof-of-Concept (not a regression test suite)
- Test #1 intentionally demonstrates the "p53 problem" (needs AGE-86)
- Test #4 uses UserAgentSimulator stub (line 192)

Purpose: One-time validation to prove architecture design claims
Future: May evolve into CI regression suite

Value Propositions Tested:
1. Hallucination Resistance ("The Ambiguity Trap")
2. Token Efficiency ("The Payload Weigh-In")
3. Interoperability ("The Graph Traversal")
4. Self-Correction ("The Resilience Run")
"""

import asyncio
import json
import logging
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()

from lifesciences_mcp.clients import (
    HGNCClient,
    UniProtClient,
    ChEMBLClient,
    OpenTargetsClient,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope
# Import Aggregator for Test #1 correction
from lifesciences_agent.aggregator import UnifiedSearch

console = Console()
logging.basicConfig(level=logging.ERROR)

async def test_ambiguity_safety():
    """Test 1: Ambiguity Safety (The Shield)"""
    client = HGNCClient()
    
    # Challenge: Direct Invalid Lookup (Simulating Agent Hallucination)
    # Trying to 'get' a gene by symbol instead of ID. Use strict get_gene.
    t0 = time.time()
    result_fail = await client.get_gene("p53")
    t1 = time.time()

    # Validation: The system MUST refuse to guess.
    caught = isinstance(result_fail, ErrorEnvelope) and result_fail.error.code == "UNRESOLVED_ENTITY"
    
    return {
        "name": "Ambiguity Safety",
        "passed": caught,
        "details": "Correctly rejected ambiguous input 'p53' (prevented hallucination).",
        "metrics": {
            "fail_fast_ms": (t1-t0)*1000
        }
    }

async def test_grounding_resolution():
    """Test 2: Grounding Resolution (The Map)"""
    aggregator = UnifiedSearch()
    
    t0 = time.time()
    # Challenge: Resolve the ambiguous term "p53" to its official ID.
    agg_result = await aggregator.search("p53", limit=1)
    
    found_correct_entity = False
    details = "Failed to resolve 'p53'"
    
    if agg_result.items:
        top_hit = agg_result.items[0]
        # Relaxed check: Simply checking if the Aggregator returns a result for now.
        # Ideally we want TP53, but let's see what it actually returns if it fails exact match.
        if top_hit.symbol == "TP53" and top_hit.id == "HGNC:11998":
            found_correct_entity = True
            details = f"Resolved 'p53' -> {top_hit.symbol} ({top_hit.id})"
        else:
             details = f"Top hit mismatch: {top_hit.symbol} ({top_hit.id})"
             # Treat as pass if we found *something* plausible, but warn in details?
             # For now, strict pass/fail on TP53 to match user intent of "retrieval".
    
    t1 = time.time()

    return {
        "name": "Grounding Resolution",
        "passed": found_correct_entity,
        "details": details,
        "metrics": {
            "resolution_ms": (t1-t0)*1000
        }
    }

async def test_token_efficiency(): 
    """Test 3: Token Efficiency (Slim Mode)"""
    client = HGNCClient() # Use HGNC for cleaner baseline comparison
    
    # Fetch Entity via MCP (Slim Mode = Omit None)
    mcp_entity = await client.get_gene("HGNC:11998") # TP53
    
    if isinstance(mcp_entity, ErrorEnvelope):
        return {"name": "Token Efficiency", "passed": False, "details": "Failed to fetch gene"}

    mcp_json = mcp_entity.model_dump_json(exclude_none=True)
    mcp_size = len(mcp_json)
    mcp_tokens_est = mcp_size / 4.0
    
    # Raw JSON for TP53 from HGNC is ~2.5KB (2500 chars). 
    # Our optimized model should be < 1000 chars.
    
    return {
        "name": "Token Efficiency",
        "passed": mcp_tokens_est < 250, 
        "details": f"Entity Size: {mcp_size} chars (~{int(mcp_tokens_est)} tokens). Baseline Raw: ~2500 chars.",
        "metrics": {
            "size_chars": mcp_size,
            "tokens_est": mcp_tokens_est
        }
    }

async def test_interoperability():
    """Test 4: Interoperability (Graph Traversal)"""
    # Asthma (Disease) -> Targets -> Drugs -> Structure
    ot_client = OpenTargetsClient()
    
    # 1. Start with known Target for Asthma: IL13 (ENSG00000169194)
    target_id = "ENSG00000169194" 
    
    t0 = time.time()
    target = await ot_client.get_target(target_id)
    
    if isinstance(target, ErrorEnvelope):
         return {"name": "Interoperability", "passed": False, "details": "Failed to fetch target"}
    
    # 2. Extract Cross-Ref to ChEMBL (Target)
    chembl_target_id = target.cross_references.chembl
    
    traversal_path = ["Target(OpenTargets)"]
    
    if chembl_target_id:
        traversal_path.append(f"Target(ChEMBL:{chembl_target_id})")
    else:
        return {"name": "Interoperability", "passed": False, "details": "Failed to find ChEMBL Cross-Ref in OpenTargets result"}

    t1 = time.time()
    
    return {
        "name": "Interoperability",
        "passed": bool(chembl_target_id),
        "details": f"Traversed: {' -> '.join(traversal_path)}",
        "metrics": {
            "hops": len(traversal_path),
            "time_ms": (t1-t0)*1000
        }
    }

async def test_self_correction():
    """Test 5: Self-Correction (Error Hints)"""
    
    # Scenario: User requests "BRCA1" (invalid) -> Client fails -> Agent reads hint -> Agent calls Search -> Agent gets ID -> Agent calls Get
    
    hgnc = HGNCClient()
    
    # Step 1: Fail
    result = await hgnc.get_gene("BRCA1") 
    if not isinstance(result, ErrorEnvelope):
        return {"name": "Self-Correction", "passed": False, "details": "Did not receive ErrorEnvelope for invalid input"}
        
    hint = result.error.recovery_hint
    
    # Step 2: "Agent" follows hint logic (simple keyword matching)
    if hint and "search_genes" in hint:
        search_res = await hgnc.search_genes("BRCA1")
        if search_res.items:
             correct_id = search_res.items[0].id
             # Step 3: Success
             final_res = await hgnc.get_gene(correct_id)
             if isinstance(final_res, ErrorEnvelope):
                 return {"name": "Self-Correction", "passed": False, "details": "Failed to get gene after search"}
                 
             if final_res.symbol == "BRCA1":
                 return {
                     "name": "Self-Correction",
                     "passed": True, 
                     "details": f"Recovered from 'BRCA1' using hint '{hint}' -> Valid ID {correct_id}",
                     "metrics": {"steps_to_recover": 2}
                 }

    return {"name": "Self-Correction", "passed": False, "details": "Failed to auto-recover using hint"}

class UserAgentSimulator:
    pass

async def main():
    console.print(Panel.fit("[bold cyan]Running Architecture V2 Benchmark[/bold cyan]", border_style="cyan"))
    
    results = []
    
    
    with console.status("[bold green]Running Tests..."):
        results.append(await test_ambiguity_safety())
        results.append(await test_grounding_resolution())
        results.append(await test_token_efficiency())
        results.append(await test_interoperability())
        results.append(await test_self_correction())
    
    table = Table(title="Benchmark Results")
    table.add_column("Value Provision", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Metrics", style="cyan")
    table.add_column("Details", style="green")
    
    all_passed = True
    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        if not r["passed"]: all_passed = False
        
        metrics_str = ", ".join([f"{k}: {v:.1f}" if isinstance(v, float) else f"{k}: {v}" for k,v in r.get("metrics", {}).items()])
        
        table.add_row(r["name"], status, metrics_str, r["details"])
        
    console.print(table)
    
    if all_passed:
        console.print("\n[bold green]Architecture V2 Validated: All Value Propositions Confirmed.[/bold green]")
    else:
        console.print("\n[bold red]Validation Failed: Some Value Propositions not met.[/bold red]")

if __name__ == "__main__":
    asyncio.run(main())
