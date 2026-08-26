import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from codemuscle.application.problems.schemas import ProblemResponse
from codemuscle.domain.enums import Difficulty


class QueueGenerationRequest(BaseModel):
    available_minutes: int = Field(ge=5, le=720)
    topic_focus_ids: list[uuid.UUID] = Field(default_factory=list, max_length=30)
    difficulty_focus: list[Difficulty] = Field(default_factory=list, max_length=4)
    requested_problem_count: int | None = Field(default=None, ge=1, le=100)


class QueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position: int
    estimated_duration_minutes: int
    recommendation_score: float
    recommendation_reasons: list[str]
    status: str
    problem: ProblemResponse


class QueueResponse(BaseModel):
    id: uuid.UUID
    available_minutes: int
    topic_focus_ids: list[str]
    difficulty_focus: list[Difficulty]
    requested_problem_count: int | None
    status: str
    created_at: datetime
    total_estimated_minutes: int
    items: list[QueueItemResponse]


class QueueAddItemRequest(BaseModel):
    problem_id: uuid.UUID


class QueueItemUpdateRequest(BaseModel):
    status: str = Field(pattern="^(PENDING|POSTPONED|COMPLETED)$")
