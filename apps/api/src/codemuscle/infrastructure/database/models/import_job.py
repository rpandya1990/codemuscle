import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codemuscle.infrastructure.database.base import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="UPLOADED")
    headers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    mapping: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    rows: Mapped[list["ImportRow"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="ImportRow.row_number"
    )


class ImportRow(Base):
    __tablename__ = "import_rows"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    import_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    parsed_data: Mapped[dict[str, object] | None] = mapped_column(JSON)
    errors: Mapped[dict[str, list[str]]] = mapped_column(JSON, nullable=False, default=dict)
    duplicate_problem_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_problem_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("problems.id"))
    retry_notes: Mapped[str | None] = mapped_column(Text)

    job: Mapped[ImportJob] = relationship(back_populates="rows")
