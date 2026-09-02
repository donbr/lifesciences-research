"""DepMap MCP Server: genotype-selective cancer dependencies.

Exposes the genotype-contrast capability (the S′-paper gap) plus a live Sanger
Cell Model Passports search, following ADR-001 (Fuzzy-to-Fact) and ADR-004 (singleton).
"""

from lifesciences_mcp.clients.depmap import DepMapClient, MutationType
from lifesciences_mcp.models.depmap import (
    DataSource,
    DepMapModelCandidate,
    GenotypeContrast,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

from fastmcp import FastMCP

mcp = FastMCP("depmap")

# Module-level singleton client (per ADR-004)
_client: DepMapClient | None = None


def get_client() -> DepMapClient:
    """Get or create singleton DepMapClient instance."""
    global _client
    if _client is None:
        _client = DepMapClient()
    return _client


@mcp.tool()
async def search_models(
    query: str, limit: int = 10
) -> PaginationEnvelope[DepMapModelCandidate] | ErrorEnvelope:
    """Search cancer cell-line models by name (Fuzzy Phase 1, Sanger Cell Model Passports).

    Args:
        query: Cell-line name or synonym (e.g., "A549", "NCI-H1975").
        limit: Max candidates to return.

    Returns:
        PaginationEnvelope of model candidates (provenance = sanger_project_score), or ErrorEnvelope.
    """
    return await get_client().search_models(query, limit=limit)


@mcp.tool()
async def get_model(model_id: str) -> DepMapModelCandidate | ErrorEnvelope:
    """Fetch one cancer cell-line model by Sanger id (Strict, e.g. "SIDM00748")."""
    return await get_client().get_model(model_id)


@mcp.tool()
async def models_with_mutation(
    gene: str, mut_type: MutationType = "mutation", max_models: int = 500
) -> PaginationEnvelope[DepMapModelCandidate] | ErrorEnvelope:
    """Resolve the cohort of models carrying a mutation in a gene (genotype resolution).

    Uses Sanger /models/by_<mut_type>/<gene>.

    Args:
        gene: HGNC gene symbol (e.g. "RB1").
        mut_type: mutation | frameshift | snp | insertion | deletion | splice_variant.
        max_models: cap on models returned (paginates JSONAPI links.next).

    Returns:
        PaginationEnvelope of model candidates (sanger_project_score), or ErrorEnvelope.

    Warning:
        mut_type="mutation" matches ANY variant (very broad — not the paper's damaging call).
        Prefer a specific damaging type or reconcile against the mutations dataset.
    """
    return await get_client().models_with_mutation(gene, mut_type, max_models=max_models)


@mcp.tool()
def genotype_contrast(
    target_gene: str,
    genotype_gene: str,
    gene_effect_by_model: dict[str, float],
    genotype_by_model: dict[str, int],
    min_lines: int = 5,
    data_source: DataSource = "broad_24q2",
) -> GenotypeContrast:
    """Contrast a target gene's dependency between wild-type and mutant cohorts (Strict).

    The key DepMap capability the S′ synthetic-lethality work needed: does loss of
    ``genotype_gene`` make cells selectively dependent on ``target_gene``?

    Args:
        target_gene: Gene whose dependency is contrasted (e.g., "AURKB").
        genotype_gene: Tumor-suppressor genotype defining the cohorts (e.g., "RB1").
        gene_effect_by_model: {model_id: Chronos/gene-effect} for target_gene (negative = dependent).
        genotype_by_model: {model_id: 0|1|2} damaging call for genotype_gene (0=WT, 2=mutant, 1=excluded).
        min_lines: Minimum per-cohort n; below this the contrast is reported as not tested.
        data_source: Provenance label (broad_24q2 | sanger_project_score).

    Returns:
        GenotypeContrast. delta_dep < 0 => mutant-selective dependency. Cohorts smaller than
        min_lines are returned with tested=False and a note (never silently reported).

    Example:
        >>> genotype_contrast("AURKB", "RB1", gene_effect_by_model, genotype_by_model)
        # RB1-mutant-selective AURKB dependency on Broad 24Q2 (matches sprime-lung-repro).
    """
    return get_client().genotype_contrast(
        target_gene,
        genotype_gene,
        gene_effect_by_model,
        genotype_by_model,
        min_lines=min_lines,
        data_source=data_source,
    )
