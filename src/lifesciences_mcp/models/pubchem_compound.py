"""Pydantic models for PubChem compound data.

This module defines data models for PubChem chemical compounds following
ADR-001 v1.2 (Agentic Biolink Schema) and Constitution Principle III.
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

# CURIE validation pattern (T018)
PUBCHEM_CURIE_PATTERN = re.compile(r"^PubChem:CID\d+$")


class PubChemSearchCandidate(BaseModel):
    """Lightweight compound search result for fuzzy discovery.

    Token Budget: ~20-30 tokens in slim mode, ~40-50 tokens in full mode

    Usage: Returned by search_compounds tool to enable agent triage
    before strict lookup with get_compound.
    """

    id: str = Field(
        ...,
        description="PubChem CURIE in format 'PubChem:CID{number}' (e.g., 'PubChem:CID2244')",
    )

    name: str | None = Field(
        None,
        description="Common compound name (Title from PubChem)",
    )

    molecular_formula: str | None = Field(
        None,
        description="Molecular formula (e.g., 'C9H8O4' for aspirin)",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (1.0 = best match, decreasing by position)",
    )

    @field_validator("id")
    @classmethod
    def validate_pubchem_curie(cls, v: str) -> str:
        """Validate PubChem CURIE format."""
        if not PUBCHEM_CURIE_PATTERN.match(v):
            msg = (
                f"Invalid PubChem CURIE format: '{v}'. "
                "Must match 'PubChem:CID{number}' (e.g., 'PubChem:CID2244')"
            )
            raise ValueError(msg)
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "PubChem:CID2244",
                    "name": "Aspirin",
                    "molecular_formula": "C9H8O4",
                    "score": 1.0,
                },
                {
                    "id": "PubChem:CID3672",
                    "name": "Ibuprofen",
                    "molecular_formula": "C13H18O2",
                    "score": 0.95,
                },
            ]
        }
    }


class PubChemCompound(BaseModel):
    """Complete PubChem compound record with Agentic Biolink cross-references.

    Token Budget:
    - Full mode: ~115-300 tokens (depends on cross-references and synonyms)
    - Slim mode: ~20 tokens (id, name, molecular_formula only)

    Usage: Returned by get_compound for strict factual lookups.
    Cross-references enable multi-hop reasoning to ChEMBL, DrugBank, etc.
    """

    id: str = Field(
        ...,
        description="PubChem CURIE in format 'PubChem:CID{number}'",
    )

    name: str | None = Field(
        None,
        description="Common compound name (Title from PubChem)",
    )

    iupac_name: str | None = Field(
        None,
        description="IUPAC systematic name",
    )

    molecular_formula: str | None = Field(
        None,
        description="Molecular formula (e.g., 'C9H8O4')",
    )

    molecular_weight: float | None = Field(
        None,
        description="Molecular weight in Daltons (g/mol)",
    )

    canonical_smiles: str | None = Field(
        None,
        description="Canonical SMILES string (unique molecular representation)",
    )

    isomeric_smiles: str | None = Field(
        None,
        description="Isomeric SMILES string (includes stereochemistry)",
    )

    inchi: str | None = Field(
        None,
        description="IUPAC International Chemical Identifier (InChI)",
    )

    inchikey: str | None = Field(
        None,
        description="Hashed InChI key (27 characters, for searching/comparison)",
    )

    synonyms: list[str] = Field(
        default_factory=list,
        description="Alternative names, trade names, and identifiers",
    )

    cross_references: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Cross-references to other databases (22-key registry)",
    )

    @field_validator("id")
    @classmethod
    def validate_pubchem_curie(cls, v: str) -> str:
        """Validate PubChem CURIE format."""
        if not PUBCHEM_CURIE_PATTERN.match(v):
            msg = (
                f"Invalid PubChem CURIE format: '{v}'. "
                "Must match 'PubChem:CID{number}' (e.g., 'PubChem:CID2244')"
            )
            raise ValueError(msg)
        return v

    def to_slim(self) -> dict[str, Any]:
        """Return slim representation with minimal fields (~20 tokens).

        Used for token budgeting in batch operations.
        """
        return {
            "id": self.id,
            "name": self.name,
            "molecular_formula": self.molecular_formula,
        }

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "PubChem:CID2244",
                    "name": "Aspirin",
                    "iupac_name": "2-acetoxybenzoic acid",
                    "molecular_formula": "C9H8O4",
                    "molecular_weight": 180.16,
                    "canonical_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
                    "isomeric_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
                    "inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
                    "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                    "synonyms": [
                        "acetylsalicylic acid",
                        "2-acetoxybenzoic acid",
                        "Ecotrin",
                        "Bayer Aspirin",
                    ],
                    "cross_references": {
                        "pubchem_compound": ["2244"],
                        "chembl": ["CHEMBL:25"],
                        "drugbank": ["DB00945"],
                    },
                }
            ]
        }
    }
