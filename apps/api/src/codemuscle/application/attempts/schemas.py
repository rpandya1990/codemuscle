import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from codemuscle.domain.enums import AttemptOutcome, MasteryState


class AttemptCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    attempted_at: datetime | None = None
    outcome: AttemptOutcome
    time_spent_minutes: int | None = Field(default=None, ge=0, le=1440)
    notes: str | None = None


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    problem_id: uuid.UUID
    attempted_at: datetime
    outcome: AttemptOutcome
    time_spent_minutes: int | None
    notes: str | None
    previous_mastery_state: MasteryState
    calculated_mastery_state: MasteryState
    calculated_next_revision_date: date
    schedule_explanation: str
    created_at: datetime


class RecentAttemptResponse(AttemptResponse):
    problem_title: str
