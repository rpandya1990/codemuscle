from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from codemuscle.application.attempts.schemas import AttemptCreate
from codemuscle.application.attempts.service import AttemptService
from codemuscle.application.problems.schemas import ProblemCreate
from codemuscle.application.problems.service import ProblemService
from codemuscle.application.statistics.policy import classify_area
from codemuscle.application.statistics.service import StatisticsService
from codemuscle.domain.enums import AttemptOutcome, HintUsage
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import Attempt, Pattern, Problem, Topic  # noqa: F401


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {
                "total_attempts": 0,
                "independent_success_rate": 0.0,
                "failed_attempt_rate": 0.0,
                "last_practiced_date": None,
                "recent_success_rate": None,
                "older_success_rate": None,
            },
            "NEGLECTED",
        ),
        (
            {
                "total_attempts": 4,
                "independent_success_rate": 0.25,
                "failed_attempt_rate": 0.5,
                "last_practiced_date": date(2026, 7, 28),
                "recent_success_rate": 0.5,
                "older_success_rate": 0.5,
            },
            "WEAK",
        ),
        (
            {
                "total_attempts": 4,
                "independent_success_rate": 0.75,
                "failed_attempt_rate": 0.0,
                "last_practiced_date": date(2026, 7, 28),
                "recent_success_rate": 1.0,
                "older_success_rate": 0.5,
            },
            "IMPROVING",
        ),
    ],
)
def test_area_classification(kwargs: dict[str, object], expected: str) -> None:
    status, reasons = classify_area(today=date(2026, 7, 29), **kwargs)  # type: ignore[arg-type]
    assert status == expected
    assert reasons


def test_dashboard_topic_pattern_and_trend_statistics(session: Session) -> None:
    problem = ProblemService(session).create(
        ProblemCreate(title="Course Schedule", topics=["Graphs"], patterns=["Topological Sort"])
    )
    problem_model = session.get(Problem, problem.id)
    assert problem_model is not None
    problem_model.next_revision_date = date(2026, 7, 28)
    session.commit()
    attempts = AttemptService(session)
    attempts.create(
        problem.id,
        AttemptCreate(
            attempted_at=datetime(2026, 7, 28, 10, tzinfo=UTC),
            outcome=AttemptOutcome.FAILED,
            hint_usage=HintUsage.SOLUTION_VIEWED,
        ),
    )
    service = StatisticsService(session)

    dashboard = service.dashboard(date(2026, 7, 29))
    topics = service.topics(date(2026, 7, 29))
    patterns = service.patterns(date(2026, 7, 29))
    trends = service.trends(weeks=2, today=date(2026, 7, 29))

    assert dashboard.total_active_problems == 1
    assert dashboard.practiced_this_week == 1
    assert dashboard.needs_relearning == 1
    assert dashboard.recent_activity[0].problem_title == "Course Schedule"
    assert topics[0].name == "Graphs"
    assert topics[0].total_attempts == 1
    assert patterns[0].name == "Topological Sort"
    assert sum(point.attempts for point in trends.points) == 1
    assert len(trends.points) == 2


def test_neglected_threshold_is_thirty_days() -> None:
    status, _ = classify_area(
        total_attempts=1,
        independent_success_rate=1.0,
        failed_attempt_rate=0.0,
        last_practiced_date=date(2026, 6, 29),
        recent_success_rate=1.0,
        older_success_rate=None,
        today=date(2026, 7, 29),
    )
    assert status == "NEGLECTED"
