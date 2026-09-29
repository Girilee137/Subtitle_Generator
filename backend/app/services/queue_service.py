from sqlalchemy.ext.asyncio import AsyncSession

from app.models.queued_task import QueuedTask


def enqueue_task(
    session: AsyncSession,
    task_name: str,
    payload: dict,
    *,
    priority: int = 5,
    queue_name: str = "default",
) -> QueuedTask:
    task = QueuedTask(
        task_name=task_name,
        queue_name=queue_name,
        payload=payload,
        priority=priority,
    )
    session.add(task)
    return task
