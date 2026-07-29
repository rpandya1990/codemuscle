import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from codemuscle.application.queues.schemas import (
    QueueAddItemRequest,
    QueueGenerationRequest,
    QueueItemUpdateRequest,
    QueueResponse,
)
from codemuscle.application.queues.service import QueueService
from codemuscle.infrastructure.database.session import get_session

router = APIRouter(prefix="/queues", tags=["queues"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.post("", response_model=QueueResponse, status_code=201)
def generate_queue(request: QueueGenerationRequest, session: DatabaseSession) -> QueueResponse:
    return QueueService(session).generate(request)


@router.get("/{queue_id}", response_model=QueueResponse)
def get_queue(queue_id: uuid.UUID, session: DatabaseSession) -> QueueResponse:
    return QueueService(session).get(queue_id)


@router.patch("/{queue_id}/items/{item_id}", response_model=QueueResponse)
def update_queue_item(
    queue_id: uuid.UUID,
    item_id: uuid.UUID,
    request: QueueItemUpdateRequest,
    session: DatabaseSession,
) -> QueueResponse:
    return QueueService(session).update_item(queue_id, item_id, request)


@router.delete("/{queue_id}/items/{item_id}", response_model=QueueResponse)
def remove_queue_item(
    queue_id: uuid.UUID, item_id: uuid.UUID, session: DatabaseSession
) -> QueueResponse:
    return QueueService(session).remove_item(queue_id, item_id)


@router.post("/{queue_id}/items/{item_id}/replace", response_model=QueueResponse)
def replace_queue_item(
    queue_id: uuid.UUID, item_id: uuid.UUID, session: DatabaseSession
) -> QueueResponse:
    return QueueService(session).replace_item(queue_id, item_id)


@router.post("/{queue_id}/items", response_model=QueueResponse)
def add_queue_item(
    queue_id: uuid.UUID, request: QueueAddItemRequest, session: DatabaseSession
) -> QueueResponse:
    return QueueService(session).add_item(queue_id, request)


@router.post("/{queue_id}/items/{item_id}/complete", response_model=QueueResponse)
def complete_queue_item(
    queue_id: uuid.UUID, item_id: uuid.UUID, session: DatabaseSession
) -> QueueResponse:
    return QueueService(session).update_item(
        queue_id, item_id, QueueItemUpdateRequest(status="COMPLETED")
    )
