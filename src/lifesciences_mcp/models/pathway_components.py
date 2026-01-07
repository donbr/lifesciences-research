"""Pathway component models for WikiPathways MCP Server.

This module defines Pydantic models for pathway components (genes, proteins,
metabolites, interactions) extracted from WikiPathways pathways.

Models:
    - DataNode: Pathway component entity (gene, protein, metabolite, complex)
    - Interaction: Pathway relationship entity connecting two DataNodes
    - PathwayComponents: Structured pathway composition data

Usage:
    Used by get_pathway_components tool to return structured lists of
    biological entities participating in a pathway.
"""

from pydantic import BaseModel, ConfigDict, Field


class DataNode(BaseModel):
    """Pathway component entity (gene, protein, metabolite, complex).

    Represents a biological entity participating in a pathway with
    cross-references to external databases.

    Used within PathwayComponents lists (genes, proteins, metabolites).

    Token Budget: ~50 tokens per node

    Example:
        ```python
        gene = DataNode(
            id="ncbigene:672",
            label="BRCA1",
            type="Gene",
            database="Entrez Gene",
            cross_references={
                "entrez": "672",
                "hgnc": "HGNC:1100",
                "ensembl_gene": "ENSG00000012048",
                "uniprot": "P38398"
            }
        )
        ```
    """

    id: str = Field(
        ...,
        description="Internal node identifier or external database ID"
    )
    label: str = Field(
        ...,
        description="Display name (gene symbol, protein name, metabolite name)"
    )
    type: str = Field(
        ...,
        description="Entity type: Gene, Protein, Metabolite, Complex"
    )
    database: str = Field(
        ...,
        description="Source database (e.g., 'Entrez Gene', 'UniProt', 'ChEMBL')"
    )
    cross_references: dict[str, str | list[str]] = Field(
        default_factory=dict,
        description="Cross-references to external databases (omit-if-null pattern)"
    )

    # Pydantic v2 model configuration
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ncbigene:672",
                "label": "BRCA1",
                "type": "Gene",
                "database": "Entrez Gene",
                "cross_references": {
                    "entrez": "672",
                    "hgnc": "HGNC:1100",
                    "ensembl_gene": "ENSG00000012048",
                    "uniprot": "P38398"
                }
            }
        }
    )


class Interaction(BaseModel):
    """Pathway relationship entity connecting two DataNodes.

    Represents interactions between biological entities (activation, inhibition,
    binding, conversion, catalysis).

    Used within PathwayComponents.interactions list.

    Token Budget: ~15 tokens per interaction

    Example:
        ```python
        interaction = Interaction(
            source="ncbigene:5213",
            target="chebi:17234",
            type="catalysis"
        )
        ```
    """

    source: str = Field(..., description="Source DataNode ID")
    target: str = Field(..., description="Target DataNode ID")
    type: str = Field(
        ...,
        description="Interaction type: activation, inhibition, binding, conversion, catalysis"
    )

    # Pydantic v2 model configuration
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "ncbigene:5213",
                "target": "chebi:17234",
                "type": "catalysis"
            }
        }
    )


class PathwayComponents(BaseModel):
    """Structured pathway composition data.

    Returned by get_pathway_components tool with genes, proteins, metabolites,
    and interactions extracted from WikiPathways pathway.

    Token Budget: ~500-1000 tokens (depends on pathway complexity)

    Omit Empty Lists: If pathway has no metabolites, omit `metabolites` key
    entirely per ADR-001 §4 omit-if-null pattern.

    Example:
        ```python
        components = PathwayComponents(
            genes=[DataNode(id="ncbigene:5213", label="PFKM", type="Gene", ...)],
            proteins=[DataNode(id="uniprot:P08237", label="PFKM", type="Protein", ...)],
            metabolites=[DataNode(id="chebi:17234", label="Glucose", type="Metabolite", ...)],
            interactions=[Interaction(source="ncbigene:5213", target="chebi:17234", type="catalysis")]
        )
        ```
    """

    genes: list[DataNode] = Field(
        default_factory=list,
        description="Gene entities in pathway"
    )
    proteins: list[DataNode] = Field(
        default_factory=list,
        description="Protein entities in pathway"
    )
    metabolites: list[DataNode] = Field(
        default_factory=list,
        description="Metabolite entities in pathway"
    )
    interactions: list[Interaction] = Field(
        default_factory=list,
        description="Interactions between components"
    )

    # Pydantic v2 model configuration
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "genes": [
                    {
                        "id": "ncbigene:5213",
                        "label": "PFKM",
                        "type": "Gene",
                        "database": "Entrez Gene",
                        "cross_references": {"entrez": "5213", "hgnc": "HGNC:8877"}
                    }
                ],
                "proteins": [
                    {
                        "id": "uniprot:P08237",
                        "label": "PFKM",
                        "type": "Protein",
                        "database": "UniProt",
                        "cross_references": {"uniprot": "P08237", "hgnc": "HGNC:8877"}
                    }
                ],
                "metabolites": [
                    {
                        "id": "chebi:17234",
                        "label": "Glucose",
                        "type": "Metabolite",
                        "database": "ChEBI",
                        "cross_references": {"pubchem_compound": "5793"}
                    }
                ],
                "interactions": [
                    {
                        "source": "ncbigene:5213",
                        "target": "chebi:17234",
                        "type": "catalysis"
                    }
                ]
            }
        }
    )
