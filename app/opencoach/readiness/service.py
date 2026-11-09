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
