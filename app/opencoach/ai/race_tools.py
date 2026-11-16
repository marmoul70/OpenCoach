"""Adaptateur conversationnel pour l'analyse Coach d'une course."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.services import RacePreparationService


class RacePreparationArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    race_id: UUID = Field(description="Identifiant de la course obtenu via race_calendar.")
    history_days: int = Field(
        description="Nombre de jours calendaires d'historique récent à analyser. Obligatoire.",
    )


def build_race_preparation_tool(service: RacePreparationService) -> AITool:
    """Expose le service métier de préparation sans dupliquer son calcul."""

    def execute(arguments: BaseModel) -> dict:
        return service.analyze(
            race_id=arguments.race_id,
            history_days=arguments.history_days,
        )

    return AITool(
        name="race_preparation_analysis",
        description=(
            "Analyse une course future du calendrier de l'athlète authentifié en "
            "croisant ses caractéristiques (distance, D+, date, objectif) avec le "
            "profil d'entraînement et l'historique réellement observé. race_id doit "
            "être obtenu via race_calendar. history_days est obligatoire (7 à 180) : "
            "si la période n'est pas précisée, demande à l'utilisateur combien de "
            "jours analyser. Les totaux et moyennes sont masqués si la couverture "
            "des métriques est incomplète. Aucun score de préparation n'est inventé."
        ),
        arguments_model=RacePreparationArguments,
        handler=execute,
    )
