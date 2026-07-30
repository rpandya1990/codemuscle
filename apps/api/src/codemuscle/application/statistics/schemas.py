import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class RecentActivity(BaseModel):
    attempt_id: uuid.UUID
    problem_id: uuid.UUID
    problem_title: str
    outcome: str
    attempted_at: datetime


class DashboardStatistics(BaseModel):
    total_active_problems: int
    due_today: int
    overdue: int
    practiced_this_week: int
    mastered: int
    needs_relearning: int
    recent_activity: list[RecentActivity]


class AreaStatistics(BaseModel):
    id: uuid.UUID
    name: str
    total_problems: int
    total_attempts: int
    independent_success_rate: float
    hint_assisted_success_rate: float
    failed_attempt_rate: float
    problems_due: int
    problems_overdue: int
    mastery_distribution: dict[str, int]
    last_practiced_date: date | None
    recent_trend: str
    status: str
    status_reasons: list[str]


class TrendPoint(BaseModel):
    week_start: date
    attempts: int
    independent_successes: int
    failures: int


class TrendsResponse(BaseModel):
    points: list[TrendPoint] = Field(default_factory=list)
