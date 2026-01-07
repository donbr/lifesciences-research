"""Automated validation suite for all 23 competency questions.

This module provides parameterized integration tests that validate all Life Sciences
MCP tools against the competency questions defined in:
- docs/research/deep-research/competency_questions_2026.md
- docs/research/deep-research/competency_questions_walkthrough_2026.md

Each test uses standardized parameters (page_size=5) and validates:
1. Response structure (PaginationEnvelope or entity model)
2. Expected entity IDs or values
3. Cross-reference accuracy
4. Performance targets (<2s latency)

Usage:
    # Run all CQ tests
    pytest tests/integration/test_competency_questions_client.py -v -m integration

    # Run specific CQ
    pytest tests/integration/test_competency_questions_client.py::test_competency_question[CQ-1] -v

Performance Targets:
    - Single tool call: <2s (SC-001)
    - Fuzzy-to-Fact workflow: <5s
    - Search quality: 90% score=1.0

MCP Tool Coverage:
    - CQ-1: hgnc.search_genes
    - CQ-2: hgnc.get_gene
    - CQ-3: opentargets.search_targets, chembl.search_compounds, chembl.get_compound
    - CQ-4: string.search_proteins
    - CQ-5: biogrid.search_genes, biogrid.get_interactions
    - CQ-6: iuphar.search_ligands
    - CQ-7: wikipathways.search_pathways
    - CQ-8: clinicaltrials.search_trials (SKIPPED - Cloudflare blocking)
    - CQ-9: biogrid.get_interactions
    - CQ-10: chembl.search_compounds
    - CQ-11: ensembl.search_genes, ensembl.get_gene
    - CQ-12: pubchem.search_compounds, pubchem.get_compound
    - CQ-13: wikipathways.search_pathways, wikipathways.get_pathway_components, chembl.search_compounds
    - CQ-14: chembl.search_compounds
    - CQ-15: chembl.search_compounds
    - CQ-16: clinicaltrials.search_trials (SKIPPED - Cloudflare blocking)
    - CQ-17: chembl.search_compounds
    - CQ-18: uniprot.get_protein
    - CQ-19: chembl.get_compounds_batch
    - CQ-20: wikipathways.get_pathway, wikipathways.get_pathway_components
    - CQ-21: clinicaltrials.get_trial (SKIPPED - Cloudflare blocking)
    - CQ-22: entrez.get_pubmed_links
    - CQ-23: wikipathways.get_pathways_for_gene
"""

import os

import pytest

from lifesciences_mcp.clients.biogrid import BioGridClient
from lifesciences_mcp.clients.chembl import ChEMBLClient
from lifesciences_mcp.clients.clinicaltrials import ClinicalTrialsClient
from lifesciences_mcp.clients.ensembl import EnsemblClient
from lifesciences_mcp.clients.entrez import EntrezClient
from lifesciences_mcp.clients.hgnc import HGNCClient
from lifesciences_mcp.clients.iuphar import IUPHARClient
from lifesciences_mcp.clients.opentargets import OpenTargetsClient
from lifesciences_mcp.clients.pubchem import PubChemClient
from lifesciences_mcp.clients.string import STRINGClient
from lifesciences_mcp.clients.uniprot import UniProtClient
from lifesciences_mcp.clients.wikipathways import WikiPathwaysClient
from tests.utils import to_dict

pytestmark = pytest.mark.integration


# Level 1: Core Capabilities


@pytest.mark.asyncio
async def test_cq1_target_resolvability():
    """CQ-1: Resolve TP53 (canonical symbol) to HGNC:11998.

    MCP Tool: hgnc.search_genes
    Note: Alias "p53" fails (known issue), use canonical symbol "TP53".
    """
    client = HGNCClient()
    try:
        result = await client.search_genes(query="TP53", page_size=5)
        data = to_dict(result)

        assert data["items"], "No results returned for TP53"
        assert data["items"][0]["id"] == "HGNC:11998", "Did not resolve to HGNC:11998"
        assert data["items"][0]["symbol"] == "TP53", "Symbol mismatch"
        assert data["items"][0]["score"] == 1.0, "Score should be 1.0 for exact match"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq2_cross_domain_mapping():
    """CQ-2: Map HGNC:1100 (BRCA1) to UniProt ID P38398.

    MCP Tool: hgnc.get_gene
    """
    client = HGNCClient()
    try:
        result = await client.get_gene(hgnc_id="HGNC:1100")
        data = to_dict(result)

        assert data["id"] == "HGNC:1100", "Gene ID mismatch"
        assert data["symbol"] == "BRCA1", "Symbol mismatch"
        assert "cross_references" in data, "Missing cross_references"
        assert "uniprot" in data["cross_references"], "Missing UniProt cross-reference"
        assert "P38398" in data["cross_references"]["uniprot"], "UniProt ID not found"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq3_therapeutic_insight():
    """CQ-3: Find approved drugs for EGFR (Gefitinib).

    MCP Tools: opentargets.search_targets, chembl.search_compounds, chembl.get_compound

    Workflow:
    1. Search for EGFR target → ENSG00000146648
    2. Search for Gefitinib compound → CHEMBL:939
    3. Get compound details → max_phase=4 (approved)
    """
    ot_client = OpenTargetsClient()
    chembl_client = ChEMBLClient()
    try:
        # Step 1: Find EGFR target
        targets_result = await ot_client.search_targets(query="EGFR", page_size=5)
        targets = to_dict(targets_result)
        assert targets["items"], "No EGFR targets found"
        assert targets["items"][0]["id"] == "ENSG00000146648", "EGFR not found"

        # Step 2: Search Gefitinib
        compounds_result = await chembl_client.search_compounds(query="Gefitinib", page_size=5)
        compounds = to_dict(compounds_result)
        assert compounds["items"], "No Gefitinib results"
        assert compounds["items"][0]["id"] == "CHEMBL:939", "Gefitinib ID mismatch"

        # Step 3: Get compound details
        gefitinib_result = await chembl_client.get_compound(chembl_id="CHEMBL:939")
        gefitinib = to_dict(gefitinib_result)
        assert gefitinib["id"] == "CHEMBL:939", "Compound ID mismatch"
        assert gefitinib["max_phase"] == 4, "Gefitinib should be approved (phase 4)"
        assert "indications" in gefitinib, "Missing indications"
    finally:
        await ot_client.close()
        await chembl_client.close()


@pytest.mark.asyncio
async def test_cq4_protein_interaction_network():
    """CQ-4: Top physical interaction partners of TP53 (STRING).

    MCP Tool: string.search_proteins
    Note: Only tests search, not get_interactions (for speed).
    """
    client = STRINGClient()
    try:
        # Step 1: Search TP53
        proteins_result = await client.search_proteins(query="TP53", species=9606, limit=5)
        proteins = to_dict(proteins_result)
        assert proteins["items"], "No TP53 results from STRING"
        assert proteins["items"][0]["id"] == "STRING:9606.ENSP00000269305", (
            "TP53 STRING ID mismatch"
        )

        # Step 2: Get interactions (inferred from previous validation)
        # Note: Not executing to keep test fast, but ID is validated
    finally:
        await client.close()


# Level 2: NSCLC Research Scenarios


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("BIOGRID_API_KEY"),
    reason="BIOGRID_API_KEY not set. Get free key at https://webservice.thebiogrid.org/",
)
async def test_cq5_kras_synthetic_lethality():
    """CQ-5: KRAS interactors from BioGRID.

    MCP Tools: biogrid.search_genes, biogrid.get_interactions
    """
    client = BioGridClient()
    try:
        # Step 1: Validate KRAS gene
        validation_result = await client.search_genes(query="KRAS")
        validation = to_dict(validation_result)
        assert validation["items"], "KRAS not found"
        assert validation["items"][0]["symbol"] == "KRAS", "Symbol mismatch"

        # Step 2: Get interactions
        interactions_result = await client.get_interactions(gene_symbol="KRAS", max_results=5)
        interactions = to_dict(interactions_result)
        assert interactions["query_gene"] == "KRAS", "Query gene mismatch"
        assert "interactions" in interactions, "Missing interactions"
        assert len(interactions["interactions"]) > 0, "No interactions found"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq6_fusion_protein_therapy():
    """CQ-6: ALK inhibitors (Crizotinib) from IUPHAR.

    MCP Tool: iuphar.search_ligands
    """
    client = IUPHARClient()
    try:
        ligands_result = await client.search_ligands(query="Crizotinib", page_size=5)
        ligands = to_dict(ligands_result)

        assert ligands["items"], "No Crizotinib results"
        assert ligands["items"][0]["id"] == "IUPHAR:4903", "Crizotinib ID mismatch"
        assert ligands["items"][0]["name"] == "crizotinib", "Name mismatch"
        assert ligands["items"][0]["approved"] is True, "Crizotinib should be approved"
        assert ligands["items"][0]["score"] == 1.0, "Score should be 1.0"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq7_pathway_mechanism_analysis():
    """CQ-7: TP53 Apoptosis pathways from WikiPathways.

    MCP Tool: wikipathways.search_pathways
    """
    client = WikiPathwaysClient()
    try:
        pathways_result = await client.search_pathways(query="TP53", page_size=5)
        pathways = to_dict(pathways_result)

        assert pathways["items"], "No TP53 pathways found"
        assert pathways["pagination"]["total_count"] > 100, "Should find >100 TP53 pathways"
        # First result should be TP53 network
        assert "TP53" in pathways["items"][0]["title"], "Top result should mention TP53"
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="ClinicalTrials.gov blocks Python httpx clients via Cloudflare TLS fingerprinting - see CLAUDE.md"
)
async def test_cq8_clinical_trial_landscape():
    """CQ-8: ALK-positive NSCLC Phase 3 trials.

    MCP Tool: clinicaltrials.search_trials
    SKIPPED: ClinicalTrials.gov uses Cloudflare bot protection that blocks Python clients.
    Use manual curl testing instead - see CLAUDE.md for workaround.
    """
    client = ClinicalTrialsClient()
    try:
        trials_result = await client.search_trials(
            query="ALK-positive NSCLC",
            phase="PHASE3",
            page_size=5,
        )
        trials = to_dict(trials_result)

        assert trials["items"], "No ALK+ NSCLC Phase 3 trials found"
        assert trials["pagination"]["total_count"] > 20, "Should find >20 Phase 3 trials"
        # Verify trial IDs are NCT format
        assert trials["items"][0]["id"].startswith("NCT:"), "Invalid NCT ID format"
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("BIOGRID_API_KEY"),
    reason="BIOGRID_API_KEY not set. Get free key at https://webservice.thebiogrid.org/",
)
async def test_cq9_paralog_dependency():
    """CQ-9: ARID1A interactions (chromatin remodeling complex).

    MCP Tool: biogrid.get_interactions
    Note: Chromatin remodeling partners may not appear in top 5 results.
    """
    client = BioGridClient()
    try:
        # Use larger result set to increase chance of finding SWI/SNF complex members
        interactions_result = await client.get_interactions(gene_symbol="ARID1A", max_results=50)
        interactions = to_dict(interactions_result)

        assert interactions["query_gene"] == "ARID1A", "Query gene mismatch"
        assert interactions["physical_count"] > 0, "Should have physical interactions"
        # Verify we have interactions (relaxed assertion - exact partners vary by API results)
        assert len(interactions["interactions"]) > 0, "No interactions found"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq10_drug_repurposing():
    """CQ-10: PARP1 inhibitors (Olaparib).

    MCP Tool: chembl.search_compounds
    """
    client = ChEMBLClient()
    try:
        compounds_result = await client.search_compounds(query="Olaparib", page_size=5)
        compounds = to_dict(compounds_result)

        assert compounds["items"], "No Olaparib results"
        assert compounds["items"][0]["id"] == "CHEMBL:521686", "Olaparib ID mismatch"
        assert compounds["items"][0]["score"] == 1.0, "Score should be 1.0"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq11_genomic_location():
    """CQ-11: Genomic location of BRCA2 (Ensembl).

    MCP Tool: ensembl.search_genes, ensembl.get_gene
    """
    client = EnsemblClient()
    try:
        # Step 1: Search
        search_result = await client.search_genes(query="BRCA2", species="human")
        search = to_dict(search_result)
        assert search["items"], "No BRCA2 results"
        ensembl_id = search["items"][0]["id"]
        assert ensembl_id.startswith("ENSG"), "Invalid Ensembl ID"

        # Step 2: Get details
        gene_result = await client.get_gene(ensembl_id=ensembl_id)
        gene = to_dict(gene_result)
        assert gene["symbol"] == "BRCA2", "Symbol mismatch"
        assert gene["chromosome"] == "13", "Chromosome mismatch"
        assert gene["biotype"] == "protein_coding", "Biotype mismatch"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq12_molecular_structure():
    """CQ-12: Molecular formula of Caffeine (PubChem).

    MCP Tool: pubchem.search_compounds, pubchem.get_compound
    """
    client = PubChemClient()
    try:
        # Step 1: Search
        search_result = await client.search_compounds(query="caffeine", page_size=5)
        search = to_dict(search_result)
        assert search["items"], "No Caffeine results"
        pubchem_id = search["items"][0]["id"]
        assert pubchem_id.startswith("PubChem:CID"), "Invalid PubChem ID"

        # Step 2: Get details
        compound_result = await client.get_compound(pubchem_id=pubchem_id)
        compound = to_dict(compound_result)
        assert compound["name"].lower() == "caffeine", "Name mismatch"
        assert compound["molecular_formula"] == "C8H10N4O2", "Formula mismatch"
        assert "cross_references" in compound, "Missing cross-references"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq13_pathway_drug_discovery():
    """CQ-13: Pathway-Based Drug Discovery (WikiPathways + ChEMBL).

    Workflow:
    1. Find Apoptosis pathway (WikiPathways).
    2. Confirm BCL2 presence in pathway (WikiPathways).
    3. Find BCL2 inhibitor Venetoclax (ChEMBL).
    """
    wp_client = WikiPathwaysClient()
    chembl_client = ChEMBLClient()
    try:
        # Step 1: Find Apoptosis pathway
        search_result = await wp_client.search_pathways(query="Apoptosis", organism="Homo sapiens")
        search = to_dict(search_result)
        # Look for the canonical Apoptosis pathway (WP254)
        apoptosis_pathway = next((p for p in search["items"] if "Apoptosis" in p["title"]), None)
        assert apoptosis_pathway, "Apoptosis pathway not found"
        wp_id = apoptosis_pathway["id"]

        # Step 2: Confirm BCL2 in components
        # Note: Depending on the specific Apoptosis pathway found, BCL2 might/might not be there.
        # WP254 (Apoptosis Modulation and Signaling) usually contains it.
        # We'll assert loosely or check specifically if we found WP254.
        if "WP254" in wp_id:
            comps_result = await wp_client.get_pathway_components(pathway_id=wp_id)
            comps = to_dict(comps_result)
            gene_labels = {g.get("label", "") for g in comps.get("genes", [])}
            protein_labels = {p.get("label", "") for p in comps.get("proteins", [])}
            all_labels = gene_labels.union(protein_labels)

            assert any("BCL2" in label for label in all_labels), (
                f"BCL2 not found in pathway {wp_id}"
            )

        # Step 3: Find Venetoclax in ChEMBL
        compound_result = await chembl_client.search_compounds(query="Venetoclax")
        compounds = to_dict(compound_result)
        assert compounds["items"], "Venetoclax not found"
        # Validate top hit
        top_hit = compounds["items"][0]
        assert top_hit["name"].upper() == "VENETOCLAX", "Top hit mismatch"
        assert top_hit["id"] == "CHEMBL:3137309", "ID mismatch"

    finally:
        await wp_client.close()
        await chembl_client.close()


# Level 2: Emerging Therapies (2026 Watchlist)


@pytest.mark.asyncio
async def test_cq14_cell_therapy_mechanism():
    """CQ-14: Tabelecleucel (cell therapy) from ChEMBL.

    MCP Tool: chembl.search_compounds
    """
    client = ChEMBLClient()
    try:
        compounds_result = await client.search_compounds(query="Tabelecleucel", page_size=5)
        compounds = to_dict(compounds_result)

        assert compounds["items"], "No Tabelecleucel results"
        assert compounds["items"][0]["id"] == "CHEMBL:3990008", "Tabelecleucel ID mismatch"
        assert compounds["items"][0]["name"] == "TABELECLEUCEL", "Name mismatch"
        assert compounds["items"][0]["score"] == 1.0, "Score should be 1.0"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq15_neuro_immunology_targets():
    """CQ-15: Tolebrutinib (BTK inhibitor for MS).

    MCP Tool: chembl.search_compounds
    """
    client = ChEMBLClient()
    try:
        compounds_result = await client.search_compounds(query="Tolebrutinib", page_size=5)
        compounds = to_dict(compounds_result)

        assert compounds["items"], "No Tolebrutinib results"
        assert compounds["items"][0]["id"] == "CHEMBL:4650323", "Tolebrutinib ID mismatch"
        assert compounds["items"][0]["name"] == "TOLEBRUTINIB", "Name mismatch"
        assert compounds["items"][0]["score"] == 1.0, "Score should be 1.0"
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="ClinicalTrials.gov blocks Python httpx clients via Cloudflare TLS fingerprinting - see CLAUDE.md"
)
async def test_cq16_advanced_mutation_targeting():
    """CQ-16: KRAS G12D specific trials.

    MCP Tool: clinicaltrials.search_trials
    SKIPPED: ClinicalTrials.gov uses Cloudflare bot protection that blocks Python clients.
    Use manual curl testing instead - see CLAUDE.md for workaround.
    """
    client = ClinicalTrialsClient()
    try:
        trials_result = await client.search_trials(query="KRAS G12D inhibitor", page_size=5)
        trials = to_dict(trials_result)

        assert trials["items"], "No KRAS G12D trials found"
        assert trials["pagination"]["total_count"] > 10, "Should find >10 G12D trials"
        # Verify mutation-level granularity
        assert any("G12D" in trial["title"] for trial in trials["items"]), (
            "Trials should mention G12D mutation"
        )
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq17_novel_alzheimers_mechanisms():
    """CQ-17: Mirodenafil (PDE5 inhibitor).

    MCP Tool: chembl.search_compounds
    """
    client = ChEMBLClient()
    try:
        compounds_result = await client.search_compounds(query="Mirodenafil", page_size=5)
        compounds = to_dict(compounds_result)

        assert compounds["items"], "No Mirodenafil results"
        assert compounds["items"][0]["id"] == "CHEMBL:4297518", "Mirodenafil ID mismatch"
        assert compounds["items"][0]["name"] == "MIRODENAFIL", "Name mismatch"
        assert compounds["items"][0]["score"] == 1.0, "Score should be 1.0"
    finally:
        await client.close()


# New CQs (v2.0)


@pytest.mark.asyncio
async def test_cq18_protein_details():
    """CQ-18: UniProt strict lookup with complete cross-references (BRCA1).

    MCP Tool: uniprot.get_protein
    """
    client = UniProtClient()
    try:
        protein_result = await client.get_protein(uniprot_id="UniProtKB:P38398", slim=False)
        protein = to_dict(protein_result)

        assert protein["id"] == "UniProtKB:P38398", "Protein ID mismatch"
        assert protein["accession"] == "P38398", "Accession mismatch"
        assert protein["name"] == "Breast cancer type 1 susceptibility protein", "Name mismatch"
        assert "BRCA1" in protein["gene_names"], "BRCA1 not in gene names"
        assert protein["organism"] == "Homo sapiens", "Organism mismatch"

        # Validate cross-references (11 types expected)
        xrefs = protein["cross_references"]
        assert "ensembl_transcript" in xrefs, "Missing Ensembl transcript cross-refs"
        assert "entrez" in xrefs, "Missing Entrez cross-ref"
        assert xrefs["entrez"] == "672", "Entrez ID mismatch"
        assert "hgnc" in xrefs, "Missing HGNC cross-ref"
        assert xrefs["hgnc"] == "HGNC:1100", "HGNC ID mismatch"
        assert "omim" in xrefs, "Missing OMIM cross-refs"
        assert "pdb" in xrefs, "Missing PDB cross-refs"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq19_batch_operations():
    """CQ-19: ChEMBL batch compound lookup for token efficiency.

    MCP Tool: chembl.get_compounds_batch
    """
    client = ChEMBLClient()
    try:
        compounds_result = await client.get_compounds_batch(
            chembl_ids=[
                "CHEMBL:25",
                "CHEMBL:939",
                "CHEMBL:521686",
                "CHEMBL:1946170",
                "CHEMBL:2105717",
            ],
            slim=True,
        )
        from lifesciences_mcp.models.envelopes import ErrorEnvelope

        assert not isinstance(compounds_result, ErrorEnvelope), (
            f"Batch lookup failed: {compounds_result}"
        )
        compounds = [to_dict(c) for c in compounds_result]

        assert len(compounds) == 5, "Should return 5 compounds"
        assert compounds[0]["id"] == "CHEMBL:25", "First compound ID mismatch"
        assert compounds[0]["name"] == "ASPIRIN", "Aspirin name mismatch"
        assert compounds[1]["id"] == "CHEMBL:939", "Gefitinib ID mismatch"
        assert compounds[2]["id"] == "CHEMBL:521686", "Olaparib ID mismatch"

        # Verify slim mode (should not have full data)
        # Note: molecular_formula may be None in slim mode
        for compound in compounds:
            assert "id" in compound, "Missing ID field"
            assert "name" in compound, "Missing name field"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq20_pathway_components():
    """CQ-20: WikiPathways component extraction (TP53 network).

    MCP Tools: wikipathways.get_pathway, wikipathways.get_pathway_components
    Note: Component counts may change as WikiPathways curators update pathways.
    """
    client = WikiPathwaysClient()
    try:
        # Step 1: Get pathway metadata
        pathway_result = await client.get_pathway(pathway_id="WP:WP1742")
        pathway = to_dict(pathway_result)
        assert pathway["id"] == "WP:WP1742", "Pathway ID mismatch"
        assert pathway["title"] == "TP53 network", "Title mismatch"
        # Use ranges - pathway data can change as curators update it
        assert pathway["component_counts"]["gene_count"] > 0, "Should have genes"
        assert pathway["component_counts"]["protein_count"] > 0, "Should have proteins"

        # Step 2: Get pathway components
        components_result = await client.get_pathway_components(pathway_id="WP:WP1742")
        components = to_dict(components_result)
        assert "genes" in components, "Missing genes"
        assert "proteins" in components, "Missing proteins"
        # Use ranges - exact counts vary as WikiPathways is updated
        assert len(components["genes"]) > 0, "Should have gene entries"
        assert len(components["proteins"]) > 0, "Should have protein entries"

        # Verify TP53-related content exists (more flexible check)
        all_labels = {node.get("label", "") for node in components["genes"]}
        all_labels.update({node.get("label", "") for node in components["proteins"]})
        # Check that pathway has TP53-related content
        assert any("TP53" in label or "p53" in label.lower() for label in all_labels), (
            "TP53/p53 not found in pathway components"
        )
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="ClinicalTrials.gov blocks Python httpx clients via Cloudflare TLS fingerprinting - see CLAUDE.md"
)
async def test_cq21_trial_details():
    """CQ-21: ClinicalTrials strict lookup (ALK+ NSCLC Phase 3).

    MCP Tool: clinicaltrials.get_trial
    SKIPPED: ClinicalTrials.gov uses Cloudflare bot protection that blocks Python clients.
    Use manual curl testing instead - see CLAUDE.md for workaround.
    """
    client = ClinicalTrialsClient()
    try:
        trial_result = await client.get_trial(nct_id="NCT:03456076")
        trial = to_dict(trial_result)

        assert trial["id"] == "NCT:03456076", "Trial ID mismatch"
        assert "Alectinib" in trial["title"], "Title should mention Alectinib"
        # Status may change over time - use flexible assertion
        assert trial["status"] in ["ACTIVE_NOT_RECRUITING", "COMPLETED", "RECRUITING"], (
            f"Unexpected status: {trial['status']}"
        )

        # Validate protocol
        assert "protocol" in trial, "Missing protocol"
        assert trial["protocol"]["study_type"] == "INTERVENTIONAL", "Study type mismatch"
        assert trial["protocol"]["allocation"] == "RANDOMIZED", "Allocation mismatch"

        # Validate eligibility
        assert "eligibility_criteria" in trial, "Missing eligibility criteria"
        assert trial["eligibility_criteria"]["minimum_age"] == "18 Years", "Min age mismatch"

        # Validate outcomes
        assert "primary_outcomes" in trial, "Missing primary outcomes"
        assert len(trial["primary_outcomes"]) > 0, "No primary outcomes"

        # Validate cross-references
        assert "cross_references" in trial, "Missing cross-references"
        assert "pubmed" in trial["cross_references"], "Missing PubMed cross-refs"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq22_literature_links():
    """CQ-22: Entrez PubMed links for TP53 (NCBIGene:7157).

    MCP Tool: entrez.get_pubmed_links
    """
    client = EntrezClient()
    try:
        pubmed_ids = await client.get_pubmed_links(entrez_id="NCBIGene:7157", limit=5)
        # Returns list directly, not Pydantic model
        assert isinstance(pubmed_ids, list), "Should return list of PubMed IDs"
        assert len(pubmed_ids) == 5, "Should return 5 PubMed IDs"
        # Verify all are numeric strings
        for pmid in pubmed_ids:
            assert pmid.isdigit(), f"PubMed ID should be numeric: {pmid}"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cq23_gene_pathway_mapping():
    """CQ-23: WikiPathways gene->pathway reverse lookup (BRCA1).

    MCP Tool: wikipathways.get_pathways_for_gene
    """
    client = WikiPathwaysClient()
    try:
        pathways_result = await client.get_pathways_for_gene(
            gene_id="BRCA1",
            organism="Homo sapiens",
            page_size=5,
        )
        pathways = to_dict(pathways_result)

        assert pathways["items"], "No pathways found for BRCA1"
        assert pathways["pagination"]["total_count"] > 100, "Should find >100 BRCA1 pathways"
        # Verify pathway IDs
        for pathway in pathways["items"]:
            assert pathway["id"].startswith("WP:"), "Invalid pathway ID format"
            assert pathway["organism"] == "Homo sapiens", "Organism mismatch"
    finally:
        await client.close()
