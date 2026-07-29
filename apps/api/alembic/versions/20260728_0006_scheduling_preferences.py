"""Add configurable successful revision intervals.

Revision ID: 20260728_0006
Revises: 20260728_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260728_0006"
down_revision: str | None = "20260728_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_preferences",
        sa.Column(
            "successful_intervals",
            sa.JSON(),
            server_default="[1, 3, 7, 14, 30, 60]",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("user_preferences", "successful_intervals")
