"""Drug-related Pydantic models for DrugBank MCP Server.

Models follow the Agentic Biolink schema defined in ADR-001.
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# DrugBank CURIE pattern: DrugBank:DBXXXXX (5-digit ID)
DRUGBANK_CURIE_PATTERN = re.compile(r"^DrugBank:DB\d{5}$")


class DrugCrossReferences(BaseModel):
    """External database identifiers for drugs per ADR-001 22-key registry.

    Keys are omitted if no value exists (never null or empty string).
    DrugBank provides mappings to: chembl, uniprot, kegg, pubchem_compound,
    pubchem_substance, pdb.
    """

    # Drug identifiers
    drugbank: str | None = Field(
        default=None,
        description="DrugBank CURIE (self-reference)",
    )
    chembl: str | None = Field(
        default=None,
        description="ChEMBL compound ID (e.g., CHEMBL:25)",
    )

    # Target identifiers
    uniprot: list[str] | None = Field(
        default=None,
        description="UniProt target accessions",
    )

    # Compound identifiers
    kegg: str | None = Field(
        default=None,
        description="KEGG Drug ID",
    )
    pubchem_compound: str | None = Field(
        default=None,
        description="PubChem compound ID (CID)",
    )
    pubchem_substance: str | None = Field(
        default=None,
        description="PubChem substance ID (SID)",
    )
    pdb: list[str] | None = Field(
        default=None,
        description="PDB structure IDs",
    )

    @model_validator(mode="after")
    def omit_empty_values(self) -> "DrugCrossReferences":
        """Ensure no empty strings or empty lists are stored (omit instead)."""
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if value == "" or value == []:
                setattr(self, field_name, None)
        return self

    def model_dump(self, **kwargs) -> dict:
        """Override to exclude None values (ADR-001: omit keys with no value)."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class DrugSearchCandidate(BaseModel):
    """Lightweight drug search result for fuzzy discovery.

    Token Budget: ~20-30 tokens in slim mode, ~40-50 tokens in full mode

    Used in Phase 1 (Fuzzy) of the Fuzzy-to-Fact protocol.
    """

    id: Annotated[
        str,
        Field(
            pattern=r"^DrugBank:DB\d{5}$",
            description="DrugBank CURIE in format DrugBank:DBXXXXX",
        ),
    ]
    name: str = Field(
        description="Primary drug name (e.g., 'Aspirin', 'Metformin')",
    )
    drug_type: str | None = Field(
        default=None,
        description="Drug type classification (e.g., 'Small molecule', 'Biotech')",
    )
    categories: list[str] | None = Field(
        default=None,
        description="Therapeutic categories",
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance score (1.0 = exact match, decreasing for partial matches)",
    )

    @field_validator("id")
    @classmethod
    def validate_drugbank_curie(cls, v: str) -> str:
        """Validate DrugBank CURIE format."""
        if not DRUGBANK_CURIE_PATTERN.match(v):
            msg = f"Invalid DrugBank CURIE format: {v}"
            raise ValueError(msg)
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "DrugBank:DB00945",
                    "name": "Aspirin",
                    "drug_type": "Small molecule",
                    "categories": [
                        "Analgesics",
                        "Antipyretics",
                        "Anti-Inflammatory Agents, Non-Steroidal",
                    ],
                    "score": 1.0,
                }
            ]
        }
    }


class Drug(BaseModel):
    """Complete DrugBank drug record with Agentic Biolink cross-references.

    Token Budget: ~115-300 tokens in full mode, ~20 tokens in slim mode

    Used in Phase 2 (Fact) of the Fuzzy-to-Fact protocol.
    """

    id: Annotated[
        str,
        Field(
            pattern=r"^DrugBank:DB\d{5}$",
            description="DrugBank CURIE in format DrugBank:DBXXXXX",
        ),
    ]
    name: str = Field(
        description="Primary drug name",
    )
    drug_type: str | None = Field(
        default=None,
        description="Drug type (Small molecule, Biotech)",
    )
    categories: list[str] | None = Field(
        default=None,
        description="Therapeutic categories",
    )
    description: str | None = Field(
        default=None,
        description="Therapeutic description and background",
    )
    indication: str | None = Field(
        default=None,
        description="Approved therapeutic uses and indications",
    )
    mechanism_of_action: str | None = Field(
        default=None,
        description="How the drug works at molecular/cellular level",
    )
    pharmacodynamics: str | None = Field(
        default=None,
        description="Effects on the body",
    )
    absorption: str | None = Field(
        default=None,
        description="Absorption characteristics",
    )
    metabolism: str | None = Field(
        default=None,
        description="Metabolic pathway information",
    )
    half_life: str | None = Field(
        default=None,
        description="Elimination half-life",
    )
    cross_references: DrugCrossReferences = Field(
        default_factory=DrugCrossReferences,
        description="Cross-references to other biological databases (22-key registry)",
    )

    @field_validator("id")
    @classmethod
    def validate_drugbank_curie(cls, v: str) -> str:
        """Validate DrugBank CURIE format."""
        if not DRUGBANK_CURIE_PATTERN.match(v):
            msg = f"Invalid DrugBank CURIE format: {v}"
            raise ValueError(msg)
        return v

    def to_search_candidate(self, score: float = 1.0) -> DrugSearchCandidate:
        """Convert to DrugSearchCandidate for search results."""
        return DrugSearchCandidate(
            id=self.id,
            name=self.name,
            drug_type=self.drug_type,
            categories=self.categories,
            score=score,
        )

    def to_slim_dict(self) -> dict:
        """Return slim mode representation (~20 tokens)."""
        result = {
            "id": self.id,
            "name": self.name,
        }
        if self.drug_type:
            result["drug_type"] = self.drug_type
        if self.categories:
            result["categories"] = self.categories
        return result

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "DrugBank:DB00945",
                    "name": "Aspirin",
                    "drug_type": "Small molecule",
                    "categories": [
                        "Analgesics",
                        "Antipyretics",
                        "Anti-Inflammatory Agents, Non-Steroidal",
                    ],
                    "description": "The prototypical analgesic used in the treatment of mild to moderate pain.",
                    "indication": "For the treatment of mild to moderate pain, inflammation, and fever.",
                    "mechanism_of_action": "Irreversibly inhibits cyclooxygenase (COX) enzymes.",
                    "half_life": "15-20 minutes (aspirin); 2-3 hours (salicylate)",
                    "cross_references": {
                        "drugbank": "DrugBank:DB00945",
                        "chembl": "CHEMBL:25",
                        "uniprot": ["UniProtKB:P23219", "UniProtKB:P35354"],
                        "kegg": "D00109",
                        "pubchem_compound": "2244",
                    },
                }
            ]
        }
    }
