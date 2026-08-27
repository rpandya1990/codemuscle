from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from codemuscle.application.attempts.schemas import AttemptCreate
from codemuscle.application.attempts.service import AttemptService
from codemuscle.application.problems.schemas import ProblemCreate
from codemuscle.application.problems.service import ProblemService
from codemuscle.domain.enums import AttemptOutcome, HintUsage, MasteryState
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import Attempt, Pattern, Problem, Topic  # noqa: F401


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def test_attempts_are_immutable_history_and_update_summary(session: Session) -> None:
    problem = ProblemService(session).create(ProblemCreate(title="Two Sum"))
    service = AttemptService(session)
    first = service.create(
        problem.id,
        AttemptCreate(
            attempted_at=datetime(2026, 7, 20, 9, tzinfo=UTC),
            outcome=AttemptOutcome.SOLVED_INDEPENDENTLY,
            hint_usage=HintUsage.NONE,
            time_spent_minutes=18,
        ),
    )
    second = service.create(
        problem.id,
        AttemptCreate(
            attempted_at=datetime(2026, 7, 21, 9, tzinfo=UTC),
            outcome=AttemptOutcome.FAILED,
            hint_usage=HintUsage.SOLUTION_VIEWED,
            notes="Missed the duplicate case",
        ),
    )

    history = service.list_for_problem(problem.id)
    updated = ProblemService(session).get(problem.id)
    assert [attempt.id for attempt in history] == [second.id, first.id]
    assert updated.total_attempts == 2
    assert updated.successful_revision_streak == 0
    assert updated.current_mastery_state == MasteryState.NEEDS_RELEARNING
    assert first.previous_mastery_state == MasteryState.NEW
    assert second.previous_mastery_state == MasteryState.LEARNING


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (AttemptOutcome.SOLVED_SMALL_HINT, MasteryState.FRAGILE),
        (AttemptOutcome.SOLVED_SIGNIFICANT_HELP, MasteryState.LEARNING),
        (AttemptOutcome.UNDERSTOOD_AFTER_SOLUTION, MasteryState.LEARNING),
        (AttemptOutcome.FAILED, MasteryState.NEEDS_RELEARNING),
        (AttemptOutcome.SKIPPED, MasteryState.NEW),
    ],
)
def test_initial_mastery_policy(
    session: Session, outcome: AttemptOutcome, expected: MasteryState
) -> None:
    problem = ProblemService(session).create(ProblemCreate(title=outcome.value))
    attempt = AttemptService(session).create(problem.id, AttemptCreate(outcome=outcome))
    assert attempt.calculated_mastery_state == expected
