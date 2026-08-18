from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opencoach.database.base import Base


if TYPE_CHECKING:
    from opencoach.database.models.activity import Activity
    from opencoach.database.models.athlete_profile import (
        AthleteProfile,
    )


class TrainingSession(Base):
    """Séance d'entraînement planifiée."""

    __tablename__ = "training_sessions"

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

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    sport_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Run",
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(2000),
        default="",
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    distance_km: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_gain_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    intensity: Mapped[str] = mapped_column(
        String(100),
        default="",
        nullable=False,
    )

    heart_rate_zone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="planned",
        nullable=False,
    )

    activity_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "activities.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
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
        back_populates="training_sessions",
    )

    activity: Mapped["Activity | None"] = relationship()
