from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from codemuscle.application.settings.schemas import SettingsResponse, SettingsUpdateRequest
from codemuscle.config import Settings
from codemuscle.domain.defaults import DEFAULT_SUCCESS_INTERVALS
from codemuscle.infrastructure.database.models.settings import UserPreference


class SettingsService:
    def __init__(self, session: Session, runtime_settings: Settings) -> None:
        self.session = session
        self.runtime_settings = runtime_settings

    def get(self) -> SettingsResponse:
        preference = self._get_preference()
        stored_workspace_path = preference.workspace_path if preference else None
        return SettingsResponse(
            workspace_path=(
                Path(stored_workspace_path)
                if stored_workspace_path is not None
                else self.runtime_settings.workspace_path
            ),
            ai_enabled=self.runtime_settings.ai_enabled,
            web_origin=str(self.runtime_settings.web_origin).rstrip("/"),
            default_available_minutes=(preference.default_available_minutes if preference else 60),
            timezone=preference.timezone if preference else "UTC",
            successful_intervals=(
                preference.successful_intervals
                if preference
                else list(DEFAULT_SUCCESS_INTERVALS)
            ),
        )

    def update(self, request: SettingsUpdateRequest) -> SettingsResponse:
        preference = self._get_or_create_preference()
        for field, value in request.model_dump(exclude_none=True).items():
            setattr(preference, field, value)
        self.session.commit()
        self.session.refresh(preference)
        return self.get()

    def set_workspace_path(self, path: str) -> None:
        preference = self._get_or_create_preference()
        preference.workspace_path = path
        self.session.commit()

    def _get_preference(self) -> UserPreference | None:
        return self.session.scalar(select(UserPreference).limit(1))

    def _get_or_create_preference(self) -> UserPreference:
        preference = self._get_preference()
        if preference is None:
            preference = UserPreference()
            self.session.add(preference)
        return preference
