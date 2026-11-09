"""Propositions de mise à jour du profil soumises à confirmation explicite."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from opencoach.database.base import Base


class AIDataProposal(Base):
    """Valeur de profil proposée par le coach, jamais appliquée sans confirmation."""

    __tablename__ = "ai_data_proposals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    athlete_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("athlete_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_key: Mapped[str] = mapped_column(String(80), nullable=False)
    proposed_value: Mapped[object] = mapped_column(JSON, nullable=False)
    existing_value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
