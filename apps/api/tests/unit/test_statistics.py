from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from codemuscle.application.attempts.schemas import AttemptCreate
from codemuscle.application.attempts.service import AttemptService
from codemuscle.application.problems.schemas import ProblemCreate
from codemuscle.application.problems.service import ProblemService
from codemuscle.application.statistics.policy import classify_area
from codemuscle.application.statistics.schemas import TrendInterval
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


def test_total_percentage_uses_all_attempts_not_one_topic_or_average(session: Session) -> None:
    problems = ProblemService(session)
    first = problems.create(ProblemCreate(title="First", topics=["Arrays", "Sorting"]))
    second = problems.create(ProblemCreate(title="Second", topics=["Graphs"]))
    attempts = AttemptService(session)
    for problem_id, outcome in [
        (first.id, AttemptOutcome.SOLVED_INDEPENDENTLY),
        (second.id, AttemptOutcome.SOLVED_INDEPENDENTLY),
        (second.id, AttemptOutcome.FAILED),
        (second.id, AttemptOutcome.SOLVED_SMALL_HINT),
    ]:
        attempts.create(problem_id, AttemptCreate(outcome=outcome))
    total = StatisticsService(session).topic_totals()
    assert total.independent_successes == 2
    assert total.total_attempts == 4
    assert total.independent_success_rate == 0.5
    assert total.failed_attempt_rate == 0.25
    assert all(
        area.independent_success_rate != total.independent_success_rate
        for area in StatisticsService(session).topics()
    )


@pytest.mark.parametrize(
    ("interval", "today", "expected"),
    [
        (
            "day",
            date(2024, 3, 2),
            [
                date(2024, 2, 27),
                date(2024, 2, 28),
                date(2024, 2, 29),
                date(2024, 3, 1),
                date(2024, 3, 2),
            ],
        ),
        (
            "week",
            date(2026, 1, 14),
            [
                date(2025, 12, 15),
                date(2025, 12, 22),
                date(2025, 12, 29),
                date(2026, 1, 5),
                date(2026, 1, 12),
            ],
        ),
        (
            "month",
            date(2026, 3, 15),
            [
                date(2025, 11, 1),
                date(2025, 12, 1),
                date(2026, 1, 1),
                date(2026, 2, 1),
                date(2026, 3, 1),
            ],
        ),
        (
            "year",
            date(2026, 3, 15),
            [
                date(2022, 1, 1),
                date(2023, 1, 1),
                date(2024, 1, 1),
                date(2025, 1, 1),
                date(2026, 1, 1),
            ],
        ),
    ],
)
def test_trends_calendar_buckets(
    session: Session, interval: TrendInterval, today: date, expected: list[date]
) -> None:
    problem = ProblemService(session).create(ProblemCreate(title="Calendar"))
    for day, outcome in [
        (expected[0] - timedelta(days=1), AttemptOutcome.FAILED),
        (expected[0], AttemptOutcome.SOLVED_INDEPENDENTLY),
        (today, AttemptOutcome.FAILED),
        (today + timedelta(days=1), AttemptOutcome.FAILED),
    ]:
        AttemptService(session).create(
            problem.id,
            AttemptCreate(
                attempted_at=datetime.combine(day, datetime.min.time(), UTC), outcome=outcome
            ),
        )
    session.commit()
    points = StatisticsService(session).trends(today=today, interval=interval, count=5).points
    assert [point.period_start for point in points] == expected
    assert [point.attempts for point in points] == [1, 0, 0, 0, 1]
    assert points[0].independent_successes == 1
    assert points[-1].failures == 1


def test_health_counts_problems_including_unattempted_not_attempts(session: Session) -> None:
    problems = ProblemService(session)
    solved = problems.create(ProblemCreate(title="Solved", topics=["Arrays", "Sorting"]))
    problems.create(ProblemCreate(title="Unattempted", topics=["Arrays"]))
    assisted = problems.create(ProblemCreate(title="Assisted", topics=["Arrays"]))
    untagged = problems.create(ProblemCreate(title="Untagged"))
    archived = problems.create(ProblemCreate(title="Archived", topics=["Arrays"]))
    for problem_id, outcomes in [
        (solved.id, [AttemptOutcome.SOLVED_INDEPENDENTLY] * 3 + [AttemptOutcome.FAILED]),
        (assisted.id, [AttemptOutcome.SOLVED_SMALL_HINT]),
        (untagged.id, [AttemptOutcome.SOLVED_INDEPENDENTLY]),
        (archived.id, [AttemptOutcome.SOLVED_INDEPENDENTLY]),
    ]:
        for outcome in outcomes:
            AttemptService(session).create(problem_id, AttemptCreate(outcome=outcome))
    problems.archive(archived.id)
    statistics = StatisticsService(session)
    topics = {topic.name: topic for topic in statistics.topics()}
    assert topics["Arrays"].independently_solved_problems == 1
    assert topics["Arrays"].total_problems == 3
    assert topics["Arrays"].health_rate == pytest.approx(1 / 3)
    assert topics["Sorting"].health_rate == 1
    total = statistics.topic_totals()
    assert total.independently_solved_problems == 2
    assert total.total_problems == 4
    assert total.health_rate == 0.5


def test_health_is_zero_for_empty_or_unattempted_topics(session: Session) -> None:
    statistics = StatisticsService(session)
    assert statistics.topic_totals().health_rate == 0
    problems = ProblemService(session)
    problem = problems.create(ProblemCreate(title="Unattempted", topics=["Arrays"]))
    assert statistics.topics()[0].health_rate == 0
    assert statistics.topic_totals().independently_solved_problems == 0
    problems.archive(problem.id)
    assert statistics.topics()[0].total_problems == 0
    assert statistics.topics()[0].health_rate == 0
