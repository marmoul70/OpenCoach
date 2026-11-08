from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from opencoach.database.base import Base


class AICoachPreference(Base):
    """Préférences personnelles du coach IA."""

    __tablename__ = "ai_coach_preferences"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    personality: Mapped[str] = mapped_column(String(24), nullable=False, default="balanced")
    firmness: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    motivation: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    response_style: Mapped[str] = mapped_column(String(24), nullable=False, default="detailed")
    custom_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
