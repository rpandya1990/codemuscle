import uuid

from pydantic import BaseModel, ConfigDict, Field


class ImportMappingRequest(BaseModel):
    mapping: dict[str, str]


class ImportRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    row_number: int
    raw_data: dict[str, object]
    parsed_data: dict[str, object] | None
    errors: dict[str, list[str]]
    duplicate_problem_ids: list[str]
    status: str
    created_problem_id: uuid.UUID | None


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    status: str
    headers: list[str]
    mapping: dict[str, str]
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    rows: list[ImportRowResponse] = Field(default_factory=list)


class ImportCommitRequest(BaseModel):
    include_duplicate_row_ids: list[uuid.UUID] = Field(default_factory=list)


class ImportCommitResponse(BaseModel):
    import_id: uuid.UUID
    imported: int
    skipped_invalid: int
    skipped_duplicates: int


class ImportRetryRequest(BaseModel):
    corrections: dict[uuid.UUID, dict[str, object]]
