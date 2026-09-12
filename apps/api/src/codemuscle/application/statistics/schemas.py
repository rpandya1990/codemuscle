import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

TrendInterval = Literal["day", "week", "month", "year"]


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
    independently_solved_problems: int
    health_rate: float
    total_attempts: int
    independent_successes: int
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
    period_start: date
    week_start: date  # Compatibility for existing weekly clients.
    attempts: int
    independent_successes: int
    failures: int


class TrendsResponse(BaseModel):
    points: list[TrendPoint] = Field(default_factory=list)
