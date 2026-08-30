"""Persistance SQL d'un débriefing de séance."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
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


class SessionExecutionAnalysis(Base):
    """Analyse persistée d'une séance validée par l'athlète."""

    __tablename__ = "session_execution_analyses"

    __table_args__ = (
        UniqueConstraint(
            "training_session_id",
            name=(
                "uq_session_execution_analyses_"
                "training_session_id"
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

    training_session_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "training_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    activity_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "activities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    goal_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    overall_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    technical_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    objective: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    metrics: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    strengths: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    attention_points: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    debriefing: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    derived_results: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )
