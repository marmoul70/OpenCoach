from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
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


class PhysiologicalMeasurement(Base):
    """Mesure physiologique historisée d'un athlète."""

    __tablename__ = "physiological_measurements"

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

    metric: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    measured_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    protocol: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
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
        back_populates="physiological_measurements",
    )
