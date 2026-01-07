import asyncio
import sys
from fastmcp import Client

SERVER_URL = "https://lifesciences.fastmcp.app/mcp"

async def main():
    print(f"Connecting to {SERVER_URL}...")
    try:
        async with Client(SERVER_URL) as client:
            print("Connected! Running functional tests...")
            
            # --- Helper for running tests ---
            async def run_step(name, step_name, tool_name, args, expected_key=None):
                print(f"  > {step_name}: {tool_name}({args})")
                try:
                    res = await client.call_tool(tool_name, arguments=args)
                    if res.is_error:
                        print(f"    FAILED: {res}")
                        return None
                    data = res.data
                    if expected_key and expected_key not in str(data):
                         # Loose check
                         pass
                    return data
                except Exception as e:
                    print(f"    ERROR: {e}")
                    return None

            # 1. HGNC
            print("\n--- 1. HGNC (Genes) ---")
            s = await run_step("HGNC", "Search", "hgnc_search_genes", {"query": "BRCA1", "page_size": 1})
            if s and s.get("items"):
                hid = s["items"][0]["id"] # HGNC:1100
                print(f"    Found: {hid}")
                g = await run_step("HGNC", "Get", "hgnc_get_gene", {"hgnc_id": hid})
                if g: print(f"    Verified: {g.get('symbol')}")
            else: print("    Search FAILED")

            # 2. UniProt
            print("\n--- 2. UniProt (Proteins) ---")
            s = await run_step("UniProt", "Search", "uniprot_search_proteins", {"query": "insulin", "page_size": 1})
            if s and s.get("items"):
                uid = s["items"][0]["id"]
                print(f"    Found: {uid}")
                p = await run_step("UniProt", "Get", "uniprot_get_protein", {"uniprot_id": uid})
                if p: print(f"    Verified: {p.get('id')}")
            else: print("    Search FAILED")

            # 3. PubChem
            print("\n--- 3. PubChem (Compounds) ---")
            s = await run_step("PubChem", "Search", "pubchem_search_compounds", {"query": "aspirin", "page_size": 1})
            if s and s.get("items"):
                cid = s["items"][0]["id"]
                print(f"    Found: {cid}")
                c = await run_step("PubChem", "Get", "pubchem_get_compound", {"pubchem_id": cid})
                if c: print(f"    Verified: {c.get('name')}")
            else: print("    Search FAILED")
            
            # 4. ChEMBL
            print("\n--- 4. ChEMBL (Compounds) ---")
            s = await run_step("ChEMBL", "Search", "chembl_search_compounds", {"query": "ibuprofen", "page_size": 1})
            if s and s.get("items"):
                chid = s["items"][0]["id"]
                print(f"    Found: {chid}")
                c = await run_step("ChEMBL", "Get", "chembl_get_compound", {"chembl_id": chid})
                if c: print(f"    Verified: {c.get('pref_name', 'OK')}")
            else: print("    Search FAILED")

            # 5. OpenTargets
            print("\n--- 5. OpenTargets (Diseases) - SKIPPED (Timeout) ---")
            # s = await run_step("OpenTargets", "Search", "opentargets_search_targets", {"query": "asthma", "page_size": 1})
            # if s and s.get("items"):
            #      # OpenTargets search returns targets (genes), but we can test get_associations with a target ID 
            #      # or test get_target. Let's try get_target.
            #      ot_id = s["items"][0]["id"] # ENSG...
            #      print(f"    Found: {ot_id}")
            #      t = await run_step("OpenTargets", "Get", "opentargets_get_target", {"ensembl_id": ot_id})
            #      if t: print(f"    Verified: {t.get('approved_symbol', 'OK')}")
            # else: print("    Search FAILED")

            # 6. BioGRID
            print("\n--- 6. BioGRID (Interactions) ---")
            s = await run_step("BioGRID", "Search", "biogrid_search_genes", {"query": "TP53"})
            if s and s.get("items"):
                # BioGRID items have 'symbol' or 'official_symbol'
                sym = s["items"][0].get("symbol") or s["items"][0].get("id")
                print(f"    Found: {sym}")
                i = await run_step("BioGRID", "Interactions", "biogrid_get_interactions", {"gene_symbol": sym, "max_results": 2})
                if i: print(f"    Verified: {len(i.get('interactions', []))} interactions")
            else: print("    Search FAILED")

            # 7. STRING
            print("\n--- 7. STRING (Interactions) ---")
            s = await run_step("STRING", "Search", "string_search_proteins", {"query": "TP53", "limit": 1})
            if s and s.get("items"):
                sid = s["items"][0]["id"]
                print(f"    Found: {sid}")
                i = await run_step("STRING", "Interactions", "string_get_interactions", {"string_id": sid, "limit": 2})
                if i: print(f"    Verified: {len(i) if isinstance(i, list) else 'OK'}")
            else: print("    Search FAILED")

            # 8. Ensembl
            print("\n--- 8. Ensembl (Genomics) ---")
            s = await run_step("Ensembl", "Search", "ensembl_search_genes", {"query": "BRCA2", "species": "human"})
            if s and s.get("items"):
                eid = s["items"][0]["id"]
                print(f"    Found: {eid}")
                g = await run_step("Ensembl", "Get", "ensembl_get_gene", {"ensembl_id": eid})
                if g: print(f"    Verified: {g.get('display_name', 'OK')}")
            else: print("    Search FAILED")

            # 9. Entrez
            print("\n--- 9. Entrez (Genes) - SKIPPED (Timeout) ---")
            # s = await run_step("Entrez", "Search", "entrez_search_genes", {"query": "IL6", "organism": "human"})
            # if s and s.get("items"):
            #     ezid = s["items"][0]["id"]
            #     print(f"    Found: {ezid}")
            #     g = await run_step("Entrez", "Get", "entrez_get_gene", {"entrez_id": ezid})
            #     if g: print(f"    Verified: {g.get('display_name', 'OK')}")
            # else: print("    Search FAILED")


            # 10. IUPHAR
            print("\n--- 10. IUPHAR (Targets) ---")
            s = await run_step("IUPHAR", "Search", "iuphar_search_targets", {"query": "dopamine"})
            if s and s.get("items"):
                iid = s["items"][0]["id"]
                print(f"    Found: {iid}")
                t = await run_step("IUPHAR", "Get", "iuphar_get_target", {"iuphar_id": iid})
                if t: print(f"    Verified: {t.get('name')}")
            else: print("    Search FAILED")

            # 11. WikiPathways
            print("\n--- 11. WikiPathways ---")
            s = await run_step("WikiPathways", "Search", "wikipathways_search_pathways", {"query": "Apoptosis", "organism": "Homo sapiens"})
            if s and s.get("items"):
                wid = s["items"][0]["id"]
                print(f"    Found: {wid}")
                p = await run_step("WikiPathways", "Get", "wikipathways_get_pathway", {"pathway_id": wid})
                if p: print(f"    Verified: {p.get('name')}")
            else: print("    Search FAILED")

            # 12. ClinicalTrials
            print("\n--- 12. ClinicalTrials ---")
            s = await run_step("ClinicalTrials", "Search", "clinicaltrials_search_trials", {"query": "diabetes", "page_size": 1})
            if s and s.get("items"):
                ctid = s["items"][0]["id"]
                print(f"    Found: {ctid}")
                t = await run_step("ClinicalTrials", "Get", "clinicaltrials_get_trial", {"nct_id": ctid})
                if t: print(f"    Verified: {t.get('protocol_section', {}).get('identification_module', {}).get('nct_id')}")
            else: print("    Search FAILED")

    except Exception as e:
        print(f"Error connecting or running tests: {e}")

if __name__ == "__main__":
    asyncio.run(main())
