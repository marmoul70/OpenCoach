"""Recalcul kilométrique des équipements OpenCoach.

Le kilométrage courant n'est jamais incrémenté directement.

Il est dérivé de manière idempotente :

    baseline historique
    + somme des activités affectées dans OpenCoach

Le service ne commit jamais lui-même la transaction.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from opencoach.database.models.activity_equipment_assignment import (
    ActivityEquipmentAssignment,
)
from opencoach.database.models.bike import Bike
from opencoach.database.models.shoe import Shoe


class EquipmentMileageError(RuntimeError):
    """Impossible de recalculer le kilométrage matériel."""


class EquipmentMileageService:
    """Recalcule les compteurs à partir des affectations persistées."""

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def recalculate_shoe(
        self,
        *,
        athlete_profile_id: UUID,
        shoe_id: str,
    ) -> float:
        """Recalcule une paire de chaussures du profil."""

        shoe = (
            self.db.query(Shoe)
            .filter(
                Shoe.id == shoe_id,
                Shoe.athlete_profile_id
                == athlete_profile_id,
            )
            .one_or_none()
        )

        if shoe is None:
            raise EquipmentMileageError(
                "La chaussure est introuvable "
                "pour ce profil."
            )

        assigned_distance = (
            self.db.query(
                func.coalesce(
                    func.sum(
                        ActivityEquipmentAssignment.distance_km
                    ),
                    0.0,
                )
            )
            .filter(
                ActivityEquipmentAssignment.athlete_profile_id
                == athlete_profile_id,
                ActivityEquipmentAssignment.shoe_id
                == shoe_id,
            )
            .scalar()
        )

        total = (
            float(shoe.baseline_distance_km or 0.0)
            + float(assigned_distance or 0.0)
        )

        shoe.distance_km = total
        self.db.flush()

        return total

    def recalculate_bike(
        self,
        *,
        athlete_profile_id: UUID,
        bike_id: str,
    ) -> float:
        """Recalcule un vélo du profil."""

        bike = (
            self.db.query(Bike)
            .filter(
                Bike.id == bike_id,
                Bike.athlete_profile_id
                == athlete_profile_id,
            )
            .one_or_none()
        )

        if bike is None:
            raise EquipmentMileageError(
                "Le vélo est introuvable "
                "pour ce profil."
            )

        assigned_distance = (
            self.db.query(
                func.coalesce(
                    func.sum(
                        ActivityEquipmentAssignment.distance_km
                    ),
                    0.0,
                )
            )
            .filter(
                ActivityEquipmentAssignment.athlete_profile_id
                == athlete_profile_id,
                ActivityEquipmentAssignment.bike_id
                == bike_id,
            )
            .scalar()
        )

        total = (
            float(bike.baseline_distance_km or 0.0)
            + float(assigned_distance or 0.0)
        )

        bike.distance_km = total
        self.db.flush()

        return total
