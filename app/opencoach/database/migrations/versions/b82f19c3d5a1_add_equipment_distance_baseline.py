"""add equipment distance baseline

Revision ID: b82f19c3d5a1
Revises: f4c2a91d8e73
Create Date: 2026-09-06

Le baseline représente le kilométrage acquis avant que
les affectations d'activités OpenCoach ne deviennent la
source du kilométrage automatique.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b82f19c3d5a1"
down_revision: Union[str, Sequence[str], None] = (
    "f4c2a91d8e73"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Initialise le baseline depuis le kilométrage existant."""

    op.add_column(
        "athlete_shoes",
        sa.Column(
            "baseline_distance_km",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "athlete_bikes",
        sa.Column(
            "baseline_distance_km",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.execute(
        """
        UPDATE athlete_shoes
        SET baseline_distance_km = distance_km
        """
    )

    op.execute(
        """
        UPDATE athlete_bikes
        SET baseline_distance_km = distance_km
        """
    )


def downgrade() -> None:
    """Retire les baselines kilométriques."""

    op.drop_column(
        "athlete_bikes",
        "baseline_distance_km",
    )

    op.drop_column(
        "athlete_shoes",
        "baseline_distance_km",
    )
