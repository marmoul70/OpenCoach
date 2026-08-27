from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
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


class WeeklyTrainingPlan(Base):
    """Référence persistante d'une semaine d'entraînement."""

    __tablename__ = "weekly_training_plans"

    __table_args__ = (
        UniqueConstraint(
            "athlete_profile_id",
            "week_start",
            name=(
                "uq_weekly_training_plans_"
                "athlete_week_start"
            ),
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

    week_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    week_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    phase: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    week_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    phase_week_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    target_load: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    load_min: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    load_max: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reference_duration_minutes: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    target_duration_minutes: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    long_endurance_reference_minutes: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    schedule_pressure: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    athlete_schedule_constrained: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
    )

    athlete_profile: Mapped[
        "AthleteProfile"
    ] = relationship(
        back_populates="weekly_training_plans",
    )
