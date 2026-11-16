"""Registre générique des capacités métier exécutées par le plan Coach."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable, Literal, Type

from pydantic import BaseModel, ConfigDict, ValidationError



logger = logging.getLogger(__name__)


ToolStatus = Literal["ok", "invalid_arguments", "needs_clarification", "not_found", "failed"]


class CoachCapabilityResult(BaseModel):
    """Enveloppe stable et sérialisable d'un résultat d'outil."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tool: str
    status: ToolStatus
    data: dict[str, Any] | None = None
    metadata: dict[str, Any]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CoachCapability:
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


class CoachCapabilityRegistry:
    """Registre en liste blanche et exécuteur synchrone des outils métier."""

    def __init__(
        self,
        argument_guard: Callable[
            [str, dict[str, Any], list[str], list[str]], str | None
        ] | None = None,
    ) -> None:
        self._tools: dict[str, CoachCapability] = {}
        self._argument_guard = argument_guard
        self._execution_results: list[CoachCapabilityResult] = []
        self._execution_cache: dict[tuple[str, str], CoachCapabilityResult] = {}
        self._allowed_tool_names: set[str] | None = None

    def restrict_to(self, names: set[str]) -> None:
        """Limite les outils exposés et exécutables pour la requête courante."""
        unknown = names.difference(self._tools)
        if unknown:
            raise ValueError(f"Outils inconnus dans la sélection : {', '.join(sorted(unknown))}")
        self._allowed_tool_names = set(names)

    @property
    def allowed_tool_names(self) -> frozenset[str] | None:
        """Liste blanche active ; None signifie que le registre est non filtré."""
        return None if self._allowed_tool_names is None else frozenset(self._allowed_tool_names)

    @property
    def execution_results(self) -> tuple[CoachCapabilityResult, ...]:
        """Résultats des appels effectués pendant la requête courante."""
        return tuple(self._execution_results)

    def register(self, tool: CoachCapability) -> None:
        """Enregistre un outil ; les doublons sont refusés."""
        if tool.name in self._tools:
            raise ValueError(f"L'outil '{tool.name}' est déjà enregistré.")
        self._tools[tool.name] = tool

    def definitions(self) -> list[dict[str, Any]]:
        """Expose un catalogue interne pour l'inspection et les tests, jamais au modèle."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.arguments_model.model_json_schema(),
            }
            for tool in self._tools.values()
            if self._allowed_tool_names is None or tool.name in self._allowed_tool_names
        ]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        user_messages: list[str] | None = None,
        assistant_messages: list[str] | None = None,
        trusted_arguments: bool = False,
    ) -> CoachCapabilityResult:
        """Valide puis exécute un outil ; les plans déterministes peuvent marquer leurs arguments comme fiables."""
        started_at = perf_counter()
        tool = self._tools.get(name)
        if tool is None or (
            self._allowed_tool_names is not None and name not in self._allowed_tool_names
        ):
            result = CoachCapabilityResult(
                tool=name,
                status="not_found",
                metadata=_execution_metadata(started_at),
                error="Outil non autorisé ou inconnu.",
            )
            self._record_result(result)
            return result

        if self._argument_guard is not None and not trusted_arguments:
            clarification = self._argument_guard(name, arguments, user_messages or [], assistant_messages or [])
            if clarification:
                result = CoachCapabilityResult(
                    tool=name,
                    status="needs_clarification",
                    metadata=_execution_metadata(started_at, business_tool_executed=False),
                    error=clarification,
                )
                self._record_result(result)
                return result

        try:
            validated_arguments = tool.arguments_model.model_validate(arguments)
        except ValidationError:
            result = CoachCapabilityResult(
                tool=name,
                status="invalid_arguments",
                metadata=_execution_metadata(started_at),
                error="Les paramètres fournis ne respectent pas le schéma de l'outil.",
            )
            self._record_result(result)
            return result

        # Une même invocation exacte ne doit pas déclencher deux fois un
        # outil métier pendant une seule requête (y compris un outil d'écriture).
        canonical_arguments = json.dumps(
            validated_arguments.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        cache_key = (name, canonical_arguments)
        cached_result = self._execution_cache.get(cache_key)
        if cached_result is not None:
            return cached_result.model_copy(
                update={
                    "metadata": {
                        **cached_result.metadata,
                        "replayed": True,
                        "business_tool_executed": False,
                    }
                }
            )

        try:
            data = tool.handler(validated_arguments)
        except Exception as exc:
            # Le message d'exception peut contenir une requête SQL ou des
            # données métier : ne journaliser que son type.
            logger.error(
                "Échec d'exécution de l'outil coach '%s' (type=%s)",
                name,
                type(exc).__name__,
            )
            result = CoachCapabilityResult(
                tool=name,
                status="failed",
                metadata=_execution_metadata(
                    started_at,
                    business_tool_executed=True,
                    error_type=type(exc).__name__,
                ),
                error="L'exécution de l'outil a échoué.",
            )
            self._record_result(result)
            self._execution_cache[cache_key] = result
            return result

        result = CoachCapabilityResult(
            tool=name,
            status="ok",
            data=data,
            metadata=_execution_metadata(started_at),
        )
        self._record_result(result)
        self._execution_cache[cache_key] = result
        return result

    def _record_result(self, result: CoachCapabilityResult) -> None:
        """Conserve le résultat de l'exécution courante."""
        self._execution_results.append(result)


def _execution_metadata(started_at: float, **extra: Any) -> dict[str, Any]:
    """Ajoute une durée monotone à chaque issue d'exécution, sans donnée métier."""
    return {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round((perf_counter() - started_at) * 1000, 3),
        **extra,
    }
