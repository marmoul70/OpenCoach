"""add equipment metadata

Revision ID: 8c366e314170
Revises: da950a25c05f
Create Date: 2026-09-06 00:33:52.953860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c366e314170'
down_revision: Union[str, Sequence[str], None] = 'da950a25c05f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajoute les métadonnées de suivi des équipements."""
    op.add_column(
        "athlete_shoes",
        sa.Column(
            "category",
            sa.String(length=50),
            nullable=True,
        ),
    )
    op.add_column(
        "athlete_shoes",
        sa.Column(
            "preferred",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "athlete_shoes",
        sa.Column(
            "warning_distance_km",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "athlete_bikes",
        sa.Column(
            "category",
            sa.String(length=50),
            nullable=True,
        ),
    )
    op.add_column(
        "athlete_bikes",
        sa.Column(
            "preferred",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "athlete_bikes",
        sa.Column(
            "maintenance_distance_km",
            sa.Float(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Retire les métadonnées de suivi des équipements."""
    op.drop_column(
        "athlete_bikes",
        "maintenance_distance_km",
    )
    op.drop_column(
        "athlete_bikes",
        "preferred",
    )
    op.drop_column(
        "athlete_bikes",
        "category",
    )

    op.drop_column(
        "athlete_shoes",
        "warning_distance_km",
    )
    op.drop_column(
        "athlete_shoes",
        "preferred",
    )
    op.drop_column(
        "athlete_shoes",
        "category",
    )
