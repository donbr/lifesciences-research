"""Unit tests for ClinicalTrials.gov client.

Run with: pytest tests/unit/test_clinicaltrials_client.py -v
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from lifesciences_mcp.clients import ClinicalTrialsClient
from lifesciences_mcp.models import PaginationEnvelope


class TestClinicalTrialsClient:
    """Unit tests for ClinicalTrialsClient."""

    @pytest.fixture
    async def client(self):
        """Create a ClinicalTrials client."""
        client = ClinicalTrialsClient()
        yield client
        await client.close()

    async def test_client_initialization(self, client: ClinicalTrialsClient):
        """Test client initializes with correct base URL."""
        assert client.base_url == "https://clinicaltrials.gov/api/v2"

    async def test_search_trials_basic(self, client: ClinicalTrialsClient):
        """Test search_trials method exists and has correct signature."""
        # Test that method exists and is callable
        assert callable(client.search_trials)
        # Full integration test in test_clinicaltrials_api.py

    async def test_get_trial_basic(self, client: ClinicalTrialsClient):
        """Test get_trial method exists and has correct signature."""
        # Test that method exists and is callable
        assert callable(client.get_trial)
        # Full integration test in test_clinicaltrials_api.py


class TestSearchTrialsParameterBuilding:
    """Unit tests for search_trials parameter building logic.

    These tests verify that filter parameters are built correctly per research.md
    without making actual HTTP requests (mocked).
    """

    @pytest.fixture
    async def client(self):
        """Create a ClinicalTrials client."""
        client = ClinicalTrialsClient()
        yield client
        await client.close()

    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {
            "studies": [],
            "nextPageToken": None,
            "totalCount": 0,
        }
        return response

    async def test_status_parameter_uses_filter_overallStatus(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that status parameter uses filter.overallStatus (not query.overallStatus).

        Per research.md line 1016: params["filter.overallStatus"] = status.upper().replace(" ", "_")
        """
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            result = await client.search_trials(query="cancer", status="RECRUITING")

            # Verify the request was made
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args.kwargs

            # Verify params contains filter.overallStatus
            assert "params" in call_kwargs
            params = call_kwargs["params"]
            assert "filter.overallStatus" in params
            assert params["filter.overallStatus"] == "RECRUITING"

            # Verify it does NOT use query.overallStatus (the bug we fixed)
            assert "query.overallStatus" not in params

            # Verify result is PaginationEnvelope
            assert isinstance(result, PaginationEnvelope)

    async def test_status_parameter_uppercase_conversion(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that status parameter converts to uppercase with underscores.

        Per research.md: status.upper().replace(" ", "_")
        """
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            # Test lowercase with spaces
            await client.search_trials(query="cancer", status="not yet recruiting")

            params = mock_request.call_args.kwargs["params"]
            assert params["filter.overallStatus"] == "NOT_YET_RECRUITING"

    async def test_phase_parameter_uses_filter_advanced_essie_syntax(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that phase parameter uses filter.advanced with Essie syntax.

        Per research.md line 1018: params["filter.advanced"] = f"AREA[Phase]{phase}"
        """
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            result = await client.search_trials(query="cancer", phase="PHASE3")

            params = mock_request.call_args.kwargs["params"]
            assert "filter.advanced" in params
            assert params["filter.advanced"] == "AREA[Phase]PHASE3"

            # Verify it does NOT use query.phase (the bug we fixed)
            assert "query.phase" not in params

            assert isinstance(result, PaginationEnvelope)

    async def test_condition_parameter_uses_query_cond(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that condition parameter uses query.cond (correct per research.md)."""
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            await client.search_trials(query="cancer", condition="diabetes")

            params = mock_request.call_args.kwargs["params"]
            assert "query.cond" in params
            assert params["query.cond"] == "diabetes"

    async def test_intervention_parameter_uses_query_intr(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that intervention parameter uses query.intr (correct per research.md)."""
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            await client.search_trials(query="cancer", intervention="bevacizumab")

            params = mock_request.call_args.kwargs["params"]
            assert "query.intr" in params
            assert params["query.intr"] == "bevacizumab"

    async def test_location_parameter_uses_query_locn(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that location parameter uses query.locn (correct per research.md)."""
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            await client.search_trials(query="cancer", location="Boston")

            params = mock_request.call_args.kwargs["params"]
            assert "query.locn" in params
            assert params["query.locn"] == "Boston"

    async def test_multi_filter_parameter_combination(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that multiple filter parameters can be combined correctly.

        This tests the actual use case from AGE-132: multi-filter search.
        """
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            await client.search_trials(
                query="diabetes",
                condition="Type 2 Diabetes",
                phase="PHASE3",
                status="COMPLETED",
                intervention="insulin",
                location="Massachusetts",
                page_size=10,
            )

            params = mock_request.call_args.kwargs["params"]

            # Verify all parameters use correct names
            assert params["query.term"] == "diabetes"
            assert params["query.cond"] == "Type 2 Diabetes"
            assert params["filter.advanced"] == "AREA[Phase]PHASE3"
            assert params["filter.overallStatus"] == "COMPLETED"
            assert params["query.intr"] == "insulin"
            assert params["query.locn"] == "Massachusetts"
            assert params["pageSize"] == 10

            # Verify no wrong parameter names
            assert "query.overallStatus" not in params
            assert "query.phase" not in params

    async def test_base_parameters_always_included(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that base parameters are always included in requests."""
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            await client.search_trials(query="cancer")

            params = mock_request.call_args.kwargs["params"]

            # Base parameters should always be present
            assert params["query.term"] == "cancer"
            assert params["pageSize"] == 50  # default
            assert params["countTotal"] == "true"
            assert params["format"] == "json"

    async def test_slim_mode_field_selection(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that slim mode uses minimal field selection."""
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            # Test slim mode
            await client.search_trials(query="cancer", slim=True)
            params_slim = mock_request.call_args.kwargs["params"]

            # Slim mode should request fewer fields
            assert "fields" in params_slim
            assert "BriefTitle" in params_slim["fields"]
            assert "BriefSummary" in params_slim["fields"]

        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            # Test default mode
            await client.search_trials(query="cancer", slim=False)
            params_default = mock_request.call_args.kwargs["params"]

            # Default mode should request more fields
            assert "fields" in params_default
            assert "OfficialTitle" in params_default["fields"]

    async def test_pagination_cursor_parameter(
        self, client: ClinicalTrialsClient, mock_response
    ):
        """Test that pagination cursor is passed correctly."""
        with patch.object(
            client, "_rate_limited_request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            cursor = "eyJraW5kIjoiZXNjb3JlIiwic29ydF9pZCI6WzAuMzQxNTUxLCIwNDEyMzQ1NiJdfQ=="
            await client.search_trials(query="cancer", cursor=cursor)

            params = mock_request.call_args.kwargs["params"]
            assert "pageToken" in params
            assert params["pageToken"] == cursor
