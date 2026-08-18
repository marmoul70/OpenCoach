from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
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


class DailyContext(Base):
    """Contexte subjectif quotidien renseigné par l'athlète."""

    __tablename__ = "daily_contexts"

    __table_args__ = (
        UniqueConstraint(
            "athlete_profile_id",
            "date",
            name="uq_daily_context_profile_date",
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

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    fatigue_subjective: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    pain_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    illness_status: Mapped[str] = mapped_column(
        String(30),
        default="none",
        nullable=False,
    )

    treatment_impact: Mapped[str] = mapped_column(
        String(30),
        default="none",
        nullable=False,
    )

    motivation: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
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
        back_populates="daily_contexts",
    )
