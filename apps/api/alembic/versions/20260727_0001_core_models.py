"""Create workspace preferences and core models.

Revision ID: 20260727_0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260727_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

difficulty = postgresql.ENUM(
    "EASY", "MEDIUM", "HARD", "UNKNOWN", name="difficulty", create_type=False
)
mastery_state = postgresql.ENUM(
    "NEW",
    "LEARNING",
    "FRAGILE",
    "RETAINED",
    "MASTERED",
    "NEEDS_RELEARNING",
    "ARCHIVED",
    name="mastery_state",
    create_type=False,
)
attempt_outcome = postgresql.ENUM(
    "SOLVED_INDEPENDENTLY",
    "SOLVED_SMALL_HINT",
    "SOLVED_SIGNIFICANT_HELP",
    "UNDERSTOOD_AFTER_SOLUTION",
    "FAILED",
    "SKIPPED",
    name="attempt_outcome",
    create_type=False,
)
hint_usage = postgresql.ENUM(
    "NONE",
    "SMALL",
    "SIGNIFICANT",
    "SOLUTION_VIEWED",
    "NOT_APPLICABLE",
    name="hint_usage",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    difficulty.create(bind, checkfirst=True)
    mastery_state.create(bind, checkfirst=True)
    attempt_outcome.create(bind, checkfirst=True)
    hint_usage.create(bind, checkfirst=True)

    op.create_table(
        "problems",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("normalized_title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(2048)),
        sa.Column("normalized_url", sa.String(2048)),
        sa.Column("platform", sa.String(100)),
        sa.Column("platform_identifier", sa.String(255)),
        sa.Column("difficulty", difficulty, nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("date_added", sa.Date(), nullable=False),
        sa.Column("current_mastery_state", mastery_state, nullable=False),
        sa.Column("mastery_overridden", sa.Boolean(), nullable=False),
        sa.Column("next_revision_date", sa.Date()),
        sa.Column("calculated_next_revision_date", sa.Date()),
        sa.Column("next_revision_overridden", sa.Boolean(), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer()),
        sa.Column("successful_revision_streak", sa.Integer(), nullable=False),
        sa.Column("total_attempts", sa.Integer(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("priority BETWEEN 1 AND 5", name="priority_range"),
        sa.CheckConstraint(
            "estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0",
            name="positive_estimated_duration",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_problems"),
    )
    op.create_index("ix_problems_normalized_title", "problems", ["normalized_title"])
    op.create_index("ix_problems_normalized_url", "problems", ["normalized_url"])
    op.create_index("ix_problems_next_revision_date", "problems", ["next_revision_date"])
    op.create_index("ix_problems_archived_at", "problems", ["archived_at"])
    op.create_index("ix_problems_mastery_state", "problems", ["current_mastery_state"])

    for table_name in ("topics", "patterns"):
        op.create_table(
            table_name,
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("normalized_name", sa.String(255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id", name=f"pk_{table_name}"),
            sa.UniqueConstraint("normalized_name", name=f"uq_{table_name}_normalized_name"),
        )

    op.create_table(
        "problem_topics",
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            ondelete="CASCADE",
            name="fk_problem_topics_problem_id_problems",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            ondelete="CASCADE",
            name="fk_problem_topics_topic_id_topics",
        ),
        sa.PrimaryKeyConstraint("problem_id", "topic_id", name="pk_problem_topics"),
    )
    op.create_table(
        "problem_patterns",
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("pattern_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            ondelete="CASCADE",
            name="fk_problem_patterns_problem_id_problems",
        ),
        sa.ForeignKeyConstraint(
            ["pattern_id"],
            ["patterns.id"],
            ondelete="CASCADE",
            name="fk_problem_patterns_pattern_id_patterns",
        ),
        sa.PrimaryKeyConstraint("problem_id", "pattern_id", name="pk_problem_patterns"),
    )
    op.create_table(
        "attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", attempt_outcome, nullable=False),
        sa.Column("hint_usage", hint_usage, nullable=False),
        sa.Column("time_spent_minutes", sa.Integer()),
        sa.Column("confidence", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.Column("complexity_understood", sa.Boolean()),
        sa.Column("previous_mastery_state", mastery_state, nullable=False),
        sa.Column("calculated_mastery_state", mastery_state, nullable=False),
        sa.Column("previous_revision_date", sa.Date()),
        sa.Column("calculated_next_revision_date", sa.Date(), nullable=False),
        sa.Column("schedule_explanation", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "time_spent_minutes IS NULL OR time_spent_minutes >= 0",
            name="nonnegative_time_spent",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 1 AND 5", name="confidence_range"
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            ondelete="RESTRICT",
            name="fk_attempts_problem_id_problems",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_attempts"),
    )
    op.create_index("ix_attempts_problem_id", "attempts", ["problem_id"])
    op.create_index("ix_attempts_problem_attempted", "attempts", ["problem_id", "attempted_at"])

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_path", sa.String(2048)),
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("default_available_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_preferences"),
    )
    op.create_table(
        "backup_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("manifest_version", sa.Integer(), nullable=False),
        sa.Column("application_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_backup_records"),
    )


def downgrade() -> None:
    for table_name in (
        "backup_records",
        "user_preferences",
        "attempts",
        "problem_patterns",
        "problem_topics",
        "patterns",
        "topics",
        "problems",
    ):
        op.drop_table(table_name)
    bind = op.get_bind()
    hint_usage.drop(bind, checkfirst=True)
    attempt_outcome.drop(bind, checkfirst=True)
    mastery_state.drop(bind, checkfirst=True)
    difficulty.drop(bind, checkfirst=True)
