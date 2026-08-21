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
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from opencoach.database.base import Base


if TYPE_CHECKING:
    from opencoach.database.models.activity import Activity
    from opencoach.database.models.athlete_profile import (
        AthleteProfile,
    )


class Race(Base):
    """Course planifiée ou réalisée par un athlète."""

    __tablename__ = "races"

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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(255),
        default="",
        nullable=False,
    )

    race_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        default="training",
        nullable=False,
        index=True,
    )

    distance_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    elevation_gain_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    target_time_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="planned",
        nullable=False,
        index=True,
    )

    actual_distance_km: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    actual_elevation_gain_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    actual_time_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    ranking: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    notes: Mapped[str] = mapped_column(
        String(4000),
        default="",
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
        back_populates="races",
    )

    activity: Mapped["Activity | None"] = relationship()
