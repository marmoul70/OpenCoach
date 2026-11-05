"""Add daily average, minimum and maximum heart rate to wellness.

Revision ID: 3b7d9a1c5e20
Revises: f3a7c9d2e610
Create Date: 2026-11-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3b7d9a1c5e20"
down_revision: Union[str, Sequence[str], None] = "f3a7c9d2e610"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("wellness_daily", sa.Column("avg_hr", sa.Float(), nullable=True))
    op.add_column("wellness_daily", sa.Column("min_hr", sa.Float(), nullable=True))
    op.add_column("wellness_daily", sa.Column("max_hr", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("wellness_daily", "max_hr")
    op.drop_column("wellness_daily", "min_hr")
    op.drop_column("wellness_daily", "avg_hr")
