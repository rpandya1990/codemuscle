from pathlib import Path

from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    workspace_path: Path | None
    ai_enabled: bool
    web_origin: str
    default_available_minutes: int = 60
    timezone: str = "UTC"


class SettingsUpdateRequest(BaseModel):
    default_available_minutes: int | None = Field(default=None, ge=5, le=720)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
