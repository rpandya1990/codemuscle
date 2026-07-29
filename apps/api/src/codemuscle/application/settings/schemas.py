from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class SettingsResponse(BaseModel):
    workspace_path: Path | None
    ai_enabled: bool
    web_origin: str
    default_available_minutes: int = 60
    timezone: str = "UTC"
    successful_intervals: list[int] = Field(default_factory=lambda: [1, 3, 7, 14, 30, 60])


class SettingsUpdateRequest(BaseModel):
    default_available_minutes: int | None = Field(default=None, ge=5, le=720)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    successful_intervals: list[int] | None = Field(default=None, min_length=1, max_length=20)

    @field_validator("successful_intervals")
    @classmethod
    def validate_intervals(cls, value: list[int] | None) -> list[int] | None:
        if value is not None and (
            any(day < 1 or day > 3650 for day in value) or value != sorted(set(value))
        ):
            raise ValueError("Intervals must be unique ascending days from 1 to 3650.")
        return value
