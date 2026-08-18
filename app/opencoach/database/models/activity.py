from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
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


class Activity(Base):
    """Activité sportive importée depuis un fournisseur externe."""

    __tablename__ = "activities"

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_activity_id",
            name="uq_activities_provider_activity",
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

    # Identification de la source
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    provider_activity_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    source_file_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Informations générales
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sport_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    start_at_local: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    device_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Durée / distance
    elapsed_time_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    moving_time_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    distance_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_gain_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_loss_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Vitesse
    average_speed_mps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_speed_mps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Fréquence cardiaque
    average_heart_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_heart_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    lactate_threshold_heart_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    athlete_max_heart_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Dynamique / puissance
    average_cadence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_stride_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_stance_time_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_vertical_oscillation_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_power_w: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Altitude / température
    average_altitude_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    min_altitude_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_altitude_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    min_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    calories: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Charge d'entraînement Intervals.icu
    training_load: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    fitness_ctl: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    fatigue_atl: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    hr_load: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    intensity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    feel: Mapped[int | None] = mapped_column(
        Integer,
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
        back_populates="activities",
    )