"""Add a solution to problems.

Revision ID: 20260906_0013
Revises: 20260830_0012
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260906_0013"
down_revision: str | None = "20260830_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("solution", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("problems", "solution")
