from datetime import date, timedelta
from uuid import UUID

from .load_comparison_service import (
    TrainingLoadComparisonService,
)
from .recent_load import (
    RecentTrainingLoad,
)


class RecentTrainingLoadService:
    """Construit l'historique récent de charge d'un athlète."""

    def __init__(
        self,
        comparison_service: TrainingLoadComparisonService,
        *,
        reference_date_provider=date.today,
    ) -> None:
        self.comparison_service = (
            comparison_service
        )
        self.reference_date_provider = reference_date_provider

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date | None = None,
        *,
        days: int = 7,
    ) -> RecentTrainingLoad:
        """Analyse les jours précédant la date cible."""

        target_date = target_date or self.reference_date_provider()
        if not 1 <= days <= 90:
            raise ValueError(
                "La période de charge doit être comprise entre 1 et 90 jours (au moins un jour)."
            )

        comparisons = []

        for offset in range(
            1,
            days + 1,
        ):
            comparison_date = (
                target_date
                - timedelta(
                    days=offset,
                )
            )

            comparisons.append(
                self.comparison_service.calculate(
                    athlete_profile_id,
                    comparison_date,
                )
            )

        days_tuple = tuple(
            comparisons,
        )

        planned_load_total = round(
            sum(
                day.planned_load
                for day in days_tuple
            ),
            2,
        )

        actual_load_total = round(
            sum(
                day.actual_load
                for day in days_tuple
            ),
            2,
        )

        return RecentTrainingLoad(
            days=days_tuple,
            analyzed_days=len(
                days_tuple,
            ),
            planned_load_total=(
                planned_load_total
            ),
            actual_load_total=(
                actual_load_total
            ),
            above_plan_days=sum(
                day.status == "above_plan"
                for day in days_tuple
            ),
            below_plan_days=sum(
                day.status == "below_plan"
                for day in days_tuple
            ),
            on_plan_days=sum(
                day.status == "on_plan"
                for day in days_tuple
            ),
            broken_rest_days=sum(
                day.status == "rest_broken"
                for day in days_tuple
            ),
            respected_rest_days=sum(
                day.status == "rest_respected"
                for day in days_tuple
            ),

            planning_covered_days=sum(
                day.status != "unplanned"
                for day in days_tuple
            ),

            unplanned_days=sum(
                day.status == "unplanned"
                for day in days_tuple
            ),
)