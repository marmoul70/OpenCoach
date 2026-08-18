from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opencoach.database.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opencoach.database.models.activity import Activity
    from opencoach.database.models.bike import Bike
    from opencoach.database.models.shoe import Shoe
    from opencoach.database.models.watch import Watch
    from opencoach.database.models.wellness import WellnessDaily

class AthleteProfile(Base):
    """Profil sportif associé à un compte utilisateur."""

    __tablename__ = "athlete_profiles"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Identité
    first_name: Mapped[str] = mapped_column(
        String(100),
        default="",
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        default="",
        nullable=False,
    )

    birth_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    gender: Mapped[str] = mapped_column(
        String(30),
        default="unspecified",
        nullable=False,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Physique
    height_cm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    weight_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Physiologie
    max_heart_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    resting_heart_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    vma: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    threshold_heart_rate_1: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    threshold_heart_rate_2: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Entraînement
    weekly_sessions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    weekly_duration_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    weekly_distance_km: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    available_days: Mapped[list[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    fatigue_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    experience: Mapped[str] = mapped_column(
        String(30),
        default="beginner",
        nullable=False,
    )

    # Localisation
    location_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Nutrition
    carbohydrates_per_hour: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    fluids_per_hour: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    sodium_per_hour: Mapped[float | None] = mapped_column(
        Float,
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

    wellness_days: Mapped[list["WellnessDaily"]] = relationship(
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )

    activities: Mapped[list["Activity"]] = relationship(
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )

    shoes: Mapped[list["Shoe"]] = relationship(
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )

    bikes: Mapped[list["Bike"]] = relationship(
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )

    watches: Mapped[list["Watch"]] = relationship(
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )

    user: Mapped["User"] = relationship(
        back_populates="athlete_profile",
    )