from dataclasses import dataclass
from datetime import date

from codemuscle.domain.defaults import DEFAULT_PROBLEM_DURATION_MINUTES
from codemuscle.domain.enums import AttemptOutcome, MasteryState
from codemuscle.infrastructure.database.models import Problem

SCORE_WEIGHTS = {
    "overdue_day": 10.0,
    "previous_failure": 80.0,
    "fragile": 60.0,
    "due_today": 50.0,
    "priority": 5.0,
    "neglect_day": 0.5,
}


@dataclass(frozen=True)
class Candidate:
    problem: Problem
    score: float
    duration: int
    reasons: list[str]
    primary_topic_id: str | None


def score_problem(problem: Problem, today: date) -> Candidate:
    score = problem.priority * SCORE_WEIGHTS["priority"]
    reasons = [f"Priority {problem.priority} problem"]
    if problem.next_revision_date is not None:
        overdue = (today - problem.next_revision_date).days
        if overdue > 0:
            score += min(overdue, 30) * SCORE_WEIGHTS["overdue_day"]
            reasons.insert(0, f"Overdue by {overdue} day{'s' if overdue != 1 else ''}")
        elif overdue == 0:
            score += SCORE_WEIGHTS["due_today"]
            reasons.insert(0, "Due today")
    latest = max(problem.attempts, key=lambda attempt: attempt.attempted_at, default=None)
    if latest is not None and latest.outcome == AttemptOutcome.FAILED:
        score += SCORE_WEIGHTS["previous_failure"]
        reasons.insert(0, "Previous attempt failed")
    if problem.current_mastery_state in {MasteryState.FRAGILE, MasteryState.NEEDS_RELEARNING}:
        score += SCORE_WEIGHTS["fragile"]
        reasons.append(
            f"Mastery is {problem.current_mastery_state.value.replace('_', ' ').lower()}"
        )
    if latest is not None:
        neglected = max(0, (today - latest.attempted_at.date()).days)
        score += min(neglected, 60) * SCORE_WEIGHTS["neglect_day"]
        if neglected >= 14:
            reasons.append(f"Not practiced for {neglected} days")
    elif problem.total_attempts == 0:
        reasons.append("Not practiced yet")
    duration = (
        problem.estimated_duration_minutes
        or DEFAULT_PROBLEM_DURATION_MINUTES[problem.difficulty]
    )
    primary_topic = str(problem.topics[0].id) if problem.topics else None
    return Candidate(problem, score, duration, reasons, primary_topic)


def select_candidates(
    candidates: list[Candidate], available_minutes: int, requested_count: int | None
) -> list[Candidate]:
    ordered = sorted(
        candidates, key=lambda item: (-item.score, item.problem.title, str(item.problem.id))
    )
    selected: list[Candidate] = []
    used_topics: set[str] = set()
    total = 0

    def try_add(item: Candidate) -> None:
        nonlocal total
        if requested_count is not None and len(selected) >= requested_count:
            return
        if total + item.duration <= available_minutes:
            selected.append(item)
            total += item.duration
            if item.primary_topic_id:
                used_topics.add(item.primary_topic_id)

    for item in ordered:
        if item.primary_topic_id is None or item.primary_topic_id not in used_topics:
            try_add(item)
    for item in ordered:
        if item not in selected:
            try_add(item)
    return selected
