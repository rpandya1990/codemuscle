import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from codemuscle.application.attempts.schemas import (
    AttemptCreate,
    AttemptResponse,
    RecentAttemptResponse,
)
from codemuscle.application.scheduling.policy import calculate_schedule
from codemuscle.domain.defaults import DEFAULT_SUCCESS_INTERVALS
from codemuscle.domain.exceptions import ProblemNotFoundError
from codemuscle.infrastructure.database.models import Attempt, Problem, UserPreference


class AttemptService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, problem_id: uuid.UUID, data: AttemptCreate) -> AttemptResponse:
        problem = self.session.get(Problem, problem_id)
        if problem is None:
            raise ProblemNotFoundError(problem_id)
        attempted_at = data.attempted_at or datetime.now(UTC)
        preference = self.session.scalar(select(UserPreference).limit(1))
        schedule = calculate_schedule(
            attempted_on=attempted_at.date(),
            outcome=data.outcome,
            hint_usage=data.hint_usage,
            previous_mastery=problem.current_mastery_state,
            successful_streak=problem.successful_revision_streak,
            difficulty=problem.difficulty,
            priority=problem.priority,
            intervals=(
                preference.successful_intervals if preference else list(DEFAULT_SUCCESS_INTERVALS)
            ),
        )
        attempt = Attempt(
            problem_id=problem.id,
            attempted_at=attempted_at,
            outcome=data.outcome,
            hint_usage=data.hint_usage,
            time_spent_minutes=data.time_spent_minutes,
            notes=data.notes or None,
            previous_mastery_state=problem.current_mastery_state,
            calculated_mastery_state=schedule.mastery_state,
            previous_revision_date=problem.next_revision_date,
            calculated_next_revision_date=schedule.next_revision_date,
            schedule_explanation=schedule.explanation,
        )
        self.session.add(attempt)
        problem.total_attempts += 1
        problem.successful_revision_streak = schedule.successful_revision_streak
        problem.current_mastery_state = schedule.mastery_state
        problem.calculated_next_revision_date = schedule.next_revision_date
        problem.next_revision_date = schedule.next_revision_date
        problem.next_revision_overridden = False
        self.session.commit()
        self.session.refresh(attempt)
        return AttemptResponse.model_validate(attempt)

    def list_for_problem(self, problem_id: uuid.UUID) -> list[AttemptResponse]:
        if self.session.get(Problem, problem_id) is None:
            raise ProblemNotFoundError(problem_id)
        attempts = self.session.scalars(
            select(Attempt)
            .where(Attempt.problem_id == problem_id)
            .order_by(Attempt.attempted_at.desc(), Attempt.created_at.desc())
        ).all()
        return [AttemptResponse.model_validate(attempt) for attempt in attempts]

    def recent(self, limit: int = 20) -> list[RecentAttemptResponse]:
        attempts = self.session.scalars(
            select(Attempt)
            .options(joinedload(Attempt.problem))
            .order_by(Attempt.attempted_at.desc())
            .limit(limit)
        ).all()
        return [
            RecentAttemptResponse(
                **AttemptResponse.model_validate(attempt).model_dump(),
                problem_title=attempt.problem.title,
            )
            for attempt in attempts
        ]
