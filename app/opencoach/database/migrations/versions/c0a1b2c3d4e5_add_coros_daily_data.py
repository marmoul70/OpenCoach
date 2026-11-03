"""add COROS daily health snapshots

Revision ID: c0a1b2c3d4e5
Revises: f7188bb7dc22
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "f7188bb7dc22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coros_daily_data",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_profile_id", sa.Uuid(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "athlete_profile_id",
            "metric_date",
            "category",
            name="uq_coros_daily_data_profile_date_category",
        ),
    )
    op.create_index(
        op.f("ix_coros_daily_data_athlete_profile_id"),
        "coros_daily_data",
        ["athlete_profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_coros_daily_data_metric_date"),
        "coros_daily_data",
        ["metric_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_coros_daily_data_metric_date"),
        table_name="coros_daily_data",
    )
    op.drop_index(
        op.f("ix_coros_daily_data_athlete_profile_id"),
        table_name="coros_daily_data",
    )
    op.drop_table("coros_daily_data")
