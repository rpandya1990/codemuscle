import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from codemuscle.application.attempts.schemas import (
    AttemptCreate,
    AttemptResponse,
    RecentAttemptResponse,
)
from codemuscle.application.attempts.service import AttemptService
from codemuscle.infrastructure.database.session import get_session

router = APIRouter(tags=["attempts"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.post("/problems/{problem_id}/attempts", response_model=AttemptResponse, status_code=201)
def create_attempt(
    problem_id: uuid.UUID, data: AttemptCreate, session: DatabaseSession
) -> AttemptResponse:
    return AttemptService(session).create(problem_id, data)


@router.get("/problems/{problem_id}/attempts", response_model=list[AttemptResponse])
def list_problem_attempts(problem_id: uuid.UUID, session: DatabaseSession) -> list[AttemptResponse]:
    return AttemptService(session).list_for_problem(problem_id)


@router.get("/attempts/recent", response_model=list[RecentAttemptResponse])
def list_recent_attempts(
    session: DatabaseSession, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[RecentAttemptResponse]:
    return AttemptService(session).recent(limit)
