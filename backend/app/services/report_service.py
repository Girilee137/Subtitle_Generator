import csv
import io
import json
from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import JobMode, ProcessingStatus
from app.models.job import Job
from app.models.media_file import MediaFile
from app.models.project import Project
from app.models.user import User


async def analytics(session: AsyncSession) -> dict:
    users = int(await session.scalar(select(func.count()).select_from(User)) or 0)
    active_users = int(await session.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0)
    storage_used = int(await session.scalar(select(func.coalesce(func.sum(User.storage_used), 0))) or 0)
    project_rows = await session.execute(select(Project.status, func.count()).group_by(Project.status))
    mode_rows = await session.execute(select(Job.mode, func.count()).group_by(Job.mode))
    day_rows = await session.execute(
        select(func.date(Job.created_at), func.count()).group_by(func.date(Job.created_at)).order_by(func.date(Job.created_at))
    )
    duration = await session.scalar(
        select(
            func.avg(
                case(
                    (
                        Job.completed_at.is_not(None),
                        func.extract("epoch", Job.completed_at - Job.started_at),
                    ),
                    else_=None,
                )
            )
        )
    )
    return {
        "users": users,
        "active_users": active_users,
        "projects_by_status": {status.value: count for status, count in project_rows},
        "storage_used": storage_used,
        "jobs_by_mode": {mode.value: count for mode, count in mode_rows},
        "jobs_by_day": {str(day): count for day, count in day_rows},
        "avg_processing_seconds": float(duration) if duration is not None else None,
    }


async def storage_summary(session: AsyncSession) -> dict:
    row = await session.execute(
        select(
            func.coalesce(func.sum(MediaFile.size_bytes), 0),
            func.count(MediaFile.file_id),
            func.coalesce(func.sum(case((MediaFile.is_stored.is_(True), 1), else_=0)), 0),
        )
    )
    storage_used, files_count, stored_files_count = row.one()
    return {
        "storage_used": int(storage_used or 0),
        "files_count": int(files_count or 0),
        "stored_files_count": int(stored_files_count or 0),
    }


async def report_payload(session: AsyncSession) -> dict:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "analytics": await analytics(session),
        "storage": await storage_summary(session),
    }


def render_report(payload: dict, fmt: str) -> tuple[str, str, str]:
    if fmt == "json":
        return json.dumps(payload, indent=2), "application/json", "admin-report.json"
    if fmt == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["section", "metric", "value"])
        for key, value in payload["analytics"].items():
            writer.writerow(["analytics", key, json.dumps(value) if isinstance(value, dict) else value])
        for key, value in payload["storage"].items():
            writer.writerow(["storage", key, value])
        return out.getvalue(), "text/csv", "admin-report.csv"
    raise ValueError("Unsupported report format")
