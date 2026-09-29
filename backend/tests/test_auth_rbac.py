import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jwt import InvalidTokenError

from app.core.errors import ForbiddenError, RateLimitError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.enums import Role
from app.models.user import User
from app.services import auth_service


def test_argon2_password_hash_round_trip() -> None:
    password_hash = hash_password("secret-password")
    assert verify_password("secret-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_jwt_access_and_refresh_types_are_enforced() -> None:
    user_id = uuid.uuid4()
    token_id = uuid.uuid4()
    access = create_access_token(user_id, Role.USER.value)
    refresh = create_refresh_token(user_id, token_id)
    assert decode_token(access, "access")["sub"] == str(user_id)
    assert decode_token(refresh, "refresh")["jti"] == str(token_id)
    with pytest.raises(InvalidTokenError):
        decode_token(access, "refresh")


def test_hash_token_is_stable_and_not_plaintext() -> None:
    token = "refresh-token"
    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != token


@pytest.mark.asyncio
async def test_postgres_login_rate_limit(monkeypatch) -> None:
    count = 0

    async def increment_counter(_key: str, _window: int) -> int:
        nonlocal count
        count += 1
        return count

    monkeypatch.setattr(auth_service, "increment_counter", increment_counter)
    for _ in range(5):
        await auth_service.check_login_rate_limit("127.0.0.1", "user@example.com")
    with pytest.raises(RateLimitError):
        await auth_service.check_login_rate_limit("127.0.0.1", "user@example.com")


@pytest.mark.asyncio
async def test_reset_token_store_rejects_expired_token() -> None:
    token = "expired"
    auth_service._reset_tokens[hash_token(token)] = (uuid.uuid4(), datetime.now(UTC) - timedelta(seconds=1))
    with pytest.raises(Exception):
        await auth_service.reset_password(session=None, token=token, password="new-password")


@pytest.mark.asyncio
async def test_require_admin_rejects_regular_user() -> None:
    from app.core.deps import require_admin

    user = User(
        user_id=uuid.uuid4(),
        name="User",
        email="user@example.com",
        password_hash="hash",
        role=Role.USER,
        is_active=True,
    )
    with pytest.raises(ForbiddenError):
        await require_admin(user)
