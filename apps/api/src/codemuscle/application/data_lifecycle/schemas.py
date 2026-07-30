import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExportRequest(BaseModel):
    format: str = Field(pattern="^(CSV|JSON|XLSX)$")
    include_archived: bool = True


class ExportResponse(BaseModel):
    filename: str
    format: str
    status: str
    problem_count: int
    attempt_count: int


class BackupCreateRequest(BaseModel):
    include_imports: bool = False
    include_exports: bool = False


class BackupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    manifest_version: int
    application_version: str
    status: str
    created_at: datetime


class RestoreRequest(BaseModel):
    confirmation: str


class RestoreResponse(BaseModel):
    backup_id: uuid.UUID
    status: str
    restored_tables: int
    restored_rows: int


class DeleteDataRequest(BaseModel):
    confirmation: str
    delete_import_files: bool = True
    delete_export_files: bool = True
    delete_backup_files: bool = False


class DeleteDataResponse(BaseModel):
    status: str
    deleted_rows: int
    cleared_directories: list[str]
    backups_preserved: bool
