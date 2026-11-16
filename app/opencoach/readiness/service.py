from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from opencoach.config import ThresholdSettings, get_threshold_settings
from opencoach.database.repositories.daily_context import DailyContextRepository
from opencoach.database.repositories.wellness import WellnessRepository
from opencoach.models import DailyContext, WellnessDay
from opencoach.wellness_aggregation import aggregate_wellness_days

from .baseline import calculate_readiness_baseline
from .comparison import ReadinessComparison, compare_with_baseline
from .context import apply_daily_context
from .models import DailyReadiness, ReadinessBaseline
from .scoring import calculate_daily_readiness


class ReadinessServiceError(RuntimeError):
    """Erreur métier du service Daily Readiness."""


class ReadinessDataUnavailableError(ReadinessServiceError):
    """Aucune donnée Wellness exploitable n'est disponible."""


@dataclass(frozen=True)
class ReadinessAssessment:
    """Évaluation calculée exclusivement depuis le référentiel OpenCoach."""

    date: date
    provider: str
    current: WellnessDay
    baseline: ReadinessBaseline
    comparison: ReadinessComparison
    context: DailyContext | None
    readiness: DailyReadiness
    source_date: date
    data_age_days: int
    data_status: str
    data_conflicts: tuple[str, ...] = ()


class ReadinessService:
    """Calcule le Readiness depuis les imports centralisés dans OpenCoach.

    Aucun fournisseur n'est sélectionné ou priorisé ici. La provenance reste
    attachée aux lignes pour la traçabilité ; l'agrégation résout chaque métrique
    indépendamment avant tout calcul de score.
    """

    def __init__(
        self,
        repository: WellnessRepository,
        *,
        daily_context_repository: DailyContextRepository | None = None,
        thresholds: ThresholdSettings | None = None,
    ) -> None:
        self.repository = repository
        self.daily_context_repository = daily_context_repository
        self.thresholds = thresholds if thresholds is not None else get_threshold_settings()

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> ReadinessAssessment:
        """Calcule le Readiness à partir de toutes les données importées dans OpenCoach."""

        latest_import = self.repository.get_latest_on_or_before(
            athlete_profile_id,
            target_date,
        )
        if latest_import is None:
            raise ReadinessDataUnavailableError(
                "Aucune donnée Wellness exploitable dans le stockage centralisé OpenCoach "
                f"n'est disponible avant ou pour le {target_date.isoformat()}."
            )

        source_date = latest_import.date
        current_imports = self.repository.list_range(
            athlete_profile_id,
            source_date,
            source_date,
        )
        current_aggregation = aggregate_wellness_days(current_imports)
        current = current_aggregation.days[-1] if current_aggregation.days else None
        if current is None:
            raise ReadinessDataUnavailableError(
                "Aucune donnée Wellness exploitable n'est disponible dans OpenCoach "
                f"pour le {source_date.isoformat()}."
            )

        data_conflicts = [
            f"{day}:{metric}"
            for day, metrics in current_aggregation.conflicts.items()
            for metric in metrics
        ]

        readiness_inputs = (
            current.hrv,
            current.resting_hr,
            current.sleep_seconds,
            current.sleep_score,
            current.fitness_ctl,
            current.fatigue_atl,
        )
        if all(value is None for value in readiness_inputs):
            raise ReadinessDataUnavailableError(
                "Les données importées dans OpenCoach ne contiennent aucune mesure "
                "exploitable pour calculer le Readiness à cette date."
            )

        data_age_days = (target_date - source_date).days
        data_status = "fresh" if data_age_days == 0 else "stale"

        baseline_thresholds = self.thresholds.readiness.baseline
        history_start = source_date - timedelta(days=baseline_thresholds.window_days)
        history_end = source_date - timedelta(days=1)

        history_imports = self.repository.list_range(
            athlete_profile_id,
            history_start,
            history_end,
        )
        history_aggregation = aggregate_wellness_days(history_imports)
        history = list(history_aggregation.days)
        data_conflicts.extend(
            f"{day}:{metric}"
            for day, metrics in history_aggregation.conflicts.items()
            for metric in metrics
        )

        baseline = calculate_readiness_baseline(
            history,
            current_date=source_date,
            window_days=baseline_thresholds.window_days,
            minimum_samples=baseline_thresholds.minimum_samples,
        )
        comparison = compare_with_baseline(current, baseline)
        readiness = calculate_daily_readiness(
            current=current,
            comparison=comparison,
            thresholds=self.thresholds.readiness,
        )

        context = self._get_daily_context(athlete_profile_id, target_date)
        readiness = apply_daily_context(
            readiness=readiness,
            context=context,
            thresholds=self.thresholds.readiness,
        )

        return ReadinessAssessment(
            date=target_date,
            provider="opencoach",
            current=current,
            baseline=baseline,
            comparison=comparison,
            context=context,
            readiness=readiness,
            source_date=source_date,
            data_age_days=data_age_days,
            data_status=data_status,
            data_conflicts=tuple(sorted(set(data_conflicts))),
        )

    def _get_daily_context(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> DailyContext | None:
        """Charge le contexte subjectif si un repository est configuré."""

        if self.daily_context_repository is None:
            return None
        return self.daily_context_repository.get_by_date(athlete_profile_id, target_date)



def readiness_assessment_to_dict(assessment: ReadinessAssessment) -> dict:
    """Sérialise le résultat canonique Readiness et ses limites d'interprétation.

    Les règles de fraîcheur, de fiabilité des baselines et les avertissements
    appartiennent au domaine Readiness. Les adaptateurs (API, IA) ne doivent
    pas reconstruire ces informations à partir des métriques brutes.
    """
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

    warnings: list[str] = []
    data_conflicts = getattr(assessment, "data_conflicts", ())
    if data_conflicts:
        warnings.append(
            "Certaines métriques ont été écartées à cause de conflits entre imports OpenCoach : "
            + ", ".join(data_conflicts)
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
