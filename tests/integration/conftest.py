"""Shared fixtures for integration tests.

This module provides health check fixtures that skip tests when external services
are unavailable, preventing hanging tests and improving CI/CD reliability.
"""

import pytest
import httpx


@pytest.fixture(scope="function")
async def check_iuphar_available():
    """Check if IUPHAR/GtoPdb service is reachable before running tests.

    Skips tests if the service is down to prevent hanging tests.
    Uses a quick connectivity check with strict timeout.
    """
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get(
                "https://www.guidetopharmacology.org/services/ligands",
                params={"name": "test"},
            )
            # 200 (results), 204 (no results), or 404 (no results) are all acceptable
            if response.status_code in (200, 204, 404):
                return True
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"IUPHAR/GtoPdb service unavailable: {e}")
    except Exception as e:
        pytest.skip(f"IUPHAR/GtoPdb health check failed: {e}")
    return False


@pytest.fixture(scope="function")
async def check_wikipathways_available():
    """Check if WikiPathways service is reachable before running tests."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get(
                "https://webservice.wikipathways.org/listPathways",
                params={"organism": "Homo sapiens"},
            )
            if response.status_code == 200:
                return True
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"WikiPathways service unavailable: {e}")
    except Exception as e:
        pytest.skip(f"WikiPathways health check failed: {e}")
    return False


@pytest.fixture(scope="function")
async def check_string_available():
    """Check if STRING database service is reachable before running tests."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get(
                "https://string-db.org/api/json/get_string_ids",
                params={"identifiers": "TP53", "species": 9606},
            )
            if response.status_code == 200:
                return True
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"STRING database service unavailable: {e}")
    except Exception as e:
        pytest.skip(f"STRING health check failed: {e}")
    return False


@pytest.fixture(scope="function")
async def check_chembl_available():
    """Check if ChEMBL service is reachable before running tests."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get(
                "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL25.json"
            )
            if response.status_code == 200:
                return True
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"ChEMBL service unavailable: {e}")
    except Exception as e:
        pytest.skip(f"ChEMBL health check failed: {e}")
    return False


@pytest.fixture(scope="function")
async def check_ensembl_available():
    """Check if Ensembl REST API is reachable before running tests.

    Uses the dedicated /info/ping endpoint for health checks.
    Skips tests if the service is down to prevent cascading failures.
    """
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get(
                "https://rest.ensembl.org/info/ping",
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("ping") == 1:
                    return True
            pytest.skip(f"Ensembl API unhealthy: status={response.status_code}")
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"Ensembl API unavailable: {e}")
    except Exception as e:
        pytest.skip(f"Ensembl health check failed: {e}")
    return False


@pytest.fixture(scope="function")
async def check_entrez_available():
    """Check if NCBI Entrez service is reachable before running tests.

    Uses einfo as a lightweight health check endpoint.
    """
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi",
                params={"retmode": "json"},
            )
            if response.status_code == 200:
                return True
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"NCBI Entrez service unavailable: {e}")
    except Exception as e:
        pytest.skip(f"Entrez health check failed: {e}")
    return False


@pytest.fixture(scope="function")
async def check_depmap_available():
    """Check if the Sanger Cell Model Passports API is reachable before running tests.

    Skips tests if the service is down to prevent hanging tests.
    """
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
        ) as client:
            response = await client.get(
                "https://api.cellmodelpassports.sanger.ac.uk/models",
                params={"page[size]": 1},
                headers={"Accept": "application/vnd.api+json"},
                follow_redirects=True,
            )
            if response.status_code == 200:
                return True
            pytest.skip(f"Cell Model Passports API unhealthy: status={response.status_code}")
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        pytest.skip(f"Cell Model Passports service unavailable: {e}")
    except Exception as e:
        pytest.skip(f"Cell Model Passports health check failed: {e}")
    return False
