from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkspaceInitializeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    path: Path

    @field_validator("path")
    @classmethod
    def require_absolute_path(cls, value: Path) -> Path:
        expanded = value.expanduser()
        if not expanded.is_absolute():
            raise ValueError("Workspace path must be absolute")
        return expanded.resolve()


class WorkspaceManifest(BaseModel):
    workspace_version: int = Field(default=1, ge=1)
    created_at: datetime
    exports_directory: str = "exports"
    backups_directory: str = "backups"


class WorkspaceResponse(BaseModel):
    path: Path
    manifest: WorkspaceManifest
