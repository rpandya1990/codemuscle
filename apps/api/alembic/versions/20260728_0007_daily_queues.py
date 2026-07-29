"""Add persistent daily queues.

Revision ID: 20260728_0007
Revises: 20260728_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260728_0007"
down_revision: str | None = "20260728_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "queue_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("available_minutes", sa.Integer(), nullable=False),
        sa.Column("topic_focus_ids", sa.JSON(), nullable=False),
        sa.Column("requested_problem_count", sa.Integer()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_queue_sessions"),
    )
    op.create_table(
        "queue_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("queue_session_id", sa.Uuid(), nullable=False),
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("recommendation_score", sa.Float(), nullable=False),
        sa.Column("recommendation_reasons", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            ondelete="RESTRICT",
            name="fk_queue_items_problem_id_problems",
        ),
        sa.ForeignKeyConstraint(
            ["queue_session_id"],
            ["queue_sessions.id"],
            ondelete="CASCADE",
            name="fk_queue_items_queue_session_id_queue_sessions",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_queue_items"),
    )
    op.create_index(
        "ix_queue_items_session_position", "queue_items", ["queue_session_id", "position"]
    )


def downgrade() -> None:
    op.drop_table("queue_items")
    op.drop_table("queue_sessions")
