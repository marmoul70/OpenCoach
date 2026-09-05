"""Persistance SQL du débrief hebdomadaire."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from opencoach.database.base import Base


class WeeklyDebriefRecord(Base):
    """Snapshot immutable d'une semaine d'entraînement clôturée."""

    __tablename__ = "weekly_debriefs"

    __table_args__ = (
        UniqueConstraint(
            "athlete_profile_id",
            "week_start",
            name=(
                "uq_weekly_debriefs_"
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

    facts_payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    verdict: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    adaptation_direction: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    overall_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    adherence_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    duration_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    load_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    key_sessions_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    intensity_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completion_ratio: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    duration_ratio: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    load_ratio: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    headline: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    analysis: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    strengths: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    warnings: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    adaptation_payload: Mapped[
        dict | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    recalculated_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime,
        nullable=True,
    )

    planning_updated_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime,
        nullable=True,
    )

    notification_sent_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime,
        nullable=True,
    )
