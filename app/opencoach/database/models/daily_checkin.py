"""Persistance SQLAlchemy des check-ins quotidiens."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from opencoach.database.base import Base


class DailyCheckIn(Base):
    """Check-in quotidien déclaré par un athlète."""

    __tablename__ = "daily_checkins"

    __table_args__ = (
        UniqueConstraint(
            "athlete_profile_id",
            "date",
            name="uq_daily_checkins_athlete_date",
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

    energy_rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    pain_wellness_rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    illness: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    unavailable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    pain_locations: Mapped[list[dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    note: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
