from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from codemuscle.application.settings.schemas import SettingsResponse, SettingsUpdateRequest
from codemuscle.application.settings.service import SettingsService
from codemuscle.config import Settings, get_settings
from codemuscle.infrastructure.database.session import get_session

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def read_settings(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> SettingsResponse:
    return SettingsService(session, settings).get()


@router.put("", response_model=SettingsResponse)
def update_settings(
    request: SettingsUpdateRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> SettingsResponse:
    return SettingsService(session, settings).update(request)
