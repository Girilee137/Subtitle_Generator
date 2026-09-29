import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class MediaFile(TimestampMixin, Base):
    __tablename__ = "media_files"

    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    is_stored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    audio_path: Mapped[str | None] = mapped_column(String(1024))

    project: Mapped["Project"] = relationship(back_populates="media_files")
    tracks: Mapped[list["SubtitleTrack"]] = relationship(
        back_populates="media_file", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(back_populates="media_file")
