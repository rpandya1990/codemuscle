"""Remove confidence and complexity-understood attempt fields.

Revision ID: 20260827_0011
Revises: 20260827_0010
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260827_0011"
down_revision: str | None = "20260827_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Recalculate independent solves before dropping the self-assessment columns.
    # Immutable attempt snapshots and explicit manual overrides remain unchanged.
    op.execute(
        sa.text(
            """
            WITH preference AS (
                SELECT CAST(
                    successful_intervals ->> (json_array_length(successful_intervals) - 1)
                    AS integer
                ) AS long_term_days
                FROM user_preferences
                LIMIT 1
            ),
            latest_attempt AS (
                SELECT DISTINCT ON (a.problem_id)
                    a.problem_id,
                    CAST(a.attempted_at AS date) AS attempted_on,
                    a.outcome,
                    a.hint_usage
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
                        WHEN la.outcome = 'UNDERSTOOD_AFTER_SOLUTION'
                            OR la.hint_usage = 'SOLUTION_VIEWED' THEN 14
                        WHEN la.outcome = 'SOLVED_SIGNIFICANT_HELP'
                            OR la.hint_usage = 'SIGNIFICANT' THEN 30
                        WHEN la.outcome = 'SKIPPED' THEN 14
                        WHEN la.outcome = 'SOLVED_SMALL_HINT' OR la.hint_usage = 'SMALL' THEN 60
                        WHEN p.difficulty = 'EASY'
                            THEN COALESCE((SELECT long_term_days FROM preference), 365)
                        WHEN p.difficulty = 'HARD'
                            THEN CAST(round(
                                COALESCE((SELECT long_term_days FROM preference), 365) * 0.5
                            ) AS integer)
                        ELSE CAST(round(
                            COALESCE((SELECT long_term_days FROM preference), 365) * 0.75
                        ) AS integer)
                    END AS base_days,
                    CASE
                        WHEN la.outcome = 'SOLVED_INDEPENDENTLY'
                            AND la.hint_usage IN ('NONE', 'NOT_APPLICABLE') THEN FALSE
                        ELSE TRUE
                    END AS apply_hard_modifier
                FROM problems AS p
                JOIN latest_attempt AS la ON la.problem_id = p.id
            ),
            difficulty_schedule AS (
                SELECT
                    *,
                    CASE
                        WHEN difficulty = 'HARD' AND apply_hard_modifier
                            THEN CAST(round(base_days * 0.75) AS integer)
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
    op.drop_constraint("confidence_range", "attempts", type_="check")
    op.drop_column("attempts", "confidence")
    op.drop_column("attempts", "complexity_understood")


def downgrade() -> None:
    op.add_column("attempts", sa.Column("complexity_understood", sa.Boolean(), nullable=True))
    op.add_column("attempts", sa.Column("confidence", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "confidence_range", "attempts", "confidence IS NULL OR confidence BETWEEN 1 AND 5"
    )
