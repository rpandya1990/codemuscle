from datetime import date

from pydantic import BaseModel

from codemuscle.domain.enums import MasteryState


class SchedulingResult(BaseModel):
    next_revision_date: date
    mastery_state: MasteryState
    successful_revision_streak: int
    explanation: str
    factors: list[str]


class ScheduleOverrideRequest(BaseModel):
    next_revision_date: date
