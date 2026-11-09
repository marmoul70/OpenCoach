"""Outil de disponibilité quotidienne basé sur le moteur Readiness OpenCoach."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.readiness import ReadinessDataUnavailableError, ReadinessService


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
    """Construit l'outil Readiness pour l'athlète authentifié."""

    def execute(arguments: BaseModel) -> dict:
        target_date = arguments.target_date
        try:
            assessment = service.calculate(athlete_profile_id, target_date)
        except ReadinessDataUnavailableError:
            return {
                "available": False,
                "target_date": target_date.isoformat(),
                "reason": "no_readiness_data",
                "message": "Aucune donnée de récupération exploitable n'est disponible pour cette date.",
            }

        def metric_payload(name: str) -> dict:
            baseline = getattr(assessment.baseline, name)
            comparison = getattr(assessment.comparison, name)
            return {
                "current": comparison.current,
                "baseline": comparison.baseline,
                "absolute_delta": comparison.absolute_delta,
                "percent_delta": comparison.percent_delta,
                "comparison_reliable": comparison.reliable,
                "baseline_samples": baseline.sample_count,
                "baseline_reliable": baseline.reliable,
            }

        warnings = []
        if assessment.data_status == "stale":
            warnings.append(
                f"Les dernières données disponibles datent du {assessment.source_date.isoformat()}."
            )
        unreliable_metrics = [
            name
            for name in ("hrv", "resting_hr", "sleep_seconds", "sleep_score")
            if not getattr(assessment.baseline, name).reliable
        ]
        if unreliable_metrics:
            warnings.append(
                "Baseline personnelle insuffisamment renseignée pour : "
                + ", ".join(unreliable_metrics)
                + "."
            )

        readiness = assessment.readiness
        return {
            "available": True,
            "target_date": assessment.date.isoformat(),
            "source": assessment.provider,
            "data": {
                "source_date": assessment.source_date.isoformat(),
                "age_days": assessment.data_age_days,
                "freshness": assessment.data_status,
            },
            "readiness": {
                "score": readiness.score,
                "level": readiness.level,
                "warning_count": readiness.warning_count,
                "critical_count": readiness.critical_count,
                "training_constraints": list(readiness.training_constraints),
                "fitness_ctl": readiness.fitness_ctl,
                "fatigue_atl": readiness.fatigue_atl,
                "training_balance": readiness.training_balance,
            },
            "baseline_period": {
                "start_date": assessment.baseline.start_date.isoformat(),
                "end_date": assessment.baseline.end_date.isoformat(),
            },
            "metrics": {
                "hrv": metric_payload("hrv"),
                "resting_hr": metric_payload("resting_hr"),
                "sleep_seconds": metric_payload("sleep_seconds"),
                "sleep_score": metric_payload("sleep_score"),
            },
            "signals": [
                {
                    "metric": signal.metric,
                    "level": signal.level,
                    "reason": signal.reason,
                    "current_value": signal.current_value,
                    "reference_value": signal.reference_value,
                }
                for signal in readiness.signals
            ],
            "warnings": warnings,
        }

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
