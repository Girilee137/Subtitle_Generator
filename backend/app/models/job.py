import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import JobMode, JobStage, ProcessingStatus


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_project_status", "project_id", "status"),)

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_files.file_id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[JobMode] = mapped_column(Enum(JobMode, name="job_mode"), nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status", create_type=False),
        nullable=False,
        default=ProcessingStatus.QUEUED,
    )
    stage: Mapped[JobStage | None] = mapped_column(
        Enum(JobStage, name="job_stage", values_callable=lambda values: [item.value for item in values])
    )
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    chunks_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship(back_populates="jobs")
    media_file: Mapped["MediaFile"] = relationship(back_populates="jobs")
    chunks: Mapped[list["JobChunk"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="JobChunk.idx"
    )
