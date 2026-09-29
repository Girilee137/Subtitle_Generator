import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ProcessingStatus


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_owner_status", "owner_id", "status"),
        Index("ix_projects_search_vector", "search_vector", postgresql_using="gin"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status"),
        nullable=False,
        default=ProcessingStatus.QUEUED,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    search_vector = mapped_column(TSVECTOR)

    owner: Mapped["User"] = relationship(back_populates="projects")
    media_files: Mapped[list["MediaFile"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(back_populates="project")
