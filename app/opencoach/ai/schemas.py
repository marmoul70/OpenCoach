"""Contrats de données du moteur IA."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIMessage(BaseModel):
    """Message transmis au modèle local."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: str
    content: str = Field(min_length=1, max_length=20_000)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in {"system", "user", "assistant"}:
            raise ValueError("Rôle de message IA non autorisé.")
        return value


class AIChatRequest(BaseModel):
    """Demande de génération indépendante des données métier."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    messages: list[AIMessage] = Field(min_length=1, max_length=30)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    num_predict: int = Field(default=512, ge=1, le=4096)


class AIChatResult(BaseModel):
    """Réponse normalisée du fournisseur Ollama."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str
    content: str = Field(min_length=1, max_length=40_000)
    done: bool
