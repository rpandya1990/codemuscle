import uuid
from collections.abc import Iterator
from datetime import date

import pytest
from pydantic import HttpUrl
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from codemuscle.application.problems.schemas import ProblemCreate, ProblemUpdate
from codemuscle.application.problems.service import ProblemService
from codemuscle.application.scheduling.schemas import ScheduleOverrideRequest
from codemuscle.domain.enums import Difficulty
from codemuscle.domain.exceptions import ProblemNotFoundError
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import Attempt, Pattern, Problem, Topic  # noqa: F401


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def test_create_update_filter_archive_and_restore_problem(session: Session) -> None:
    service = ProblemService(session)
    created = service.create(
        ProblemCreate(
            title="Two Sum",
            url=HttpUrl("https://leetcode.com/problems/two-sum/"),
            difficulty=Difficulty.EASY,
            topics=["Array", "Hash Table", "array"],
            patterns=["Lookup"],
        )
    )

    assert {topic.name for topic in created.topics} == {"Array", "Hash Table"}
    assert service.list(search="two", difficulty=Difficulty.EASY).total == 1
    assert service.list(topic_id=created.topics[0].id).total == 1

    updated = service.update(
        created.id,
        ProblemUpdate(title="Two Sum Updated", priority=5, topics=["Arrays"]),
    )
    assert updated.title == "Two Sum Updated"
    assert updated.priority == 5
    assert [topic.name for topic in updated.topics] == ["Arrays"]

    assert service.archive(created.id).archived_at is not None
    assert service.list().total == 0
    assert service.list(archived=True).total == 1
    assert service.restore(created.id).archived_at is None

    overridden = service.override_schedule(
        created.id, ScheduleOverrideRequest(next_revision_date=date(2026, 8, 15))
    )
    assert overridden.next_revision_date == date(2026, 8, 15)
    assert overridden.next_revision_overridden is True
    cleared = service.clear_schedule_override(created.id)
    assert cleared.next_revision_date == cleared.calculated_next_revision_date
    assert cleared.next_revision_overridden is False


def test_duplicate_detection_returns_strongest_reason(session: Session) -> None:
    service = ProblemService(session)
    service.create(
        ProblemCreate(
            title="Two Sum",
            url=HttpUrl("https://leetcode.com/problems/two-sum/"),
            platform="LeetCode",
            platform_identifier="1",
        )
    )

    duplicates = service.duplicates(
        title="two-sum",
        url="https://leetcode.com/problems/two-sum",
        platform="leetcode",
        platform_identifier="1",
    )

    assert len(duplicates) == 1
    assert duplicates[0].confidence == 1.0
    assert duplicates[0].reason == "Exact normalized URL match"

    fuzzy = service.duplicates(title="Two Sums", url=None, platform=None, platform_identifier=None)
    assert fuzzy[0].reason == "Similar normalized title"


def test_missing_problem_raises_domain_error(session: Session) -> None:
    with pytest.raises(ProblemNotFoundError):
        ProblemService(session).get(uuid.uuid4())
