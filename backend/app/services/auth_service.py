import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import ConflictError, RateLimitError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    new_secret_token,
    verify_password,
)
from app.models.enums import Role
from app.models.user import AdminProfile, RefreshToken, User
from app.services.log_service import write_system_log
from app.services.db_cache import increment_counter
from app.services.notification_service import send_password_reset_email

_reset_tokens: dict[str, tuple[uuid.UUID, datetime]] = {}


async def seed_admin(session: AsyncSession, email: str, password: str) -> None:
    normalized_email = email.lower().strip()
    result = await session.execute(
        select(User).options(selectinload(User.admin_profile)).where(User.email == normalized_email)
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.role != Role.ADMIN:
            existing.role = Role.ADMIN
        if existing.admin_profile is None:
            session.add(AdminProfile(admin_id=existing.user_id, permissions=["*"]))
        await session.commit()
        return

    admin = User(
        name="Admin",
        email=normalized_email,
        password_hash=hash_password(password),
        role=Role.ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.flush()
    session.add(AdminProfile(admin_id=admin.user_id, permissions=["*"]))
    await session.commit()


def normalize_email(email: str) -> str:
    return email.lower().strip()


async def check_login_rate_limit(ip: str, email: str) -> None:
    key = f"login:{ip}:{normalize_email(email)}"
    if await increment_counter(key, 60) > 5:
        raise RateLimitError()


async def register_user(session: AsyncSession, name: str, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    result = await session.execute(select(User).where(User.email == normalized_email))
    if result.scalar_one_or_none() is not None:
        raise ConflictError("Email already registered", "EMAIL_EXISTS")
    user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        role=Role.USER,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    await write_system_log(session, "auth.register", {"email": normalized_email}, actor_id=user.user_id)
    await session.commit()
    await session.refresh(user)
    return user


async def create_token_pair(session: AsyncSession, user: User) -> tuple[str, str]:
    token_id = uuid.uuid4()
    refresh_token = create_refresh_token(user.user_id, token_id)
    settings = get_settings()
    session.add(
        RefreshToken(
            token_id=token_id,
            user_id=user.user_id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    access_token = create_access_token(user.user_id, user.role.value)
    return access_token, refresh_token


async def login_user(session: AsyncSession, email: str, password: str, ip: str) -> tuple[User, str, str]:
    await check_login_rate_limit(ip, email)
    normalized_email = normalize_email(email)
    result = await session.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        await write_system_log(session, "auth.login_failed", {"email": normalized_email}, level="WARN")
        await session.commit()
        raise UnauthorizedError("Invalid email or password", "INVALID_CREDENTIALS")
    access_token, refresh_token = await create_token_pair(session, user)
    await write_system_log(session, "auth.login", {"email": normalized_email}, actor_id=user.user_id)
    await session.commit()
    return user, access_token, refresh_token


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> tuple[User, str, str]:
    try:
        payload = decode_token(refresh_token, "refresh")
        token_id = uuid.UUID(payload["jti"])
        user_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise UnauthorizedError("Invalid refresh token", "INVALID_REFRESH_TOKEN") from None
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_id == token_id,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    stored = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if stored is None or stored.expires_at < now or stored.token_hash != hash_token(refresh_token):
        raise UnauthorizedError("Invalid refresh token", "INVALID_REFRESH_TOKEN")
    user_result = await session.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("Inactive or missing user", "INVALID_REFRESH_TOKEN")
    stored.revoked_at = now
    access_token, new_refresh_token = await create_token_pair(session, user)
    await write_system_log(session, "auth.refresh", {}, actor_id=user.user_id)
    await session.commit()
    return user, access_token, new_refresh_token


async def request_password_reset(session: AsyncSession, email: str) -> None:
    normalized_email = normalize_email(email)
    result = await session.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user is not None and user.is_active:
        token = new_secret_token()
        expires_at = datetime.now(UTC) + timedelta(minutes=get_settings().password_reset_minutes)
        _reset_tokens[hash_token(token)] = (user.user_id, expires_at)
        await send_password_reset_email(user.email, token)
        await write_system_log(session, "auth.password_reset_requested", {"email": normalized_email}, actor_id=user.user_id)
    else:
        await write_system_log(session, "auth.password_reset_unknown", {"email": normalized_email}, level="WARN")
    await session.commit()


async def reset_password(session: AsyncSession, token: str, password: str) -> None:
    token_hash = hash_token(token)
    stored = _reset_tokens.pop(token_hash, None)
    if stored is None:
        raise UnauthorizedError("Invalid reset token", "INVALID_RESET_TOKEN")
    user_id, expires_at = stored
    if expires_at < datetime.now(UTC):
        raise UnauthorizedError("Expired reset token", "EXPIRED_RESET_TOKEN")
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("Inactive or missing user", "INVALID_RESET_TOKEN")
    user.password_hash = hash_password(password)
    await write_system_log(session, "auth.password_reset", {}, actor_id=user.user_id)
    await session.commit()


async def update_profile(
    session: AsyncSession,
    user: User,
    name: str | None = None,
    password: str | None = None,
) -> User:
    if name is not None:
        user.name = name.strip()
    if password is not None:
        user.password_hash = hash_password(password)
    await write_system_log(session, "user.profile_update", {"name_changed": name is not None}, actor_id=user.user_id)
    await session.commit()
    await session.refresh(user)
    return user
