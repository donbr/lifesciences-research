from unittest.mock import MagicMock, patch

import pytest

from lifesciences_mcp.clients.chembl import ChEMBLClient
from lifesciences_mcp.clients.hgnc import HGNCClient
from lifesciences_mcp.clients.uniprot import UniProtClient


@pytest.mark.asyncio
async def test_hgnc_grounding():
    """Test that HGNC client extracts aliases/previous symbols as synonyms."""
    client = HGNCClient()

    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": {
            "numFound": 1,
            "docs": [
                {
                    "hgnc_id": "HGNC:11998",
                    "symbol": "TP53",
                    "name": "tumor protein p53",
                    "alias_symbol": ["p53", "BCC7", "LFS1", "TRP53"],
                    "prev_symbol": ["P53"],
                }
            ],
        }
    }

    with patch.object(client, "_rate_limited_get", return_value=mock_response):
        envelope = await client.search_genes("TP53")
        assert len(envelope.items) == 1
        candidate = envelope.items[0]

        assert candidate.symbol == "TP53"
        # Check synonyms contain aliases and prev symbols
        assert "p53" in candidate.synonyms
        assert "BCC7" in candidate.synonyms
        assert "P53" in candidate.synonyms
        assert len(candidate.synonyms) >= 5


@pytest.mark.asyncio
async def test_chembl_grounding():
    """Test that ChEMBL client extracts molecule_synonyms."""
    # Mock requests directly since ChEMBLClient uses run_in_executor with updated underlying logic
    # But since we patched the 'search_compounds' method logic in python source, we can test it
    # if we mock the underlying SDK call or if we assume the structure.
    # Actually, ChEMBLClient wraps the chembl_webresource_client in a thread.
    # We should mock `client.search_compounds` logic or inspecting the `_search_compounds_sync`?
    # No, the best way for unit test without touching SDK is to mock the SDK client in ChEMBLClient.

    client = ChEMBLClient()

    # Result data
    mock_result = {
        "molecule_chembl_id": "CHEMBL25",
        "pref_name": "ASPIRIN",
        "molecule_properties": {"full_molformula": "C9H8O4"},
        "molecule_synonyms": [
            {"molecule_synonym": "ASA"},
            {"molecule_synonym": "Acetylsalicylic acid"},
            "2-(Acetyloxy)benzoic acid",  # Mixed types
        ],
    }

    # Mock _sdk_call_with_backoff to return the result directly
    # This bypasses the thread pool and SDK complexity
    with patch.object(client, "_sdk_call_with_backoff", return_value=[mock_result]):
        envelope = await client.search_compounds("Aspirin")
        assert len(envelope.items) == 1
        candidate = envelope.items[0]

        assert candidate.name == "ASPIRIN"
        assert "ASA" in candidate.synonyms
        assert "Acetylsalicylic acid" in candidate.synonyms
        assert "2-(Acetyloxy)benzoic acid" in candidate.synonyms


@pytest.mark.asyncio
async def test_uniprot_grounding():
    """Test that UniProt client extracts alternative names."""
    client = UniProtClient()

    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "primaryAccession": "P04637",
                "uniProtkbId": "P53_HUMAN",
                "proteinDescription": {
                    "recommendedName": {"fullName": {"value": "Cellular tumor antigen p53"}},
                    "alternativeNames": [
                        {"fullName": {"value": "Antigen NY-CO-13"}},
                        {"shortName": [{"value": "p53"}]},
                        {"fullName": {"value": "Phosphoprotein p53"}},
                    ],
                },
                "organism": {"scientificName": "Homo sapiens"},
            }
        ]
    }

    with patch.object(client, "_rate_limited_get", return_value=mock_response):
        envelope = await client.search_proteins("P04637")
        assert len(envelope.items) == 1
        candidate = envelope.items[0]

        # id should be explicitly P04637 with prefix... wait, let's check code.
        # It adds "UniProtKB:"? code: uniprot_id = f"UniProtKB:{result['primaryAccession']}"
        assert candidate.id == "UniProtKB:P04637"

        # Check synonyms
        assert "Antigen NY-CO-13" in candidate.synonyms
        assert "p53" in candidate.synonyms
        assert "Phosphoprotein p53" in candidate.synonyms


@pytest.mark.asyncio
async def test_opentargets_grounding_placeholder():
    """Test that Open Targets client handles the lack of synonyms gracefully."""
    from lifesciences_mcp.clients.opentargets import OpenTargetsClient

    client = OpenTargetsClient()

    # Mock _rate_limited_graphql to return httpx response
    mock_http_response = MagicMock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = {
        "data": {
            "search": {
                "hits": [
                    {
                        "id": "ENSG00000141510",
                        "name": "TP53",
                        "description": "tumor protein p53",
                        "entity": "target",
                    }
                ],
                "total": 1,
            }
        }
    }

    with patch.object(client, "_rate_limited_graphql", return_value=mock_http_response):
        envelope = await client.search_targets("TP53")
        assert len(envelope.items) == 1
        candidate = envelope.items[0]

        assert candidate.id == "ENSG00000141510"
        assert candidate.approved_symbol == "TP53"
        assert candidate.approved_name == "tumor protein p53"
        assert candidate.synonyms == []  # Should be empty list, not None
