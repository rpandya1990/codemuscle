from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from codemuscle.application.statistics.schemas import (
    AreaStatistics,
    DashboardStatistics,
    TrendsResponse,
)
from codemuscle.application.statistics.service import StatisticsService
from codemuscle.infrastructure.database.session import get_session

router = APIRouter(prefix="/statistics", tags=["statistics"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get("/dashboard", response_model=DashboardStatistics)
def dashboard(session: DatabaseSession) -> DashboardStatistics:
    return StatisticsService(session).dashboard()


@router.get("/topics", response_model=list[AreaStatistics])
def topic_statistics(session: DatabaseSession) -> list[AreaStatistics]:
    return StatisticsService(session).topics()


@router.get("/patterns", response_model=list[AreaStatistics])
def pattern_statistics(session: DatabaseSession) -> list[AreaStatistics]:
    return StatisticsService(session).patterns()


@router.get("/trends", response_model=TrendsResponse)
def trends(
    session: DatabaseSession, weeks: Annotated[int, Query(ge=1, le=52)] = 8
) -> TrendsResponse:
    return StatisticsService(session).trends(weeks)


@router.get("/weak-areas", response_model=list[AreaStatistics])
def weak_areas(session: DatabaseSession) -> list[AreaStatistics]:
    return StatisticsService(session).weak_areas()
