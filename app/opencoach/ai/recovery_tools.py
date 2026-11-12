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
        if getattr(assessment, "data_conflicts", ()):
            warnings.append(
                "Certaines métriques ont été écartées à cause de conflits entre imports OpenCoach : "
                + ", ".join(assessment.data_conflicts)
            )
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

class RecoveryAnalysisArguments(BaseModel):
    """Fenêtre descriptive de récupération, ancrée sur une date."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_date: date = Field(
        default_factory=date.today,
        description="Date de fin de l'analyse ; aujourd'hui par défaut.",
    )


def build_recovery_analysis_tool(
    wellness_repository,
    daily_context_repository,
    daily_checkin_repository,
    athlete_profile_id: UUID,
) -> AITool:
    """Expose les données sommeil, physiologie, charge et ressenti sur 7/14/30 jours.

    Les calculs restent dans recovery_assessment.py. L'outil ne crée aucun score
    composite et conserve séparément données objectives et déclarations athlète.
    """

    from datetime import timedelta

    from opencoach.wellness_aggregation import aggregate_wellness_days
    from opencoach.recovery_assessment import (
        build_recovery_assessment,
        recovery_assessment_to_dict,
    )

    # Ne transmettre que les indicateurs utiles à une synthèse forme /
    # fatigue / sommeil. Les métriques détaillées restent disponibles dans
    # les écrans métier ; elles alourdissent inutilement le contexte du LLM.
    analysis_metrics = {
        "hrv", "resting_hr", "sleep_seconds", "sleep_score", "sleep_quality",
        "stress_avg", "spo2", "sleep_deep_seconds",
        "sleep_rem_seconds", "fatigue_atl", "fitness_ctl",
    }

    def format_duration(value: float | int | None) -> str | None:
        if value is None:
            return None
        total_minutes = round(float(value) / 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours} h {minutes:02d} min"

    def execute(arguments: BaseModel) -> dict:
        target_date = arguments.target_date
        start_date = target_date - timedelta(days=29)
        # Le coach lit uniquement les lignes déjà centralisées dans OpenCoach.
        # Aucun fournisseur n’est prioritaire : les métriques sont fusionnées
        # indépendamment, journée par journée.
        imported_wellness_days = wellness_repository.list_range(
            athlete_profile_id, start_date, target_date,
        )
        aggregation = aggregate_wellness_days(imported_wellness_days)
        provider = "opencoach"
        wellness_days = list(aggregation.days)

        subjective_context = daily_context_repository.get_by_date(
            athlete_profile_id,
            target_date,
        )
        daily_checkin = daily_checkin_repository.get_for_date(
            athlete_profile_id,
            target_date,
        )

        assessment = build_recovery_assessment(
            wellness_days=wellness_days,
            target_date=target_date,
            provider=provider,
            subjective_context=subjective_context,
        )
        payload = recovery_assessment_to_dict(assessment)

        checkin_payload = None
        if daily_checkin is not None:
            checkin_payload = {
                "date": daily_checkin.date.isoformat(),
                "energy_rating": daily_checkin.energy_rating,
                "pain_wellness_rating": daily_checkin.pain_wellness_rating,
                "illness": daily_checkin.illness,
                "unavailable": daily_checkin.unavailable,
                "pain_locations": [
                    {
                        "area": item.area.value,
                        "side": item.side.value,
                    }
                    for item in daily_checkin.pain_locations
                ],
            }

        windows = []
        for window in assessment.windows:
            windows.append({
                "days": window.days,
                "start_date": window.start_date.isoformat(),
                "end_date": window.end_date.isoformat(),
                "recorded_days": window.recorded_days,
                "coverage_ratio": round(window.coverage_ratio, 3),
                "metrics": {
                    name: (
                        {
                            "current": metric.current,
                            "average": metric.average,
                            "median": metric.median,
                            "display": (
                                {
                                    "current": format_duration(metric.current),
                                    "average": format_duration(metric.average),
                                    "median": format_duration(metric.median),
                                    "unit": "heures et minutes",
                                }
                                if name in {"sleep_seconds", "sleep_deep_seconds", "sleep_rem_seconds"}
                                else None
                            ),
                            "sample_count": metric.sample_count,
                            "coverage_days": metric.coverage_days,
                            "expected_days": metric.expected_days,
                        }
                        if metric.sample_count > 0
                        else {
                            # Garder les métriques canoniques explicitement inconnues,
                            # sans transmettre les statistiques de couverture vides.
                            "current": None,
                            "sample_count": 0,
                        }
                    )
                    for name, metric in window.metrics.items()
                    if name in analysis_metrics
                },
            })

        warnings = []
        if aggregation.conflicts:
            warnings.append(
                "Des valeurs concurrentes de fraîcheur identique ont été écartées : "
                + str(aggregation.conflicts)
            )
        if assessment.data_status == "unavailable":
            warnings.append("Aucune donnée Wellness disponible sur la période.")
        elif assessment.data_status == "stale":
            warnings.append(
                f"Dernière donnée Wellness le {assessment.source_date.isoformat()} "
                f"(J-{assessment.data_age_days})."
            )
        if checkin_payload is None and payload["subjective"] is None:
            warnings.append(
                "Aucun ressenti subjectif enregistré pour cette date. "
                "Demander à l'athlète comment il se sent ; ne rien déduire."
            )
        if windows and windows[0]["coverage_ratio"] < 0.7:
            warnings.append(
                "Couverture Wellness inférieure à 70 % sur 7 jours ; "
                "interpréter les tendances avec prudence."
            )

        metric_definitions = {
            "hrv": {"label": "Variabilité de la fréquence cardiaque", "unit": "ms"},
            "resting_hr": {"label": "Fréquence cardiaque au repos", "unit": "bpm"},
            "stress_avg": {"label": "Stress moyen", "unit": "score COROS"},
            "sleep_seconds": {"label": "Durée totale de sommeil", "unit": "h:min", "raw_unit": "s"},
            "sleep_score": {"label": "Score de sommeil", "unit": "score COROS"},
            "sleep_quality": {"label": "Qualité du sommeil", "unit": "score COROS"},
            "spo2": {"label": "Saturation périphérique en oxygène", "unit": "%"},
            "sleep_deep_seconds": {"label": "Sommeil profond", "unit": "h:min", "raw_unit": "s"},
            "sleep_rem_seconds": {"label": "Sommeil paradoxal (REM)", "unit": "h:min", "raw_unit": "s"},
            "fatigue_atl": {"label": "Charge aiguë COROS (ATL)", "unit": "points COROS"},
            "fitness_ctl": {"label": "Charge chronique COROS (CTL)", "unit": "points COROS"},
        }

        return {
            "target_date": target_date.isoformat(),
            "data_store": "OpenCoach",
            "metric_definitions": metric_definitions,
            "provider": provider if wellness_days else None,
            # Conserver la provenance sans transmettre une matrice journalière
            # répétitive qui peut dépasser le budget de contexte du modèle.
            "metric_sources": {
                metric: sorted({
                    source
                    for day_sources in aggregation.metric_sources.values()
                    for source in day_sources.get(metric, ())
                })
                for metric in sorted({
                    metric
                    for day_sources in aggregation.metric_sources.values()
                    for metric in day_sources
                    if metric in analysis_metrics
                })
            },
            "metric_source_days": {
                metric: sum(
                    1 for day_sources in aggregation.metric_sources.values()
                    if metric in day_sources and metric in analysis_metrics
                )
                for metric in sorted({
                    metric
                    for day_sources in aggregation.metric_sources.values()
                    for metric in day_sources
                    if metric in analysis_metrics
                })
            },
            "conflicting_metrics": aggregation.conflicts,
            "source_date": payload["source_date"],
            "data_age_days": payload["data_age_days"],
            "data_status": payload["data_status"],
            "windows": windows,
            "daily_context": payload["subjective"],
            "daily_checkin": checkin_payload,
            "warnings": warnings,
        }

    return AITool(
        name="recovery_analysis",
        description=(
            "Analyse descriptive de la forme et de la récupération : sommeil "
            "(durée, score et phases), HRV, fréquence cardiaque au repos, stress, "
            "charge ATL/CTL, sur des fenêtres de 7, 14 et 30 jours. Les données "
            "proviennent exclusivement du stockage centralisé OpenCoach, tous "
            "fournisseurs d’import confondus ; aucune API fournisseur n’est appelée. "
            "Inclut séparément le ressenti du jour provenant du check-in. À utiliser "
            "pour toute discussion sur fatigue, forme, récupération, sommeil ou stress. "
            "Le seul argument est target_date facultatif ; les fenêtres 7, 14 et 30 jours "
            "sont calculées automatiquement. N'ajoute aucun paramètre nb_days. "
            "Ne produit aucun diagnostic ni score composite."
        ),
        arguments_model=RecoveryAnalysisArguments,
        handler=execute,
    )
