"""Add import jobs, rows, and problem traceability.

Revision ID: 20260728_0003
Revises: 20260727_0002
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260728_0003"
down_revision: str | None = "20260727_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("stored_filename", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=False),
        sa.Column("mapping", sa.JSON(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("valid_rows", sa.Integer(), nullable=False),
        sa.Column("invalid_rows", sa.Integer(), nullable=False),
        sa.Column("duplicate_rows", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_jobs"),
    )
    op.create_table(
        "import_rows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_job_id", sa.Uuid(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=False),
        sa.Column("parsed_data", sa.JSON()),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("duplicate_problem_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_problem_id", sa.Uuid()),
        sa.Column("retry_notes", sa.Text()),
        sa.ForeignKeyConstraint(
            ["created_problem_id"],
            ["problems.id"],
            name="fk_import_rows_created_problem_id_problems",
        ),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_jobs.id"],
            ondelete="CASCADE",
            name="fk_import_rows_import_job_id_import_jobs",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_rows"),
    )
    op.create_index("ix_import_rows_import_job_id", "import_rows", ["import_job_id"])
    op.add_column("problems", sa.Column("import_job_id", sa.Uuid()))
    op.add_column("problems", sa.Column("legacy_import_metadata", sa.JSON()))
    op.create_foreign_key(
        "fk_problems_import_job_id_import_jobs",
        "problems",
        "import_jobs",
        ["import_job_id"],
        ["id"],
    )
    op.create_index("ix_problems_import_job_id", "problems", ["import_job_id"])


def downgrade() -> None:
    op.drop_index("ix_problems_import_job_id", table_name="problems")
    op.drop_constraint("fk_problems_import_job_id_import_jobs", "problems", type_="foreignkey")
    op.drop_column("problems", "import_job_id")
    op.drop_column("problems", "legacy_import_metadata")
    op.drop_table("import_rows")
    op.drop_table("import_jobs")
