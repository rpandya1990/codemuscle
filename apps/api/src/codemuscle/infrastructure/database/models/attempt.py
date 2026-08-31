import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codemuscle.domain.enums import AttemptOutcome, MasteryState
from codemuscle.infrastructure.database.base import Base

if TYPE_CHECKING:
    from codemuscle.infrastructure.database.models.problem import Problem


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint(
            "time_spent_minutes IS NULL OR time_spent_minutes >= 0", name="nonnegative_time_spent"
        ),
        Index("ix_attempts_problem_attempted", "problem_id", "attempted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome: Mapped[AttemptOutcome] = mapped_column(
        Enum(AttemptOutcome, name="attempt_outcome"), nullable=False
    )
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    previous_mastery_state: Mapped[MasteryState] = mapped_column(
        Enum(MasteryState, name="mastery_state", create_type=False), nullable=False
    )
    calculated_mastery_state: Mapped[MasteryState] = mapped_column(
        Enum(MasteryState, name="mastery_state", create_type=False), nullable=False
    )
    previous_revision_date: Mapped[date | None] = mapped_column(Date)
    calculated_next_revision_date: Mapped[date] = mapped_column(Date, nullable=False)
    schedule_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    problem: Mapped["Problem"] = relationship(back_populates="attempts")
