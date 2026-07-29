from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from codemuscle.application.problems.schemas import ProblemCreate
from codemuscle.application.problems.service import ProblemService
from codemuscle.application.queues.schemas import QueueGenerationRequest, QueueItemUpdateRequest
from codemuscle.application.queues.service import QueueService
from codemuscle.domain.enums import Difficulty
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import Attempt, Pattern, Problem, Topic  # noqa: F401


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def test_generate_persist_and_edit_queue(session: Session) -> None:
    problems = ProblemService(session)
    problems.create(ProblemCreate(title="Two Sum", difficulty=Difficulty.EASY, topics=["Arrays"]))
    problems.create(
        ProblemCreate(title="Course Schedule", difficulty=Difficulty.MEDIUM, topics=["Graphs"])
    )
    problems.create(ProblemCreate(title="LRU Cache", difficulty=Difficulty.HARD))
    service = QueueService(session)

    queue = service.generate(QueueGenerationRequest(available_minutes=60))
    assert queue.total_estimated_minutes <= 60
    assert len(queue.items) == 2
    assert all(item.recommendation_reasons for item in queue.items)

    postponed = service.update_item(
        queue.id, queue.items[0].id, QueueItemUpdateRequest(status="POSTPONED")
    )
    assert postponed.items[0].status == "POSTPONED"
    replaced = service.replace_item(queue.id, queue.items[1].id)
    assert any(
        "Replacement recommendation" in item.recommendation_reasons for item in replaced.items
    )
    removed = service.remove_item(queue.id, queue.items[0].id)
    assert len(removed.items) == 1
