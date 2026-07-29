"""Remove the data import workflow.

Revision ID: 20260728_0004
Revises: 20260728_0003
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0004"
down_revision: str | None = "20260728_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_problems_import_job_id", table_name="problems")
    op.drop_constraint("fk_problems_import_job_id_import_jobs", "problems", type_="foreignkey")
    op.drop_column("problems", "import_job_id")
    op.drop_column("problems", "legacy_import_metadata")
    op.drop_table("import_rows")
    op.drop_table("import_jobs")


def downgrade() -> None:
    # Revision 0005 owns restoration. Downgrading the historical removal is unsupported.
    raise RuntimeError("Downgrade to the removed import schema is unsupported; upgrade to 0005.")
