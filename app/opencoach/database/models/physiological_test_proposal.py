"""Persistance SQLAlchemy des propositions de tests physiologiques."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    JSON,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from opencoach.database.base import Base


class PhysiologicalTestProposal(Base):
    """Proposition de test soumise à l'athlète."""

    __tablename__ = (
        "physiological_test_proposals"
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

    target_session_id: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "training_sessions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    protocol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    target_metrics: Mapped[
        list[str]
    ] = mapped_column(
        JSON,
        nullable=False,
    )

    proposed_date: Mapped[date] = mapped_column(
        Date,
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

    replacement_stimulus: Mapped[
        str
    ] = mapped_column(
        String(100),
        nullable=False,
    )

    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
    )
