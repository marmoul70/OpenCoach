"""add training session sport type

Revision ID: a3e0e5652927
Revises: 81cea4b0abda
Create Date: 2026-08-18 17:42:53.024550

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3e0e5652927"
down_revision: Union[str, Sequence[str], None] = "81cea4b0abda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajoute le type de sport aux séances existantes."""

    op.add_column(
        "training_sessions",
        sa.Column(
            "sport_type",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE training_sessions
            SET sport_type = 'Run'
            WHERE sport_type IS NULL
            """
        )
    )

    with op.batch_alter_table(
        "training_sessions",
    ) as batch_op:
        batch_op.alter_column(
            "sport_type",
            existing_type=sa.String(length=100),
            nullable=False,
        )


def downgrade() -> None:
    """Supprime le type de sport des séances."""

    with op.batch_alter_table(
        "training_sessions",
    ) as batch_op:
        batch_op.drop_column(
            "sport_type",
        )