from datetime import date, timedelta

from codemuscle.application.scheduling.schemas import SchedulingResult
from codemuscle.domain.enums import AttemptOutcome, Difficulty, HintUsage, MasteryState


def calculate_schedule(
    *,
    attempted_on: date,
    outcome: AttemptOutcome,
    hint_usage: HintUsage,
    previous_mastery: MasteryState,
    successful_streak: int,
    difficulty: Difficulty,
    confidence: int | None,
    priority: int,
    intervals: list[int],
) -> SchedulingResult:
    factors = [f"Outcome: {outcome.value.replace('_', ' ').lower()}"]
    if outcome == AttemptOutcome.FAILED:
        mastery, streak, days = MasteryState.NEEDS_RELEARNING, 0, 1
    elif outcome == AttemptOutcome.UNDERSTOOD_AFTER_SOLUTION:
        mastery, streak, days = MasteryState.LEARNING, 0, 1
    elif outcome == AttemptOutcome.SOLVED_SIGNIFICANT_HELP:
        mastery, streak, days = MasteryState.LEARNING, 0, min(3, intervals[0])
    elif outcome == AttemptOutcome.SKIPPED:
        mastery, streak, days = previous_mastery, successful_streak, 1
    else:
        streak = successful_streak + 1
        if outcome == AttemptOutcome.SOLVED_SMALL_HINT or hint_usage == HintUsage.SMALL:
            mastery = MasteryState.FRAGILE
            days = intervals[max(0, min(streak - 2, len(intervals) - 1))]
            factors.append("Interval held back because a hint was used")
        else:
            mastery = _mastery_for_streak(streak)
            days = intervals[min(streak - 1, len(intervals) - 1)]

    original_days = days
    if confidence is not None and confidence <= 2 and days > 1:
        days = max(1, round(days * 0.75))
        factors.append("Shortened for low confidence")
    if difficulty == Difficulty.HARD and days > 1:
        days = max(1, round(days * 0.85))
        factors.append("Shortened for hard difficulty")
    if priority >= 5 and days > 1:
        days = max(1, days - 1)
        factors.append("Shortened for high priority")
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
