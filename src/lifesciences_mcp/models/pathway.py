"""Pathway data models for WikiPathways MCP Server.

This module defines Pydantic models for WikiPathways entities following the
Agentic Biolink schema with flattened JSON structure and omit-if-null pattern.

Models:
    - RevisionMetadata: Pathway revision and curation information
    - ComponentCounts: Counts of pathway components (genes, proteins, metabolites, interactions)
    - Pathway: Complete pathway record from strict lookup (get_pathway tool)
    - PathwaySearchCandidate: Lightweight search result for fuzzy discovery (search_pathways tool)
"""

from pydantic import BaseModel, ConfigDict, Field


class RevisionMetadata(BaseModel):
    """Pathway revision and curation information.

    Tracks pathway version, modification history, and curator information.
    """

    version: str = Field(..., description="Pathway revision number")
    last_modified: str | None = Field(None, description="Last modification date (ISO 8601)")
    curators: list[str] = Field(default_factory=list, description="List of pathway curators")


class ComponentCounts(BaseModel):
    """Counts of pathway components.

    Provides aggregate statistics for pathway composition without requiring
    full component extraction.
    """

    gene_count: int = Field(0, description="Number of gene entities")
    protein_count: int = Field(0, description="Number of protein entities")
    metabolite_count: int = Field(0, description="Number of metabolite entities")
    interaction_count: int = Field(0, description="Number of interactions")


class Pathway(BaseModel):
    """Complete pathway entity from WikiPathways following Agentic Biolink schema.

    Returned by get_pathway strict lookup tool after resolving pathway ID
    from search_pathways fuzzy search.

    Token Budget: ~300 tokens (full mode)

    Example:
        ```python
        pathway = Pathway(
            id="WP:WP534",
            title="Glycolysis and gluconeogenesis",
            organism="Homo sapiens",
            description="Glycolysis is the metabolic pathway...",
            revision=RevisionMetadata(version="141823", last_modified="2024-11-15T10:30:00Z"),
            component_counts=ComponentCounts(gene_count=47, protein_count=52),
            cross_references={"kegg_pathway": "hsa00010", "reactome": "R-HSA-70171"},
            url="https://classic.wikipathways.org/index.php/Pathway:WP534"
        )
        ```
    """

    id: str = Field(
        ...,
        description="WikiPathways CURIE (WP:WP###)",
        pattern=r"^WP:WP\d+$"
    )
    title: str = Field(..., description="Pathway name")
    organism: str = Field(
        ...,
        description="Scientific organism name (e.g., 'Homo sapiens')"
    )
    description: str = Field(..., description="Pathway description or summary")
    revision: RevisionMetadata = Field(..., description="Revision metadata")
    component_counts: ComponentCounts = Field(..., description="Component counts")
    cross_references: dict[str, str | list[str]] = Field(
        default_factory=dict,
        description="Cross-references to external databases (reactome, kegg_pathway, gene_ontology, etc.)"
    )
    url: str = Field(..., description="WikiPathways pathway URL")

    # Pydantic v2 model configuration
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "WP:WP534",
                "title": "Glycolysis and gluconeogenesis",
                "organism": "Homo sapiens",
                "description": "Glycolysis is the metabolic pathway that converts glucose into pyruvate...",
                "revision": {
                    "version": "141823",
                    "last_modified": "2024-11-15T10:30:00Z",
                    "curators": ["AlexanderPico", "MaintBot"]
                },
                "component_counts": {
                    "gene_count": 47,
                    "protein_count": 52,
                    "metabolite_count": 23,
                    "interaction_count": 89
                },
                "cross_references": {
                    "kegg_pathway": "hsa00010",
                    "reactome": "R-HSA-70171",
                    "gene_ontology": "GO:0006096"
                },
                "url": "https://classic.wikipathways.org/index.php/Pathway:WP534"
            }
        }
    )


class PathwaySearchCandidate(BaseModel):
    """Lightweight pathway search result for fuzzy discovery.

    Returned by search_pathways and get_pathways_for_gene fuzzy tools.
    Uses slim representation (~20 tokens vs ~300 tokens for full Pathway).

    Token Budget: ~20 tokens (slim mode)
    Reduction: 93% token savings vs full Pathway

    Example:
        ```python
        candidate = PathwaySearchCandidate(
            id="WP:WP534",
            title="Glycolysis and gluconeogenesis",
            organism="Homo sapiens",
            description="Glycolysis is the metabolic pathway that converts glucose C6H12O6...",
            score=0.95
        )
        ```
    """

    id: str = Field(
        ...,
        description="WikiPathways CURIE (WP:WP###)",
        pattern=r"^WP:WP\d+$"
    )
    title: str = Field(..., description="Pathway name")
    organism: str = Field(..., description="Scientific organism name")
    description: str = Field(
        ...,
        description="Brief description snippet (first 200 chars)"
    )
    score: float = Field(
        ...,
        description="Relevance score (0.0-1.0, higher is better)",
        ge=0.0,
        le=1.0
    )

    # Pydantic v2 model configuration
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "WP:WP534",
                "title": "Glycolysis and gluconeogenesis",
                "organism": "Homo sapiens",
                "description": "Glycolysis is the metabolic pathway that converts glucose C6H12O6, into pyruvate...",
                "score": 0.95
            }
        }
    )
