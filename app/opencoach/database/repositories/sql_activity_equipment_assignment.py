"""Persistance des affectations activité ↔ matériel."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models.activity import (
    Activity as ActivityModel,
)
from opencoach.database.models.activity_equipment_assignment import (
    ActivityEquipmentAssignment,
)
from opencoach.database.models.bike import Bike
from opencoach.database.models.shoe import Shoe


class ActivityEquipmentAssignmentError(
    RuntimeError
):
    """Erreur de persistance d'une affectation matériel."""


class SqlActivityEquipmentAssignmentRepository:
    """Repository SQL des affectations matériel."""

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def get_for_activity(
        self,
        *,
        athlete_profile_id: UUID,
        activity_id: UUID,
    ) -> ActivityEquipmentAssignment | None:
        """Charge l'affectation d'une activité du profil."""

        return self.db.scalar(
            select(
                ActivityEquipmentAssignment
            ).where(
                ActivityEquipmentAssignment.athlete_profile_id
                == athlete_profile_id,
                ActivityEquipmentAssignment.activity_id
                == activity_id,
            )
        )

    def assign_shoe(
        self,
        *,
        athlete_profile_id: UUID,
        activity_id: UUID,
        shoe_id: str,
        distance_km: float,
        assignment_source: str,
    ) -> ActivityEquipmentAssignment:
        """Affecte une chaussure à une activité.

        L'opération est un upsert déterministe :
        rappeler la méthode pour la même activité met à jour
        l'affectation existante au lieu d'ajouter une ligne.
        """

        self._validate_source(
            assignment_source,
        )

        self._require_activity(
            athlete_profile_id=athlete_profile_id,
            activity_id=activity_id,
        )

        self._require_shoe(
            athlete_profile_id=athlete_profile_id,
            shoe_id=shoe_id,
        )

        assignment = self.get_for_activity(
            athlete_profile_id=athlete_profile_id,
            activity_id=activity_id,
        )

        if assignment is None:
            assignment = ActivityEquipmentAssignment(
                athlete_profile_id=athlete_profile_id,
                activity_id=activity_id,
                shoe_id=shoe_id,
                bike_id=None,
                distance_km=max(
                    0.0,
                    float(distance_km),
                ),
                assignment_source=assignment_source,
            )
            self.db.add(
                assignment
            )
        else:
            assignment.shoe_id = shoe_id
            assignment.bike_id = None
            assignment.distance_km = max(
                0.0,
                float(distance_km),
            )
            assignment.assignment_source = (
                assignment_source
            )

        self.db.flush()

        return assignment

    def assign_bike(
        self,
        *,
        athlete_profile_id: UUID,
        activity_id: UUID,
        bike_id: str,
        distance_km: float,
        assignment_source: str,
    ) -> ActivityEquipmentAssignment:
        """Affecte un vélo à une activité de manière idempotente."""

        self._validate_source(
            assignment_source,
        )

        self._require_activity(
            athlete_profile_id=athlete_profile_id,
            activity_id=activity_id,
        )

        self._require_bike(
            athlete_profile_id=athlete_profile_id,
            bike_id=bike_id,
        )

        assignment = self.get_for_activity(
            athlete_profile_id=athlete_profile_id,
            activity_id=activity_id,
        )

        if assignment is None:
            assignment = ActivityEquipmentAssignment(
                athlete_profile_id=athlete_profile_id,
                activity_id=activity_id,
                shoe_id=None,
                bike_id=bike_id,
                distance_km=max(
                    0.0,
                    float(distance_km),
                ),
                assignment_source=assignment_source,
            )
            self.db.add(
                assignment
            )
        else:
            assignment.shoe_id = None
            assignment.bike_id = bike_id
            assignment.distance_km = max(
                0.0,
                float(distance_km),
            )
            assignment.assignment_source = (
                assignment_source
            )

        self.db.flush()

        return assignment

    def _require_activity(
        self,
        *,
        athlete_profile_id: UUID,
        activity_id: UUID,
    ) -> None:
        activity = self.db.scalar(
            select(
                ActivityModel.id
            ).where(
                ActivityModel.id
                == activity_id,
                ActivityModel.athlete_profile_id
                == athlete_profile_id,
            )
        )

        if activity is None:
            raise ActivityEquipmentAssignmentError(
                "Activité introuvable pour ce profil."
            )

    def _require_shoe(
        self,
        *,
        athlete_profile_id: UUID,
        shoe_id: str,
    ) -> None:
        shoe = self.db.scalar(
            select(
                Shoe.id
            ).where(
                Shoe.id == shoe_id,
                Shoe.athlete_profile_id
                == athlete_profile_id,
            )
        )

        if shoe is None:
            raise ActivityEquipmentAssignmentError(
                "Chaussure introuvable pour ce profil."
            )

    def _require_bike(
        self,
        *,
        athlete_profile_id: UUID,
        bike_id: str,
    ) -> None:
        bike = self.db.scalar(
            select(
                Bike.id
            ).where(
                Bike.id == bike_id,
                Bike.athlete_profile_id
                == athlete_profile_id,
            )
        )

        if bike is None:
            raise ActivityEquipmentAssignmentError(
                "Vélo introuvable pour ce profil."
            )

    @staticmethod
    def _validate_source(
        source: str,
    ) -> None:
        if source not in {
            "automatic",
            "manual",
        }:
            raise ActivityEquipmentAssignmentError(
                "Source d'affectation invalide."
            )
