"""Registre sécurisé des outils métier exposés à l'IA.

Le registre est une liste blanche explicite. Il ne découvre aucun module et
n'exécute jamais de fonction arbitraire fournie par le modèle.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Literal, Type

from pydantic import BaseModel, ConfigDict, ValidationError


ToolStatus = Literal["ok", "invalid_arguments", "not_found", "failed"]


class AIToolResult(BaseModel):
    """Enveloppe stable et sérialisable d'un résultat d'outil."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tool: str
    status: ToolStatus
    data: dict[str, Any] | None = None
    metadata: dict[str, Any]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class AITool:
    """Définition d'un outil explicitement autorisé."""

    name: str
    description: str
    arguments_model: Type[BaseModel]
    handler: Callable[[BaseModel], dict[str, Any]]

    def __post_init__(self) -> None:
        if not self.name or not self.name.replace("_", "").isalnum():
            raise ValueError("Le nom de l'outil est invalide.")
        if not self.description.strip():
            raise ValueError("La description de l'outil est obligatoire.")


class AIToolRegistry:
    """Registre en liste blanche et exécuteur synchrone des outils métier."""

    def __init__(self) -> None:
        self._tools: dict[str, AITool] = {}
        self._execution_results: list[AIToolResult] = []

    @property
    def execution_results(self) -> tuple[AIToolResult, ...]:
        """Résultats des appels effectués pendant la requête courante."""
        return tuple(self._execution_results)

    def register(self, tool: AITool) -> None:
        """Enregistre un outil ; les doublons sont refusés."""
        if tool.name in self._tools:
            raise ValueError(f"L'outil '{tool.name}' est déjà enregistré.")
        self._tools[tool.name] = tool

    def definitions(self) -> list[dict[str, Any]]:
        """Retourne les définitions utilisables par un orchestrateur IA."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.arguments_model.model_json_schema(),
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> AIToolResult:
        """Valide puis exécute uniquement un outil enregistré."""
        tool = self._tools.get(name)
        if tool is None:
            result = AIToolResult(
                tool=name,
                status="not_found",
                metadata={"executed_at": _utc_now()},
                error="Outil non autorisé ou inconnu.",
            )
            self._execution_results.append(result)
            return result

        try:
            validated_arguments = tool.arguments_model.model_validate(arguments)
        except ValidationError:
            result = AIToolResult(
                tool=name,
                status="invalid_arguments",
                metadata={"executed_at": _utc_now()},
                error="Les paramètres fournis ne respectent pas le schéma de l'outil.",
            )
            self._execution_results.append(result)
            return result

        try:
            data = tool.handler(validated_arguments)
        except Exception:
            # Ne pas transmettre au LLM les détails internes, SQL ou secrets.
            result = AIToolResult(
                tool=name,
                status="failed",
                metadata={"executed_at": _utc_now()},
                error="L'exécution de l'outil a échoué.",
            )
            self._execution_results.append(result)
            return result

        result = AIToolResult(
            tool=name,
            status="ok",
            data=data,
            metadata={"executed_at": _utc_now()},
        )
        self._execution_results.append(result)
        return result


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
