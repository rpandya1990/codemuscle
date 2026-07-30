from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from codemuscle.application.attempts.schemas import AttemptCreate
from codemuscle.application.attempts.service import AttemptService
from codemuscle.application.data_lifecycle.schemas import (
    BackupCreateRequest,
    DeleteDataRequest,
    ExportRequest,
    RestoreRequest,
)
from codemuscle.application.data_lifecycle.service import DataLifecycleService
from codemuscle.application.problems.schemas import ProblemCreate
from codemuscle.application.problems.service import ProblemService
from codemuscle.config import Settings
from codemuscle.domain.enums import AttemptOutcome
from codemuscle.domain.exceptions import DataLifecycleError
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import Problem


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    for name in ("imports", "exports", "backups"):
        (tmp_path / name).mkdir()
    return tmp_path


def service(session: Session, workspace: Path) -> DataLifecycleService:
    return DataLifecycleService(session, Settings(workspace_path=workspace))


@pytest.mark.parametrize(
    ("format_name", "suffix"), [("CSV", ".csv"), ("JSON", ".json"), ("XLSX", ".xlsx")]
)
def test_exports_create_private_artifacts(
    session: Session, workspace: Path, format_name: str, suffix: str
) -> None:
    ProblemService(session).create(ProblemCreate(title="Two Sum", topics=["Arrays"]))
    result = service(session, workspace).export(ExportRequest(format=format_name))
    assert result.problem_count == 1
    assert result.filename.endswith(suffix)
    assert (workspace / "exports" / result.filename).is_file()


def test_backup_restore_replaces_database_transactionally(
    session: Session, workspace: Path
) -> None:
    problems = ProblemService(session)
    preserved = problems.create(ProblemCreate(title="Preserved"))
    AttemptService(session).create(
        preserved.id, AttemptCreate(outcome=AttemptOutcome.SOLVED_INDEPENDENTLY)
    )
    lifecycle = service(session, workspace)
    backup = lifecycle.create_backup(BackupCreateRequest())
    problems.create(ProblemCreate(title="Created later"))

    restored = lifecycle.restore(backup.id, RestoreRequest(confirmation="RESTORE"))
    titles = set(session.scalars(select(Problem.title)))
    assert restored.status == "COMPLETED"
    assert titles == {"Preserved"}
    assert ProblemService(session).get(preserved.id).total_attempts == 1


def test_restore_and_delete_require_exact_confirmation(session: Session, workspace: Path) -> None:
    lifecycle = service(session, workspace)
    backup = lifecycle.create_backup(BackupCreateRequest())
    with pytest.raises(DataLifecycleError):
        lifecycle.restore(backup.id, RestoreRequest(confirmation="yes"))
    with pytest.raises(DataLifecycleError):
        lifecycle.delete_all(DeleteDataRequest(confirmation="yes"))


def test_delete_clears_selected_data_and_preserves_backups(
    session: Session, workspace: Path
) -> None:
    ProblemService(session).create(ProblemCreate(title="Delete me"))
    lifecycle = service(session, workspace)
    backup = lifecycle.create_backup(BackupCreateRequest())
    (workspace / "imports" / "private.csv").write_text("secret", encoding="utf-8")

    result = lifecycle.delete_all(
        DeleteDataRequest(confirmation="DELETE ALL DATA", delete_backup_files=False)
    )
    assert session.scalar(select(Problem)) is None
    assert list((workspace / "imports").iterdir()) == []
    assert (workspace / "backups" / backup.filename).is_file()
    assert result.backups_preserved is True
