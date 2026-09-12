import importlib.util
import uuid
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_migration_preserves_labels_and_deduplicates_links() -> None:
    path = (
        Path(__file__).parents[2] / "alembic/versions/20260912_0014_merge_patterns_into_topics.py"
    )
    spec = importlib.util.spec_from_file_location("merge_topics", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        metadata = sa.MetaData()
        problems = sa.Table("problems", metadata, sa.Column("id", sa.Uuid(), primary_key=True))
        topics = sa.Table(
            "topics",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("normalized_name", sa.String(), unique=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        )
        links = sa.Table(
            "problem_topics",
            metadata,
            sa.Column("problem_id", sa.Uuid(), primary_key=True),
            sa.Column("topic_id", sa.Uuid(), primary_key=True),
        )
        metadata.create_all(connection)
        migration.__dict__["op"] = Operations(MigrationContext.configure(connection))
        migration.downgrade()
        patterns = sa.Table(
            "patterns",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            autoload_with=connection,
        )
        old_links = sa.Table(
            "problem_patterns",
            metadata,
            sa.Column("problem_id", sa.Uuid(), primary_key=True),
            sa.Column("pattern_id", sa.Uuid(), primary_key=True),
            autoload_with=connection,
        )
        problem_id, topic_id, pattern_id, new_id = [uuid.uuid4() for _ in range(4)]
        connection.execute(problems.insert().values(id=problem_id))
        connection.execute(
            topics.insert().values(id=topic_id, name="Graphs", normalized_name="graphs")
        )
        connection.execute(links.insert().values(problem_id=problem_id, topic_id=topic_id))
        connection.execute(
            patterns.insert(),
            [
                {"id": pattern_id, "name": "graphs", "normalized_name": "graphs"},
                {"id": new_id, "name": "Traversal", "normalized_name": "traversal"},
            ],
        )
        connection.execute(
            old_links.insert(),
            [
                {"problem_id": problem_id, "pattern_id": pattern_id},
                {"problem_id": problem_id, "pattern_id": new_id},
            ],
        )
        migration.upgrade()
        assert "patterns" not in sa.inspect(connection).get_table_names()
        assert "problem_patterns" not in sa.inspect(connection).get_table_names()
        assert connection.scalar(sa.select(sa.func.count()).select_from(topics)) == 2
        assert connection.scalar(sa.select(sa.func.count()).select_from(links)) == 2
