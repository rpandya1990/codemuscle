import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from codemuscle.application.attempts.schemas import (
    AttemptCreate,
    AttemptResponse,
    RecentAttemptResponse,
)
from codemuscle.domain.enums import AttemptOutcome, MasteryState
from codemuscle.domain.exceptions import ProblemNotFoundError
from codemuscle.infrastructure.database.models import Attempt, Problem


class AttemptService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, problem_id: uuid.UUID, data: AttemptCreate) -> AttemptResponse:
        problem = self.session.get(Problem, problem_id)
        if problem is None:
            raise ProblemNotFoundError(problem_id)
        attempted_at = data.attempted_at or datetime.now(UTC)
        mastery, streak = self._calculate_mastery(
            problem.current_mastery_state, problem.successful_revision_streak, data.outcome
        )
        next_revision = attempted_at.date() + timedelta(days=1)
        attempt = Attempt(
            problem_id=problem.id,
            attempted_at=attempted_at,
            outcome=data.outcome,
            hint_usage=data.hint_usage,
            time_spent_minutes=data.time_spent_minutes,
            confidence=data.confidence,
            notes=data.notes or None,
            complexity_understood=data.complexity_understood,
            previous_mastery_state=problem.current_mastery_state,
            calculated_mastery_state=mastery,
            previous_revision_date=problem.next_revision_date,
            calculated_next_revision_date=next_revision,
            schedule_explanation=(
                "Initial follow-up in 1 day; interval scheduling is configured in Milestone 5."
            ),
        )
        self.session.add(attempt)
        problem.total_attempts += 1
        problem.successful_revision_streak = streak
        problem.current_mastery_state = mastery
        problem.calculated_next_revision_date = next_revision
        problem.next_revision_date = next_revision
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

    @staticmethod
    def _calculate_mastery(
        previous: MasteryState, streak: int, outcome: AttemptOutcome
    ) -> tuple[MasteryState, int]:
        if outcome == AttemptOutcome.FAILED:
            return MasteryState.NEEDS_RELEARNING, 0
        if outcome in {
            AttemptOutcome.UNDERSTOOD_AFTER_SOLUTION,
            AttemptOutcome.SOLVED_SIGNIFICANT_HELP,
        }:
            return MasteryState.LEARNING, 0
        if outcome == AttemptOutcome.SKIPPED:
            return previous, streak
        new_streak = streak + 1
        if outcome == AttemptOutcome.SOLVED_SMALL_HINT:
            return MasteryState.FRAGILE, new_streak
        if new_streak >= 4:
            return MasteryState.MASTERED, new_streak
        if new_streak >= 2:
            return MasteryState.RETAINED, new_streak
        return MasteryState.LEARNING, new_streak
