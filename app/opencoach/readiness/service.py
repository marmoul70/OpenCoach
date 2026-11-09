from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from opencoach.config import (
    ThresholdSettings,
    get_threshold_settings,
)
from opencoach.database.repositories.daily_context import (
    DailyContextRepository,
)
from opencoach.database.repositories.wellness import (
    WellnessRepository,
)
from opencoach.wellness_aggregation import aggregate_wellness_days
from opencoach.models import (
    DailyContext,
    WellnessDay,
)

from .baseline import (
    calculate_readiness_baseline,
)
from .comparison import (
    ReadinessComparison,
    compare_with_baseline,
)
from .context import (
    apply_daily_context,
)
from .models import (
    DailyReadiness,
    ReadinessBaseline,
)
from .scoring import (
    calculate_daily_readiness,
)


class ReadinessServiceError(RuntimeError):
    """Erreur métier du service Daily Readiness."""


class ReadinessDataUnavailableError(
    ReadinessServiceError
):
    """Aucune donnée Wellness disponible pour la date demandée."""


@dataclass(frozen=True)
class ReadinessAssessment:
    """Évaluation complète de la disponibilité quotidienne."""

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
    """Orchestre le calcul complet du Daily Readiness."""

    def __init__(
        self,
        repository: WellnessRepository,
        *,
        daily_context_repository: (
            DailyContextRepository | None
        ) = None,
        thresholds: ThresholdSettings | None = None,
        provider: str | None = "intervals",
        fallback_providers: tuple[str, ...] = (),
    ) -> None:
        self.repository = repository

        self.daily_context_repository = (
            daily_context_repository
        )

        self.thresholds = (
            thresholds
            if thresholds is not None
            else get_threshold_settings()
        )

        self.provider = provider
        self.fallback_providers = tuple(
            item for item in fallback_providers if item != provider
        )

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> ReadinessAssessment:
        """Calcule le Daily Readiness pour une date donnée."""

        selected_provider: str | None = self.provider
        current: WellnessDay | None = None
        data_conflicts: list[str] = []
        if self.provider is None:
            # Mode canonique : toutes les intégrations ont déjà importé leurs
            # mesures dans OpenCoach. Fusionner les métriques sans priorité fournisseur.
            imported = self.repository.list_range(
                athlete_profile_id, date.min, target_date,
            )
            aggregated = aggregate_wellness_days(imported)
            current = aggregated.days[-1] if aggregated.days else None
            if current is not None:
                data_conflicts.extend(
                    f"{day}:{metric}"
                    for day, metrics in aggregated.conflicts.items()
                    for metric in metrics
                    if day == current.date.isoformat()
                )
            selected_provider = "opencoach"
        else:
            provider_order = (self.provider, *self.fallback_providers)
            candidates: list[tuple[int, str, WellnessDay]] = []
            for priority, candidate_provider in enumerate(provider_order):
                candidate = self.repository.get_by_date(
                    athlete_profile_id, target_date, provider=candidate_provider,
                )
                if candidate is None:
                    candidate = self.repository.get_latest_on_or_before(
                        athlete_profile_id, target_date, provider=candidate_provider,
                    )
                if candidate is not None:
                    candidates.append((priority, candidate_provider, candidate))
            if candidates:
                _, selected_provider, current = max(
                    candidates, key=lambda item: (item[2].date, -item[0]),
                )

        if current is None or selected_provider is None:
            raise ReadinessDataUnavailableError(
                "Aucune donnée Wellness exploitable dans le stockage centralisé OpenCoach n'est disponible "
                f"avant ou pour le {target_date.isoformat()}."
            )

        source_date = current.date

        data_age_days = (
            target_date
            - source_date
        ).days

        data_status = (
            "fresh"
            if data_age_days == 0
            else "stale"
        )

        baseline_thresholds = (
            self.thresholds
            .readiness
            .baseline
        )

        history_start = (
            source_date
            - timedelta(
                days=(
                    baseline_thresholds
                    .window_days
                ),
            )
        )

        history_end = (
            source_date
            - timedelta(days=1)
        )

        history = self.repository.list_range(
            athlete_profile_id,
            history_start,
            history_end,
            provider=None if self.provider is None else selected_provider,
        )
        if self.provider is None:
            history_aggregation = aggregate_wellness_days(history)
            history = list(history_aggregation.days)
            data_conflicts.extend(
                f"{day}:{metric}"
                for day, metrics in history_aggregation.conflicts.items()
                for metric in metrics
            )

        baseline = calculate_readiness_baseline(
            history,
            current_date=source_date,
            window_days=(
                baseline_thresholds.window_days
            ),
            minimum_samples=(
                baseline_thresholds.minimum_samples
            ),
        )

        comparison = compare_with_baseline(
            current,
            baseline,
        )

        readiness = calculate_daily_readiness(
            current=current,
            comparison=comparison,
            thresholds=self.thresholds.readiness,
        )

        context = self._get_daily_context(
            athlete_profile_id,
            target_date,
        )

        readiness = apply_daily_context(
            readiness=readiness,
            context=context,
            thresholds=self.thresholds.readiness,
        )

        return ReadinessAssessment(
            date=target_date,
            provider=selected_provider,
            current=current,
            baseline=baseline,
            comparison=comparison,
            context=context,
            readiness=readiness,
            source_date=source_date,
            data_age_days=data_age_days,
            data_status=data_status,
            data_conflicts=tuple(data_conflicts),
        )

    def _get_daily_context(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> DailyContext | None:
        """Charge le contexte subjectif si un repository est configuré."""

        if self.daily_context_repository is None:
            return None

        return self.daily_context_repository.get_by_date(
            athlete_profile_id,
            target_date,
        )