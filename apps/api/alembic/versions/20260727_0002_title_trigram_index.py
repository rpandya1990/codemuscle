"""Add trigram support for problem-title duplicate detection.

Revision ID: 20260727_0002
Revises: 20260727_0001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260727_0002"
down_revision: str | None = "20260727_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX ix_problems_normalized_title_trgm "
        "ON problems USING gin (normalized_title gin_trgm_ops)"
    )


def downgrade() -> None:
    op.drop_index("ix_problems_normalized_title_trgm", table_name="problems")
