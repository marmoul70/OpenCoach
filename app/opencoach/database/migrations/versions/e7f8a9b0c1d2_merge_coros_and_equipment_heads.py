"""merge COROS and equipment migration heads

Revision ID: e7f8a9b0c1d2
Revises: b82f19c3d5a1, d1e2f3a4b5c6
Create Date: 2026-11-02
"""

from typing import Sequence, Union

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = (
    "b82f19c3d5a1",
    "d1e2f3a4b5c6",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
