"""Contrats de données du moteur IA local et de ses appels d'outils."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from opencoach.ai.data_proposals import AIDataProposalResponse


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


class AICoachPreferencesPayload(BaseModel):
    """Préférences de style du coach ; les règles de sécurité restent fixes."""

    model_config = ConfigDict(extra="forbid")

    personality: Literal["balanced", "demanding", "severe", "motivating", "benevolent"] = "balanced"
    firmness: int = Field(default=3, ge=1, le=5)
    motivation: int = Field(default=3, ge=1, le=5)
    response_style: Literal["concise", "detailed", "analytical"] = "concise"
    custom_prompt: str = Field(default="", max_length=6000)


class AICoachPreferencesResponse(AICoachPreferencesPayload):
    """Préférences effectivement enregistrées pour l'utilisateur."""

    pass



class AIStatusResponse(BaseModel):
    """État de configuration non sensible du moteur IA."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    provider: str
    model: str
    provider_check: str


class AIConversationMessage(BaseModel):
    """Message d'historique client, limité aux rôles conversationnels."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Le contenu d'un message ne peut pas être vide.")
        return normalized


class AIQuestionRequest(BaseModel):
    """Question et historique borné ; aucun rôle système n'est accepté."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question: str = Field(min_length=1, max_length=4_000)
    history: list[AIConversationMessage] = Field(default_factory=list, max_length=8)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("La question ne peut pas être vide.")
        return normalized

    @model_validator(mode="after")
    def validate_history_size(self):
        total_chars = sum(len(message.content) for message in self.history)
        if total_chars > 12_000:
            raise ValueError("L'historique dépasse la taille autorisée.")
        return self


class AIRaceOptionResponse(BaseModel):
    """Course du calendrier proposée pour une sélection explicite."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    race_id: UUID
    date: str
    name: str
    location: str | None = None
    race_type: str | None = None
    priority: str | None = None
    status: str | None = None
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    target_time_minutes: float | None = None


class AIQuestionResponse(BaseModel):
    """Réponse générée par le modèle local."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answer: str
    model: str
    context_used: bool = False
    data_proposals: list[AIDataProposalResponse] = Field(default_factory=list)
    race_options: list[AIRaceOptionResponse] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    analysis_periods: list[dict[str, str | int]] = Field(default_factory=list)


