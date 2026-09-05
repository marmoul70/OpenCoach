"""add training session planning importance

Revision ID: 2adb0141bfde
Revises: 0a2a7116a84e
Create Date: 2026-09-05T14:44:07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2adb0141bfde"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "0a2a7116a84e"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    """Ajoute l'importance structurelle du planning."""

    op.add_column(
        "training_sessions",
        sa.Column(
            "planning_importance",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.create_index(
        op.f(
            "ix_training_sessions_planning_importance"
        ),
        "training_sessions",
        ["planning_importance"],
        unique=False,
    )


def downgrade() -> None:
    """Supprime l'importance structurelle du planning."""

    op.drop_index(
        op.f(
            "ix_training_sessions_planning_importance"
        ),
        table_name="training_sessions",
    )

    op.drop_column(
        "training_sessions",
        "planning_importance",
    )
