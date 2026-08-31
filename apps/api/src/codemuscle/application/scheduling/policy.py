from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from codemuscle.application.scheduling.schemas import SchedulingResult
from codemuscle.domain.enums import AttemptOutcome, Difficulty, MasteryState


def calculate_schedule(
    *,
    attempted_on: date,
    outcome: AttemptOutcome,
    previous_mastery: MasteryState,
    successful_streak: int,
    difficulty: Difficulty,
    priority: int,
    intervals: list[int],
) -> SchedulingResult:
    factors = [f"Outcome: {outcome.value.replace('_', ' ').lower()}"]
    independent_without_hints = outcome == AttemptOutcome.SOLVED_INDEPENDENTLY
    if outcome == AttemptOutcome.FAILED:
        mastery, streak, days = MasteryState.NEEDS_RELEARNING, 0, 7
    elif outcome == AttemptOutcome.UNDERSTOOD_AFTER_SOLUTION:
        mastery, streak, days = MasteryState.LEARNING, 0, 14
    elif outcome == AttemptOutcome.SOLVED_SIGNIFICANT_HELP:
        mastery, streak, days = MasteryState.LEARNING, 0, 30
    elif outcome == AttemptOutcome.SKIPPED:
        mastery, streak, days = previous_mastery, successful_streak, 14
    else:
        streak = successful_streak + 1
        if outcome == AttemptOutcome.SOLVED_SMALL_HINT:
            mastery = MasteryState.FRAGILE
            days = 60
            factors.append("Scheduled for 60 days because a small hint was used")
        else:
            mastery = _mastery_for_streak(streak)
            difficulty_weight = {
                Difficulty.EASY: Decimal("1"),
                Difficulty.MEDIUM: Decimal("0.75"),
                Difficulty.HARD: Decimal("0.5"),
                Difficulty.UNKNOWN: Decimal("0.75"),
            }[difficulty]
            days = _weighted_days(max(intervals), difficulty_weight)
            factors.append(f"Applied {difficulty_weight:%} of the configured long-term interval")

    original_days = days
    if difficulty == Difficulty.HARD and not independent_without_hints and days > 1:
        days = max(1, round(days * 0.75))
        factors.append("Shortened 25% for hard difficulty")
    if priority >= 5 and days > 1:
        days = max(1, round(days * 0.8))
        factors.append("Shortened 20% for high priority")
    if days == original_days:
        factors.append("No interval modifiers applied")
    explanation = (
        f"Scheduled in {days} day{'s' if days != 1 else ''} after "
        f"{outcome.value.replace('_', ' ').lower()}."
    )
    return SchedulingResult(
        next_revision_date=attempted_on + timedelta(days=days),
        mastery_state=mastery,
        successful_revision_streak=streak,
        explanation=explanation,
        factors=factors,
    )


def _mastery_for_streak(streak: int) -> MasteryState:
    if streak >= 4:
        return MasteryState.MASTERED
    if streak >= 2:
        return MasteryState.RETAINED
    return MasteryState.LEARNING


def _weighted_days(days: int, weight: Decimal) -> int:
    return max(1, int((Decimal(days) * weight).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
