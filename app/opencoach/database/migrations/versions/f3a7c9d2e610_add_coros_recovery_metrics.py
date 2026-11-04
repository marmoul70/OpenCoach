"""Add COROS recovery detail metrics to daily wellness.

Revision ID: f3a7c9d2e610
Revises: e7f8a9b0c1d2
Create Date: 2026-11-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a7c9d2e610"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("wellness_daily", sa.Column("stress_avg", sa.Float(), nullable=True))
    op.add_column("wellness_daily", sa.Column("hrv_baseline", sa.Float(), nullable=True))
    op.add_column("wellness_daily", sa.Column("sleep_deep_seconds", sa.Integer(), nullable=True))
    op.add_column("wellness_daily", sa.Column("sleep_light_seconds", sa.Integer(), nullable=True))
    op.add_column("wellness_daily", sa.Column("sleep_rem_seconds", sa.Integer(), nullable=True))
    op.add_column("wellness_daily", sa.Column("sleep_awake_seconds", sa.Integer(), nullable=True))
    op.add_column("wellness_daily", sa.Column("min_sleeping_hr", sa.Float(), nullable=True))
    op.add_column("wellness_daily", sa.Column("max_sleeping_hr", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("wellness_daily", "max_sleeping_hr")
    op.drop_column("wellness_daily", "min_sleeping_hr")
    op.drop_column("wellness_daily", "sleep_awake_seconds")
    op.drop_column("wellness_daily", "sleep_rem_seconds")
    op.drop_column("wellness_daily", "sleep_light_seconds")
    op.drop_column("wellness_daily", "sleep_deep_seconds")
    op.drop_column("wellness_daily", "hrv_baseline")
    op.drop_column("wellness_daily", "stress_avg")
