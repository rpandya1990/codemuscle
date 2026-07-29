import uuid
from datetime import date, timedelta

from codemuscle.application.queues.policy import score_problem, select_candidates
from codemuscle.domain.enums import Difficulty, MasteryState
from codemuscle.infrastructure.database.models import Problem, Topic


def problem(
    title: str,
    *,
    difficulty: Difficulty = Difficulty.UNKNOWN,
    due_offset: int | None = None,
    topic: str | None = None,
    topic_id: uuid.UUID | None = None,
) -> Problem:
    item = Problem(
        id=uuid.uuid4(),
        title=title,
        normalized_title=title.lower(),
        difficulty=difficulty,
        priority=3,
        current_mastery_state=MasteryState.NEW,
        total_attempts=0,
        successful_revision_streak=0,
    )
    item.attempts = []
    item.topics = (
        [Topic(id=topic_id or uuid.uuid4(), name=topic, normalized_name=topic.lower())]
        if topic
        else []
    )
    if due_offset is not None:
        item.next_revision_date = date(2026, 7, 28) + timedelta(days=due_offset)
    return item


def test_scoring_prioritizes_overdue_and_explains_reason() -> None:
    overdue = score_problem(problem("Overdue", due_offset=-5), date(2026, 7, 28))
    new = score_problem(problem("New"), date(2026, 7, 28))
    assert overdue.score > new.score
    assert "Overdue by 5 days" in overdue.reasons


def test_time_fitting_and_topic_balancing_are_deterministic() -> None:
    arrays_id = uuid.uuid4()
    candidates = [
        score_problem(
            problem("Array 1", difficulty=Difficulty.EASY, topic="Arrays", topic_id=arrays_id),
            date(2026, 7, 28),
        ),
        score_problem(
            problem("Array 2", difficulty=Difficulty.EASY, topic="Arrays", topic_id=arrays_id),
            date(2026, 7, 28),
        ),
        score_problem(
            problem("Graph", difficulty=Difficulty.EASY, topic="Graphs"), date(2026, 7, 28)
        ),
    ]
    selected = select_candidates(candidates, available_minutes=40, requested_count=None)
    assert sum(item.duration for item in selected) <= 40
    assert {item.primary_topic_id for item in selected} == {
        candidates[0].primary_topic_id,
        candidates[2].primary_topic_id,
    }
