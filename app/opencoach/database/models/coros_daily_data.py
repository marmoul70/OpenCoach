from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opencoach.database.base import Base

if TYPE_CHECKING:
    from opencoach.database.models.athlete_profile import AthleteProfile


class CorosDailyData(Base):
    """Snapshot quotidien des métriques COROS importées via MCP."""

    __tablename__ = "coros_daily_data"

    __table_args__ = (
        UniqueConstraint(
            "athlete_profile_id",
            "metric_date",
            "category",
            name="uq_coros_daily_data_profile_date_category",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    athlete_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("athlete_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    metric_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    imported_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    athlete_profile: Mapped["AthleteProfile"] = relationship()
