"""Contrats de données du moteur IA local et de ses appels d'outils."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIToolCall(BaseModel):
    """Appel de fonction demandé par Ollama."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=100)
    arguments: dict[str, Any] = Field(default_factory=dict)


class AIMessage(BaseModel):
    """Message transmis au modèle local."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["system", "user", "assistant", "tool"]
    content: str = Field(default="", max_length=40_000)
    tool_name: str | None = Field(default=None, max_length=100)
    tool_calls: list[AIToolCall] = Field(default_factory=list, max_length=5)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip() and not value and not value == "":
            raise ValueError("Contenu de message invalide.")
        return value


class AIToolDefinition(BaseModel):
    """Définition compatible avec l'API Ollama."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: str
    parameters: dict[str, Any]


class AIChatRequest(BaseModel):
    """Demande de génération indépendante des données métier."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    messages: list[AIMessage] = Field(min_length=1, max_length=30)
    tools: list[AIToolDefinition] = Field(default_factory=list, max_length=10)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    num_predict: int = Field(default=512, ge=1, le=4096)


class AIChatResult(BaseModel):
    """Réponse normalisée du fournisseur Ollama."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str
    content: str = Field(default="", max_length=40_000)
    tool_calls: list[AIToolCall] = Field(default_factory=list, max_length=5)
    done: bool
