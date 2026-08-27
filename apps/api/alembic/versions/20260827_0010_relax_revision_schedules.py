"""Recalculate current revision dates with the relaxed scheduling policy.

Revision ID: 20260827_0010
Revises: 20260825_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260827_0010"
down_revision: str | None = "20260825_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Attempt rows are immutable audit records. Only each problem's current summary is
    # recalculated, and an explicit manual next-date override remains effective.
    op.execute(
        sa.text(
            """
            WITH latest_attempt AS (
                SELECT DISTINCT ON (a.problem_id)
                    a.problem_id,
                    CAST(a.attempted_at AS date) AS attempted_on,
                    a.outcome,
                    a.hint_usage,
                    a.confidence,
                    a.complexity_understood
                FROM attempts AS a
                ORDER BY a.problem_id, a.attempted_at DESC, a.created_at DESC
            ),
            base_schedule AS (
                SELECT
                    p.id AS problem_id,
                    la.attempted_on,
                    p.difficulty,
                    p.priority,
                    CASE
                        WHEN la.outcome = 'FAILED' THEN 7
                        WHEN la.outcome = 'UNDERSTOOD_AFTER_SOLUTION' THEN 14
                        WHEN la.outcome = 'SOLVED_SIGNIFICANT_HELP' THEN 30
                        WHEN la.outcome = 'SKIPPED' THEN 14
                        WHEN la.outcome = 'SOLVED_SMALL_HINT' OR la.hint_usage = 'SMALL' THEN 60
                        WHEN la.confidence = 5 AND la.complexity_understood IS TRUE THEN 365
                        WHEN la.confidence <= 2 THEN 90
                        ELSE 180
                    END AS base_days
                FROM problems AS p
                JOIN latest_attempt AS la ON la.problem_id = p.id
            ),
            difficulty_schedule AS (
                SELECT
                    *,
                    CASE
                        WHEN difficulty = 'HARD' THEN CAST(round(base_days * 0.75) AS integer)
                        ELSE base_days
                    END AS difficulty_days
                FROM base_schedule
            ),
            final_schedule AS (
                SELECT
                    problem_id,
                    attempted_on + CASE
                        WHEN priority >= 5
                            THEN CAST(round(difficulty_days * 0.8) AS integer)
                        ELSE difficulty_days
                    END AS next_revision_date
                FROM difficulty_schedule
            )
            UPDATE problems AS p
            SET
                calculated_next_revision_date = fs.next_revision_date,
                next_revision_date = CASE
                    WHEN p.next_revision_overridden THEN p.next_revision_date
                    ELSE fs.next_revision_date
                END
            FROM final_schedule AS fs
            WHERE p.id = fs.problem_id
            """
        )
    )


def downgrade() -> None:
    # Previous calculated dates cannot be reconstructed without rewriting immutable
    # attempt history, so downgrading intentionally leaves current summaries intact.
    pass
