import pytest
from lifesciences_mcp.servers.gateway import mcp

@pytest.mark.asyncio
async def test_gateway_tools_exposed():
    """Verify that the gateway exposes the expected tools, including search_genes."""
    tools = await mcp.get_tools()
    
    # Handle dict (when using mounts) or list return type
    if isinstance(tools, dict):
        tool_names = list(tools.keys())
    else:
        tool_names = [t.name for t in tools]
        
    print(f"Gateway tools: {tool_names}")
    
    # Updated to match User's consistent namespaced strategy
    expected_namespaced_tools = [
        "hgnc_search_genes", "hgnc_get_gene",
        "uniprot_search_proteins", "uniprot_get_protein",
        "pubchem_search_compounds", "pubchem_get_compound",
        "clinicaltrials_search_trials", "clinicaltrials_get_trial",
        "wikipathways_search_pathways", "wikipathways_get_pathway",
        "opentargets_get_associations",
        "iuphar_search_targets", "iuphar_get_target",
        "ensembl_get_transcript",
        "entrez_get_pubmed_links",
        "chembl_get_compounds_batch",
        "string_get_interactions", "string_get_network_image_url",
        # Secondary tools are also namespaced, checking a few:
        "biogrid_search_genes", "biogrid_get_interactions"
    ]
    
    for tool in expected_namespaced_tools:
        assert tool in tool_names, f"Expected namespaced tool '{tool}' not found in Gateway."

    # Verify NO generic root tools exist anymore to ensure strategy is clean
    generic_tools = [
        "search_genes", "get_gene", "search_proteins", "get_protein",
        "search_compounds", "get_compound", "search_trials", "get_trial"
    ]
    for tool in generic_tools:
        assert tool not in tool_names, f"Generic tool '{tool}' should NOT be present (strategy is fully namespaced)."

    # Check total count (should be >= 30)
    assert len(tool_names) >= 30
