import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codemuscle.infrastructure.database.base import Base

if TYPE_CHECKING:
    from codemuscle.infrastructure.database.models.problem import Problem


class QueueSession(Base):
    __tablename__ = "queue_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    available_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    topic_focus_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    requested_problem_count: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    items: Mapped[list["QueueItem"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="QueueItem.position"
    )


class QueueItem(Base):
    __tablename__ = "queue_items"
    __table_args__ = (Index("ix_queue_items_session_position", "queue_session_id", "position"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    queue_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("queue_sessions.id", ondelete="CASCADE"), nullable=False
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendation_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[QueueSession] = relationship(back_populates="items")
    problem: Mapped["Problem"] = relationship()
