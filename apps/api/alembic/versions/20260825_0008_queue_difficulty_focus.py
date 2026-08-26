"""Add difficulty focus to daily queues.

Revision ID: 20260825_0008
Revises: 20260728_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260825_0008"
down_revision: str | None = "20260728_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "queue_sessions",
        sa.Column("difficulty_focus", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.alter_column("queue_sessions", "difficulty_focus", server_default=None)


def downgrade() -> None:
    op.drop_column("queue_sessions", "difficulty_focus")
