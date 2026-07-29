import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from codemuscle.application.imports.schemas import (
    ImportCommitRequest,
    ImportCommitResponse,
    ImportJobResponse,
    ImportMappingRequest,
    ImportRetryRequest,
)
from codemuscle.application.imports.service import ImportService
from codemuscle.application.settings.service import SettingsService
from codemuscle.config import Settings, get_settings
from codemuscle.domain.exceptions import ImportFileError, WorkspaceNotInitializedError
from codemuscle.infrastructure.database.session import get_session

router = APIRouter(prefix="/imports", tags=["imports"])
DatabaseSession = Annotated[Session, Depends(get_session)]
RuntimeSettings = Annotated[Settings, Depends(get_settings)]


def get_import_service(session: Session, settings: Settings) -> ImportService:
    workspace_path = SettingsService(session, settings).get().workspace_path
    if workspace_path is None:
        raise WorkspaceNotInitializedError()
    return ImportService(session, Path(workspace_path))


@router.post("", response_model=ImportJobResponse, status_code=201)
async def upload_import(
    session: DatabaseSession,
    settings: RuntimeSettings,
    file: Annotated[UploadFile, File()],
) -> ImportJobResponse:
    if not file.filename:
        raise ImportFileError("The uploaded file must have a filename.")
    content = await file.read(ImportService.max_file_size + 1)
    return get_import_service(session, settings).upload(file.filename, content)


@router.get("/{import_id}", response_model=ImportJobResponse)
def get_import(
    import_id: uuid.UUID, session: DatabaseSession, settings: RuntimeSettings
) -> ImportJobResponse:
    return get_import_service(session, settings).get(import_id)


@router.put("/{import_id}/mapping", response_model=ImportJobResponse)
def update_mapping(
    import_id: uuid.UUID,
    request: ImportMappingRequest,
    session: DatabaseSession,
    settings: RuntimeSettings,
) -> ImportJobResponse:
    return get_import_service(session, settings).set_mapping(import_id, request.mapping)


@router.post("/{import_id}/preview", response_model=ImportJobResponse)
def preview_import(
    import_id: uuid.UUID, session: DatabaseSession, settings: RuntimeSettings
) -> ImportJobResponse:
    return get_import_service(session, settings).preview(import_id)


@router.post("/{import_id}/commit", response_model=ImportCommitResponse)
def commit_import(
    import_id: uuid.UUID,
    request: ImportCommitRequest,
    session: DatabaseSession,
    settings: RuntimeSettings,
) -> ImportCommitResponse:
    return get_import_service(session, settings).commit(import_id, request)


@router.post("/{import_id}/retry", response_model=ImportJobResponse)
def retry_import(
    import_id: uuid.UUID,
    request: ImportRetryRequest,
    session: DatabaseSession,
    settings: RuntimeSettings,
) -> ImportJobResponse:
    return get_import_service(session, settings).retry(import_id, request)
