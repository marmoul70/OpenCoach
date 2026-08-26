"""Persistance SQLAlchemy des propositions d'adaptation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from opencoach.database.base import Base


class DailyAdaptationProposal(Base):
    """Proposition du coach liée à un check-in quotidien."""

    __tablename__ = "daily_adaptation_proposals"

    __table_args__ = (
        UniqueConstraint(
            "checkin_id",
            name="uq_daily_adaptation_proposals_checkin",
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

    checkin_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "daily_checkins.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    recommendation: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
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
