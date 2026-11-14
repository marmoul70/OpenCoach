"""Contrats de données du moteur IA local et de ses appels d'outils."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    @model_validator(mode="after")
    def validate_tool_message_shape(self):
        if not self.content.strip() and not (
            self.role == "assistant" and self.tool_calls
        ):
            raise ValueError("Le contenu du message ne peut pas être vide.")
        if self.tool_name and self.role != "tool":
            raise ValueError("tool_name est réservé aux réponses d'outils.")
        if self.tool_calls and self.role != "assistant":
            raise ValueError("Seul un message assistant peut demander un outil.")
        return self


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
    tools: list[AIToolDefinition] = Field(default_factory=list, max_length=15)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    num_predict: int = Field(default=512, ge=1, le=4096)
    # Identifiant interne de corrélation ; jamais transmis à Ollama.
    trace_id: str | None = Field(default=None, max_length=64)


class AIChatResult(BaseModel):
    """Réponse normalisée du fournisseur Ollama."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str
    content: str = Field(default="", max_length=40_000)
    tool_calls: list[AIToolCall] = Field(default_factory=list, max_length=5)
    done: bool
    done_reason: str | None = Field(default=None, max_length=40)
    total_duration: int | None = Field(default=None, ge=0)
    load_duration: int | None = Field(default=None, ge=0)
    prompt_eval_count: int | None = Field(default=None, ge=0)
    prompt_eval_duration: int | None = Field(default=None, ge=0)
    eval_count: int | None = Field(default=None, ge=0)
    eval_duration: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_content_or_tool_call(self):
        if not self.content.strip() and not self.tool_calls:
            raise ValueError("La réponse IA ne contient ni texte ni appel d'outil.")
        return self
