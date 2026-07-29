import re
import uuid
from pathlib import Path

from pydantic import HttpUrl, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from codemuscle.application.imports.parser import read_tabular_file
from codemuscle.application.imports.schemas import (
    ImportCommitRequest,
    ImportCommitResponse,
    ImportJobResponse,
    ImportRetryRequest,
)
from codemuscle.application.problems.schemas import ProblemCreate
from codemuscle.application.problems.service import ProblemService
from codemuscle.domain.enums import Difficulty
from codemuscle.domain.exceptions import ImportFileError, ImportNotFoundError
from codemuscle.infrastructure.database.models.import_job import ImportJob, ImportRow

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("problem title", "title", "problem"),
    "url": ("problem link", "url", "link"),
    "difficulty": ("difficulty",),
    "notes": ("notes",),
    "topic": ("topic", "topics"),
    "pattern": ("pattern", "patterns"),
    "last_revised_date": (
        "last revised or solved date",
        "last revised date",
        "last revised",
        "last solved date",
    ),
    "revision_count": ("number of revisions", "revision count"),
    "successful_streak": (
        "number of successful continuous revisions",
        "successful revision streak",
        "successful streak",
    ),
    "next_revision_date": ("next revision date",),
}


class ImportService:
    max_file_size = 10 * 1024 * 1024

    def __init__(self, session: Session, workspace_path: Path) -> None:
        self.session = session
        self.imports_path = workspace_path / "imports"

    def upload(self, filename: str, content: bytes) -> ImportJobResponse:
        suffix = Path(filename).suffix.casefold()
        if suffix not in {".csv", ".xlsx"}:
            raise ImportFileError("Only .csv and .xlsx files are supported.")
        if not content or len(content) > self.max_file_size:
            raise ImportFileError("The import file must be between 1 byte and 10 MB.")
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)
        stored_name = f"{uuid.uuid4()}_{safe_name}"
        self.imports_path.mkdir(parents=True, exist_ok=True)
        destination = self.imports_path / stored_name
        destination.write_bytes(content)
        try:
            headers, _rows = read_tabular_file(destination)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        job = ImportJob(
            original_filename=Path(filename).name,
            stored_filename=stored_name,
            headers=headers,
            mapping=self._suggest_mapping(headers),
            status="UPLOADED",
        )
        self.session.add(job)
        self.session.commit()
        return self.get(job.id)

    def get(self, import_id: uuid.UUID) -> ImportJobResponse:
        job = self.session.scalar(
            select(ImportJob).options(selectinload(ImportJob.rows)).where(ImportJob.id == import_id)
        )
        if job is None:
            raise ImportNotFoundError(import_id)
        return ImportJobResponse.model_validate(job)

    def set_mapping(self, import_id: uuid.UUID, mapping: dict[str, str]) -> ImportJobResponse:
        job = self._get_model(import_id)
        selected_mapping = {field: header for field, header in mapping.items() if header}
        unknown_fields = set(selected_mapping) - set(FIELD_ALIASES)
        unknown_headers = set(selected_mapping.values()) - set(job.headers)
        if unknown_fields or unknown_headers or "title" not in selected_mapping:
            raise ImportFileError(
                "Mapping must include title and reference only supported fields and headers."
            )
        job.mapping = selected_mapping
        job.status = "MAPPED"
        self.session.commit()
        return self.get(import_id)

    def preview(self, import_id: uuid.UUID) -> ImportJobResponse:
        job = self._get_model(import_id)
        if not job.mapping.get("title"):
            raise ImportFileError("Map a title column before previewing the import.")
        _headers, source_rows = read_tabular_file(self.imports_path / job.stored_filename)
        imported_row_numbers = {row.row_number for row in job.rows if row.status == "IMPORTED"}
        for row in list(job.rows):
            if row.status != "IMPORTED":
                self.session.delete(row)
        self.session.flush()
        for number, raw in enumerate(source_rows, start=2):
            if number in imported_row_numbers:
                continue
            parsed = {field: raw.get(header) for field, header in job.mapping.items()}
            job.rows.append(self._build_row(job.id, number, raw, parsed))
        self._update_counts(job)
        job.status = "PREVIEWED"
        self.session.commit()
        return self.get(import_id)

    def retry(self, import_id: uuid.UUID, request: ImportRetryRequest) -> ImportJobResponse:
        job = self._get_model(import_id)
        rows_by_id = {row.id: row for row in job.rows}
        for row_id, corrections in request.corrections.items():
            row = rows_by_id.get(row_id)
            if row is None or row.status == "IMPORTED":
                continue
            parsed = dict(row.parsed_data or {})
            parsed.update(corrections)
            replacement = self._build_row(job.id, row.row_number, row.raw_data, parsed)
            row.parsed_data = replacement.parsed_data
            row.errors = replacement.errors
            row.duplicate_problem_ids = replacement.duplicate_problem_ids
            row.status = replacement.status
        self._update_counts(job)
        self.session.commit()
        return self.get(import_id)

    def commit(self, import_id: uuid.UUID, request: ImportCommitRequest) -> ImportCommitResponse:
        job = self._get_model(import_id)
        accepted_duplicates = set(request.include_duplicate_row_ids)
        imported = 0
        skipped_invalid = 0
        skipped_duplicates = 0
        problem_service = ProblemService(self.session)
        for row in job.rows:
            if row.status == "IMPORTED":
                continue
            if row.status == "INVALID":
                skipped_invalid += 1
                continue
            if row.status == "DUPLICATE" and row.id not in accepted_duplicates:
                skipped_duplicates += 1
                continue
            assert row.parsed_data is not None
            data = self._problem_create(row.parsed_data)
            legacy = {
                key: value
                for key, value in row.parsed_data.items()
                if key
                in {
                    "last_revised_date",
                    "revision_count",
                    "successful_streak",
                    "next_revision_date",
                }
                and value not in (None, "")
            }
            problem = problem_service.add(data, import_job_id=job.id, legacy_import_metadata=legacy)
            row.created_problem_id = problem.id
            row.status = "IMPORTED"
            imported += 1
        job.status = "COMPLETED" if skipped_invalid == 0 else "PARTIALLY_COMPLETED"
        self._update_counts(job)
        self.session.commit()
        return ImportCommitResponse(
            import_id=job.id,
            imported=imported,
            skipped_invalid=skipped_invalid,
            skipped_duplicates=skipped_duplicates,
        )

    def _build_row(
        self,
        job_id: uuid.UUID,
        number: int,
        raw: dict[str, object],
        parsed: dict[str, object],
    ) -> ImportRow:
        errors: dict[str, list[str]] = {}
        try:
            data = self._problem_create(parsed)
        except ValidationError as error:
            for item in error.errors():
                field = str(item["loc"][0]) if item["loc"] else "row"
                errors.setdefault(field, []).append(str(item["msg"]))
            data = None
        duplicate_ids: list[str] = []
        if data is not None:
            duplicates = ProblemService(self.session).duplicates(
                title=data.title,
                url=str(data.url) if data.url else None,
                platform=data.platform,
                platform_identifier=data.platform_identifier,
            )
            duplicate_ids = [str(candidate.problem.id) for candidate in duplicates]
        status = "INVALID" if errors else "DUPLICATE" if duplicate_ids else "VALID"
        return ImportRow(
            import_job_id=job_id,
            row_number=number,
            raw_data=raw,
            parsed_data=parsed,
            errors=errors,
            duplicate_problem_ids=duplicate_ids,
            status=status,
        )

    @staticmethod
    def _problem_create(parsed: dict[str, object]) -> ProblemCreate:
        difficulty_value = str(parsed.get("difficulty") or "UNKNOWN").strip().upper()
        difficulty = (
            Difficulty(difficulty_value) if difficulty_value in Difficulty else Difficulty.UNKNOWN
        )
        url_value = str(parsed["url"]).strip() if parsed.get("url") else None
        return ProblemCreate(
            title=str(parsed.get("title") or "").strip(),
            url=HttpUrl(url_value) if url_value else None,
            difficulty=difficulty,
            notes=str(parsed["notes"]) if parsed.get("notes") else None,
            topics=ImportService._split_values(parsed.get("topic")),
            patterns=ImportService._split_values(parsed.get("pattern")),
        )

    @staticmethod
    def _split_values(value: object) -> list[str]:
        return [item.strip() for item in re.split(r"[,;|]", str(value or "")) if item.strip()]

    @staticmethod
    def _suggest_mapping(headers: list[str]) -> dict[str, str]:
        normalized = {" ".join(header.casefold().split()): header for header in headers}
        return {
            field: normalized[alias]
            for field, aliases in FIELD_ALIASES.items()
            for alias in aliases
            if alias in normalized
        }

    def _get_model(self, import_id: uuid.UUID) -> ImportJob:
        job = self.session.scalar(
            select(ImportJob).options(selectinload(ImportJob.rows)).where(ImportJob.id == import_id)
        )
        if job is None:
            raise ImportNotFoundError(import_id)
        return job

    @staticmethod
    def _update_counts(job: ImportJob) -> None:
        pending = [row for row in job.rows if row.status != "IMPORTED"]
        job.total_rows = len(job.rows)
        job.valid_rows = sum(row.status == "VALID" for row in pending)
        job.invalid_rows = sum(row.status == "INVALID" for row in pending)
        job.duplicate_rows = sum(row.status == "DUPLICATE" for row in pending)
