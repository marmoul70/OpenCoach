"""Affectation du matériel réellement utilisé pour une activité."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from opencoach.database.base import Base


class ActivityEquipmentAssignment(Base):
    """Matériel kilométrique réellement utilisé pour une activité.

    Une activité ne peut posséder qu'une affectation kilométrique :
    soit une chaussure, soit un vélo.

    La distance est stockée comme snapshot de l'activité afin que les
    recalculs de kilométrage puissent être déterministes et idempotents.
    """

    __tablename__ = "activity_equipment_assignments"

    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            name="uq_activity_equipment_assignment_activity",
        ),
        CheckConstraint(
            """
            (
                shoe_id IS NOT NULL
                AND bike_id IS NULL
            )
            OR
            (
                shoe_id IS NULL
                AND bike_id IS NOT NULL
            )
            """,
            name="ck_activity_equipment_exactly_one_equipment",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    athlete_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "athlete_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    activity_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "activities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    shoe_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "athlete_shoes.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    bike_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "athlete_bikes.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    distance_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    assignment_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="automatic",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
