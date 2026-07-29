import uuid
from datetime import date, timedelta

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from codemuscle.application.problems.schemas import ProblemResponse
from codemuscle.application.queues.policy import score_problem, select_candidates
from codemuscle.application.queues.schemas import (
    QueueAddItemRequest,
    QueueGenerationRequest,
    QueueItemResponse,
    QueueItemUpdateRequest,
    QueueResponse,
)
from codemuscle.domain.exceptions import ProblemNotFoundError, QueueNotFoundError
from codemuscle.infrastructure.database.models import Problem, QueueItem, QueueSession, Topic


class QueueService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def generate(self, request: QueueGenerationRequest) -> QueueResponse:
        query = self._problem_query().where(Problem.archived_at.is_(None))
        if request.topic_focus_ids:
            query = query.where(Problem.topics.any(Topic.id.in_(request.topic_focus_ids)))
        problems = list(self.session.scalars(query).unique())
        candidates = [score_problem(problem, date.today()) for problem in problems]
        selected = select_candidates(
            candidates, request.available_minutes, request.requested_problem_count
        )
        queue = QueueSession(
            available_minutes=request.available_minutes,
            topic_focus_ids=[str(topic_id) for topic_id in request.topic_focus_ids],
            requested_problem_count=request.requested_problem_count,
        )
        self.session.add(queue)
        for position, candidate in enumerate(selected, start=1):
            queue.items.append(
                QueueItem(
                    problem_id=candidate.problem.id,
                    position=position,
                    estimated_duration_minutes=candidate.duration,
                    recommendation_score=candidate.score,
                    recommendation_reasons=candidate.reasons,
                )
            )
        self.session.commit()
        return self.get(queue.id)

    def get(self, queue_id: uuid.UUID) -> QueueResponse:
        queue = self._get(queue_id)
        active_items = [item for item in queue.items if item.status != "REMOVED"]
        return QueueResponse(
            id=queue.id,
            available_minutes=queue.available_minutes,
            topic_focus_ids=queue.topic_focus_ids,
            requested_problem_count=queue.requested_problem_count,
            status=queue.status,
            created_at=queue.created_at,
            total_estimated_minutes=sum(
                item.estimated_duration_minutes
                for item in active_items
                if item.status != "POSTPONED"
            ),
            items=[self._item_response(item) for item in active_items],
        )

    def update_item(
        self, queue_id: uuid.UUID, item_id: uuid.UUID, request: QueueItemUpdateRequest
    ) -> QueueResponse:
        queue, item = self._get_item(queue_id, item_id)
        item.status = request.status
        if request.status == "POSTPONED":
            item.problem.next_revision_date = date.today() + timedelta(days=1)
            item.problem.next_revision_overridden = True
        self.session.commit()
        return self.get(queue.id)

    def remove_item(self, queue_id: uuid.UUID, item_id: uuid.UUID) -> QueueResponse:
        queue, item = self._get_item(queue_id, item_id)
        item.status = "REMOVED"
        self.session.commit()
        return self.get(queue.id)

    def add_item(self, queue_id: uuid.UUID, request: QueueAddItemRequest) -> QueueResponse:
        queue = self._get(queue_id)
        problem = self.session.get(Problem, request.problem_id)
        if problem is None:
            raise ProblemNotFoundError(request.problem_id)
        existing = next(
            (
                item
                for item in queue.items
                if item.problem_id == problem.id and item.status != "REMOVED"
            ),
            None,
        )
        if existing is None:
            candidate = score_problem(problem, date.today())
            queue.items.append(
                QueueItem(
                    problem_id=problem.id,
                    position=max((item.position for item in queue.items), default=0) + 1,
                    estimated_duration_minutes=candidate.duration,
                    recommendation_score=candidate.score,
                    recommendation_reasons=["Manually added to queue"],
                )
            )
            self.session.commit()
        return self.get(queue.id)

    def replace_item(self, queue_id: uuid.UUID, item_id: uuid.UUID) -> QueueResponse:
        queue, item = self._get_item(queue_id, item_id)
        excluded = {queue_item.problem_id for queue_item in queue.items}
        problems = self.session.scalars(
            self._problem_query().where(Problem.archived_at.is_(None), Problem.id.not_in(excluded))
        ).unique()
        candidates = sorted(
            (score_problem(problem, date.today()) for problem in problems),
            key=lambda candidate: (-candidate.score, candidate.problem.title),
        )
        if candidates:
            replacement = candidates[0]
            item.problem_id = replacement.problem.id
            item.estimated_duration_minutes = replacement.duration
            item.recommendation_score = replacement.score
            item.recommendation_reasons = ["Replacement recommendation", *replacement.reasons]
            item.status = "PENDING"
            self.session.commit()
        return self.get(queue.id)

    def _get(self, queue_id: uuid.UUID) -> QueueSession:
        queue = self.session.scalar(
            select(QueueSession)
            .where(QueueSession.id == queue_id)
            .options(
                selectinload(QueueSession.items)
                .selectinload(QueueItem.problem)
                .selectinload(Problem.topics),
                selectinload(QueueSession.items)
                .selectinload(QueueItem.problem)
                .selectinload(Problem.patterns),
            )
        )
        if queue is None:
            raise QueueNotFoundError(queue_id)
        return queue

    def _get_item(self, queue_id: uuid.UUID, item_id: uuid.UUID) -> tuple[QueueSession, QueueItem]:
        queue = self._get(queue_id)
        item = next((candidate for candidate in queue.items if candidate.id == item_id), None)
        if item is None:
            raise QueueNotFoundError(queue_id)
        return queue, item

    @staticmethod
    def _item_response(item: QueueItem) -> QueueItemResponse:
        return QueueItemResponse(
            id=item.id,
            position=item.position,
            estimated_duration_minutes=item.estimated_duration_minutes,
            recommendation_score=item.recommendation_score,
            recommendation_reasons=item.recommendation_reasons,
            status=item.status,
            problem=ProblemResponse.model_validate(item.problem),
        )

    @staticmethod
    def _problem_query() -> Select[tuple[Problem]]:
        return select(Problem).options(
            selectinload(Problem.topics),
            selectinload(Problem.patterns),
            selectinload(Problem.attempts),
        )
