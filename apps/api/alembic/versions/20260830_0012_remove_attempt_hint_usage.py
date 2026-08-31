"""Remove redundant attempt hint usage.

Revision ID: 20260830_0012
Revises: 20260827_0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260830_0012"
down_revision: str | None = "20260827_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("attempts", "hint_usage")
    postgresql.ENUM(name="hint_usage").drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    hint_usage = postgresql.ENUM(
        "NONE",
        "SMALL",
        "SIGNIFICANT",
        "SOLUTION_VIEWED",
        "NOT_APPLICABLE",
        name="hint_usage",
    )
    hint_usage.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "attempts",
        sa.Column(
            "hint_usage",
            hint_usage,
            nullable=False,
            server_default="NOT_APPLICABLE",
        ),
    )
    op.alter_column("attempts", "hint_usage", server_default=None)
