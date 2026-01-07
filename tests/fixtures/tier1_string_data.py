"""Golden Record Test Fixtures for STRING DB (Tier 1).

This module provides verified test fixtures for the STRING MCP server.
Based on the "Library Reversal" strategy from api-tier1-plus-expansion.md.

Biological Anchor: TP53 Network
- Most frequently mutated gene in human cancers
- Dense, well-characterized interaction network
- MDM2 interaction is canonical example (score: 0.999)

Reference: https://string-db.org/network/9606.ENSP00000269305
"""

# =============================================================================
# STRING Protein Search Fixtures
# =============================================================================

STRING_SEARCH_TP53 = {
    "query": "TP53",
    "species": 9606,
    "response": [
        {
            "stringId": "9606.ENSP00000269305",
            "preferredName": "TP53",
            "ncbiTaxonId": 9606,
            "annotation": "Cellular tumor antigen p53",
            "queryItem": "TP53",
        }
    ],
}

STRING_SEARCH_MDM2 = {
    "query": "MDM2",
    "species": 9606,
    "response": [
        {
            "stringId": "9606.ENSP00000353483",
            "preferredName": "MDM2",
            "ncbiTaxonId": 9606,
            "annotation": "E3 ubiquitin-protein ligase Mdm2",
            "queryItem": "MDM2",
        }
    ],
}

# =============================================================================
# STRING Interaction Fixtures (Golden Record)
# =============================================================================

TIER1_STRING_INTERACTIONS = [
    {
        "stringId_A": "9606.ENSP00000269305",
        "stringId_B": "9606.ENSP00000353483",  # MDM2
        "preferredName_A": "TP53",
        "preferredName_B": "MDM2",
        "ncbiTaxonId": "9606",  # STRING API returns as string
        "score": 0.999,  # STRING API returns 0-1 scale
        "nscore": 0.0,  # Neighborhood: 0.0 (humans don't have operons)
        "fscore": 0.0,  # Fusion: 0.0
        "pscore": 0.0,  # Phyletic Profile: 0.0
        "ascore": 0.612,  # Co-expression (mRNA correlation)
        "escore": 0.943,  # Experimental (Physical binding)
        "dscore": 0.900,  # Database (Curated knowledge)
        "tscore": 0.985,  # Textmining (Literature mentions)
    },
    {
        "stringId_A": "9606.ENSP00000269305",
        "stringId_B": "9606.ENSP00000259261",  # ATM
        "preferredName_A": "TP53",
        "preferredName_B": "ATM",
        "ncbiTaxonId": "9606",
        "score": 0.999,
        "nscore": 0.0,
        "fscore": 0.0,
        "pscore": 0.0,
        "ascore": 0.067,  # Low co-expression
        "escore": 0.921,  # High experimental evidence
        "dscore": 0.900,
        "tscore": 0.956,
    },
    {
        "stringId_A": "9606.ENSP00000269305",
        "stringId_B": "9606.ENSP00000261584",  # BRCA1
        "preferredName_A": "TP53",
        "preferredName_B": "BRCA1",
        "ncbiTaxonId": "9606",
        "score": 0.997,
        "nscore": 0.0,
        "fscore": 0.0,
        "pscore": 0.0,
        "ascore": 0.412,
        "escore": 0.876,
        "dscore": 0.900,
        "tscore": 0.923,
    },
]

# =============================================================================
# Expected Model Outputs
# =============================================================================

EXPECTED_INTERACTION_SEARCH_CANDIDATE = {
    "id": "STRING:9606.ENSP00000269305",
    "preferred_name": "TP53",
    "annotation": "Cellular tumor antigen p53",
    "taxon_id": 9606,
    "score": 1.0,
}

EXPECTED_INTERACTION_NETWORK = {
    "id": "STRING:9606.ENSP00000269305",
    "preferred_name": "TP53",
    "taxon_id": 9606,
    "interaction_count": 3,
    "network_image_url": (
        "https://string-db.org/api/highres_image/network"
        "?identifiers=9606.ENSP00000269305&species=9606&add_nodes=10"
    ),
}

EXPECTED_MDM2_INTERACTION = {
    "string_id_a": "9606.ENSP00000269305",
    "string_id_b": "9606.ENSP00000353483",
    "preferred_name_a": "TP53",
    "preferred_name_b": "MDM2",
    "taxon_id": 9606,
    "score": 0.999,  # STRING API returns 0-1 scale directly
    "evidence": {
        "nscore": 0.0,
        "fscore": 0.0,
        "pscore": 0.0,
        "ascore": 0.612,
        "escore": 0.943,
        "dscore": 0.900,
        "tscore": 0.985,
    },
}

# =============================================================================
# Error Cases
# =============================================================================

STRING_INVALID_CURIE = "TP53"  # Missing STRING: prefix
STRING_INVALID_CURIE_2 = "STRING:TP53"  # Missing taxid.ENSP format
STRING_VALID_CURIE = "STRING:9606.ENSP00000269305"

# =============================================================================
# Network Image URL Fixtures
# =============================================================================

STRING_NETWORK_IMAGE_URLS = {
    "single_protein": (
        "https://string-db.org/api/highres_image/network?identifiers=TP53&species=9606&add_nodes=10"
    ),
    "multiple_proteins": (
        "https://string-db.org/api/highres_image/network"
        "?identifiers=TP53%0dMDM2%0dBRCA1&species=9606&add_nodes=10"
    ),
    "custom_flavor": (
        "https://string-db.org/api/highres_image/network"
        "?identifiers=TP53&species=9606&add_nodes=10&network_flavor=evidence"
    ),
}

# =============================================================================
# Cross-Reference Fixtures (for validation)
# =============================================================================

TP53_CROSS_REFERENCES = {
    "ensembl_gene": "ENSG00000141510",
    "uniprot": "P04637",
    "hgnc": "11998",
    "entrez": "7157",  # Not in allowed keys, stored in attributes
}
