"""add planning key to training sessions

Revision ID: 72a1783bfc9f
Revises: aae290fc5415
Create Date: 2026-08-24 00:43:49.601025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72a1783bfc9f'
down_revision: Union[str, Sequence[str], None] = 'aae290fc5415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "training_sessions",
        sa.Column(
            "planning_key",
            sa.String(
                length=255,
            ),
            nullable=True,
        ),
    )

    op.create_index(
        op.f(
            "ix_training_sessions_planning_key"
        ),
        "training_sessions",
        [
            "planning_key",
        ],
        unique=False,
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f(
            "ix_training_sessions_planning_key"
        ),
        table_name="training_sessions",
    )

    op.drop_column(
        "training_sessions",
        "planning_key",
    )
    pass
