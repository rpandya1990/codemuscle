from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from codemuscle.application.scheduling.policy import calculate_schedule
from codemuscle.application.scheduling.schemas import SchedulingResult
from codemuscle.domain.defaults import DEFAULT_SUCCESS_INTERVALS
from codemuscle.domain.enums import AttemptOutcome, Difficulty, MasteryState


def schedule(
    outcome: AttemptOutcome,
    *,
    streak: int = 0,
    difficulty: Difficulty = Difficulty.MEDIUM,
    priority: int = 3,
) -> SchedulingResult:
    return calculate_schedule(
        attempted_on=date(2026, 7, 28),
        outcome=outcome,
        previous_mastery=MasteryState.NEW,
        successful_streak=streak,
        difficulty=difficulty,
        priority=priority,
        intervals=list(DEFAULT_SUCCESS_INTERVALS),
    )


@pytest.mark.parametrize(
    ("outcome", "mastery", "days", "streak"),
    [
        (AttemptOutcome.FAILED, MasteryState.NEEDS_RELEARNING, 7, 0),
        (AttemptOutcome.UNDERSTOOD_AFTER_SOLUTION, MasteryState.LEARNING, 14, 0),
        (AttemptOutcome.SOLVED_SIGNIFICANT_HELP, MasteryState.LEARNING, 30, 0),
        (AttemptOutcome.SOLVED_SMALL_HINT, MasteryState.FRAGILE, 60, 1),
        (AttemptOutcome.SOLVED_INDEPENDENTLY, MasteryState.LEARNING, 274, 1),
    ],
)
def test_baseline_policy(
    outcome: AttemptOutcome, mastery: MasteryState, days: int, streak: int
) -> None:
    result = schedule(outcome)
    assert result.mastery_state == mastery
    assert (result.next_revision_date - date(2026, 7, 28)).days == days
    assert result.successful_revision_streak == streak
    assert result.explanation


@given(st.integers(min_value=0, max_value=20))
def test_failure_never_increases_streak(streak: int) -> None:
    result = schedule(AttemptOutcome.FAILED, streak=streak)
    assert result.successful_revision_streak == 0


@given(st.integers(min_value=0, max_value=20))
def test_independent_success_never_shortens_interval(streak: int) -> None:
    current = schedule(AttemptOutcome.SOLVED_INDEPENDENTLY, streak=streak)
    following = schedule(AttemptOutcome.SOLVED_INDEPENDENTLY, streak=streak + 1)
    assert following.next_revision_date >= current.next_revision_date


@pytest.mark.parametrize(
    ("difficulty", "days"),
    [
        (Difficulty.EASY, 365),
        (Difficulty.MEDIUM, 274),
        (Difficulty.HARD, 183),
    ],
)
def test_independent_solve_uses_difficulty(difficulty: Difficulty, days: int) -> None:
    result = schedule(
        AttemptOutcome.SOLVED_INDEPENDENTLY,
        difficulty=difficulty,
    )
    assert (result.next_revision_date - date(2026, 7, 28)).days == days


def test_medium_small_hint_is_scheduled_in_sixty_days() -> None:
    result = schedule(
        AttemptOutcome.SOLVED_SMALL_HINT,
        difficulty=Difficulty.MEDIUM,
    )
    assert (result.next_revision_date - date(2026, 7, 28)).days == 60


def test_hard_and_high_priority_modifiers_stack() -> None:
    result = schedule(
        AttemptOutcome.SOLVED_INDEPENDENTLY,
        difficulty=Difficulty.HARD,
        priority=5,
    )
    assert (result.next_revision_date - date(2026, 7, 28)).days == 146
    assert "Shortened 25% for hard difficulty" not in result.factors
    assert "Shortened 20% for high priority" in result.factors
