from __future__ import annotations

import uuid
from datetime import UTC, datetime
from difflib import SequenceMatcher
from typing import TypeVar

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.elements import ColumnElement

from codemuscle.application.problems.normalization import (
    normalize_name,
    normalize_title,
    normalize_url,
)
from codemuscle.application.problems.schemas import (
    DuplicateCandidate,
    ProblemCreate,
    ProblemListResponse,
    ProblemResponse,
    ProblemUpdate,
)
from codemuscle.domain.enums import Difficulty, MasteryState
from codemuscle.domain.exceptions import ProblemNotFoundError
from codemuscle.infrastructure.database.models.problem import Pattern, Problem, Topic

NamedModel = TypeVar("NamedModel", Topic, Pattern)


class ProblemService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: ProblemCreate) -> ProblemResponse:
        problem = self.add(data)
        self.session.commit()
        return self.get(problem.id)

    def add(self, data: ProblemCreate) -> Problem:
        problem = Problem(
            title=data.title,
            normalized_title=normalize_title(data.title),
            url=str(data.url) if data.url else None,
            normalized_url=normalize_url(str(data.url)) if data.url else None,
            platform=data.platform,
            platform_identifier=data.platform_identifier,
            difficulty=data.difficulty,
            notes=data.notes,
            priority=data.priority,
            estimated_duration_minutes=data.estimated_duration_minutes,
            topics=self._resolve_names(Topic, data.topics),
            patterns=self._resolve_names(Pattern, data.patterns),
        )
        self.session.add(problem)
        self.session.flush()
        return problem

    def get(self, problem_id: uuid.UUID) -> ProblemResponse:
        problem = self.session.scalar(self._base_query().where(Problem.id == problem_id))
        if problem is None:
            raise ProblemNotFoundError(problem_id)
        return ProblemResponse.model_validate(problem)

    def update(self, problem_id: uuid.UUID, data: ProblemUpdate) -> ProblemResponse:
        problem = self._get_model(problem_id)
        values = data.model_dump(exclude_unset=True, exclude={"topics", "patterns"})
        if "url" in values:
            url = str(values["url"]) if values["url"] else None
            values["url"] = url
            problem.normalized_url = normalize_url(url)
        if "title" in values:
            problem.normalized_title = normalize_title(str(values["title"]))
        for field, value in values.items():
            setattr(problem, field, value)
        if data.topics is not None:
            problem.topics = self._resolve_names(Topic, data.topics)
        if data.patterns is not None:
            problem.patterns = self._resolve_names(Pattern, data.patterns)
        self.session.commit()
        return self.get(problem_id)

    def archive(self, problem_id: uuid.UUID) -> ProblemResponse:
        problem = self._get_model(problem_id)
        problem.archived_at = datetime.now(UTC)
        self.session.commit()
        return self.get(problem_id)

    def restore(self, problem_id: uuid.UUID) -> ProblemResponse:
        problem = self._get_model(problem_id)
        problem.archived_at = None
        self.session.commit()
        return self.get(problem_id)

    def list(
        self,
        *,
        search: str | None = None,
        topic_id: uuid.UUID | None = None,
        pattern_id: uuid.UUID | None = None,
        difficulty: Difficulty | None = None,
        mastery_state: MasteryState | None = None,
        platform: str | None = None,
        archived: bool = False,
        page: int = 1,
        page_size: int = 25,
    ) -> ProblemListResponse:
        query: Select[tuple[Problem]] = select(Problem)
        if search:
            term = f"%{normalize_name(search)}%"
            query = query.where(
                or_(func.lower(Problem.title).like(term), func.lower(Problem.notes).like(term))
            )
        if topic_id:
            query = query.where(Problem.topics.any(Topic.id == topic_id))
        if pattern_id:
            query = query.where(Problem.patterns.any(Pattern.id == pattern_id))
        if difficulty:
            query = query.where(Problem.difficulty == difficulty)
        if mastery_state:
            query = query.where(Problem.current_mastery_state == mastery_state)
        if platform:
            query = query.where(func.lower(Problem.platform) == normalize_name(platform))
        query = query.where(
            Problem.archived_at.is_not(None) if archived else Problem.archived_at.is_(None)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.session.scalars(
            query.options(selectinload(Problem.topics), selectinload(Problem.patterns))
            .order_by(Problem.created_at.desc(), Problem.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return ProblemListResponse(
            items=[ProblemResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def duplicates(
        self,
        *,
        title: str | None,
        url: str | None,
        platform: str | None,
        platform_identifier: str | None,
    ) -> list[DuplicateCandidate]:
        candidates: dict[uuid.UUID, DuplicateCandidate] = {}
        checks: list[tuple[ColumnElement[bool], float, str]] = []
        if url and (normalized := normalize_url(url)):
            checks.append((Problem.normalized_url == normalized, 1.0, "Exact normalized URL match"))
        if platform and platform_identifier:
            checks.append(
                (
                    (func.lower(Problem.platform) == normalize_name(platform))
                    & (Problem.platform_identifier == platform_identifier),
                    1.0,
                    "Exact platform identifier match",
                )
            )
        if title:
            checks.append(
                (
                    Problem.normalized_title == normalize_title(title),
                    0.9,
                    "Exact normalized title match",
                )
            )
        for condition, confidence, reason in checks:
            for problem in self.session.scalars(self._base_query().where(condition)).unique():
                existing = candidates.get(problem.id)
                if existing is None or existing.confidence < confidence:
                    candidates[problem.id] = DuplicateCandidate(
                        problem=ProblemResponse.model_validate(problem),
                        confidence=confidence,
                        reason=reason,
                    )
        if title:
            normalized_title = normalize_title(title)
            for problem in self.session.scalars(self._base_query()).unique():
                similarity = SequenceMatcher(
                    None, normalized_title, problem.normalized_title
                ).ratio()
                if similarity >= 0.65 and problem.id not in candidates:
                    candidates[problem.id] = DuplicateCandidate(
                        problem=ProblemResponse.model_validate(problem),
                        confidence=round(similarity * 0.8, 2),
                        reason="Similar normalized title",
                    )
        return sorted(candidates.values(), key=lambda item: (-item.confidence, item.problem.title))

    def _get_model(self, problem_id: uuid.UUID) -> Problem:
        problem = self.session.get(Problem, problem_id)
        if problem is None:
            raise ProblemNotFoundError(problem_id)
        return problem

    def _base_query(self) -> Select[tuple[Problem]]:
        return select(Problem).options(selectinload(Problem.topics), selectinload(Problem.patterns))

    def _resolve_names(self, model: type[NamedModel], names: list[str]) -> list[NamedModel]:
        resolved: list[NamedModel] = []
        seen: set[str] = set()
        for name in names:
            normalized = normalize_name(name)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            item = self.session.scalar(select(model).where(model.normalized_name == normalized))
            if item is None:
                item = model(name=name.strip(), normalized_name=normalized)
                self.session.add(item)
            resolved.append(item)
        return resolved
