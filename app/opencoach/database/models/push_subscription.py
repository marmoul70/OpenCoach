from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from opencoach.database.base import Base


class PushSubscription(Base):
    """Abonnement Web Push d'un appareil OpenCoach."""

    __tablename__ = "push_subscriptions"

    __table_args__ = (
        UniqueConstraint(
            "endpoint",
            name="uq_push_subscription_endpoint",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    endpoint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    p256dh: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    auth: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    badge_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    system_notifications_enabled: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    system_sync_errors_enabled: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    system_backup_errors_enabled: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    training_reminder_enabled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
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
