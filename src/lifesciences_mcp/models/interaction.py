"""Pydantic models for STRING protein-protein interactions.

This module defines models for the STRING API:
- InteractionSearchCandidate: Fuzzy search result
- Interaction: Single protein-protein interaction with evidence scores
- InteractionNetwork: Full network for a protein
- InteractionCrossReferences: Cross-database references

Status: NEW - Tier 1 implementation.
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# STRING protein ID pattern: <taxid>.ENSP<numbers>
# Example: 9606.ENSP00000269305
STRING_PROTEIN_ID_PATTERN = re.compile(r"^\d+\.ENSP\d+$")

# CURIE pattern for STRING: STRING:<taxid>.ENSP<numbers>
STRING_CURIE_PATTERN = re.compile(r"^STRING:\d+\.ENSP\d+$")


class InteractionSearchCandidate(BaseModel):
    """Search result candidate from STRING protein search.

    Returned by search_proteins fuzzy search phase.
    Contains minimal info for agent disambiguation.
    """

    id: Annotated[
        str,
        Field(
            description="STRING CURIE: STRING:<taxid>.ENSP<id>",
            examples=["STRING:9606.ENSP00000269305"],
        ),
    ]
    preferred_name: Annotated[
        str,
        Field(
            description="Gene symbol / preferred name",
            examples=["TP53", "BRCA1"],
        ),
    ]
    annotation: Annotated[
        str | None,
        Field(
            default=None,
            description="Protein annotation/description",
            examples=["Cellular tumor antigen p53"],
        ),
    ]
    taxon_id: Annotated[
        int,
        Field(
            description="NCBI Taxonomy ID",
            examples=[9606],
        ),
    ]
    score: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Relevance score (0-1)",
        ),
    ]

    @field_validator("id")
    @classmethod
    def validate_curie_format(cls, v: str) -> str:
        """Validate STRING CURIE format."""
        if not STRING_CURIE_PATTERN.match(v):
            raise ValueError(
                f"Invalid STRING CURIE format: '{v}'. "
                "Expected STRING:<taxid>.ENSP<id> (e.g., STRING:9606.ENSP00000269305)"
            )
        return v


class EvidenceScores(BaseModel):
    """Evidence channel scores for a protein-protein interaction.

    STRING provides multiple evidence types, each scored 0-1.
    Combined score uses a probabilistic framework.
    """

    nscore: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.0,
            description="Neighborhood score (gene proximity)",
        ),
    ]
    fscore: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.0,
            description="Fusion score (gene fusion events)",
        ),
    ]
    pscore: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.0,
            description="Phyletic profile score (co-occurrence)",
        ),
    ]
    ascore: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.0,
            description="Co-expression score (mRNA correlation)",
        ),
    ]
    escore: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.0,
            description="Experimental score (physical binding)",
        ),
    ]
    dscore: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.0,
            description="Database score (curated knowledge)",
        ),
    ]
    tscore: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.0,
            description="Textmining score (literature mentions)",
        ),
    ]


class Interaction(BaseModel):
    """Single protein-protein interaction from STRING.

    Represents an edge in the protein interaction network
    with confidence score and evidence breakdown.
    """

    string_id_a: Annotated[
        str,
        Field(
            description="STRING ID of protein A",
            examples=["9606.ENSP00000269305"],
        ),
    ]
    string_id_b: Annotated[
        str,
        Field(
            description="STRING ID of protein B",
            examples=["9606.ENSP00000353483"],
        ),
    ]
    preferred_name_a: Annotated[
        str,
        Field(
            description="Gene symbol of protein A",
            examples=["TP53"],
        ),
    ]
    preferred_name_b: Annotated[
        str,
        Field(
            description="Gene symbol of protein B",
            examples=["MDM2"],
        ),
    ]
    taxon_id: Annotated[
        int,
        Field(
            description="NCBI Taxonomy ID",
            examples=[9606],
        ),
    ]
    score: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Combined confidence score (0-1)",
        ),
    ]
    evidence: Annotated[
        EvidenceScores,
        Field(
            description="Breakdown of evidence channel scores",
        ),
    ]


class InteractionCrossReferences(BaseModel):
    """Cross-database references for a STRING protein.

    Per ADR-001: omit keys with no value (never null/empty).
    Only includes keys from the allowed cross-reference registry.
    """

    ensembl_gene: Annotated[
        str | None,
        Field(
            default=None,
            description="Ensembl Gene ID",
            examples=["ENSG00000141510"],
        ),
    ]
    uniprot: Annotated[
        str | None,
        Field(
            default=None,
            description="UniProt accession",
            examples=["P04637"],
        ),
    ]
    hgnc: Annotated[
        str | None,
        Field(
            default=None,
            description="HGNC ID (numeric only)",
            examples=["11998"],
        ),
    ]


class InteractionNetwork(BaseModel):
    """Full interaction network for a protein.

    Represents the node (query protein) and its edges (interactions).
    """

    id: Annotated[
        str,
        Field(
            description="STRING CURIE of query protein",
            examples=["STRING:9606.ENSP00000269305"],
        ),
    ]
    preferred_name: Annotated[
        str,
        Field(
            description="Gene symbol / preferred name",
            examples=["TP53"],
        ),
    ]
    annotation: Annotated[
        str | None,
        Field(
            default=None,
            description="Protein annotation/description",
        ),
    ]
    taxon_id: Annotated[
        int,
        Field(
            description="NCBI Taxonomy ID",
            examples=[9606],
        ),
    ]
    interaction_count: Annotated[
        int,
        Field(
            ge=0,
            description="Number of interactions returned",
        ),
    ]
    interactions: Annotated[
        list[Interaction],
        Field(
            description="List of protein-protein interactions",
        ),
    ]
    network_image_url: Annotated[
        str | None,
        Field(
            default=None,
            description="URL for network visualization image",
        ),
    ]
    cross_references: Annotated[
        InteractionCrossReferences | None,
        Field(
            default=None,
            description="Cross-database references (omit if empty)",
        ),
    ]

    @field_validator("id")
    @classmethod
    def validate_curie_format(cls, v: str) -> str:
        """Validate STRING CURIE format."""
        if not STRING_CURIE_PATTERN.match(v):
            raise ValueError(
                f"Invalid STRING CURIE format: '{v}'. Expected STRING:<taxid>.ENSP<id>"
            )
        return v
