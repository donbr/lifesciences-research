"""DepMap MCP Server: genotype-selective cancer dependencies.

Exposes the genotype-contrast capability plus Sanger Cell Model Passports model and
genotype resolution, following ADR-001 (Fuzzy-to-Fact) and ADR-004 (module-level singleton,
no shutdown hooks).

The analysis pipeline this capability came from stays file-based and must gain no dependency
on this server: byte-reproducibility there depends on pinned release files, not live calls.
This server is for interactive research.

Usage:
    uv run fastmcp run src/lifesciences_mcp/servers/depmap.py
"""

from typing import Any

from fastmcp import FastMCP

from lifesciences_mcp.clients.depmap import ACCESS_TERMS, DepMapClient
from lifesciences_mcp.models.depmap import (
    CellModel,
    DataSource,
    DependencyRecord,
    GenotypeContrast,
    MutationType,
)
from lifesciences_mcp.models.envelopes import ErrorEnvelope, PaginationEnvelope

mcp = FastMCP("depmap")

# Module-level singleton client (per ADR-004)
_client: DepMapClient | None = None


def get_client() -> DepMapClient:
    """Get or create singleton DepMapClient instance."""
    global _client
    if _client is None:
        _client = DepMapClient()
    return _client


@mcp.tool
async def search_models(
    query: str, slim: bool = False, page_size: int = 50
) -> PaginationEnvelope[Any] | ErrorEnvelope:
    """Search cancer cell-line models by name (Fuzzy Phase 1, Sanger Cell Model Passports).

    Matching ignores capitalisation and punctuation, so "a549", "A549", "MCF-7" and "hela"
    all resolve. A query that matches nothing returns an empty result set, not an error.

    Args:
        query: Cell-line name or alias, at least 2 characters.
        slim: Return only id, name and data_source (~20 tokens per candidate).
        page_size: Maximum candidates to return.

    Returns:
        PaginationEnvelope of cell models (provenance sanger_project_score), or ErrorEnvelope.

    Data access: Cell Model Passports is non-commercial; third-party application use
    requires prior permission from depmap@sanger.ac.uk.
    """
    return await get_client().search_models(query, slim=slim, page_size=page_size)


@mcp.tool
async def get_model(model_id: str) -> CellModel | ErrorEnvelope:
    """Fetch one cancer cell-line model by CURIE (Strict Phase 2).

    Args:
        model_id: Model CURIE in the format SIDM:NNNNN, e.g. "SIDM:00903". The bare upstream
            form "SIDM00903" is also accepted. Free text such as "A549" is refused with
            UNRESOLVED_ENTITY; resolve it with search_models first.

    Returns:
        CellModel with aliases and cross-references, or ErrorEnvelope.

    Data access: Cell Model Passports is non-commercial; third-party application use
    requires prior permission from depmap@sanger.ac.uk.
    """
    return await get_client().get_model(model_id)


@mcp.tool
async def models_with_mutation(
    gene: str,
    mutation_type: MutationType,
    slim: bool = False,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginationEnvelope[Any] | ErrorEnvelope:
    """Assemble the cohort of models carrying a variant class in a gene (genotype resolution).

    Args:
        gene: HGNC gene symbol, e.g. "RB1".
        mutation_type: Required. One of frameshift, snp, insertion, deletion, splice_variant,
            mutation. There is deliberately no default: "mutation" means ANY variant and
            returns 2185 of 2266 models for RB1, which would put almost the whole catalogue in
            the mutant arm and destroy any contrast built from it. Prefer a damaging class
            (deletion: 501 models for RB1; splice_variant: 60; frameshift: 27).
        slim: Return only id, name and data_source per model.
        cursor: Opaque cursor from a previous page.
        page_size: Models per page.

    Returns:
        PaginationEnvelope of cell models, or ErrorEnvelope. Follow the cursor to reach a
        cohort larger than one page.

    Data access: Cell Model Passports is non-commercial; third-party application use
    requires prior permission from depmap@sanger.ac.uk.
    """
    return await get_client().models_with_mutation(
        gene, mutation_type, slim=slim, cursor=cursor, page_size=page_size
    )


@mcp.tool
async def get_dependency(
    gene: str, model_id: str, data_source: DataSource = "broad_24q2"
) -> DependencyRecord | ErrorEnvelope:
    """Report how essential one gene is in one cell model (Strict Phase 2).

    Values come from a cached, checksum-pinned release. Gene effect is not served by any
    query API: Cell Model Passports exposes only a crispr_ko_available flag, and the
    dependency matrix is a Project Score release file. When no release is configured this
    returns UPSTREAM_ERROR naming what is missing, rather than a zero that would read as a
    measurement.

    Args:
        gene: HGNC gene symbol, e.g. "AURKB".
        model_id: Model CURIE, e.g. "SIDM:00903".
        data_source: broad_24q2 or sanger_project_score. The two are different screens and
            their values are not comparable.

    Returns:
        DependencyRecord, or ErrorEnvelope.
    """
    return await get_client().get_dependency(gene, model_id, data_source=data_source)


@mcp.tool
async def genotype_contrast_by_gene(
    target_gene: str,
    genotype_gene: str,
    mutation_type: MutationType = "deletion",
    min_lines: int = 5,
    data_source: DataSource = "broad_24q2",
) -> GenotypeContrast | ErrorEnvelope:
    """Contrast a target gene's dependency between wild-type and mutant cohorts (Strict).

    The capability this server exists for: does loss of genotype_gene make cells selectively
    dependent on target_gene?

    Read `tested` first. When it is false the cohort was below min_lines, the statistics are
    omitted by design, and `note` says why: an underpowered comparison is never reported as a
    finding. Read `data_source` next, because Broad and Sanger are different screens.

    Args:
        target_gene: Gene whose dependency is contrasted, e.g. "AURKB".
        genotype_gene: Tumour suppressor defining the cohorts, e.g. "RB1".
        mutation_type: Variant class the mutant cohort is built from. Recorded on the result.
        min_lines: Minimum models per cohort; below this the contrast is not tested.
        data_source: Provenance of the underlying matrix.

    Returns:
        GenotypeContrast where delta_dep < 0 means the mutant cohort is more dependent, or
        ErrorEnvelope when no cached release is available.
    """
    return await get_client().genotype_contrast_by_gene(
        target_gene,
        genotype_gene,
        mutation_type=mutation_type,
        min_lines=min_lines,
        data_source=data_source,
    )


__all__ = [
    "ACCESS_TERMS",
    "genotype_contrast_by_gene",
    "get_dependency",
    "get_model",
    "mcp",
    "models_with_mutation",
    "search_models",
]


if __name__ == "__main__":
    mcp.run()
