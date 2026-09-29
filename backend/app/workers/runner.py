import argparse
import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select

from app.db.session import async_session
from app.models.queued_task import QueuedTask
from app.services.processing_service import run_job_pipeline
from app.services.worker_translation_service import translate_track_async, transliterate_track_async

logger = logging.getLogger("subtitle_platform.worker")


async def claim_task(queue_name: str) -> QueuedTask | None:
    async with async_session() as session:
        result = await session.execute(
            select(QueuedTask)
            .where(
                QueuedTask.queue_name == queue_name,
                or_(
                    QueuedTask.status == "QUEUED",
                    (QueuedTask.status == "RUNNING")
                    & (QueuedTask.claimed_at < datetime.now(UTC) - timedelta(hours=6)),
                ),
            )
            .order_by(QueuedTask.priority.asc(), QueuedTask.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        task = result.scalar_one_or_none()
        if task is None:
            await session.rollback()
            return None
        task.status = "RUNNING"
        task.claimed_at = datetime.now(UTC)
        await session.commit()
        return task


async def run_task(task_name: str, payload: dict) -> None:
    if task_name == "process_job":
        await run_job_pipeline(payload["job_id"], payload["language"])
    elif task_name == "translate_track":
        await translate_track_async(payload["track_id"], payload["user_id"], payload["target_language"])
    elif task_name == "transliterate_track":
        await transliterate_track_async(payload["track_id"], payload["user_id"])
    else:
        raise ValueError(f"Unknown queued task type: {task_name}")


async def finish_task(task_id: uuid.UUID, error: str | None = None) -> None:
    async with async_session() as session:
        task = await session.get(QueuedTask, task_id)
        if task is not None:
            if error:
                task.status = "FAILED"
                task.error = error
            else:
                await session.delete(task)
            await session.commit()


async def worker_loop(queue_name: str) -> None:
    while True:
        task = await claim_task(queue_name)
        if task is None:
            await asyncio.sleep(0.5)
            continue
        try:
            await run_task(task.task_name, task.payload)
            await finish_task(task.task_id)
        except Exception as exc:
            logger.exception("Queued task failed", extra={"task_id": str(task.task_id)})
            await finish_task(task.task_id, str(exc))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", choices=("default", "gpu"), default="default")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(worker_loop(args.queue))


if __name__ == "__main__":
    main()
