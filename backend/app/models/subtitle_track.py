import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import TrackKind


class SubtitleTrack(TimestampMixin, Base):
    __tablename__ = "subtitle_tracks"
    __table_args__ = (Index("ix_subtitle_tracks_file_kind", "file_id", "kind"),)

    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_files.file_id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    source_language: Mapped[str | None] = mapped_column(String(16))
    is_translated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kind: Mapped[TrackKind] = mapped_column(Enum(TrackKind, name="track_kind"), nullable=False)

    media_file: Mapped["MediaFile"] = relationship(back_populates="tracks")
    segments: Mapped[list["SubtitleSegment"]] = relationship(
        back_populates="track", cascade="all, delete-orphan", order_by="SubtitleSegment.idx"
    )
    exports: Mapped[list["ExportRecord"]] = relationship(back_populates="track")
