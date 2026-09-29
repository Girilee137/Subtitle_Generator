import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QueuedTask(Base):
    __tablename__ = "queued_tasks"
    __table_args__ = (
        Index("ix_queued_tasks_claim", "queue_name", "status", "priority", "created_at"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_name: Mapped[str] = mapped_column(String(80), nullable=False)
    queue_name: Mapped[str] = mapped_column(String(20), nullable=False, default="default")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="QUEUED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
