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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opencoach.database.base import Base

if TYPE_CHECKING:
    from opencoach.database.models.athlete_profile import AthleteProfile


class WellnessDaily(Base):
    """Données quotidiennes de forme et récupération."""

    __tablename__ = "wellness_daily"

    __table_args__ = (
        UniqueConstraint(
            "athlete_profile_id",
            "provider",
            "date",
            name="uq_wellness_daily_profile_provider_date",
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

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    fitness_ctl: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    fatigue_atl: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    ramp_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resting_hr: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    hrv: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    sleep_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    sleep_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    sleep_quality: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    avg_sleeping_hr: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    spo2: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    steps: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    provider_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
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
        back_populates="wellness_days",
    )
