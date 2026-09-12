"""Merge existing pattern labels into topics and remove pattern tables."""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260912_0014"
down_revision: str | None = "20260906_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData()
    topics = sa.Table(
        "topics", metadata, sa.Column("id", sa.Uuid(), primary_key=True), autoload_with=connection
    )
    patterns = sa.Table(
        "patterns", metadata, sa.Column("id", sa.Uuid(), primary_key=True), autoload_with=connection
    )
    links = sa.Table(
        "problem_topics",
        metadata,
        sa.Column("problem_id", sa.Uuid(), primary_key=True),
        sa.Column("topic_id", sa.Uuid(), primary_key=True),
        autoload_with=connection,
    )
    old_links = sa.Table(
        "problem_patterns",
        metadata,
        sa.Column("problem_id", sa.Uuid(), primary_key=True),
        sa.Column("pattern_id", sa.Uuid(), primary_key=True),
        autoload_with=connection,
    )
    by_name = {
        name: identifier
        for name, identifier in connection.execute(sa.select(topics.c.normalized_name, topics.c.id))
    }
    existing = {
        (problem_id, topic_id) for problem_id, topic_id in connection.execute(sa.select(links))
    }
    for pattern in connection.execute(sa.select(patterns)).mappings():
        topic_id = by_name.get(pattern["normalized_name"])
        if topic_id is None:
            topic_id = uuid.uuid4()
            connection.execute(
                topics.insert().values(
                    id=topic_id,
                    name=pattern["name"],
                    normalized_name=pattern["normalized_name"],
                    created_at=pattern["created_at"],
                )
            )
            by_name[pattern["normalized_name"]] = topic_id
        for problem_id in connection.scalars(
            sa.select(old_links.c.problem_id).where(old_links.c.pattern_id == pattern["id"])
        ):
            if (problem_id, topic_id) not in existing:
                connection.execute(links.insert().values(problem_id=problem_id, topic_id=topic_id))
                existing.add((problem_id, topic_id))
    op.drop_table("problem_patterns")
    op.drop_table("patterns")


def downgrade() -> None:
    op.create_table(
        "patterns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("normalized_name", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "problem_patterns",
        sa.Column(
            "problem_id",
            sa.Uuid(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "pattern_id",
            sa.Uuid(),
            sa.ForeignKey("patterns.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
