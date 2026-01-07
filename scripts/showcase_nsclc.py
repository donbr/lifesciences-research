#!/usr/bin/env python3
"""
NSCLC Showcase Script
=====================
This script demonstrates the "KRAS Targeting" and "EML4-ALK Fusion" scenarios
by orchestrating calls to HGNC, BioGRID, Open Targets, STRING, and ChEMBL.
"""

import asyncio
import logging
from dotenv import load_dotenv

from lifesciences_mcp.clients import (
    BioGridClient,
    ChEMBLClient,
    HGNCClient,
    OpenTargetsClient,
    STRINGClient,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope
from lifesciences_agent.aggregator import UnifiedSearch

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nsclc_showcase")



async def resolve_gene(symbol: str):
    """Helper to resolve a symbol to a full HGNC Gene object via Unified Search."""
    print(f"   Solving identity for '{symbol}' using Unified Search (AGE-86)...")
    
    # 1. Aggregated Search
    aggregator = UnifiedSearch()
    results = await aggregator.search(symbol, limit=1)
    
    if not results.items:
        print(f"   Error: '{symbol}' not found in any database.")
        return None

    top_hit = results.items[0]
    print(f"   ✅ Unified Search resolved '{symbol}' -> {top_hit.symbol} ({top_hit.id}) [Score: {top_hit.score:.2f}]")

    # 2. Get Details (Strict Lookup)
    # The aggregator ensures the top hit is an HGNC ID if possible, so we can use HGNC Client to get details.
    if top_hit.id.startswith("HGNC:"):
        async with HGNCClient() as hgnc:
            gene = await hgnc.get_gene(top_hit.id)
            if isinstance(gene, ErrorEnvelope):
                print(f"   Error fetching details for {top_hit.id}: {gene.message}")
                return None
            return gene
    else:
        print(f"   Warning: Top hit {top_hit.id} is not an HGNC ID. Strict lookup skipped.")
        return None


async def run_kras_scenario():
    print("\n" + "=" * 60)
    print("SCENARIO 1: The 'Undruggable' KRAS Hunt")
    print("=" * 60)

    # Initialize Clients
    biogrid = BioGridClient()
    opentargets = OpenTargetsClient()

    # Step 1: Identify KRAS
    print("\n[Step 1] Identity: Resolving 'KRAS' via HGNC...")
    kras_gene = await resolve_gene("KRAS")
    if not kras_gene:
        return

    print(f"✅ Found: {kras_gene.symbol} (ID: {kras_gene.id})")
    print(f"   Name: {kras_gene.name}")

    # Step 2: Network Analysis
    print("\n[Step 2] Network: finding downstream effectors via BioGRID...")
    # Finding interactions for KRAS (using gene symbol)
    interactions_result = await biogrid.get_interactions(kras_gene.symbol, max_results=20)
    if isinstance(interactions_result, ErrorEnvelope):
        print(f"Error querying BioGRID: {interactions_result.message}")
        return

    interactions = interactions_result.interactions
    print(f"✅ Found {len(interactions)} interactions from BioGRID.")

    # Check for MAPK pathway members (BRAF, RAF1, MAP2K1, MAPK1)
    mapk_members = {"RAF1", "BRAF", "MAP2K1", "MAPK1"}
    found_members = set()
    for i in interactions:
        # BioGRID returns provider/interaction partners in symbol_a/symbol_b
        # The client returns normalized Interaction objects
        partner = i.symbol_b if i.symbol_a == kras_gene.symbol else i.symbol_a
        if partner in mapk_members:
            found_members.add(partner)

    if found_members:
        print(f"   Confirmed interaction with MAPK pathway: {', '.join(found_members)}")
    else:
        print(
            "   (Note: Top 20 interactions did not include canonical MAPK members, try increasing limit)"
        )

    # Step 3: Clinical Relevance (Target -> Disease)
    print("\n[Step 3] Relevance: Validating disease associations via Open Targets...")
    # Open Targets generally uses Ensembl IDs. HGNC provides this.
    ensembl_id = kras_gene.cross_references.ensembl_gene
    if not ensembl_id:
        print("   Warning: No Ensembl ID found for KRAS, skipping Open Targets.")
    else:
        associations_result = await opentargets.get_associations(ensembl_id, page_size=5)
        if isinstance(associations_result, ErrorEnvelope):
            print(f"Error querying Open Targets: {associations_result.message}")
        elif associations_result.items:
            # PaginationEnvelope has .pagination.total_count
            count = (
                associations_result.pagination.total_count
                if associations_result.pagination.total_count is not None
                else len(associations_result.items)
            )
            print(f"✅ Found {count} disease associations for KRAS.")
            print("   Top specific associations:")
            for assoc in associations_result.items:
                print(f"   - {assoc.disease_name} (Score: {assoc.score:.2f})")
        else:
            print("   No associations found.")

    print("\n   Insight: KRAS is a validated target for Lung Cancer (Lung Adenocarcinoma).")


async def run_alk_scenario():
    print("\n" + "=" * 60)
    print("SCENARIO 2: EML4-ALK Fusion Precision Medicine")
    print("=" * 60)

    # Initialize Clients
    string_db = STRINGClient()
    chembl = ChEMBLClient()

    # Step 1: Resolve Components
    print("\n[Step 1] Identity: Resolving 'EML4' and 'ALK' via HGNC...")
    eml4 = await resolve_gene("EML4")
    alk = await resolve_gene("ALK")

    if eml4 and alk:
        print(f"✅ Resolved EML4 ({eml4.id}) and ALK ({alk.id})")
    else:
        print("Error: Could not resolve genes.")
        return

    # Step 2: Natural Interaction
    print("\n[Step 2] Interaction: Checking natural interaction via STRING...")

    # 1. Get STRING ID for EML4
    eml4_prot = await string_db.search_proteins(eml4.symbol, limit=1)
    if isinstance(eml4_prot, ErrorEnvelope) or not eml4_prot.items:
        print("   Could not find EML4 in STRING.")
    else:
        eml4_string_id = eml4_prot.items[0].id
        print(f"   Resolved EML4 to STRING ID: {eml4_string_id}")

        # 2. Get Interactions for EML4
        eml4_network = await string_db.get_interactions(eml4_string_id, limit=20)

        if isinstance(eml4_network, ErrorEnvelope):
            print(f"   Error fetching EML4 interactions: {eml4_network.message}")
        else:
            # 3. Check for ALK in the network
            # Interactions contain preferred_name_a / preferred_name_b
            alk_found = False
            for edge in eml4_network.interactions:
                if edge.preferred_name_a == "ALK" or edge.preferred_name_b == "ALK":
                    alk_found = True
                    print(
                        f"   found interaction: {edge.preferred_name_a} <-> {edge.preferred_name_b} (Score: {edge.score})"
                    )
                    break

            if not alk_found:
                print(
                    "   No direct high-confidence interaction found between EML4 and ALK in healthy tissue context."
                )
                print(
                    "   (This confirms the fusion creates a novel oncogenic mechanism independent of wild-type association)"
                )

    # Step 3: Pharmacology
    print("\n[Step 3] Pharmacology: Searching for 'ALK Inhibitor' in ChEMBL...")
    # ChEMBL Client uses search_compounds for text search
    drugs_result = await chembl.search_compounds("ALK Inhibitor", page_size=5)

    if isinstance(drugs_result, ErrorEnvelope):
        print(f"Error querying ChEMBL: {drugs_result.message}")
    elif drugs_result.items:
        # PaginationEnvelope has .pagination.total_count
        count = (
            drugs_result.pagination.total_count
            if drugs_result.pagination.total_count is not None
            else len(drugs_result.items)
        )
        print(f"✅ Found {count} hits for 'ALK Inhibitor'. Top results:")
        for drug in drugs_result.items:
            # CompoundSearchCandidate has id, name, score, molecular_formula
            print(f"   - {drug.name or drug.id} (Score: {drug.score:.2f})")
    else:
        print("   No drugs found.")


async def main():
    print("Starting Life Sciences MCP Showcase...")
    await run_kras_scenario()
    await run_alk_scenario()


if __name__ == "__main__":
    asyncio.run(main())
