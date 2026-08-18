from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    DailyContext as DailyContextModel,
)
from opencoach.models import DailyContext

from .daily_context import (
    DailyContextRepository,
)
from .errors import (
    DailyContextRepositoryError,
)


class SqlDailyContextRepository(
    DailyContextRepository
):
    """Persiste le contexte subjectif quotidien."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save(
        self,
        athlete_profile_id: UUID,
        context: DailyContext,
    ) -> DailyContext:
        try:
            database_context = self._get_database_context(
                athlete_profile_id,
                context.date,
            )

            if database_context is None:
                database_context = DailyContextModel(
                    athlete_profile_id=athlete_profile_id,
                    date=context.date,
                )

                self.session.add(
                    database_context
                )

            database_context.fatigue_subjective = (
                context.fatigue_subjective
            )
            database_context.pain_level = (
                context.pain_level
            )
            database_context.illness_status = (
                context.illness_status
            )
            database_context.treatment_impact = (
                context.treatment_impact
            )
            database_context.motivation = (
                context.motivation
            )
            database_context.notes = (
                context.notes
            )

            self.session.commit()
            self.session.refresh(
                database_context
            )

            return self._to_domain(
                database_context
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise DailyContextRepositoryError(
                (
                    "Impossible d'enregistrer "
                    "le contexte quotidien."
                )
            ) from exc

    def get_by_date(
        self,
        athlete_profile_id: UUID,
        context_date: date,
    ) -> DailyContext | None:
        try:
            database_context = self._get_database_context(
                athlete_profile_id,
                context_date,
            )

            if database_context is None:
                return None

            return self._to_domain(
                database_context
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise DailyContextRepositoryError(
                (
                    "Impossible de charger "
                    "le contexte quotidien."
                )
            ) from exc

    def _get_database_context(
        self,
        athlete_profile_id: UUID,
        context_date: date,
    ) -> DailyContextModel | None:
        statement = (
            select(DailyContextModel)
            .where(
                DailyContextModel.athlete_profile_id
                == athlete_profile_id,
                DailyContextModel.date
                == context_date,
            )
        )

        return self.session.scalar(
            statement
        )

    @staticmethod
    def _to_domain(
        context: DailyContextModel,
    ) -> DailyContext:
        return DailyContext(
            date=context.date,
            fatigue_subjective=(
                context.fatigue_subjective
            ),
            pain_level=context.pain_level,
            illness_status=context.illness_status,
            treatment_impact=(
                context.treatment_impact
            ),
            motivation=context.motivation,
            notes=context.notes,
        )
