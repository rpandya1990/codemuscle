from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from codemuscle.application.scheduling.policy import calculate_schedule
from codemuscle.application.scheduling.schemas import SchedulingResult
from codemuscle.domain.enums import AttemptOutcome, Difficulty, HintUsage, MasteryState


def schedule(
    outcome: AttemptOutcome,
    *,
    streak: int = 0,
    hint: HintUsage = HintUsage.NONE,
    confidence: int | None = None,
) -> SchedulingResult:
    return calculate_schedule(
        attempted_on=date(2026, 7, 28),
        outcome=outcome,
        hint_usage=hint,
        previous_mastery=MasteryState.NEW,
        successful_streak=streak,
        difficulty=Difficulty.MEDIUM,
        confidence=confidence,
        priority=3,
        intervals=[1, 3, 7, 14, 30, 60],
    )


@pytest.mark.parametrize(
    ("outcome", "mastery", "days", "streak"),
    [
        (AttemptOutcome.FAILED, MasteryState.NEEDS_RELEARNING, 1, 0),
        (AttemptOutcome.UNDERSTOOD_AFTER_SOLUTION, MasteryState.LEARNING, 1, 0),
        (AttemptOutcome.SOLVED_SIGNIFICANT_HELP, MasteryState.LEARNING, 1, 0),
        (AttemptOutcome.SOLVED_SMALL_HINT, MasteryState.FRAGILE, 1, 1),
        (AttemptOutcome.SOLVED_INDEPENDENTLY, MasteryState.LEARNING, 1, 1),
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


def test_low_confidence_modifier_is_explained() -> None:
    result = schedule(AttemptOutcome.SOLVED_INDEPENDENTLY, streak=3, confidence=1)
    assert "Shortened for low confidence" in result.factors
