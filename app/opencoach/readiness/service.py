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
        provider: str = "intervals",
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

        selected_provider: str | None = None
        current: WellnessDay | None = None
        provider_order = (self.provider, *self.fallback_providers)

        # Chaque fournisseur est évalué séparément : les métriques du jour
        # et l'historique de référence proviennent toujours de la même source.
        for candidate_provider in provider_order:
            current = self.repository.get_by_date(
                athlete_profile_id,
                target_date,
                provider=candidate_provider,
            )
            if current is None:
                current = self.repository.get_latest_on_or_before(
                    athlete_profile_id,
                    target_date,
                    provider=candidate_provider,
                )
            if current is not None:
                selected_provider = candidate_provider
                break

        if current is None or selected_provider is None:
            providers = ", ".join(provider_order)
            raise ReadinessDataUnavailableError(
                (
                    "Aucune donnée Wellness exploitable "
                    f"n'est disponible avant ou pour "
                    f"le {target_date.isoformat()} "
                    f"avec les fournisseurs : {providers}."
                )
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
            provider=selected_provider,
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