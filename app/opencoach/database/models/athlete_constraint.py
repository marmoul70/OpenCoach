from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from opencoach.database.base import Base


if TYPE_CHECKING:
    from opencoach.database.models.athlete_profile import (
        AthleteProfile,
    )


class AthleteConstraint(Base):
    """Contrainte temporaire affectant la disponibilité d'un athlète."""

    __tablename__ = "athlete_constraints"

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

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    constraint_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    availability: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    running_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    cross_training_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    max_duration_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(4000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    athlete_profile: Mapped["AthleteProfile"] = relationship(
        back_populates="constraints",
    )
