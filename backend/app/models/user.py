import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import Role


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email_lower", text("lower(email)"), unique=True),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), nullable=False, default=Role.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    storage_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    server_processing_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    admin_profile: Mapped["AdminProfile | None"] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(back_populates="owner")


class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    permissions: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    user: Mapped[User] = relationship(back_populates="admin_profile")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    token_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
