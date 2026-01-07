#!/usr/bin/env python3
"""
Verify CQ-8: Paralog Dependency (SWI/SNF)
=========================================
Testing if we can detect the relationship between SMARCA4 and SMARCA2.
"""

import asyncio
import logging
from lifesciences_mcp.clients import BioGridClient, HGNCClient

from dotenv import load_dotenv

load_dotenv()

async def run():
    print("Checking SWI/SNF Paralogs (SMARCA4 / SMARCA2)...")
    
    biogrid = BioGridClient()
    
    # SMARCA4 (BRG1) - HGNC:11100
    # SMARCA2 (BRM)  - HGNC:11099
    
    print("Fetching interactions for SMARCA4...")
    # Note: BioGRID uses Symbols
    result = await biogrid.get_interactions("SMARCA4", max_results=100)
    
    found = False
    for i in result.interactions:
        partner = i.symbol_b if i.symbol_a == "SMARCA4" else i.symbol_a
        if partner == "SMARCA2":
            found = True
            print(f"✅ Found Interaction: SMARCA4 <-> SMARCA2")
            print(f"   System: {i.experimental_system}")
            # In a real synthetic lethality check, we'd look for "Negative Genetic" or similar tags
            # BioGRID often just gives physical/genetic generic tags.
            break
            
    if not found:
        print("❌ Did not find direct interaction in top 100 results.")

if __name__ == "__main__":
    asyncio.run(run())
