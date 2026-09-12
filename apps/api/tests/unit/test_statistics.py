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
from codemuscle.domain.enums import AttemptOutcome
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import Attempt, Problem, Topic  # noqa: F401


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


def test_dashboard_topic_and_trend_statistics(session: Session) -> None:
    problem = ProblemService(session).create(
        ProblemCreate(title="Course Schedule", topics=["Graphs"])
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
        ),
    )
    service = StatisticsService(session)

    dashboard = service.dashboard(date(2026, 7, 29))
    topics = service.topics(date(2026, 7, 29))
    trends = service.trends(weeks=2, today=date(2026, 7, 29))

    assert dashboard.total_active_problems == 1
    assert dashboard.practiced_this_week == 1
    assert dashboard.needs_relearning == 1
    assert dashboard.recent_activity[0].problem_title == "Course Schedule"
    assert topics[0].name == "Graphs"
    assert topics[0].total_attempts == 1
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


def test_totals_count_shared_and_untagged_problems_once(session: Session) -> None:
    service = ProblemService(session)
    shared = service.create(ProblemCreate(title="Shared", topics=["Arrays", "Sorting"]))
    service.create(ProblemCreate(title="Untagged"))
    archived = service.create(ProblemCreate(title="Archived", topics=["Arrays"]))
    service.archive(archived.id)
    AttemptService(session).create(
        shared.id,
        AttemptCreate(
            attempted_at=datetime(2025, 1, 1, tzinfo=UTC),
            outcome=AttemptOutcome.SOLVED_INDEPENDENTLY,
        ),
    )
    statistics = StatisticsService(session)
    total = statistics.topic_totals(date(2026, 7, 29))
    assert total.total_problems == 2
    assert total.total_attempts == 1
    assert total.independent_success_rate == 1
    assert sum(point.attempts for point in statistics.trends(2, date(2026, 7, 29)).points) == 0
    history = statistics.trends(0, date(2026, 7, 29)).points
    assert len(history) > 52
    assert sum(point.attempts for point in history) == 1
    assert history[0].week_start == date(2024, 12, 30)
    assert history[-1].week_start == date(2026, 7, 27)


def test_empty_totals_and_history(session: Session) -> None:
    statistics = StatisticsService(session)
    assert statistics.topic_totals().total_attempts == 0
    assert statistics.topic_totals().independent_success_rate == 0
    assert len(statistics.trends(0).points) == 1
