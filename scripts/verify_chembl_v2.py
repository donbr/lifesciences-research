import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")))

from lifesciences_mcp.clients.chembl import ChEMBLClient

async def verify_aspirin():
    # Debug: Direct SDK Access
    from chembl_webresource_client.new_client import new_client
    try:
        raw = new_client.molecule.get("CHEMBL25")
        print(f"DEBUG: SDK max_phase type: {type(raw.get('max_phase'))}")
        print(f"DEBUG: SDK max_phase value: {raw.get('max_phase')}")
    except Exception as e:
        print(f"DEBUG Error: {e}")

    client = ChEMBLClient()
    try:
        print("Fetching Aspirin (CHEMBL:25)...")
        
        # Force slim=False to get indications
        result = await client.get_compound("CHEMBL:25", slim=False)
        
        if "error" in result:
            print(f"FAILED: {result}")
            return

        print(f"Name: {result['name']}")
        print(f"Max Phase: {result.get('max_phase')}")
        
        indications = result.get('indications', [])
        print(f"Indications Count: {len(indications)}")
        if len(indications) > 5:
            print(f"Indications (first 5): {indications[:5]}...")
        else:
            print(f"Indications: {indications}")
        
        # Validate Max Phase
        if result.get("max_phase") == 4:
            print("✅ PASS: Max Phase is 4")
        else:
            print(f"❌ FAIL: Max Phase is {result.get('max_phase')}")
            
        # Validate Indications
        if indications and len(indications) > 0:
            print(f"✅ PASS: Found {len(indications)} indications")
            # Aspirin is indicated for fever, pain, inflammation etc.
            # Names might vary in Mesh/ChEMBL e.g. "Fever" or "Pyrexia" or "Inflammation"
            common_indications = ["Pain", "Fever", "Inflammation", "Headache", "Myocardial Infarction"]
            found = [i for i in indications if any(c.lower() in i.lower() for c in common_indications)]
            
            if found:
                 print(f"✅ PASS: Found expected indications: {found[:3]}")
            else:
                 print("⚠️ CAUTION: Did not find simple match for basic indications, please check list.")
        else:
            print("❌ FAIL: No indications found")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(verify_aspirin())
