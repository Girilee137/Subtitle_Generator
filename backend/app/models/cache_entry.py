from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CacheEntry(Base):
    __tablename__ = "cache_entries"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[object] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
