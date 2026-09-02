"""Integration tests for the DepMap client against the live Sanger Cell Model Passports API.

These tests require network access. Run with:
    uv run pytest tests/integration/test_depmap_api.py -v -m integration

Data access: Cell Model Passports is non-commercial; third-party application use requires
prior permission from depmap@sanger.ac.uk.
"""

import pytest

from lifesciences_mcp.clients import DepMapClient
from lifesciences_mcp.models.depmap import CellModel
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

# Confirmed live on 2026-09-02. If a count drifts, the upstream release changed and the
# assertion should be re-measured rather than loosened away.
A549_CURIE = "SIDM:00903"
RB1_DELETION_COHORT = 501
CATALOGUE_SIZE = 2266


@pytest.mark.integration
@pytest.mark.depmap
class TestDepMapClientIntegration:
    """Integration tests for DepMapClient with the real Cell Model Passports API."""

    @pytest.fixture
    async def client(self, check_depmap_available):
        """Create a DepMap client. Skips if the API is unavailable."""
        client = DepMapClient()
        yield client
        await client.close()

    # --- User Story 2: resolve a model from the name a researcher types ------
    @pytest.mark.parametrize("query", ["A549", "a549", "NCI-A549", "A549/ATCC"])
    async def test_search_resolves_a549_in_any_form(self, client: DepMapClient, query: str):
        """The upstream filter is exact and case-sensitive; the local index must not be."""
        result = await client.search_models(query)
        assert isinstance(result, PaginationEnvelope), f"{query!r} errored"
        assert result.items, f"{query!r} resolved to nothing"
        assert result.items[0].id == A549_CURIE

    async def test_mixed_case_name_resolves_both_ways(self, client: DepMapClient):
        """HeLa is stored in mixed case, so neither raw nor upper-cased matching works upstream."""
        as_stored = await client.search_models("HeLa")
        lowered = await client.search_models("hela")
        assert as_stored.items and lowered.items
        assert as_stored.items[0].id == lowered.items[0].id

    async def test_no_match_returns_an_empty_envelope(self, client: DepMapClient):
        result = await client.search_models("zzzznotacellline")
        assert isinstance(result, PaginationEnvelope)
        assert result.items == []

    async def test_slim_search_is_three_keys(self, client: DepMapClient):
        result = await client.search_models("A549", slim=True)
        assert set(result.items[0]) == {"id", "name", "data_source"}

    async def test_alias_index_covers_the_catalogue(self, client: DepMapClient):
        """One request must cover every model; a truncated index silently loses cell lines."""
        index = await client._get_alias_index()
        assert len({model.id for _, model in index}) == pytest.approx(CATALOGUE_SIZE, abs=50)

    # --- User Story 2: strict lookup ----------------------------------------
    async def test_get_model_by_curie(self, client: DepMapClient):
        result = await client.get_model(A549_CURIE)
        assert isinstance(result, CellModel)
        assert result.id == A549_CURIE
        assert "A549" in result.aliases

    async def test_get_model_rejects_free_text(self, client: DepMapClient):
        result = await client.get_model("A549")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "UNRESOLVED_ENTITY"

    async def test_get_model_unknown_curie_is_not_found(self, client: DepMapClient):
        result = await client.get_model("SIDM:99999")
        assert isinstance(result, ErrorEnvelope)
        assert result.error.code.value == "ENTITY_NOT_FOUND"

    async def test_resolve_by_external_identifier(self, client: DepMapClient):
        """CCLE_ID and cosmic_id are the confirmed sources; model_name is not one."""
        by_ccle = await client.resolve_model("CCLE_ID", "A549_LUNG")
        assert isinstance(by_ccle, CellModel)
        assert by_ccle.id == A549_CURIE

    async def test_model_name_is_not_a_valid_source(self, client: DepMapClient):
        result = await client.resolve_model("model_name", "A549")
        assert isinstance(result, ErrorEnvelope)
        assert "search_models" in result.error.recovery_hint

    # --- User Story 3: genotype cohorts -------------------------------------
    async def test_deletion_cohort_is_a_usable_size(self, client: DepMapClient):
        result = await client.models_with_mutation("RB1", "deletion", page_size=10)
        assert isinstance(result, PaginationEnvelope)
        assert result.pagination.total_count == pytest.approx(RB1_DELETION_COHORT, rel=0.15)
        assert result.pagination.page_size == 10

    async def test_default_mutation_class_is_far_too_broad(self, client: DepMapClient):
        """Documents why mutation_type has no default: it would take almost the catalogue."""
        broad = await client.models_with_mutation("RB1", "mutation", page_size=1)
        damaging = await client.models_with_mutation("RB1", "deletion", page_size=1)
        assert broad.pagination.total_count > 0.9 * CATALOGUE_SIZE
        assert damaging.pagination.total_count < 0.5 * broad.pagination.total_count

    async def test_unaccepted_mutation_type_is_rejected(self, client: DepMapClient):
        result = await client.models_with_mutation("RB1", "nonsense")  # type: ignore[arg-type]
        assert isinstance(result, ErrorEnvelope)
        assert "deletion" in result.error.recovery_hint

    async def test_cohort_pagination_reaches_a_second_page(self, client: DepMapClient):
        """A 501-model cohort must not be silently truncated at one page."""
        first = await client.models_with_mutation("RB1", "deletion", page_size=10)
        assert first.pagination.cursor, "no cursor on a cohort larger than one page"
        second = await client.models_with_mutation(
            "RB1", "deletion", cursor=first.pagination.cursor, page_size=10
        )
        assert isinstance(second, PaginationEnvelope)
        assert second.items
        assert {m.id for m in second.items} != {m.id for m in first.items}

    async def test_alias_resolution_rate_meets_the_success_criterion(self, client: DepMapClient):
        """SC-002: at least 95% of real aliases resolve in any capitalisation.

        Sampled from the live index rather than a hand-picked list, so the figure the spec
        claims is measured rather than asserted. Matching runs against the cached index, so
        this costs one request regardless of sample size.
        """
        index = await client._get_alias_index()
        by_id = {}
        for _, model in index:
            by_id.setdefault(model.id, model)
        sample = [m for m in list(by_id.values())[::37] if m.aliases][:60]
        assert len(sample) >= 30, "sample too small to substantiate the criterion"

        attempts = 0
        resolved = 0
        for model in sample:
            alias = model.aliases[0]
            for variant in (alias, alias.lower(), alias.upper(), alias.replace("-", "")):
                attempts += 1
                result = await client.search_models(variant)
                if isinstance(result, PaginationEnvelope) and any(
                    item.id == model.id for item in result.items
                ):
                    resolved += 1

        rate = resolved / attempts
        assert rate >= 0.95, (
            f"only {rate:.1%} of {attempts} alias variants resolved, below the 95% in SC-002"
        )

    # --- Fuzzy-to-Fact end to end -------------------------------------------
    async def test_fuzzy_to_fact_workflow(self, client: DepMapClient):
        search = await client.search_models("a549")
        assert isinstance(search, PaginationEnvelope) and search.items
        model = await client.get_model(search.items[0].id)
        assert isinstance(model, CellModel)
        assert model.id == search.items[0].id
