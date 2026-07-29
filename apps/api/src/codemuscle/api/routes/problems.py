import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from codemuscle.application.problems.schemas import (
    DuplicateCandidate,
    ProblemCreate,
    ProblemListResponse,
    ProblemResponse,
    ProblemUpdate,
)
from codemuscle.application.problems.service import ProblemService
from codemuscle.domain.enums import Difficulty, MasteryState
from codemuscle.infrastructure.database.session import get_session

router = APIRouter(prefix="/problems", tags=["problems"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get("/duplicates", response_model=list[DuplicateCandidate])
def find_duplicates(
    session: DatabaseSession,
    title: str | None = None,
    url: str | None = None,
    platform: str | None = None,
    platform_identifier: str | None = None,
) -> list[DuplicateCandidate]:
    return ProblemService(session).duplicates(
        title=title, url=url, platform=platform, platform_identifier=platform_identifier
    )


@router.get("", response_model=ProblemListResponse)
def list_problems(
    session: DatabaseSession,
    search: str | None = None,
    topic_id: uuid.UUID | None = None,
    pattern_id: uuid.UUID | None = None,
    difficulty: Difficulty | None = None,
    mastery_state: MasteryState | None = None,
    platform: str | None = None,
    archived: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=5000)] = 25,
) -> ProblemListResponse:
    return ProblemService(session).list(
        search=search,
        topic_id=topic_id,
        pattern_id=pattern_id,
        difficulty=difficulty,
        mastery_state=mastery_state,
        platform=platform,
        archived=archived,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ProblemResponse, status_code=201)
def create_problem(data: ProblemCreate, session: DatabaseSession) -> ProblemResponse:
    return ProblemService(session).create(data)


@router.get("/{problem_id}", response_model=ProblemResponse)
def get_problem(problem_id: uuid.UUID, session: DatabaseSession) -> ProblemResponse:
    return ProblemService(session).get(problem_id)


@router.patch("/{problem_id}", response_model=ProblemResponse)
def update_problem(
    problem_id: uuid.UUID, data: ProblemUpdate, session: DatabaseSession
) -> ProblemResponse:
    return ProblemService(session).update(problem_id, data)


@router.post("/{problem_id}/archive", response_model=ProblemResponse)
def archive_problem(problem_id: uuid.UUID, session: DatabaseSession) -> ProblemResponse:
    return ProblemService(session).archive(problem_id)


@router.post("/{problem_id}/restore", response_model=ProblemResponse)
def restore_problem(problem_id: uuid.UUID, session: DatabaseSession) -> ProblemResponse:
    return ProblemService(session).restore(problem_id)
