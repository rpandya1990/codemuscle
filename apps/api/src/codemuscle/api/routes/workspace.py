from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from codemuscle.application.settings.service import SettingsService
from codemuscle.application.workspace.schemas import WorkspaceInitializeRequest, WorkspaceResponse
from codemuscle.application.workspace.service import WorkspaceService
from codemuscle.config import Settings, get_settings
from codemuscle.infrastructure.database.session import get_session

router = APIRouter(prefix="/workspace", tags=["workspace"])


def get_workspace_service() -> WorkspaceService:
    return WorkspaceService()


@router.post("/initialize", response_model=WorkspaceResponse, status_code=201)
def initialize_workspace(
    request: WorkspaceInitializeRequest,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> WorkspaceResponse:
    result = service.initialize(request.path)
    SettingsService(session, settings).set_workspace_path(str(result.path))
    return result
