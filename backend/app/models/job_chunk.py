import uuid

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class JobChunk(TimestampMixin, Base):
    __tablename__ = "job_chunks"
    __table_args__ = (
        CheckConstraint("end_s > start_s", name="chunk_end_after_start"),
        Index("ix_job_chunks_job_idx", "job_id", "idx", unique=True),
    )

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    start_s: Mapped[float] = mapped_column(Float, nullable=False)
    end_s: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    result: Mapped[dict | None] = mapped_column(JSONB)

    job: Mapped["Job"] = relationship(back_populates="chunks")
