from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from opencoach.database.base import Base


class CorosSyncLock(Base):
    """Verrou DB empêchant deux imports COROS simultanés par athlète."""

    __tablename__ = "coros_sync_locks"
    __table_args__ = (
        UniqueConstraint("athlete_profile_id", name="uq_coros_sync_lock_profile"),
    )

    athlete_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("athlete_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    job_id: Mapped[str] = mapped_column(String(36), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )
