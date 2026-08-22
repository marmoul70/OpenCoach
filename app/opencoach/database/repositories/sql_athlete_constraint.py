from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    AthleteConstraint as AthleteConstraintModel,
)
from opencoach.models import AthleteConstraint

from .athlete_constraint import (
    AthleteConstraintRepository,
)
from .errors import (
    AthleteConstraintRepositoryError,
)


class SqlAthleteConstraintRepository(
    AthleteConstraintRepository,
):
    """Persiste les contraintes temporaires d'un athlète."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_constraint(
        self,
        athlete_profile_id: UUID,
        constraint: AthleteConstraint,
    ) -> AthleteConstraint:
        """Crée ou met à jour une contrainte."""

        try:
            database_constraint = self.session.scalar(
                select(AthleteConstraintModel).where(
                    AthleteConstraintModel.id
                    == constraint.id,
                    AthleteConstraintModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_constraint is None:
                database_constraint = AthleteConstraintModel(
                    id=constraint.id,
                    athlete_profile_id=athlete_profile_id,
                )

                self.session.add(
                    database_constraint
                )

            database_constraint.start_date = (
                constraint.start_date
            )

            database_constraint.end_date = (
                constraint.end_date
            )

            database_constraint.constraint_type = (
                constraint.constraint_type
            )

            database_constraint.availability = (
                constraint.availability
            )

            database_constraint.running_allowed = (
                constraint.running_allowed
            )

            database_constraint.cross_training_allowed = (
                constraint.cross_training_allowed
            )

            database_constraint.max_duration_minutes = (
                constraint.max_duration_minutes
            )

            database_constraint.notes = (
                constraint.notes
            )

            self.session.commit()
            self.session.refresh(
                database_constraint
            )

            return self._to_domain(
                database_constraint
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise AthleteConstraintRepositoryError(
                "Impossible d'enregistrer la contrainte temporaire."
            ) from exc

    def get_constraint(
        self,
        athlete_profile_id: UUID,
        constraint_id: UUID,
    ) -> AthleteConstraint | None:
        """Retourne une contrainte par identifiant."""

        try:
            database_constraint = self.session.scalar(
                select(AthleteConstraintModel).where(
                    AthleteConstraintModel.id
                    == constraint_id,
                    AthleteConstraintModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_constraint is None:
                return None

            return self._to_domain(
                database_constraint
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise AthleteConstraintRepositoryError(
                "Impossible de charger la contrainte temporaire."
            ) from exc

    def delete_constraint(
        self,
        athlete_profile_id: UUID,
        constraint_id: UUID,
    ) -> None:
        """Supprime une contrainte."""

        try:
            database_constraint = self.session.scalar(
                select(AthleteConstraintModel).where(
                    AthleteConstraintModel.id
                    == constraint_id,
                    AthleteConstraintModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_constraint is None:
                raise AthleteConstraintRepositoryError(
                    "Contrainte temporaire introuvable."
                )

            self.session.delete(
                database_constraint
            )

            self.session.commit()

        except AthleteConstraintRepositoryError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise AthleteConstraintRepositoryError(
                "Impossible de supprimer la contrainte temporaire."
            ) from exc

    def list_overlapping(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[AthleteConstraint]:
        """Retourne les contraintes chevauchant une période."""

        if end_date < start_date:
            raise ValueError(
                "La date de fin doit être postérieure "
                "ou égale à la date de début."
            )

        try:
            statement = (
                select(AthleteConstraintModel)
                .where(
                    AthleteConstraintModel.athlete_profile_id
                    == athlete_profile_id,
                    AthleteConstraintModel.start_date
                    <= end_date,
                    AthleteConstraintModel.end_date
                    >= start_date,
                )
                .order_by(
                    AthleteConstraintModel.start_date.asc(),
                    AthleteConstraintModel.end_date.asc(),
                    AthleteConstraintModel.id.asc(),
                )
            )

            database_constraints = (
                self.session.scalars(
                    statement
                ).all()
            )

            return [
                self._to_domain(
                    database_constraint
                )
                for database_constraint
                in database_constraints
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise AthleteConstraintRepositoryError(
                "Impossible de charger les contraintes temporaires."
            ) from exc

    @staticmethod
    def _to_domain(
        constraint: AthleteConstraintModel,
    ) -> AthleteConstraint:
        """Convertit le modèle SQL en modèle métier."""

        return AthleteConstraint(
            id=constraint.id,
            start_date=constraint.start_date,
            end_date=constraint.end_date,
            constraint_type=constraint.constraint_type,
            availability=constraint.availability,
            running_allowed=constraint.running_allowed,
            cross_training_allowed=(
                constraint.cross_training_allowed
            ),
            max_duration_minutes=(
                constraint.max_duration_minutes
            ),
            notes=constraint.notes,
        )
