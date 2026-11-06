from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from opencoach.database.base import Base


class Notification(Base):
    """Notification métier persistée dans la boîte de réception utilisateur."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index(
            "ix_notifications_user_created",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_notifications_user_read",
            "user_id",
            "read_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="system",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
    )
    url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
