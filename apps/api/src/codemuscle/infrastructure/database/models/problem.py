import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codemuscle.domain.enums import Difficulty, MasteryState
from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from codemuscle.infrastructure.database.models.attempt import Attempt

problem_topics = Table(
    "problem_topics",
    Base.metadata,
    Column("problem_id", ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
)

problem_patterns = Table(
    "problem_patterns",
    Base.metadata,
    Column("problem_id", ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True),
    Column("pattern_id", ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True),
)


class Problem(TimestampMixin, Base):
    __tablename__ = "problems"
    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="priority_range"),
        CheckConstraint(
            "estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0",
            name="positive_estimated_duration",
        ),
        Index("ix_problems_mastery_state", "current_mastery_state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(2048))
    normalized_url: Mapped[str | None] = mapped_column(String(2048), index=True)
    platform: Mapped[str | None] = mapped_column(String(100))
    platform_identifier: Mapped[str | None] = mapped_column(String(255))
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty"), default=Difficulty.UNKNOWN, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    date_added: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    current_mastery_state: Mapped[MasteryState] = mapped_column(
        Enum(MasteryState, name="mastery_state"), default=MasteryState.NEW, nullable=False
    )
    mastery_overridden: Mapped[bool] = mapped_column(default=False, nullable=False)
    next_revision_date: Mapped[date | None] = mapped_column(Date, index=True)
    calculated_next_revision_date: Mapped[date | None] = mapped_column(Date)
    next_revision_overridden: Mapped[bool] = mapped_column(default=False, nullable=False)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    successful_revision_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    import_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("import_jobs.id"), index=True
    )
    legacy_import_metadata: Mapped[dict[str, object] | None] = mapped_column(JSON)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    topics: Mapped[list["Topic"]] = relationship(
        secondary=problem_topics, back_populates="problems"
    )
    patterns: Mapped[list["Pattern"]] = relationship(
        secondary=problem_patterns, back_populates="problems"
    )
    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan", order_by="Attempt.attempted_at"
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    problems: Mapped[list[Problem]] = relationship(
        secondary=problem_topics, back_populates="topics"
    )


class Pattern(Base):
    __tablename__ = "patterns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    problems: Mapped[list[Problem]] = relationship(
        secondary=problem_patterns, back_populates="patterns"
    )
