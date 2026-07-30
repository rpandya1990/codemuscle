import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from codemuscle.application.data_lifecycle.schemas import (
    BackupCreateRequest,
    BackupResponse,
    DeleteDataRequest,
    DeleteDataResponse,
    ExportRequest,
    ExportResponse,
    RestoreRequest,
    RestoreResponse,
)
from codemuscle.application.data_lifecycle.service import DataLifecycleService
from codemuscle.config import Settings, get_settings
from codemuscle.infrastructure.database.session import get_session

router = APIRouter(tags=["data lifecycle"])
DatabaseSession = Annotated[Session, Depends(get_session)]
RuntimeSettings = Annotated[Settings, Depends(get_settings)]


@router.post("/exports", response_model=ExportResponse, status_code=201)
def create_export(
    request: ExportRequest, session: DatabaseSession, settings: RuntimeSettings
) -> ExportResponse:
    return DataLifecycleService(session, settings).export(request)


@router.post("/backups", response_model=BackupResponse, status_code=201)
def create_backup(
    request: BackupCreateRequest, session: DatabaseSession, settings: RuntimeSettings
) -> BackupResponse:
    return DataLifecycleService(session, settings).create_backup(request)


@router.get("/backups", response_model=list[BackupResponse])
def list_backups(session: DatabaseSession, settings: RuntimeSettings) -> list[BackupResponse]:
    return DataLifecycleService(session, settings).list_backups()


@router.post("/backups/{backup_id}/restore", response_model=RestoreResponse)
def restore_backup(
    backup_id: uuid.UUID,
    request: RestoreRequest,
    session: DatabaseSession,
    settings: RuntimeSettings,
) -> RestoreResponse:
    return DataLifecycleService(session, settings).restore(backup_id, request)


@router.delete("/data", response_model=DeleteDataResponse)
def delete_all_data(
    request: DeleteDataRequest, session: DatabaseSession, settings: RuntimeSettings
) -> DeleteDataResponse:
    return DataLifecycleService(session, settings).delete_all(request)
