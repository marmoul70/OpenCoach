from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    WeeklyTrainingPlan as WeeklyTrainingPlanModel,
)
from opencoach.database.repositories.weekly_training_plan import (
    WeeklyTrainingPlanRepository,
)
from opencoach.models import (
    WeeklyTrainingPlan,
)


class WeeklyTrainingPlanRepositoryError(
    RuntimeError
):
    """Erreur de persistance d'un plan hebdomadaire."""


class SqlWeeklyTrainingPlanRepository(
    WeeklyTrainingPlanRepository,
):
    """Persiste la référence d'une semaine d'entraînement."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_plan(
        self,
        plan: WeeklyTrainingPlan,
    ) -> WeeklyTrainingPlan:
        """Crée ou met à jour le plan de la semaine."""

        try:
            database_plan = self.session.scalar(
                select(
                    WeeklyTrainingPlanModel
                ).where(
                    WeeklyTrainingPlanModel.athlete_profile_id
                    == plan.athlete_profile_id,
                    WeeklyTrainingPlanModel.week_start
                    == plan.week_start,
                )
            )

            now = datetime.now(
                timezone.utc
            )

            if database_plan is None:
                database_plan = (
                    WeeklyTrainingPlanModel(
                        athlete_profile_id=(
                            plan.athlete_profile_id
                        ),
                        week_start=plan.week_start,
                        generated_at=(
                            plan.generated_at
                            or now
                        ),
                    )
                )

                self.session.add(
                    database_plan
                )

            database_plan.week_end = (
                plan.week_end
            )

            database_plan.phase = (
                plan.phase
            )

            database_plan.week_type = (
                plan.week_type
            )

            database_plan.phase_week_index = (
                plan.phase_week_index
            )

            database_plan.target_load = (
                plan.target_load
            )

            database_plan.load_min = (
                plan.load_min
            )

            database_plan.load_max = (
                plan.load_max
            )

            database_plan.reference_duration_minutes = (
                plan.reference_duration_minutes
            )

            database_plan.target_duration_minutes = (
                plan.target_duration_minutes
            )

            database_plan.long_endurance_reference_minutes = (
                plan.long_endurance_reference_minutes
            )

            database_plan.schedule_pressure = (
                plan.schedule_pressure
            )

            database_plan.athlete_schedule_constrained = (
                plan.athlete_schedule_constrained
            )

            database_plan.updated_at = now

            self.session.commit()
            self.session.refresh(
                database_plan
            )

            return self._to_domain(
                database_plan
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WeeklyTrainingPlanRepositoryError(
                "Impossible d'enregistrer "
                "le plan hebdomadaire."
            ) from exc

    def get_plan_for_week(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> WeeklyTrainingPlan | None:
        """Retourne le plan associé à une semaine."""

        try:
            database_plan = self.session.scalar(
                select(
                    WeeklyTrainingPlanModel
                ).where(
                    WeeklyTrainingPlanModel.athlete_profile_id
                    == athlete_profile_id,
                    WeeklyTrainingPlanModel.week_start
                    == week_start,
                )
            )

            if database_plan is None:
                return None

            return self._to_domain(
                database_plan
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WeeklyTrainingPlanRepositoryError(
                "Impossible de charger "
                "le plan hebdomadaire."
            ) from exc

    @staticmethod
    def _to_domain(
        plan: WeeklyTrainingPlanModel,
    ) -> WeeklyTrainingPlan:
        return WeeklyTrainingPlan(
            id=plan.id,
            athlete_profile_id=(
                plan.athlete_profile_id
            ),
            week_start=plan.week_start,
            week_end=plan.week_end,
            phase=plan.phase,
            week_type=plan.week_type,
            phase_week_index=(
                plan.phase_week_index
            ),
            target_load=plan.target_load,
            load_min=plan.load_min,
            load_max=plan.load_max,
            reference_duration_minutes=(
                plan.reference_duration_minutes
            ),
            target_duration_minutes=(
                plan.target_duration_minutes
            ),
            long_endurance_reference_minutes=(
                plan.long_endurance_reference_minutes
            ),
            schedule_pressure=(
                plan.schedule_pressure
            ),
            athlete_schedule_constrained=(
                plan.athlete_schedule_constrained
            ),
            generated_at=plan.generated_at,
            updated_at=plan.updated_at,
        )
