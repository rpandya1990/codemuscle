import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from codemuscle.domain.enums import Difficulty, MasteryState


class NamedReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class ProblemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl | None = None
    platform: str | None = Field(default=None, max_length=100)
    platform_identifier: str | None = Field(default=None, max_length=255)
    difficulty: Difficulty = Difficulty.UNKNOWN
    notes: str | None = None
    priority: int = Field(default=3, ge=1, le=5)
    estimated_duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    topics: list[str] = Field(default_factory=list, max_length=30)
    patterns: list[str] = Field(default_factory=list, max_length=30)


class ProblemUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=500)
    url: HttpUrl | None = None
    platform: str | None = Field(default=None, max_length=100)
    platform_identifier: str | None = Field(default=None, max_length=255)
    difficulty: Difficulty | None = None
    notes: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    estimated_duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    topics: list[str] | None = Field(default=None, max_length=30)
    patterns: list[str] | None = Field(default=None, max_length=30)


class ProblemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    url: str | None
    platform: str | None
    platform_identifier: str | None
    difficulty: Difficulty
    notes: str | None
    priority: int
    date_added: date
    current_mastery_state: MasteryState
    next_revision_date: date | None
    estimated_duration_minutes: int | None
    archived_at: datetime | None
    topics: list[NamedReference]
    patterns: list[NamedReference]
    created_at: datetime
    updated_at: datetime


class ProblemListResponse(BaseModel):
    items: list[ProblemResponse]
    total: int
    page: int
    page_size: int


class DuplicateCandidate(BaseModel):
    problem: ProblemResponse
    confidence: float
    reason: str
