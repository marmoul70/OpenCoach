"""Service de projection de charge hebdomadaire."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from opencoach.database.repositories import (
    TrainingSessionRepository,
    WeeklyTrainingPlanRepository,
)

from .daily_load_service import (
    DailyTrainingLoadService,
)
from .load_estimation import (
    estimate_prescribed_load,
)
from .weekly_load_projection import (
    WeeklyLoadProjection,
)


class WeeklyLoadProjectionService:
    """Projette la charge de la semaine courante au jour J."""

    def __init__(
        self,
        training_session_repository: TrainingSessionRepository,
        daily_training_load_service: DailyTrainingLoadService,
        weekly_training_plan_repository: WeeklyTrainingPlanRepository,
    ) -> None:
        self.training_session_repository = (
            training_session_repository
        )

        self.daily_training_load_service = (
            daily_training_load_service
        )

        self.weekly_training_plan_repository = (
            weekly_training_plan_repository
        )

    def calculate(
        self,
        athlete_profile_id: UUID,
        as_of_date: date,
    ) -> WeeklyLoadProjection:
        """Calcule réalisé + reste prescrit pour la semaine."""

        week_start = (
            as_of_date
            - timedelta(
                days=as_of_date.weekday(),
            )
        )

        week_end = (
            week_start
            + timedelta(days=6)
        )

        weekly_plan = (
            self.weekly_training_plan_repository
            .get_plan_for_week(
                athlete_profile_id,
                week_start,
            )
        )

        sessions = (
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                week_start,
                week_end,
            )
        )

        actual_load_to_date = sum(
            self.daily_training_load_service
            .calculate(
                athlete_profile_id,
                current_date,
            )
            .total_load
            for current_date in self._dates_between(
                week_start,
                as_of_date,
            )
        )

        prescribed_sessions = [
            session
            for session in sessions
            if self._is_prescribed_session(
                session
            )
        ]

        remaining_sessions = [
            session
            for session in prescribed_sessions
            if (
                session.date >= as_of_date
                and session.status == "planned"
            )
        ]

        missed_sessions = [
            session
            for session in prescribed_sessions
            if (
                session.date < as_of_date
                and session.status == "planned"
            )
        ]

        completed_sessions = [
            session
            for session in prescribed_sessions
            if (
                session.date <= as_of_date
                and session.status == "completed"
            )
        ]

        supplementary_sessions = [
            session
            for session in sessions
            if session.type == "supplementary"
        ]

        remaining_planned_load = sum(
            estimate_prescribed_load(
                session,
            )
            for session in remaining_sessions
            if session.type != "rest"
        )

        projected_week_load = (
            actual_load_to_date
            + remaining_planned_load
        )

        target_load = (
            weekly_plan.target_load
            if weekly_plan is not None
            else None
        )

        load_min = (
            weekly_plan.load_min
            if weekly_plan is not None
            else None
        )

        load_max = (
            weekly_plan.load_max
            if weekly_plan is not None
            else None
        )

        projected_gap = None
        projected_gap_percent = None

        if (
            target_load is not None
            and target_load > 0
        ):
            projected_gap = (
                projected_week_load
                - target_load
            )

            projected_gap_percent = (
                projected_gap
                / target_load
                * 100.0
            )

        adaptation_opportunity = False
        adaptation_direction = None

        if projected_gap_percent is not None:
            if projected_gap_percent < -15.0:
                adaptation_opportunity = True
                adaptation_direction = "increase"

            elif projected_gap_percent > 15.0:
                adaptation_opportunity = True
                adaptation_direction = "reduce"

        remaining_days = max(
            0,
            (
                week_end
                - as_of_date
            ).days,
        )

        return WeeklyLoadProjection(
            week_start=week_start,
            week_end=week_end,
            as_of_date=as_of_date,
            actual_load_to_date=round(
                actual_load_to_date,
                2,
            ),
            remaining_planned_load=round(
                remaining_planned_load,
                2,
            ),
            projected_week_load=round(
                projected_week_load,
                2,
            ),

            target_load=(
                round(
                    target_load,
                    2,
                )
                if target_load is not None
                else None
            ),
            load_min=(
                round(
                    load_min,
                    2,
                )
                if load_min is not None
                else None
            ),
            load_max=(
                round(
                    load_max,
                    2,
                )
                if load_max is not None
                else None
            ),

            projected_gap=(
                round(
                    projected_gap,
                    2,
                )
                if projected_gap is not None
                else None
            ),
            projected_gap_percent=(
                round(
                    projected_gap_percent,
                    1,
                )
                if projected_gap_percent
                is not None
                else None
            ),

            remaining_days=(
                remaining_days
            ),

            adaptation_opportunity=(
                adaptation_opportunity
            ),
            adaptation_direction=(
                adaptation_direction
            ),

            completed_sessions_count=len(
                completed_sessions
            ),
            missed_sessions_count=len(
                missed_sessions
            ),
            remaining_sessions_count=len(
                remaining_sessions
            ),
            planned_sessions_count=len(
                prescribed_sessions
            ),
            supplementary_sessions_count=len(
                supplementary_sessions
            ),
        )

    @staticmethod
    def _is_prescribed_session(
        session,
    ) -> bool:
        """Distingue prescription et activité supplémentaire."""

        return (
            session.type != "supplementary"
            and session.planning_key is not None
        )

    @staticmethod
    def _dates_between(
        start: date,
        end: date,
    ):
        """Itère sur les dates inclusives d'une période."""

        current = start

        while current <= end:
            yield current
            current += timedelta(days=1)
