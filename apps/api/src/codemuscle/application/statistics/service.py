from collections import Counter
from datetime import UTC, date, datetime, timedelta
from typing import TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from codemuscle.application.statistics.policy import classify_area, trend_label
from codemuscle.application.statistics.schemas import (
    AreaStatistics,
    DashboardStatistics,
    RecentActivity,
    TrendPoint,
    TrendsResponse,
)
from codemuscle.domain.enums import AttemptOutcome, MasteryState
from codemuscle.infrastructure.database.models import Attempt, Pattern, Problem, Topic

AreaModel = TypeVar("AreaModel", Topic, Pattern)
SUCCESSFUL_OUTCOMES = {
    AttemptOutcome.SOLVED_INDEPENDENTLY,
    AttemptOutcome.SOLVED_SMALL_HINT,
    AttemptOutcome.SOLVED_SIGNIFICANT_HELP,
}
HINT_ASSISTED_OUTCOMES = {
    AttemptOutcome.SOLVED_SMALL_HINT,
    AttemptOutcome.SOLVED_SIGNIFICANT_HELP,
}


class StatisticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def dashboard(self, today: date | None = None) -> DashboardStatistics:
        current_day = today or date.today()
        problems = list(self.session.scalars(self._problem_query()).unique())
        active = [problem for problem in problems if problem.archived_at is None]
        week_start = current_day - timedelta(days=current_day.weekday())
        attempts = list(
            self.session.scalars(select(Attempt).order_by(Attempt.attempted_at.desc())).all()
        )
        recent = attempts[:10]
        return DashboardStatistics(
            total_active_problems=len(active),
            due_today=sum(problem.next_revision_date == current_day for problem in active),
            overdue=sum(
                problem.next_revision_date is not None and problem.next_revision_date < current_day
                for problem in active
            ),
            practiced_this_week=len(
                {
                    attempt.problem_id
                    for attempt in attempts
                    if attempt.attempted_at.date() >= week_start
                }
            ),
            mastered=sum(
                problem.current_mastery_state == MasteryState.MASTERED for problem in active
            ),
            needs_relearning=sum(
                problem.current_mastery_state == MasteryState.NEEDS_RELEARNING for problem in active
            ),
            recent_activity=[
                RecentActivity(
                    attempt_id=attempt.id,
                    problem_id=attempt.problem_id,
                    problem_title=attempt.problem.title,
                    outcome=attempt.outcome.value,
                    attempted_at=attempt.attempted_at,
                )
                for attempt in recent
            ],
        )

    def topics(self, today: date | None = None) -> list[AreaStatistics]:
        return self._areas(Topic, today or date.today())

    def patterns(self, today: date | None = None) -> list[AreaStatistics]:
        return self._areas(Pattern, today or date.today())

    def weak_areas(self, today: date | None = None) -> list[AreaStatistics]:
        areas = self.topics(today)
        return [area for area in areas if area.status in {"WEAK", "NEGLECTED"}]

    def trends(self, weeks: int = 8, today: date | None = None) -> TrendsResponse:
        current_day = today or date.today()
        current_week = current_day - timedelta(days=current_day.weekday())
        start = current_week - timedelta(weeks=weeks - 1)
        attempts = self.session.scalars(
            select(Attempt).where(
                Attempt.attempted_at >= datetime.combine(start, datetime.min.time(), UTC)
            )
        ).all()
        buckets: dict[date, list[Attempt]] = {
            start + timedelta(weeks=offset): [] for offset in range(weeks)
        }
        for attempt in attempts:
            attempted_day = attempt.attempted_at.date()
            week = attempted_day - timedelta(days=attempted_day.weekday())
            if week in buckets:
                buckets[week].append(attempt)
        return TrendsResponse(
            points=[
                TrendPoint(
                    week_start=week,
                    attempts=len(items),
                    independent_successes=sum(
                        item.outcome == AttemptOutcome.SOLVED_INDEPENDENTLY for item in items
                    ),
                    failures=sum(item.outcome == AttemptOutcome.FAILED for item in items),
                )
                for week, items in sorted(buckets.items())
            ]
        )

    def _areas(self, model: type[AreaModel], today: date) -> list[AreaStatistics]:
        areas = self.session.scalars(
            select(model)
            .options(selectinload(model.problems).selectinload(Problem.attempts))
            .order_by(model.normalized_name)
        ).unique()
        return [self._area(area, today) for area in areas]

    @staticmethod
    def _area(area: AreaModel, today: date) -> AreaStatistics:
        active = [problem for problem in area.problems if problem.archived_at is None]
        attempts = sorted(
            (attempt for problem in active for attempt in problem.attempts),
            key=lambda attempt: attempt.attempted_at,
        )
        total = len(attempts)
        independent = sum(
            attempt.outcome == AttemptOutcome.SOLVED_INDEPENDENTLY for attempt in attempts
        )
        assisted = sum(attempt.outcome in HINT_ASSISTED_OUTCOMES for attempt in attempts)
        failed = sum(attempt.outcome == AttemptOutcome.FAILED for attempt in attempts)
        midpoint = total // 2
        older = attempts[:midpoint]
        recent = attempts[midpoint:]

        def success_rate(items: list[Attempt]) -> float | None:
            if not items:
                return None
            return sum(item.outcome in SUCCESSFUL_OUTCOMES for item in items) / len(items)

        older_rate = success_rate(older)
        recent_rate = success_rate(recent)
        last_date = attempts[-1].attempted_at.date() if attempts else None
        independent_rate = independent / total if total else 0.0
        failure_rate = failed / total if total else 0.0
        status, reasons = classify_area(
            total_attempts=total,
            independent_success_rate=independent_rate,
            failed_attempt_rate=failure_rate,
            last_practiced_date=last_date,
            recent_success_rate=recent_rate,
            older_success_rate=older_rate,
            today=today,
        )
        mastery = Counter(problem.current_mastery_state.value for problem in active)
        return AreaStatistics(
            id=area.id,
            name=area.name,
            total_problems=len(active),
            total_attempts=total,
            independent_success_rate=round(independent_rate, 3),
            hint_assisted_success_rate=round(assisted / total, 3) if total else 0.0,
            failed_attempt_rate=round(failure_rate, 3),
            problems_due=sum(problem.next_revision_date == today for problem in active),
            problems_overdue=sum(
                problem.next_revision_date is not None and problem.next_revision_date < today
                for problem in active
            ),
            mastery_distribution=dict(mastery),
            last_practiced_date=last_date,
            recent_trend=trend_label(recent_rate, older_rate),
            status=status,
            status_reasons=reasons,
        )

    @staticmethod
    def _problem_query() -> Select[tuple[Problem]]:
        return select(Problem).options(selectinload(Problem.attempts))
