"""Life Sciences MCP Gateway Server - Unified access to all life sciences APIs.

This gateway server composes all 12 individual MCP servers into a single
unified server for deployment to FastMCP Cloud.

Tools are accessible with prefixes:
- hgnc_search_genes, hgnc_get_gene
- uniprot_search_proteins, uniprot_get_protein
- chembl_search_compounds, chembl_get_compound, chembl_get_compounds_batch
- opentargets_search_targets, opentargets_get_target, opentargets_get_associations
- string_search_proteins, string_get_interactions, string_get_network_image_url
- biogrid_search_genes, biogrid_get_interactions
- ensembl_search_genes, ensembl_get_gene, ensembl_get_transcript
- entrez_search_genes, entrez_get_gene, entrez_get_pubmed_links
- pubchem_search_compounds, pubchem_get_compound, pubchem_get_compound_synonyms
- iuphar_search_ligands, iuphar_get_ligand, iuphar_search_targets, iuphar_get_target
- wikipathways_search_pathways, wikipathways_get_pathway, wikipathways_get_pathways_for_gene, wikipathways_get_pathway_components
- clinicaltrials_search_trials, clinicaltrials_get_trial, clinicaltrials_get_trial_locations

DrugBank is excluded (requires commercial API key).

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/gateway.py

FastMCP Cloud:
    Entrypoint: src/lifesciences_mcp/servers/gateway.py:mcp
"""

from fastmcp import FastMCP

from lifesciences_mcp.servers.biogrid import mcp as biogrid_mcp
from lifesciences_mcp.servers.chembl import mcp as chembl_mcp
from lifesciences_mcp.servers.clinicaltrials import mcp as clinicaltrials_mcp
from lifesciences_mcp.servers.ensembl import mcp as ensembl_mcp
from lifesciences_mcp.servers.entrez import mcp as entrez_mcp
from lifesciences_mcp.servers.hgnc import mcp as hgnc_mcp
from lifesciences_mcp.servers.iuphar import mcp as iuphar_mcp
from lifesciences_mcp.servers.opentargets import mcp as opentargets_mcp
from lifesciences_mcp.servers.pubchem import mcp as pubchem_mcp
from lifesciences_mcp.servers.string import mcp as string_mcp
from lifesciences_mcp.servers.uniprot import mcp as uniprot_mcp
from lifesciences_mcp.servers.wikipathways import mcp as wikipathways_mcp


# Note: DrugBank excluded - requires commercial API key
# from lifesciences_mcp.servers.drugbank import mcp as drugbank_mcp

# Create the gateway server
mcp = FastMCP("Life Sciences MCP Gateway")

# Mount all servers onto the gateway (direct mounting - no proxy overhead)
mcp.mount(hgnc_mcp, prefix="hgnc", as_proxy=False, tool_names={
    "search_genes": "hgnc_search_genes",
    "get_gene": "hgnc_get_gene"
})
mcp.mount(uniprot_mcp, prefix="uniprot", as_proxy=False, tool_names={
    "search_proteins":   "uniprot_search_proteins",
    "get_protein": "uniprot_get_protein"
})
mcp.mount(chembl_mcp, prefix="chembl", as_proxy=False, tool_names={
    "search_compounds": "chembl_search_compounds",
    "get_compound": "chembl_get_compound",
    "get_compounds_batch": "chembl_get_compounds_batch"
})
mcp.mount(opentargets_mcp, prefix="opentargets", as_proxy=False, tool_names={
    "search_targets": "opentargets_search_targets",
    "get_target": "opentargets_get_target",
    "get_associations": "opentargets_get_associations"
})
mcp.mount(string_mcp, prefix="string", as_proxy=False, tool_names={
    "search_proteins": "string_search_proteins",
    "get_interactions": "string_get_interactions",
    "get_network_image_url": "string_get_network_image_url"
})
mcp.mount(biogrid_mcp, prefix="biogrid", as_proxy=False, tool_names={
    "search_genes": "biogrid_search_genes",
    "get_interactions": "biogrid_get_interactions"
})
mcp.mount(ensembl_mcp, prefix="ensembl", as_proxy=False, tool_names={
    "search_genes": "ensembl_search_genes",
    "get_gene": "ensembl_get_gene",
    "get_transcript": "ensembl_get_transcript"
})
mcp.mount(entrez_mcp, prefix="entrez", as_proxy=False, tool_names={
    "search_genes": "entrez_search_genes",
    "get_gene": "entrez_get_gene",
    "get_pubmed_links": "entrez_get_pubmed_links"
})
mcp.mount(pubchem_mcp, prefix="pubchem", as_proxy=False, tool_names={
    "search_compounds": "pubchem_search_compounds",
    "get_compound": "pubchem_get_compound"
})
mcp.mount(iuphar_mcp, prefix="iuphar", as_proxy=False, tool_names={
    "search_targets": "iuphar_search_targets",
    "get_target": "iuphar_get_target",
    "search_ligands": "iuphar_search_ligands",
    "get_ligand": "iuphar_get_ligand"
})
mcp.mount(wikipathways_mcp, prefix="wikipathways", as_proxy=False, tool_names={
    "search_pathways": "wikipathways_search_pathways",
    "get_pathway": "wikipathways_get_pathway",
    "get_pathways_for_gene": "wikipathways_get_pathways_for_gene",
    "get_pathway_components": "wikipathways_get_pathway_components"
})
mcp.mount(clinicaltrials_mcp, prefix="clinicaltrials", as_proxy=False, tool_names={
    "search_trials": "clinicaltrials_search_trials",
    "get_trial": "clinicaltrials_get_trial",
    "get_trial_locations": "clinicaltrials_get_trial_locations"
})




if __name__ == "__main__":
    mcp.run()
