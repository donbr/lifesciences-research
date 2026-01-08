#!/usr/bin/env python3
"""
NSCLC Showcase Script v2 (FastMCP Cloud)
=========================================
This script demonstrates the "KRAS Targeting" and "EML4-ALK Fusion" scenarios
using the Life Sciences MCP Server deployed at FastMCP Cloud via JSON-RPC.

Enhancements from v1:
- WikiPathways integration for pathway visualization
- ClinicalTrials.gov integration for active trial discovery
- Uses MCP protocol (JSON-RPC 2.0) over HTTP to deployed FastMCP Cloud endpoint

MCP Endpoint: https://lifesciences-research.fastmcp.app/mcp
Protocol: JSON-RPC 2.0
Transport: HTTP POST

Tools used:
- hgnc_search_genes, hgnc_get_gene
- biogrid_search_genes, biogrid_get_interactions
- opentargets_get_associations
- string_search_proteins, string_get_interactions
- chembl_search_compounds
- wikipathways_search_pathways, wikipathways_get_pathway, wikipathways_get_pathway_components
- clinicaltrials_search_trials, clinicaltrials_get_trial, clinicaltrials_get_trial_locations
"""

import asyncio
import json
import logging
from typing import Any

import httpx
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("nsclc_showcase_v2")

# MCP endpoint (use environment variable or default to FastMCP Cloud)
import os
MCP_ENDPOINT = os.getenv("FASTMCP_CLOUD_ENDPOINT", "https://lifesciences-research.fastmcp.app/mcp")
# For local testing: export FASTMCP_CLOUD_ENDPOINT=http://localhost:8000/mcp


class MCPClient:
    """Simple MCP client for JSON-RPC 2.0 over HTTP."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.client = httpx.AsyncClient(timeout=120.0)  # Increased for slow ChEMBL SDK
        self.request_id = 0

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call an MCP tool via JSON-RPC 2.0."""
        self.request_id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
        }

        logger.debug(f"Calling tool: {tool_name} with args: {arguments}")

        response = await self.client.post(
            self.endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )

        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code}: {response.text}")
            return {"success": False, "error": {"message": f"HTTP {response.status_code}"}}

        # Parse SSE response (FastMCP uses Server-Sent Events)
        response_text = response.text
        logger.debug(f"Raw response: {response_text[:500]}")

        # Extract JSON from SSE format
        data_lines = [line for line in response_text.split("\n") if line.startswith("data: ")]
        if not data_lines:
            logger.error(f"No data lines in SSE response: {response_text[:200]}")
            return {"success": False, "error": {"message": "Invalid SSE response"}}

        # Parse the last data line (complete response)
        try:
            data = json.loads(data_lines[-1].replace("data: ", ""))
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response: {response_text[:500]}")
            return {"success": False, "error": {"message": f"JSON decode error: {e}"}}

        if "error" in data:
            logger.error(f"JSON-RPC error: {data['error']}")
            return {"success": False, "error": data["error"]}

        # Extract result from MCP response
        result = data.get("result", {})

        # MCP tools return content array with text
        if "content" in result:
            content = result["content"]
            if content and isinstance(content, list):
                # Parse JSON from first text content
                text_content = content[0].get("text", "{}")
                try:
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    return text_content

        return result

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


def is_error(result: Any) -> bool:
    """Check if MCP tool result is an error envelope."""
    return isinstance(result, dict) and result.get("success") is False


async def resolve_gene(mcp: MCPClient, symbol: str):
    """Resolve a gene symbol to HGNC ID using MCP tools."""
    print(f"   Resolving '{symbol}' via MCP tool: hgnc_search_genes...")

    # Search for gene
    search_result = await mcp.call_tool("hgnc_search_genes", {"query": symbol, "page_size": 1})

    if is_error(search_result) or not search_result.get("items"):
        print(f"   Error: '{symbol}' not found.")
        return None

    top_hit = search_result["items"][0]
    print(
        f"   ✅ Resolved '{symbol}' -> {top_hit['symbol']} ({top_hit['id']}) [Score: {top_hit['score']:.2f}]"
    )

    # Get full gene details
    gene = await mcp.call_tool("hgnc_get_gene", {"hgnc_id": top_hit["id"]})

    if is_error(gene):
        print(f"   Error fetching details: {gene.get('error', {}).get('message')}")
        return None

    return gene


async def run_kras_scenario_enhanced(mcp: MCPClient):
    """KRAS scenario with WikiPathways pathway visualization."""
    print("\n" + "=" * 70)
    print("SCENARIO 1: The 'Undruggable' KRAS Hunt (Enhanced with WikiPathways)")
    print("=" * 70)

    # Step 1: Identity - Resolve KRAS
    print("\n[Step 1] Identity: Resolving 'KRAS' via hgnc_search_genes tool...")
    kras_gene = await resolve_gene(mcp, "KRAS")
    if not kras_gene:
        return

    print(f"✅ Found: {kras_gene['symbol']} (ID: {kras_gene['id']})")
    print(f"   Name: {kras_gene['name']}")

    # Step 2: Network Analysis - Find MAPK members via BioGRID
    print("\n[Step 2] Network: Finding downstream effectors via biogrid_get_interactions tool...")

    interactions_result = await mcp.call_tool(
        "biogrid_get_interactions", {"gene_symbol": kras_gene["symbol"], "max_results": 20}
    )

    if is_error(interactions_result):
        print(f"Error: {interactions_result.get('error', {}).get('message')}")
        return

    interactions = interactions_result.get("interactions", [])
    print(f"✅ Found {len(interactions)} interactions from BioGRID.")

    # Check for MAPK pathway members
    mapk_members = {"RAF1", "BRAF", "MAP2K1", "MAPK1"}
    found_members = set()
    for i in interactions:
        partner = i["symbol_b"] if i["symbol_a"] == kras_gene["symbol"] else i["symbol_a"]
        if partner in mapk_members:
            found_members.add(partner)

    if found_members:
        print(f"   Confirmed interaction with MAPK pathway: {', '.join(found_members)}")
    else:
        print("   (Note: Top 20 interactions did not include canonical MAPK members)")

    # NEW Step 2.5: Pathway Context via WikiPathways
    print(
        "\n[Step 2.5] Pathway: Visualizing MAPK signaling via wikipathways_search_pathways tool..."
    )

    pathway_results = await mcp.call_tool(
        "wikipathways_search_pathways",
        {"query": "MAPK ERK signaling", "organism": "Homo sapiens", "page_size": 3},
    )

    if is_error(pathway_results):
        print(f"   Error: {pathway_results.get('error', {}).get('message')}")
    elif pathway_results.get("items"):
        top_pathway = pathway_results["items"][0]
        print(f"   ✅ Found pathway: {top_pathway['title']} ({top_pathway['id']})")

        # Get detailed pathway information
        pathway = await mcp.call_tool("wikipathways_get_pathway", {"pathway_id": top_pathway["id"]})

        if not is_error(pathway):
            print(f"   URL: {pathway['url']}")
            counts = pathway.get("component_counts", {})
            print(
                f"   Components: {counts.get('gene_count', 0)} genes, "
                f"{counts.get('interaction_count', 0)} interactions"
            )

            # Get pathway components
            components = await mcp.call_tool(
                "wikipathways_get_pathway_components", {"pathway_id": top_pathway["id"]}
            )

            if not is_error(components) and components.get("genes"):
                pathway_genes = {node["name"] for node in components["genes"] if node.get("name")}

                kras_in_pathway = "KRAS" in pathway_genes
                mapk_overlap = found_members & pathway_genes

                if kras_in_pathway:
                    print("   ✅ KRAS confirmed in pathway")
                if mapk_overlap:
                    print(f"   ✅ Pathway contains BioGRID partners: {', '.join(mapk_overlap)}")

                print("\n   💡 Insight: Pathway shows mechanistic context for KRAS oncogenesis.")
                print("      Downstream effectors (MEK/ERK) may be alternative targets.")

    # Step 3: Clinical Relevance via Open Targets
    print(
        "\n[Step 3] Relevance: Validating disease associations via opentargets_get_associations tool..."
    )

    ensembl_id = kras_gene.get("cross_references", {}).get("ensembl_gene")
    if not ensembl_id:
        print("   Warning: No Ensembl ID found, skipping Open Targets.")
    else:
        associations_result = await mcp.call_tool(
            "opentargets_get_associations", {"target_id": ensembl_id, "page_size": 5}
        )

        if is_error(associations_result):
            print(f"Error: {associations_result.get('error', {}).get('message')}")
        elif associations_result.get("items"):
            count = associations_result.get("pagination", {}).get("total_count") or len(
                associations_result["items"]
            )
            print(f"✅ Found {count} disease associations for KRAS.")
            print("   Top associations:")
            for assoc in associations_result["items"][:3]:
                print(f"   - {assoc['disease_name']} (Score: {assoc['score']:.2f})")

    print(
        "\n   💡 Final Insight: KRAS validated as lung cancer target with known MAPK pathway mechanism."
    )


async def run_alk_scenario_enhanced(mcp: MCPClient):
    """ALK fusion scenario with ClinicalTrials discovery."""
    print("\n" + "=" * 70)
    print("SCENARIO 2: EML4-ALK Fusion Precision Medicine (Enhanced with ClinicalTrials)")
    print("=" * 70)

    # Step 1: Resolve Components
    print("\n[Step 1] Identity: Resolving 'EML4' and 'ALK' via hgnc_search_genes tool...")
    eml4 = await resolve_gene(mcp, "EML4")
    alk = await resolve_gene(mcp, "ALK")

    if not (eml4 and alk):
        print("Error: Could not resolve genes.")
        return

    print(f"✅ Resolved EML4 ({eml4['id']}) and ALK ({alk['id']})")

    # Step 2: Natural Interaction via STRING
    print("\n[Step 2] Interaction: Checking natural interaction via string_search_proteins tool...")

    eml4_prot = await mcp.call_tool("string_search_proteins", {"query": eml4["symbol"], "limit": 1})

    if is_error(eml4_prot) or not eml4_prot.get("items"):
        print("   Could not find EML4 in STRING.")
    else:
        eml4_string_id = eml4_prot["items"][0]["id"]
        print(f"   Resolved EML4 to STRING ID: {eml4_string_id}")

        eml4_network = await mcp.call_tool(
            "string_get_interactions", {"string_id": eml4_string_id, "limit": 20}
        )

        if is_error(eml4_network):
            print(f"   Error: {eml4_network.get('error', {}).get('message')}")
        else:
            alk_found = False
            for edge in eml4_network.get("interactions", []):
                if edge["preferred_name_a"] == "ALK" or edge["preferred_name_b"] == "ALK":
                    alk_found = True
                    print(
                        f"   Found interaction: {edge['preferred_name_a']} <-> {edge['preferred_name_b']} (Score: {edge['score']})"
                    )
                    break

            if not alk_found:
                print("   No direct interaction found (healthy tissue).")
                print("   💡 Confirms: Fusion creates novel oncogenic mechanism.")

    # Step 3: Pharmacology via ChEMBL
    print(
        "\n[Step 3] Pharmacology: Searching for ALK inhibitors via chembl_search_compounds tool..."
    )

    drugs_result = await mcp.call_tool(
        "chembl_search_compounds", {"query": "ALK Inhibitor", "page_size": 5}
    )

    if is_error(drugs_result):
        print(f"Error: {drugs_result.get('error', {}).get('message')}")
    elif drugs_result.get("items"):
        count = drugs_result.get("pagination", {}).get("total_count") or len(drugs_result["items"])
        print(f"✅ Found {count} hits for 'ALK Inhibitor'. Top results:")
        for drug in drugs_result["items"][:3]:
            print(f"   - {drug.get('name') or drug['id']} (Score: {drug['score']:.2f})")

    # NEW Step 4: Clinical Validation via ClinicalTrials.gov
    print("\n[Step 4] Clinical: Finding active trials via clinicaltrials_search_trials tool...")

    trial_results = await mcp.call_tool(
        "clinicaltrials_search_trials",
        {
            "query": "ALK inhibitor",
            "condition": "non-small cell lung cancer",
            "status": "RECRUITING",
            "phase": "PHASE3",
            "page_size": 3,
        },
    )

    if is_error(trial_results):
        print(f"   Error: {trial_results.get('error', {}).get('message')}")
    elif trial_results.get("items"):
        count = trial_results.get("pagination", {}).get("total_count") or len(
            trial_results["items"]
        )
        print(f"   ✅ Found {count} active Phase 3 trials for ALK inhibitors in NSCLC")
        print("   Top trials:")

        for trial in trial_results["items"][:2]:
            # Get detailed trial information
            trial_detail = await mcp.call_tool("clinicaltrials_get_trial", {"nct_id": trial["id"]})

            if not is_error(trial_detail):
                print(f"\n   [{trial_detail['id']}] {trial_detail['title'][:80]}...")
                print(
                    f"      Phase: {trial_detail.get('phase')} | Enrollment: {trial_detail.get('enrollment')}"
                )

                # Show interventions
                if trial_detail.get("interventions"):
                    interventions = trial_detail["interventions"][:3]
                    print(f"      Drugs: {', '.join(interventions)}")

                # Get trial locations
                locations = await mcp.call_tool(
                    "clinicaltrials_get_trial_locations", {"nct_id": trial["id"]}
                )

                if not is_error(locations) and locations:
                    recruiting = [
                        loc for loc in locations if loc.get("recruitment_status") == "RECRUITING"
                    ]
                    if recruiting:
                        us_sites = [
                            loc for loc in recruiting if loc.get("country") == "United States"
                        ]
                        print(f"      Sites: {len(recruiting)} recruiting ({len(us_sites)} in US)")
                        if us_sites:
                            site = us_sites[0]
                            print(
                                f"      Example: {site.get('facility_name')}, {site.get('city')}, {site.get('state')}"
                            )

        print(f"\n   💡 Final Insight: {count} active trials validate ALK as actionable target.")
        print("      EML4-ALK fusion patients have multiple treatment options available.")
    else:
        print("   No active trials found.")


async def main():
    """Run both enhanced NSCLC scenarios."""
    print("=" * 70)
    print("Life Sciences MCP Server Showcase v2")
    print("Demonstrating WikiPathways + ClinicalTrials Integration")
    print("=" * 70)
    print(f"\nMCP Endpoint: {MCP_ENDPOINT}")
    print("Protocol: JSON-RPC 2.0 over HTTP")
    print("Tools: hgnc, biogrid, opentargets, string, chembl,")
    print("       wikipathways, clinicaltrials")

    # Initialize MCP client
    mcp = MCPClient(MCP_ENDPOINT)

    try:
        await run_kras_scenario_enhanced(mcp)
        await run_alk_scenario_enhanced(mcp)
    finally:
        await mcp.close()

    print("\n" + "=" * 70)
    print("Showcase Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
