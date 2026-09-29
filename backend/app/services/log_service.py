import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_log import SystemLog


async def write_system_log(
    session: AsyncSession,
    action: str,
    detail: dict[str, Any],
    level: str = "INFO",
    actor_id: uuid.UUID | None = None,
) -> None:
    session.add(SystemLog(level=level, actor_id=actor_id, action=action, detail=detail))


async def list_system_logs(session: AsyncSession, level: str | None = None, limit: int = 100) -> list[SystemLog]:
    query = select(SystemLog)
    if level:
        query = query.where(SystemLog.level == level.upper())
    result = await session.execute(query.order_by(SystemLog.ts.desc()).limit(limit))
    return list(result.scalars())
