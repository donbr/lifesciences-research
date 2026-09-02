"""Unit tests for DepMapClient behaviour: resolution, envelopes, pacing (no network).

The contrast maths lives in test_depmap_client.py. This file covers everything around it:
the Fuzzy-to-Fact boundary, envelope conformance, cohort validation, request pacing and
error attribution. Upstream responses are stubbed, so nothing here touches the network.
"""

import asyncio

import pytest

from lifesciences_mcp.clients.depmap import (
    MUTATION_TYPES,
    DepMapClient,
    compute_genotype_contrast,
    normalize_alias,
)
from lifesciences_mcp.models.depmap import CellModel
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

pytestmark = [pytest.mark.unit, pytest.mark.depmap]


# --- stub catalogue, shaped like the real JSON:API payload --------------------
CATALOGUE = {
    "data": [
        {
            "id": "SIDM00903",
            "attributes": {
                "names": ["A549", "NCI-A549", "A549/ATCC"],
                "model_type": "Cell Line",
                "ccle_id": "A549_LUNG",
                "cosmic_id": 905949,
                "mutations_available": True,
                "cnv_available": True,
                "crispr_ko_available": False,
            },
        },
        {
            "id": "SIDM00001",
            "attributes": {"names": ["HeLa", "Hela"], "model_type": "Cell Line"},
        },
        {
            "id": "SIDM00002",
            "attributes": {"names": ["MCF-7"], "model_type": "Cell Line"},
        },
    ],
    "meta": {"count": 3},
}


def _client_with(payloads):
    """A client whose HTTP layer returns queued payloads instead of making requests."""
    client = DepMapClient()
    calls = []

    async def fake_get_json(path, params=None):
        calls.append((path, params))
        result = payloads(path, params) if callable(payloads) else payloads
        if isinstance(result, Exception):
            raise result
        return result

    client._get_json = fake_get_json  # type: ignore[method-assign]
    client.calls = calls  # type: ignore[attr-defined]
    return client


class TestAliasNormalisation:
    """FR-006. The upstream filter is exact and case-sensitive, so this must not be."""

    @pytest.mark.parametrize(
        ("a", "b"),
        [
            ("A549", "a549"),
            ("MCF-7", "MCF7"),
            ("HeLa", "hela"),
            ("NCI-H1975", "nci h1975"),
        ],
    )
    def test_equivalent_names_share_a_key(self, a, b):
        assert normalize_alias(a) == normalize_alias(b)

    def test_distinct_names_do_not_collide(self):
        assert normalize_alias("A549") != normalize_alias("A5490")


class TestSearchModels:
    async def test_resolves_regardless_of_case_or_punctuation(self):
        for query in ("a549", "A549", "A549/ATCC", "hela", "HeLa", "MCF7", "MCF-7"):
            client = _client_with(CATALOGUE)
            result = await client.search_models(query)
            assert isinstance(result, PaginationEnvelope), query
            assert result.items, f"{query!r} resolved to nothing"

    async def test_resolves_to_the_expected_curie(self):
        client = _client_with(CATALOGUE)
        result = await client.search_models("a549")
        assert result.items[0].id == "SIDM:00903"

    async def test_no_match_is_an_empty_envelope_not_an_error(self):
        """FR-007. A negative answer must be distinguishable from a failure."""
        client = _client_with(CATALOGUE)
        result = await client.search_models("zzzznotacellline")
        assert isinstance(result, PaginationEnvelope)
        assert result.items == []
        assert result.pagination.total_count == 0

    async def test_slim_payload_is_three_keys(self):
        """FR-012, Constitution Principle IV."""
        client = _client_with(CATALOGUE)
        result = await client.search_models("a549", slim=True)
        assert result.items[0] == {
            "id": "SIDM:00903",
            "name": "A549",
            "data_source": "sanger_project_score",
        }

    async def test_default_page_size_is_fifty(self):
        client = _client_with(CATALOGUE)
        result = await client.search_models("a549")
        assert result.pagination.page_size == 50

    async def test_index_is_built_once_and_reused(self):
        client = _client_with(CATALOGUE)
        await client.search_models("a549")
        await client.search_models("hela")
        assert len(client.calls) == 1, "the alias index must be cached, not refetched"

    async def test_short_query_rejected(self):
        client = _client_with(CATALOGUE)
        result = await client.search_models("a")
        assert isinstance(result, ErrorEnvelope)

    async def test_cross_references_populated_and_absent_keys_omitted(self):
        """FR-013."""
        client = _client_with(CATALOGUE)
        a549 = (await client.search_models("a549")).items[0]
        assert a549.model_dump()["cross_references"] == {
            "ccle": "A549_LUNG",
            "cosmic": "905949",
        }
        hela = (await client.search_models("hela")).items[0]
        assert "cross_references" not in hela.model_dump()


class TestStrictLookup:
    """FR-008. Free text must be refused before any request is made."""

    def test_validate_and_normalize_id(self):
        assert DepMapClient.validate_id("SIDM:00903")
        assert not DepMapClient.validate_id("SIDM00903")
        assert not DepMapClient.validate_id("A549")
        assert DepMapClient.normalize_id("SIDM00903") == "SIDM:00903"
        assert DepMapClient.normalize_id("SIDM:00903") == "SIDM:00903"
        assert DepMapClient.normalize_id("A549") is None

    async def test_free_text_is_unresolved_and_makes_no_request(self):
        client = _client_with(CATALOGUE)
        result = await client.get_model("A549")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
        assert "search_models" in result.error.recovery_hint
        assert client.calls == [], "a request was made for an unresolved name"

    async def test_valid_curie_returns_the_model(self):
        client = _client_with({"data": CATALOGUE["data"][0]})
        result = await client.get_model("SIDM:00903")
        assert isinstance(result, CellModel)
        assert result.id == "SIDM:00903"
        assert result.name == "A549"

    async def test_bare_upstream_form_is_accepted(self):
        client = _client_with({"data": CATALOGUE["data"][0]})
        result = await client.get_model("SIDM00903")
        assert isinstance(result, CellModel)


class TestGenotypeCohort:
    """FR-009, FR-010."""

    async def test_unaccepted_mutation_type_is_rejected_before_any_request(self):
        client = _client_with(CATALOGUE)
        result = await client.models_with_mutation("RB1", "nonsense")  # type: ignore[arg-type]
        assert isinstance(result, ErrorEnvelope)
        assert client.calls == []
        for accepted in MUTATION_TYPES:
            assert accepted in result.error.recovery_hint

    async def test_page_size_is_the_requested_size_not_the_item_count(self):
        client = _client_with({"data": CATALOGUE["data"][:2], "meta": {"count": 501}, "links": {}})
        result = await client.models_with_mutation("RB1", "deletion", page_size=50)
        assert result.pagination.page_size == 50
        assert len(result.items) == 2
        assert result.pagination.total_count == 501

    async def test_next_link_becomes_a_cursor(self):
        body = {
            "data": CATALOGUE["data"][:1],
            "meta": {"count": 501},
            "links": {
                "next": "https://api.cellmodelpassports.sanger.ac.uk"
                "/models/by_deletion/RB1?page%5Bnumber%5D=2"
            },
        }
        client = _client_with(body)
        result = await client.models_with_mutation("RB1", "deletion")
        assert result.pagination.cursor is not None
        assert result.pagination.cursor.startswith("/models/by_deletion/RB1")

    async def test_absent_next_link_ends_pagination(self):
        client = _client_with({"data": [], "meta": {"count": 0}, "links": {}})
        result = await client.models_with_mutation("RB1", "deletion")
        assert result.pagination.cursor is None

    async def test_cursor_is_followed_verbatim(self):
        client = _client_with({"data": [], "meta": {"count": 0}})
        await client.models_with_mutation("RB1", "deletion", cursor="/models/by_deletion/RB1?p=2")
        assert client.calls[0][0] == "/models/by_deletion/RB1?p=2"


class TestErrorAttribution:
    """FR-014. Failures must name this data source, not another API."""

    def test_upstream_error_names_cell_model_passports(self):
        env = DepMapClient._upstream_error(503, "RB1")
        assert "Cell Model Passports" in env.error.message
        assert "HGNC" not in env.error.message
        assert "HGNC" not in env.error.recovery_hint

    def test_429_maps_to_rate_limited(self):
        env = DepMapClient._upstream_error(429, "RB1")
        assert env.error.code.value == "RATE_LIMITED"


class TestRateLimiting:
    """FR-015. Constitution Required Patterns: client-side rate limiting."""

    async def test_consecutive_requests_are_spaced(self, monkeypatch):
        client = DepMapClient()
        slept: list[float] = []

        class FakeResponse:
            status_code = 200

        class FakeHttp:
            async def get(self, *args, **kwargs):
                return FakeResponse()

        async def fake_sleep(seconds):
            slept.append(seconds)

        monkeypatch.setattr(client, "_get_client", lambda: _coro(FakeHttp()))
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        await client._rate_limited_get("/models", None)
        await client._rate_limited_get("/models", None)

        assert slept, "the second request was not paced"
        assert 0 < slept[0] <= client._MIN_INTERVAL

    async def test_429_backs_off_before_retrying(self, monkeypatch):
        client = DepMapClient()
        slept: list[float] = []
        attempts = {"n": 0}

        class Throttled:
            status_code = 429

        class FakeHttp:
            async def get(self, *args, **kwargs):
                attempts["n"] += 1
                return Throttled()

        async def fake_sleep(seconds):
            slept.append(seconds)

        monkeypatch.setattr(client, "_get_client", lambda: _coro(FakeHttp()))
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        response = await client._rate_limited_get("/models", None)
        assert response.status_code == 429
        assert attempts["n"] == client._MAX_RETRIES, "it did not retry"
        assert slept, "it retried without backing off"


def _coro(value):
    """Wrap a value in an awaitable, for stubbing an async factory."""

    async def _inner():
        return value

    return _inner()


class TestContrastTie:
    """FR-004. An exact tie is neither cohort's result."""

    def test_zero_delta_is_direction_none(self):
        effects = {f"MUT{i}": -0.5 for i in range(6)}
        effects.update({f"WT{i}": -0.5 for i in range(6)})
        genotypes = {f"MUT{i}": 2 for i in range(6)}
        genotypes.update({f"WT{i}": 0 for i in range(6)})

        result = compute_genotype_contrast("AURKB", "RB1", effects, genotypes, min_lines=5)
        assert result.delta_dep == 0.0
        assert result.direction == "none"
        assert result.tested is True

    def test_mutation_type_is_recorded_on_the_result(self):
        """FR-005, FR-009."""
        effects = {f"MUT{i}": -1.0 for i in range(6)}
        effects.update({f"WT{i}": 0.0 for i in range(6)})
        genotypes = {f"MUT{i}": 2 for i in range(6)}
        genotypes.update({f"WT{i}": 0 for i in range(6)})

        result = compute_genotype_contrast(
            "AURKB", "RB1", effects, genotypes, mutation_type="deletion"
        )
        assert result.mutation_type == "deletion"

    def test_all_missing_cohort_reports_zero_and_is_untested(self):
        """FR-002, FR-003."""
        effects = {f"MUT{i}": float("nan") for i in range(6)}
        effects.update({f"WT{i}": -0.5 for i in range(6)})
        genotypes = {f"MUT{i}": 2 for i in range(6)}
        genotypes.update({f"WT{i}": 0 for i in range(6)})

        result = compute_genotype_contrast("AURKB", "RB1", effects, genotypes, min_lines=5)
        assert result.n_mut == 0
        assert result.tested is False
        assert "mean_dep_mut" not in result.model_dump()


class TestNoDependencyWithoutARelease:
    """FR-005. A missing release must be an error, never a fabricated zero."""

    async def test_contrast_without_vectors_is_an_error(self):
        client = DepMapClient()
        result = await client.genotype_contrast_by_gene("AURKB", "RB1")
        assert isinstance(result, ErrorEnvelope)
        assert "release" in result.error.recovery_hint.lower()

    async def test_dependency_without_a_value_is_an_error(self):
        client = DepMapClient()
        result = await client.get_dependency("AURKB", "SIDM:00903")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UPSTREAM_ERROR"

    async def test_dependency_rejects_free_text_model(self):
        client = DepMapClient()
        result = await client.get_dependency("AURKB", "A549")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"
