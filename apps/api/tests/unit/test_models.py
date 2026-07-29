from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from codemuscle.application.settings.schemas import SettingsUpdateRequest
from codemuscle.application.settings.service import SettingsService
from codemuscle.config import Settings
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import (  # noqa: F401
    Attempt,
    BackupRecord,
    Pattern,
    Problem,
    Topic,
    UserPreference,
)


def test_core_model_metadata_contains_milestone_one_tables() -> None:
    assert {
        "problems",
        "topics",
        "patterns",
        "problem_topics",
        "problem_patterns",
        "attempts",
        "user_preferences",
        "backup_records",
        "import_jobs",
        "import_rows",
    }.issubset(Base.metadata.tables)


def test_settings_service_persists_preferences() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = SettingsService(session, Settings())
        updated = service.update(
            SettingsUpdateRequest(default_available_minutes=90, timezone="America/Los_Angeles")
        )

    with Session(engine) as session:
        persisted = SettingsService(session, Settings()).get()

    assert updated.default_available_minutes == 90
    assert persisted.default_available_minutes == 90
    assert persisted.timezone == "America/Los_Angeles"
