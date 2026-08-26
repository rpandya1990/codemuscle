"""Scale revision defaults for a large problem library.

Revision ID: 20260825_0009
Revises: 20260825_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260825_0009"
down_revision: str | None = "20260825_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_INTERVALS = "[1, 3, 7, 14, 30, 60]"
NEW_INTERVALS = "[3, 10, 30, 90, 180, 365]"


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE user_preferences "
            "SET successful_intervals = CAST(:new_intervals AS JSON) "
            "WHERE CAST(successful_intervals AS JSONB) = CAST(:old_intervals AS JSONB)"
        ).bindparams(new_intervals=NEW_INTERVALS, old_intervals=OLD_INTERVALS)
    )
    op.alter_column("user_preferences", "successful_intervals", server_default=NEW_INTERVALS)


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE user_preferences "
            "SET successful_intervals = CAST(:old_intervals AS JSON) "
            "WHERE CAST(successful_intervals AS JSONB) = CAST(:new_intervals AS JSONB)"
        ).bindparams(new_intervals=NEW_INTERVALS, old_intervals=OLD_INTERVALS)
    )
    op.alter_column("user_preferences", "successful_intervals", server_default=OLD_INTERVALS)
