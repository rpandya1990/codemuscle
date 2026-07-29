from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from codemuscle.application.imports.schemas import (
    ImportCommitRequest,
    ImportRetryRequest,
)
from codemuscle.application.imports.service import ImportService
from codemuscle.application.problems.schemas import ProblemCreate
from codemuscle.application.problems.service import ProblemService
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import ImportJob, ImportRow, Problem  # noqa: F401


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def test_preview_partial_commit_retry_and_traceability(session: Session, tmp_path: Path) -> None:
    ProblemService(session).create(ProblemCreate(title="Two Sum"))
    service = ImportService(session, tmp_path)
    uploaded = service.upload(
        "history.csv",
        (
            b"Problem Title,Difficulty,Topic,Number of Revisions\n"
            b"Binary Search,Easy,Searching,3\n"
            b"Two Sum,Easy,Arrays,2\n"
            b",Hard,Graphs,1\n"
        ),
    )

    assert uploaded.mapping["title"] == "Problem Title"
    preview = service.preview(uploaded.id)
    assert (preview.valid_rows, preview.duplicate_rows, preview.invalid_rows) == (1, 1, 1)
    invalid_row = next(row for row in preview.rows if row.status == "INVALID")

    first_commit = service.commit(uploaded.id, ImportCommitRequest())
    assert first_commit.imported == 1
    assert first_commit.skipped_duplicates == 1
    assert first_commit.skipped_invalid == 1

    retried = service.retry(
        uploaded.id,
        ImportRetryRequest(corrections={invalid_row.id: {"title": "Course Schedule"}}),
    )
    assert next(row for row in retried.rows if row.id == invalid_row.id).status == "VALID"
    second_commit = service.commit(uploaded.id, ImportCommitRequest())
    assert second_commit.imported == 1

    imported = session.scalars(select(Problem).where(Problem.import_job_id == uploaded.id)).all()
    assert {problem.title for problem in imported} == {"Binary Search", "Course Schedule"}
    binary_search = next(problem for problem in imported if problem.title == "Binary Search")
    assert binary_search.legacy_import_metadata == {"revision_count": "3"}


def test_duplicate_row_can_be_explicitly_accepted(session: Session, tmp_path: Path) -> None:
    ProblemService(session).create(ProblemCreate(title="Two Sum"))
    service = ImportService(session, tmp_path)
    uploaded = service.upload("one.csv", b"Problem Title\nTwo Sum\n")
    preview = service.preview(uploaded.id)
    duplicate = preview.rows[0]

    result = service.commit(
        uploaded.id,
        ImportCommitRequest(include_duplicate_row_ids=[duplicate.id]),
    )

    assert result.imported == 1


def test_suggested_mapping_recognizes_verified_csv_headers(
    session: Session, tmp_path: Path
) -> None:
    service = ImportService(session, tmp_path)
    uploaded = service.upload(
        "verified.csv",
        (
            b"Problem title,Last revised date,Successful streak,Next revision date\n"
            b"Two Sum,2026-04-27,5,2026-05-01\n"
        ),
    )

    assert uploaded.mapping["last_revised_date"] == "Last revised date"
    assert uploaded.mapping["successful_streak"] == "Successful streak"
