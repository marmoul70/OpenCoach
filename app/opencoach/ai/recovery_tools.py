"""Adaptateurs conversationnels pour les capacités de récupération OpenCoach."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.database.repositories import DailyCheckInRepository
from opencoach.readiness import (
    ReadinessDataUnavailableError,
    ReadinessService,
    readiness_assessment_to_dict,
)
from opencoach.recovery_assessment import recovery_coach_summary_to_dict


class RecoveryStatusArguments(BaseModel):
    """Date de récupération à consulter ; aujourd'hui par défaut."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_date: date = Field(
        default_factory=date.today,
        description="Date à analyser ; omettre le champ pour consulter aujourd'hui.",
    )


def build_recovery_status_tool(
    service: ReadinessService,
    athlete_profile_id: UUID,
) -> AITool:
    """Expose le résultat Readiness calculé par le Coach."""

    def execute(arguments: BaseModel) -> dict:
        try:
            assessment = service.calculate(
                athlete_profile_id,
                arguments.target_date,
            )
        except ReadinessDataUnavailableError:
            return {
                "available": False,
                "target_date": arguments.target_date.isoformat(),
                "reason": "no_readiness_data",
                "message": "Aucune donnée de récupération exploitable n'est disponible pour cette date.",
            }
        return readiness_assessment_to_dict(assessment)

    return AITool(
        name="recovery_status",
        description=(
            "Retourne l'évaluation Readiness OpenCoach pour une date donnée. "
            "target_date est facultatif et vaut aujourd'hui lorsqu'il est omis. "
            "Le résultat précise la date réelle des données, leur fraîcheur, "
            "la fiabilité des baselines et les signaux de récupération."
        ),
        arguments_model=RecoveryStatusArguments,
        handler=execute,
    )


class RecoveryAnalysisArguments(BaseModel):
    """Date d'ancrage de la synthèse de récupération."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_date: date = Field(
        default_factory=date.today,
        description="Date de fin de l'analyse ; aujourd'hui par défaut.",
    )


def build_recovery_analysis_tool(
    service: ReadinessService,
    daily_checkin_repository: DailyCheckInRepository,
    athlete_profile_id: UUID,
) -> AITool:
    """Expose le résumé de récupération construit par le domaine Coach."""

    def execute(arguments: BaseModel) -> dict:
        assessment, _aggregation = service.describe_recovery(
            athlete_profile_id,
            arguments.target_date,
        )
        daily_checkin = daily_checkin_repository.get_for_date(
            athlete_profile_id,
            arguments.target_date,
        )
        return recovery_coach_summary_to_dict(
            assessment,
            _aggregation,
            daily_checkin,
        )

    return AITool(
        name="recovery_analysis",
        description=(
            "Analyse descriptive récente de la forme et de la récupération : sommeil "
            "(durée, score et phases), HRV, fréquence cardiaque au repos, stress, "
            "charge ATL/CTL, sur les 7 derniers jours uniquement. Les données "
            "proviennent exclusivement du stockage centralisé OpenCoach, tous "
            "fournisseurs d’import confondus ; aucune API fournisseur n’est appelée. "
            "Inclut séparément le ressenti du jour provenant du check-in. À utiliser "
            "pour toute discussion sur fatigue, forme, récupération, sommeil ou stress. "
            "Le seul argument est target_date facultatif ; la fenêtre de 7 jours "
            "est calculée automatiquement. N'ajoute aucun paramètre nb_days. "
            "Ne produit aucun diagnostic ni score composite."
        ),
        arguments_model=RecoveryAnalysisArguments,
        handler=execute,
    )
