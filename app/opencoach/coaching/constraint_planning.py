"""Gestion applicative des contraintes temporaires de l'athlète.

Cette couche relie deux responsabilités existantes :

- persister une AthleteConstraint ;
- recalculer la semaine courante lorsque cette contrainte peut
  influencer le planning.

Le repository reste volontairement ignorant du moteur de coaching.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from opencoach.coaching.generation import (
    CurrentWeekPlanningService,
)
from opencoach.database.repositories.athlete_constraint import (
    AthleteConstraintRepository,
)
from opencoach.models import AthleteConstraint


def current_week_bounds(
    reference_date: date,
) -> tuple[
    date,
    date,
]:
    """Retourne les bornes lundi-dimanche de la semaine courante."""

    week_start = (
        reference_date
        - timedelta(
            days=reference_date.weekday()
        )
    )

    return (
        week_start,
        week_start + timedelta(days=6),
    )


def constraint_affects_current_week(
    *,
    constraint: AthleteConstraint,
    reference_date: date,
) -> bool:
    """Indique si une contrainte chevauche la semaine courante."""

    week_start, week_end = (
        current_week_bounds(
            reference_date
        )
    )

    return (
        constraint.start_date <= week_end
        and constraint.end_date >= week_start
    )


@dataclass(slots=True)
class AthleteConstraintPlanningService:
    """Persiste les contraintes et actualise le coaching courant."""

    repository: AthleteConstraintRepository

    current_week_planning_service: (
        CurrentWeekPlanningService
    )

    def save(
        self,
        *,
        athlete_profile_id: UUID,
        constraint: AthleteConstraint,
        reference_date: date,
    ) -> AthleteConstraint:
        """Crée ou met à jour une contrainte temporaire."""

        previous = (
            self.repository.get_constraint(
                athlete_profile_id,
                constraint.id,
            )
        )

        saved = (
            self.repository.save_constraint(
                athlete_profile_id,
                constraint,
            )
        )

        if self._change_affects_current_week(
            previous=previous,
            current=saved,
            reference_date=reference_date,
        ):
            self._refresh(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                reference_date=(
                    reference_date
                ),
                reason=(
                    self._refresh_reason(
                        saved
                    )
                ),
            )

        return saved

    def delete(
        self,
        *,
        athlete_profile_id: UUID,
        constraint_id: UUID,
        reference_date: date,
    ) -> None:
        """Supprime une contrainte et recalcule si nécessaire."""

        existing = (
            self.repository.get_constraint(
                athlete_profile_id,
                constraint_id,
            )
        )

        self.repository.delete_constraint(
            athlete_profile_id,
            constraint_id,
        )

        if (
            existing is not None
            and constraint_affects_current_week(
                constraint=existing,
                reference_date=(
                    reference_date
                ),
            )
        ):
            self._refresh(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                reference_date=(
                    reference_date
                ),
                reason=(
                    "contrainte athlète supprimée"
                ),
            )

    def _change_affects_current_week(
        self,
        *,
        previous: AthleteConstraint | None,
        current: AthleteConstraint,
        reference_date: date,
    ) -> bool:
        """Vérifie l'ancien et le nouvel état d'une contrainte."""

        if constraint_affects_current_week(
            constraint=current,
            reference_date=reference_date,
        ):
            return True

        if (
            previous is not None
            and constraint_affects_current_week(
                constraint=previous,
                reference_date=reference_date,
            )
        ):
            return True

        return False

    def _refresh(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
        reason: str,
    ) -> None:
        """Demande une reconstruction de la semaine actuelle."""

        self.current_week_planning_service.refresh(
            athlete_profile_id=(
                athlete_profile_id
            ),
            reference_date=(
                reference_date
            ),
            additional_context=(
                reason,
            ),
        )

    @staticmethod
    def _refresh_reason(
        constraint: AthleteConstraint,
    ) -> str:
        """Produit une raison métier compacte pour la régénération."""

        reasons = {
            "illness": (
                "maladie ou problème de santé temporaire"
            ),
            "injury": (
                "blessure ou limitation physique temporaire"
            ),
            "work": (
                "contrainte professionnelle"
            ),
            "travel": (
                "déplacement ou voyage"
            ),
            "family": (
                "contrainte familiale"
            ),
            "personal": (
                "contrainte personnelle"
            ),
            "other": (
                "contrainte temporaire"
            ),
        }

        return reasons.get(
            constraint.constraint_type,
            "contrainte temporaire",
        )
