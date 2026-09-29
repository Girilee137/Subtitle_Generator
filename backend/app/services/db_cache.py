from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Integer, Text, case, cast, delete, func, select
from sqlalchemy.dialects.postgresql import insert

from app.db.session import async_session
from app.models.cache_entry import CacheEntry


async def cache_get(key: str) -> Any | None:
    now = datetime.now(UTC)
    async with async_session() as session:
        result = await session.execute(
            select(CacheEntry.value).where(CacheEntry.key == key, CacheEntry.expires_at > now)
        )
        value = result.scalar_one_or_none()
        if value is None:
            await session.execute(delete(CacheEntry).where(CacheEntry.key == key))
            await session.commit()
        return value


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    now = datetime.now(UTC)
    async with async_session() as session:
        statement = insert(CacheEntry).values(
            key=key,
            value=value,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        await session.execute(
            statement.on_conflict_do_update(
                index_elements=[CacheEntry.key],
                set_={"value": value, "expires_at": now + timedelta(seconds=ttl_seconds)},
            )
        )
        await session.execute(delete(CacheEntry).where(CacheEntry.expires_at <= now))
        await session.commit()


async def increment_counter(key: str, window_seconds: int) -> int:
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=window_seconds)
    statement = insert(CacheEntry).values(key=key, value=1, expires_at=expires_at)
    counter = func.to_jsonb(case(
        (CacheEntry.expires_at <= now, 1),
        else_=cast(cast(CacheEntry.value, Text), Integer) + 1,
    ))
    expiry = case((CacheEntry.expires_at <= now, expires_at), else_=CacheEntry.expires_at)
    async with async_session() as session:
        result = await session.execute(
            statement.on_conflict_do_update(
                index_elements=[CacheEntry.key],
                set_={"value": counter, "expires_at": expiry},
            ).returning(CacheEntry.value)
        )
        await session.commit()
        return int(result.scalar_one())
