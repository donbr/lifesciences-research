"""Compound models for ChEMBL MCP Server.

This module defines:
- CompoundSearchCandidate: Lightweight search result for fuzzy discovery
- Compound: Complete compound record with cross-references

Per ADR-001 §4 (Agentic Biolink Schema) and Constitution Principle III (Schema Determinism).
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

# CURIE validation pattern for ChEMBL IDs
CHEMBL_CURIE_PATTERN = re.compile(r"^CHEMBL:[0-9]+$")


class CompoundSearchCandidate(BaseModel):
    """Lightweight compound search result for fuzzy discovery.

    Token Budget: ~20-30 tokens in slim mode, ~40-50 tokens in full mode

    Usage: Returned by search_compounds tool to enable agent triage before strict lookup.
    """

    id: str = Field(
        ...,
        description="ChEMBL CURIE in format 'CHEMBL:NNNNN' (e.g., 'CHEMBL:25', 'CHEMBL:1201583')",
    )

    name: str | None = Field(
        None,
        description="Preferred compound name (IUPAC, trade name, or ChEMBL ID if no name available)",
    )

    molecular_formula: str | None = Field(
        None,
        description="Molecular formula (e.g., 'C9H8O4' for aspirin)",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (1.0 = perfect match, decreasing linearly)",
    )

    @field_validator("id")
    @classmethod
    def validate_chembl_curie(cls, v: str) -> str:
        """Validate ChEMBL CURIE format."""
        if not CHEMBL_CURIE_PATTERN.match(v):
            raise ValueError(
                f"Invalid ChEMBL CURIE format: '{v}'. Must match 'CHEMBL:NNNNN' (e.g., 'CHEMBL:25')"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "CHEMBL:25",
                    "name": "Aspirin",
                    "molecular_formula": "C9H8O4",
                    "score": 1.0,
                }
            ]
        }
    }


class Compound(BaseModel):
    """Complete ChEMBL compound record with Agentic Biolink cross-references.

    Token Budget: ~115-300 tokens in full mode, ~20 tokens in slim mode

    Usage: Returned by get_compound and get_compounds_batch for strict factual lookups.
    """

    id: str = Field(
        ...,
        description="ChEMBL CURIE in format 'CHEMBL:NNNNN'",
    )

    name: str | None = Field(
        None,
        description="Preferred compound name (IUPAC, trade name, or synonym)",
    )

    molecular_formula: str | None = Field(
        None,
        description="Molecular formula",
    )

    molecular_weight: float | None = Field(
        None,
        description="Molecular weight in g/mol",
    )

    smiles: str | None = Field(
        None,
        description="Simplified Molecular-Input Line-Entry System (SMILES) notation",
    )

    inchi: str | None = Field(
        None,
        description="International Chemical Identifier (InChI)",
    )

    max_phase: int | None = Field(
        None,
        description="Maximum clinical phase (0-4) reached",
    )

    indications: list[str] = Field(
        default_factory=list,
        description="Approved indications (Mesh headings)",
    )

    canonical_name: str | None = Field(
        None,
        description="Canonical IUPAC name",
    )

    synonyms: list[str] = Field(
        default_factory=list,
        description="Alternative names and trade names",
    )

    cross_references: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Cross-references to other biological databases (22-key registry)",
    )

    @field_validator("id")
    @classmethod
    def validate_chembl_curie(cls, v: str) -> str:
        """Validate ChEMBL CURIE format."""
        if not CHEMBL_CURIE_PATTERN.match(v):
            raise ValueError(
                f"Invalid ChEMBL CURIE format: '{v}'. Must match 'CHEMBL:NNNNN' (e.g., 'CHEMBL:25')"
            )
        return v

    def to_slim(self) -> dict[str, Any]:
        """Return slim representation with minimal fields (~20 tokens)."""
        return {
            "id": self.id,
            "name": self.name,
            "molecular_formula": self.molecular_formula,
        }

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "CHEMBL:25",
                    "name": "Aspirin",
                    "molecular_formula": "C9H8O4",
                    "molecular_weight": 180.16,
                    "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                    "inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
                    "canonical_name": "2-acetoxybenzoic acid",
                    "max_phase": 4,
                    "indications": ["Pain", "Fever", "Inflammation"],
                    "synonyms": ["Acetylsalicylic acid", "ASA", "Ecotrin"],
                    "cross_references": {
                        "uniprot": ["UniProtKB:P23219"],
                        "pdb": ["1PTY"],
                        "pubchem_compound": ["2244"],
                        "drugbank": ["DB:00945"],
                    },
                }
            ]
        }
    }
