import uuid

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SubtitleSegment(TimestampMixin, Base):
    __tablename__ = "subtitle_segments"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="segment_end_after_start"),
        UniqueConstraint("track_id", "idx", name="uq_subtitle_segments_track_idx"),
        Index("ix_subtitle_segments_track_idx", "track_id", "idx"),
        Index("ix_subtitle_segments_search_vector", "search_vector", postgresql_using="gin"),
    )

    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subtitle_tracks.track_id", ondelete="CASCADE"), nullable=False
    )
    idx: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    search_vector = mapped_column(TSVECTOR)

    track: Mapped["SubtitleTrack"] = relationship(back_populates="segments")
