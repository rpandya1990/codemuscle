import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from codemuscle.infrastructure.database.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_path: Mapped[str | None] = mapped_column(String(2048))
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", nullable=False)
    default_available_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    successful_intervals: Mapped[list[int]] = mapped_column(
        JSON, default=lambda: [1, 3, 7, 14, 30, 60], nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
