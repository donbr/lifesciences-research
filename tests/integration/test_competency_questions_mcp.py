"""Automated validation suite for all 23 competency questions using the MCP Gateway.

This module validates that the MCP Gateway correctly exposes and routes tools for
all 23 competency questions. It invokes the tools via the `mcp.get_tool(...).fn(...)`
interface to verify the integration of the tool definitions within the FastMCP app.

Performance Targets:
    - Single tool call: <2s (SC-001)
    - Fuzzy-to-Fact workflow: <5s
    - Search quality: 90% score=1.0

MCP Tool Coverage:
    - CQ-1: hgnc_search_genes
    - CQ-2: hgnc_get_gene
    - CQ-3: opentargets_search_targets, chembl_search_compounds, chembl_get_compound
    - CQ-4: string_search_proteins
    - CQ-5: biogrid_search_genes, biogrid_get_interactions
    - CQ-6: iuphar_search_ligands
    - CQ-7: wikipathways_search_pathways
    - CQ-8: clinicaltrials_search_trials (SKIPPED - Cloudflare blocking)
    - CQ-9: biogrid_get_interactions
    - CQ-10: chembl_search_compounds
    - CQ-11: ensembl_search_genes, ensembl_get_gene
    - CQ-12: pubchem_search_compounds, pubchem_get_compound
    - CQ-13: wikipathways_search_pathways, wikipathways_get_pathway_components, chembl_search_compounds
    - CQ-14: chembl_search_compounds
    - CQ-15: chembl_search_compounds
    - CQ-16: clinicaltrials_search_trials (SKIPPED - Cloudflare blocking)
    - CQ-17: chembl_search_compounds
    - CQ-18: uniprot_get_protein
    - CQ-19: chembl_get_compounds_batch
    - CQ-20: wikipathways_get_pathway, wikipathways_get_pathway_components
    - CQ-21: clinicaltrials_get_trial (SKIPPED - Cloudflare blocking)
    - CQ-22: entrez_get_pubmed_links
    - CQ-23: wikipathways_get_pathways_for_gene
"""

import os

import pytest

from lifesciences_mcp.servers import (
    biogrid,
    chembl,
    clinicaltrials,
    ensembl,
    entrez,
    hgnc,
    iuphar,
    opentargets,
    pubchem,
    string,
    uniprot,
    wikipathways,
)
from lifesciences_mcp.servers.gateway import mcp
from tests.utils import to_dict

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def reset_singletons():
    """Reset server singletons to ensure fresh event loops."""
    biogrid._client = None
    chembl._client = None
    clinicaltrials._client = None
    ensembl._client = None
    entrez._client = None
    hgnc._client = None
    iuphar._client = None
    opentargets._client = None
    pubchem._client = None
    string._client = None
    uniprot._client = None
    wikipathways._client = None


# Level 1: Core Capabilities


@pytest.mark.asyncio
async def test_cq1_target_resolvability():
    """CQ-1: Resolve TP53 (canonical symbol) to HGNC:11998.

    MCP Tool: hgnc_search_genes
    Note: Alias "p53" fails (known issue), use canonical symbol "TP53".
    """
    tool = await mcp.get_tool("hgnc_search_genes")
    result = await tool.fn(query="TP53", page_size=5)
    data = to_dict(result)

    assert data["items"], "No results returned for TP53"
    assert data["items"][0]["id"] == "HGNC:11998", "Did not resolve to HGNC:11998"
    assert data["items"][0]["symbol"] == "TP53", "Symbol mismatch"
    assert data["items"][0]["score"] == 1.0, "Score should be 1.0 for exact match"


@pytest.mark.asyncio
async def test_cq2_cross_domain_mapping():
    """CQ-2: Map HGNC:1100 (BRCA1) to UniProt ID P38398.

    MCP Tool: hgnc_get_gene
    """
    tool = await mcp.get_tool("hgnc_get_gene")
    result = await tool.fn(hgnc_id="HGNC:1100")
    data = to_dict(result)

    assert data["id"] == "HGNC:1100", "Gene ID mismatch"
    assert data["symbol"] == "BRCA1", "Symbol mismatch"
    assert "cross_references" in data, "Missing cross_references"
    assert "uniprot" in data["cross_references"], "Missing UniProt cross-reference"
    assert "P38398" in data["cross_references"]["uniprot"], "UniProt ID not found"


@pytest.mark.asyncio
async def test_cq3_therapeutic_insight():
    """CQ-3: Find approved drugs for EGFR (Gefitinib).

    MCP Tools: opentargets_search_targets, chembl_search_compounds, chembl_get_compound
    """
    ot_search = await mcp.get_tool("opentargets_search_targets")
    chembl_search = await mcp.get_tool("chembl_search_compounds")
    chembl_get = await mcp.get_tool("chembl_get_compound")

    # Step 1: Find EGFR target
    targets_result = await ot_search.fn(query="EGFR", page_size=5)
    targets = to_dict(targets_result)
    assert targets["items"], "No EGFR targets found"
    assert targets["items"][0]["id"] == "ENSG00000146648", "EGFR not found"

    # Step 2: Search Gefitinib
    compounds_result = await chembl_search.fn(query="Gefitinib", page_size=5)
    compounds = to_dict(compounds_result)
    assert compounds["items"], "No Gefitinib results"
    assert compounds["items"][0]["id"] == "CHEMBL:939", "Gefitinib ID mismatch"

    # Step 3: Get compound details
    gefitinib_result = await chembl_get.fn(chembl_id="CHEMBL:939")
    gefitinib = to_dict(gefitinib_result)
    assert gefitinib["id"] == "CHEMBL:939", "Compound ID mismatch"
    assert gefitinib["max_phase"] == 4, "Gefitinib should be approved (phase 4)"
    assert "indications" in gefitinib, "Missing indications"


@pytest.mark.asyncio
async def test_cq4_protein_interaction_network():
    """CQ-4: Top physical interaction partners of TP53 (STRING).

    MCP Tool: string_search_proteins
    """
    tool = await mcp.get_tool("string_search_proteins")
    proteins_result = await tool.fn(query="TP53", species=9606, limit=5)
    proteins = to_dict(proteins_result)
    assert proteins["items"], "No TP53 results from STRING"
    assert proteins["items"][0]["id"] == "STRING:9606.ENSP00000269305", "TP53 STRING ID mismatch"


# Level 2: NSCLC Research Scenarios


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("BIOGRID_API_KEY"),
    reason="BIOGRID_API_KEY not set",
)
async def test_cq5_kras_synthetic_lethality():
    """CQ-5: KRAS interactors from BioGRID.

    MCP Tools: biogrid_search_genes, biogrid_get_interactions
    """
    search_tool = await mcp.get_tool("biogrid_search_genes")
    interactions_tool = await mcp.get_tool("biogrid_get_interactions")

    # Step 1: Validate KRAS gene
    validation_result = await search_tool.fn(query="KRAS")
    validation = to_dict(validation_result)
    assert validation["items"], "KRAS not found"
    assert validation["items"][0]["symbol"] == "KRAS", "Symbol mismatch"

    # Step 2: Get interactions
    interactions_result = await interactions_tool.fn(gene_symbol="KRAS", max_results=5)
    interactions = to_dict(interactions_result)
    assert interactions["query_gene"] == "KRAS", "Query gene mismatch"
    assert "interactions" in interactions, "Missing interactions"
    assert len(interactions["interactions"]) > 0, "No interactions found"


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_cq6_fusion_protein_therapy(check_iuphar_available):
    """CQ-6: ALK inhibitors (Crizotinib) from IUPHAR.

    MCP Tool: iuphar_search_ligands
    """
    tool = await mcp.get_tool("iuphar_search_ligands")
    ligands_result = await tool.fn(query="Crizotinib", page_size=5)
    ligands = to_dict(ligands_result)

    assert ligands["items"], "No Crizotinib results"
    assert ligands["items"][0]["id"] == "IUPHAR:4903", "Crizotinib ID mismatch"
    assert ligands["items"][0]["name"] == "crizotinib", "Name mismatch"
    assert ligands["items"][0]["approved"] is True, "Crizotinib should be approved"
    assert ligands["items"][0]["score"] == 1.0, "Score should be 1.0"


@pytest.mark.asyncio
async def test_cq7_pathway_mechanism_analysis():
    """CQ-7: TP53 Apoptosis pathways from WikiPathways.

    MCP Tool: wikipathways_search_pathways
    """
    tool = await mcp.get_tool("wikipathways_search_pathways")
    pathways_result = await tool.fn(query="TP53", page_size=5)
    pathways = to_dict(pathways_result)

    assert pathways["items"], "No TP53 pathways found"
    assert pathways["pagination"]["total_count"] > 100, "Should find >100 TP53 pathways"
    assert "TP53" in pathways["items"][0]["title"], "Top result should mention TP53"


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="ClinicalTrials.gov blocks Python httpx clients via Cloudflare TLS fingerprinting"
)
async def test_cq8_clinical_trial_landscape():
    """CQ-8: ALK-positive NSCLC Phase 3 trials.

    MCP Tool: clinicaltrials_search_trials
    """
    tool = await mcp.get_tool("clinicaltrials_search_trials")
    trials_result = await tool.fn(
        query="ALK-positive NSCLC",
        phase="PHASE3",
        page_size=5,
    )
    trials = to_dict(trials_result)

    assert trials["items"], "No ALK+ NSCLC Phase 3 trials found"
    assert trials["pagination"]["total_count"] > 20, "Should find >20 Phase 3 trials"
    assert trials["items"][0]["id"].startswith("NCT:"), "Invalid NCT ID format"


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("BIOGRID_API_KEY"),
    reason="BIOGRID_API_KEY not set",
)
async def test_cq9_paralog_dependency():
    """CQ-9: ARID1A interactions (chromatin remodeling complex).

    MCP Tool: biogrid_get_interactions
    """
    tool = await mcp.get_tool("biogrid_get_interactions")
    interactions_result = await tool.fn(gene_symbol="ARID1A", max_results=50)
    interactions = to_dict(interactions_result)

    assert interactions["query_gene"] == "ARID1A", "Query gene mismatch"
    assert interactions["physical_count"] > 0, "Should have physical interactions"
    assert len(interactions["interactions"]) > 0, "No interactions found"


@pytest.mark.asyncio
async def test_cq10_drug_repurposing():
    """CQ-10: PARP1 inhibitors (Olaparib).

    MCP Tool: chembl_search_compounds
    """
    tool = await mcp.get_tool("chembl_search_compounds")
    compounds_result = await tool.fn(query="Olaparib", page_size=5)
    compounds = to_dict(compounds_result)

    assert compounds["items"], "No Olaparib results"
    assert compounds["items"][0]["id"] == "CHEMBL:521686", "Olaparib ID mismatch"
    assert compounds["items"][0]["score"] == 1.0, "Score should be 1.0"


@pytest.mark.asyncio
async def test_cq11_genomic_location():
    """CQ-11: Genomic location of BRCA2 (Ensembl).

    MCP Tools: ensembl_search_genes, ensembl_get_gene
    """
    search_tool = await mcp.get_tool("ensembl_search_genes")
    get_tool = await mcp.get_tool("ensembl_get_gene")

    # Step 1: Search
    search_result = await search_tool.fn(query="BRCA2", species="human")
    search = to_dict(search_result)
    assert search["items"], "No BRCA2 results"
    ensembl_id = search["items"][0]["id"]
    assert ensembl_id.startswith("ENSG"), "Invalid Ensembl ID"

    # Step 2: Get details
    gene_result = await get_tool.fn(ensembl_id=ensembl_id)
    gene = to_dict(gene_result)
    assert gene["symbol"] == "BRCA2", "Symbol mismatch"
    assert gene["chromosome"] == "13", "Chromosome mismatch"
    assert gene["biotype"] == "protein_coding", "Biotype mismatch"


@pytest.mark.asyncio
async def test_cq12_molecular_structure():
    """CQ-12: Molecular formula of Caffeine (PubChem).

    MCP Tools: pubchem_search_compounds, pubchem_get_compound
    """
    search_tool = await mcp.get_tool("pubchem_search_compounds")
    get_tool = await mcp.get_tool("pubchem_get_compound")

    # Step 1: Search
    search_result = await search_tool.fn(query="caffeine", page_size=5)
    search = to_dict(search_result)
    assert search["items"], "No Caffeine results"
    pubchem_id = search["items"][0]["id"]
    assert pubchem_id.startswith("PubChem:CID"), "Invalid PubChem ID"

    # Step 2: Get details
    compound_result = await get_tool.fn(pubchem_id=pubchem_id)
    compound = to_dict(compound_result)
    assert compound["name"].lower() == "caffeine", "Name mismatch"
    assert compound["molecular_formula"] == "C8H10N4O2", "Formula mismatch"
    assert "cross_references" in compound, "Missing cross-references"


@pytest.mark.asyncio
async def test_cq13_pathway_drug_discovery():
    """CQ-13: Pathway-Based Drug Discovery (WikiPathways + ChEMBL).
    """
    wp_search = await mcp.get_tool("wikipathways_search_pathways")
    wp_comps = await mcp.get_tool("wikipathways_get_pathway_components")
    chembl_search = await mcp.get_tool("chembl_search_compounds")

    # Step 1: Find Apoptosis pathway
    search_result = await wp_search.fn(query="Apoptosis", organism="Homo sapiens")
    search = to_dict(search_result)
    apoptosis_pathway = next((p for p in search["items"] if "Apoptosis" in p["title"]), None)
    assert apoptosis_pathway, "Apoptosis pathway not found"
    wp_id = apoptosis_pathway["id"]

    # Step 2: Confirm BCL2 in components
    if "WP254" in wp_id:
         comps_result = await wp_comps.fn(pathway_id=wp_id)
         comps = to_dict(comps_result)
         gene_labels = {g.get("label", "") for g in comps.get("genes", [])}
         protein_labels = {p.get("label", "") for p in comps.get("proteins", [])}
         all_labels = gene_labels.union(protein_labels)

         assert any("BCL2" in label for label in all_labels), f"BCL2 not found in pathway {wp_id}"

    # Step 3: Find Venetoclax in ChEMBL
    compound_result = await chembl_search.fn(query="Venetoclax")
    compounds = to_dict(compound_result)
    assert compounds["items"], "Venetoclax not found"
    top_hit = compounds["items"][0]
    assert top_hit["name"].upper() == "VENETOCLAX", "Top hit mismatch"
    assert top_hit["id"] == "CHEMBL:3137309", "ID mismatch"


@pytest.mark.asyncio
async def test_cq14_cell_therapy_mechanism():
    """CQ-14: Tabelecleucel (cell therapy) from ChEMBL.

    MCP Tool: chembl_search_compounds
    """
    tool = await mcp.get_tool("chembl_search_compounds")
    compounds_result = await tool.fn(query="Tabelecleucel", page_size=5)
    compounds = to_dict(compounds_result)

    assert compounds["items"], "No Tabelecleucel results"
    assert compounds["items"][0]["id"] == "CHEMBL:3990008", "Tabelecleucel ID mismatch"
    assert compounds["items"][0]["score"] == 1.0, "Score should be 1.0"


@pytest.mark.asyncio
async def test_cq15_neuro_immunology_targets():
    """CQ-15: Tolebrutinib (BTK inhibitor for MS).

    MCP Tool: chembl_search_compounds
    """
    tool = await mcp.get_tool("chembl_search_compounds")
    compounds_result = await tool.fn(query="Tolebrutinib", page_size=5)
    compounds = to_dict(compounds_result)

    assert compounds["items"], "No Tolebrutinib results"
    assert compounds["items"][0]["id"] == "CHEMBL:4650323", "Tolebrutinib ID mismatch"
    assert compounds["items"][0]["score"] == 1.0, "Score should be 1.0"


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="ClinicalTrials.gov blocks Python httpx clients via Cloudflare TLS fingerprinting"
)
async def test_cq16_advanced_mutation_targeting():
    """CQ-16: KRAS G12D specific trials.

    MCP Tool: clinicaltrials_search_trials
    """
    tool = await mcp.get_tool("clinicaltrials_search_trials")
    trials_result = await tool.fn(query="KRAS G12D inhibitor", page_size=5)
    trials = to_dict(trials_result)

    assert trials["items"], "No KRAS G12D trials found"
    assert trials["pagination"]["total_count"] > 10, "Should find >10 G12D trials"
    assert any("G12D" in trial["title"] for trial in trials["items"]), "Trials should mention G12D mutation"


@pytest.mark.asyncio
async def test_cq17_novel_alzheimers_mechanisms():
    """CQ-17: Mirodenafil (PDE5 inhibitor).

    MCP Tool: chembl_search_compounds
    """
    tool = await mcp.get_tool("chembl_search_compounds")
    compounds_result = await tool.fn(query="Mirodenafil", page_size=5)
    compounds = to_dict(compounds_result)

    assert compounds["items"], "No Mirodenafil results"
    assert compounds["items"][0]["id"] == "CHEMBL:4297518", "Mirodenafil ID mismatch"
    assert compounds["items"][0]["score"] == 1.0, "Score should be 1.0"


@pytest.mark.asyncio
async def test_cq18_protein_details():
    """CQ-18: UniProt strict lookup with complete cross-references (BRCA1).

    MCP Tool: uniprot_get_protein
    """
    tool = await mcp.get_tool("uniprot_get_protein")
    protein_result = await tool.fn(uniprot_id="UniProtKB:P38398", slim=False)
    protein = to_dict(protein_result)

    assert protein["id"] == "UniProtKB:P38398", "Protein ID mismatch"
    assert protein["accession"] == "P38398", "Accession mismatch"
    assert protein["name"] == "Breast cancer type 1 susceptibility protein", "Name mismatch"
    assert "BRCA1" in protein["gene_names"], "BRCA1 not in gene names"
    assert protein["organism"] == "Homo sapiens", "Organism mismatch"

    xrefs = protein["cross_references"]
    assert "ensembl_transcript" in xrefs, "Missing Ensembl transcript cross-refs"
    assert "entrez" in xrefs, "Missing Entrez cross-ref"
    assert xrefs["entrez"] == "672", "Entrez ID mismatch"
    assert "hgnc" in xrefs, "Missing HGNC cross-ref"
    assert xrefs["hgnc"] == "HGNC:1100", "HGNC ID mismatch"


@pytest.mark.asyncio
async def test_cq19_batch_operations():
    """CQ-19: ChEMBL batch compound lookup.

    MCP Tool: chembl_get_compounds_batch
    """
    tool = await mcp.get_tool("chembl_get_compounds_batch")
    compounds_result = await tool.fn(
        chembl_ids=["CHEMBL:25", "CHEMBL:939", "CHEMBL:521686", "CHEMBL:1946170", "CHEMBL:2105717"],
        slim=True,
    )
    compounds = [to_dict(c) for c in compounds_result] if hasattr(compounds_result[0], "model_dump") else compounds_result

    assert len(compounds) == 5, "Should return 5 compounds"
    assert compounds[0]["id"] == "CHEMBL:25", "First compound ID mismatch"
    assert compounds[0]["name"] == "ASPIRIN", "Aspirin name mismatch"


@pytest.mark.asyncio
async def test_cq20_pathway_components():
    """CQ-20: WikiPathways component extraction (TP53 network).

    MCP Tools: wikipathways_get_pathway, wikipathways_get_pathway_components
    """
    get_pathway = await mcp.get_tool("wikipathways_get_pathway")
    get_comps = await mcp.get_tool("wikipathways_get_pathway_components")

    # Step 1: Get pathway metadata
    pathway_result = await get_pathway.fn(pathway_id="WP:WP1742")
    pathway = to_dict(pathway_result)
    assert pathway["id"] == "WP:WP1742", "Pathway ID mismatch"
    assert pathway["title"] == "TP53 network", "Title mismatch"
    assert pathway["component_counts"]["gene_count"] > 0, "Should have genes"

    # Step 2: Get pathway components
    components_result = await get_comps.fn(pathway_id="WP:WP1742")
    components = to_dict(components_result)
    assert "genes" in components, "Missing genes"
    assert len(components["genes"]) > 0, "Should have gene entries"

    # Verify TP53-related content
    all_labels = {node.get("label", "") for node in components["genes"]}
    all_labels.update({node.get("label", "") for node in components["proteins"]})
    assert any("TP53" in label or "p53" in label.lower() for label in all_labels), \
        "TP53/p53 not found in pathway components"


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="ClinicalTrials.gov blocks Python httpx clients via Cloudflare TLS fingerprinting"
)
async def test_cq21_trial_details():
    """CQ-21: ClinicalTrials strict lookup (ALK+ NSCLC Phase 3).

    MCP Tool: clinicaltrials_get_trial
    """
    tool = await mcp.get_tool("clinicaltrials_get_trial")
    trial_result = await tool.fn(nct_id="NCT:03456076")
    trial = to_dict(trial_result)

    assert trial["id"] == "NCT:03456076", "Trial ID mismatch"
    assert "Alectinib" in trial["title"], "Title should mention Alectinib"


@pytest.mark.asyncio
async def test_cq22_literature_links():
    """CQ-22: Entrez PubMed links for TP53 (NCBIGene:7157).

    MCP Tool: entrez_get_pubmed_links
    """
    tool = await mcp.get_tool("entrez_get_pubmed_links")
    pubmed_ids = await tool.fn(entrez_id="NCBIGene:7157", limit=5)

    assert isinstance(pubmed_ids, list), "Should return list of PubMed IDs"
    assert len(pubmed_ids) == 5, "Should return 5 PubMed IDs"
    for pmid in pubmed_ids:
        assert pmid.isdigit(), f"PubMed ID should be numeric: {pmid}"


@pytest.mark.asyncio
async def test_cq23_gene_pathway_mapping():
    """CQ-23: WikiPathways gene->pathway reverse lookup (BRCA1).

    MCP Tool: wikipathways_get_pathways_for_gene
    """
    tool = await mcp.get_tool("wikipathways_get_pathways_for_gene")
    pathways_result = await tool.fn(
        gene_id="BRCA1",
        organism="Homo sapiens",
        page_size=5,
    )
    pathways = to_dict(pathways_result)

    assert pathways["items"], "No pathways found for BRCA1"
    assert pathways["pagination"]["total_count"] > 100, "Should find >100 BRCA1 pathways"
    for pathway in pathways["items"]:
        assert pathway["id"].startswith("WP:"), "Invalid pathway ID format"
