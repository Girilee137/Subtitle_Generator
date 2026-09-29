import asyncio
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import async_session
from app.models.job import Job
from app.models.project import Project

router = APIRouter(tags=["ws"])


async def user_can_read_job(user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Job.job_id).join(Project).where(Job.job_id == job_id, Project.owner_id == user_id)
        )
        return result.scalar_one_or_none() is not None


@router.websocket("/ws/jobs/{job_id}")
async def job_events(websocket: WebSocket, job_id: uuid.UUID) -> None:
    token = websocket.query_params.get("token")
    try:
        payload = decode_token(token or "", "access")
        user_id = uuid.UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=1008)
        return
    if not await user_can_read_job(user_id, job_id):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    previous: tuple[object, ...] | None = None
    try:
        while True:
            async with async_session() as session:
                result = await session.execute(
                    select(Job).where(Job.job_id == job_id)
                )
                job = result.scalar_one_or_none()
                if job is None:
                    await websocket.close(code=1008)
                    return
                state = (
                    str(job.job_id),
                    job.status.value,
                    job.stage.value if job.stage else None,
                    job.progress,
                    job.chunks_done,
                    job.chunks_total,
                    job.error,
                )
            if state != previous:
                await websocket.send_json(
                    {
                        "job_id": state[0],
                        "status": state[1],
                        "stage": state[2],
                        "progress": state[3],
                        "chunks_done": state[4],
                        "chunks_total": state[5],
                        "error": state[6],
                    }
                )
                previous = state
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
