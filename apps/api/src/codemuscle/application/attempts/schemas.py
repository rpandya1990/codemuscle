import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from codemuscle.domain.enums import AttemptOutcome, HintUsage, MasteryState


class AttemptCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    attempted_at: datetime | None = None
    outcome: AttemptOutcome
    hint_usage: HintUsage = HintUsage.NOT_APPLICABLE
    time_spent_minutes: int | None = Field(default=None, ge=0, le=1440)
    confidence: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None
    complexity_understood: bool | None = None


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    problem_id: uuid.UUID
    attempted_at: datetime
    outcome: AttemptOutcome
    hint_usage: HintUsage
    time_spent_minutes: int | None
    confidence: int | None
    notes: str | None
    complexity_understood: bool | None
    previous_mastery_state: MasteryState
    calculated_mastery_state: MasteryState
    schedule_explanation: str
    created_at: datetime


class RecentAttemptResponse(AttemptResponse):
    problem_title: str
