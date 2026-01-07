"""Pytest fixtures for Life Sciences MCP tests.

Provides async fixtures for testing MCP tools and clients.
"""

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import httpx
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file for integration tests
load_dotenv()

from lifesciences_mcp.clients import EntrezClient, HGNCClient, IUPHARClient
from lifesciences_mcp.models.entrez import EntrezGene, GeneSearchCandidate
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope
from lifesciences_mcp.models.gene import CrossReferences, Gene, SearchCandidate
from lifesciences_mcp.models.pharmacology import (
    Ligand,
    LigandSearchCandidate,
    Target,
    TargetSearchCandidate,
)


@pytest.fixture
def sample_gene() -> Gene:
    """Sample BRCA1 gene for testing."""
    return Gene(
        id="HGNC:1100",
        symbol="BRCA1",
        name="BRCA1 DNA repair associated",
        status="Approved",
        locus_type="gene with protein product",
        locus_group="protein-coding gene",
        location="17q21.31",
        alias_symbols=["BRCC1", "FANCS", "PNCA4", "RNF53"],
        cross_references=CrossReferences(
            ensembl_gene="ENSG00000012048",
            uniprot=["P38398"],
            entrez="672",
            omim="113705",
        ),
    )


@pytest.fixture
def sample_search_candidate() -> SearchCandidate:
    """Sample search candidate for testing."""
    return SearchCandidate(
        id="HGNC:1100",
        symbol="BRCA1",
        name="BRCA1 DNA repair associated",
        score=1.0,
    )


@pytest.fixture
def sample_pagination_envelope(
    sample_search_candidate: SearchCandidate,
) -> PaginationEnvelope[SearchCandidate]:
    """Sample pagination envelope with search candidates."""
    return PaginationEnvelope.create(
        items=[sample_search_candidate],
        total_count=1,
        page_size=50,
    )


@pytest.fixture
def sample_error_envelope() -> ErrorEnvelope:
    """Sample error envelope for testing."""
    return ErrorEnvelope.unresolved_entity("BRCA1")


@pytest.fixture
def mock_hgnc_search_response() -> dict:
    """Mock HGNC API search response."""
    return {
        "response": {
            "numFound": 2,
            "docs": [
                {
                    "hgnc_id": "1100",
                    "symbol": "BRCA1",
                    "name": "BRCA1 DNA repair associated",
                },
                {
                    "hgnc_id": "1101",
                    "symbol": "BRCA2",
                    "name": "BRCA2 DNA repair associated",
                },
            ],
        }
    }


@pytest.fixture
def mock_hgnc_fetch_response() -> dict:
    """Mock HGNC API fetch response."""
    return {
        "response": {
            "numFound": 1,
            "docs": [
                {
                    "hgnc_id": "1100",
                    "symbol": "BRCA1",
                    "name": "BRCA1 DNA repair associated",
                    "status": "Approved",
                    "locus_type": "gene with protein product",
                    "locus_group": "protein-coding gene",
                    "location": "17q21.31",
                    "alias_symbol": ["BRCC1", "FANCS"],
                    "ensembl_gene_id": "ENSG00000012048",
                    "uniprot_ids": ["P38398"],
                    "entrez_id": "672",
                    "omim_id": ["113705"],
                }
            ],
        }
    }


@pytest.fixture
async def hgnc_client() -> AsyncGenerator[HGNCClient, None]:
    """Real HGNC client for integration tests."""
    client = HGNCClient()
    yield client
    await client.close()


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Mock httpx.AsyncClient for unit tests."""
    mock = MagicMock(spec=httpx.AsyncClient)
    mock.is_closed = False
    return mock


@pytest.fixture
def mock_response_factory():
    """Factory for creating mock httpx responses."""

    def _create(
        status_code: int = 200,
        json_data: dict | None = None,
        text: str = "",
        headers: dict | None = None,
    ) -> MagicMock:
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.text = text
        response.headers = headers or {}
        response.json.return_value = json_data or {}
        return response

    return _create


# =============================================================================
# Entrez-specific fixtures
# =============================================================================


@pytest.fixture
def sample_entrez_gene_search_candidate() -> GeneSearchCandidate:
    """Sample Entrez gene search candidate for testing."""
    return GeneSearchCandidate(
        id="NCBIGene:7157",
        symbol="TP53",
        name="tumor protein p53",
        description="cellular tumor antigen p53",
        organism="Homo sapiens",
        score=1.0,
    )


@pytest.fixture
def sample_entrez_gene() -> EntrezGene:
    """Sample Entrez gene (TP53) for testing."""
    return EntrezGene(
        id="NCBIGene:7157",
        symbol="TP53",
        name="tumor protein p53",
        description="cellular tumor antigen p53; phosphoprotein p53",
        summary="This gene encodes a tumor suppressor protein",
        map_location="17p13.1",
        chromosome="17",
        aliases=["P53", "TRP53"],
        organism="Homo sapiens",
        taxon_id=9606,
    )


@pytest.fixture
async def entrez_client() -> AsyncGenerator[EntrezClient, None]:
    """Real EntrezClient for integration tests."""
    client = EntrezClient()
    yield client
    await client.close()


# =============================================================================
# IUPHAR-specific fixtures
# =============================================================================


@pytest.fixture
def sample_ligand_search_candidate() -> LigandSearchCandidate:
    """Sample ligand search candidate for testing."""
    return LigandSearchCandidate(
        id="IUPHAR:2713",
        name="ibuprofen",
        type="Synthetic organic",
        approved=True,
        score=1.0,
    )


@pytest.fixture
def sample_ligand() -> Ligand:
    """Sample ligand (ibuprofen) for testing."""
    return Ligand(
        id="IUPHAR:2713",
        ligand_id=2713,
        name="ibuprofen",
        approved_name="ibuprofen",
        type="Synthetic organic",
        approved=True,
        approval_source="FDA (1974)",
        synonyms=["Advil", "Motrin", "Nurofen"],
        cross_references=CrossReferences(
            chembl="CHEMBL521",
            drugbank="DB01050",
            pubchem_compound="3672",
        ),
    )


@pytest.fixture
def sample_target_search_candidate() -> TargetSearchCandidate:
    """Sample target search candidate for testing."""
    return TargetSearchCandidate(
        id="IUPHAR:215",
        name="D2 receptor",
        family="Dopamine receptors",
        type="GPCR",
        score=1.0,
    )


@pytest.fixture
def sample_target() -> Target:
    """Sample target (D2 receptor) for testing."""
    return Target(
        id="IUPHAR:215",
        target_id=215,
        name="D2 receptor",
        target_family="Dopamine receptors",
        family_ids=["78"],
        species="Homo sapiens",
        gene_symbol="DRD2",
        cross_references=CrossReferences(
            uniprot=["P14416"],
            ensembl_gene="ENSG00000149295",
            entrez="1813",
            hgnc="HGNC:3023",
        ),
    )


@pytest.fixture
async def iuphar_client() -> AsyncGenerator[IUPHARClient, None]:
    """Real IUPHARClient for integration tests."""
    client = IUPHARClient()
    yield client
    await client.close()
