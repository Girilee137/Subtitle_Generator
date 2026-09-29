import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_admin
from app.core.errors import BadRequestError, NotFoundError
from app.models.job import Job
from app.models.media_file import MediaFile
from app.models.system_log import SystemLog
from app.models.user import User
from app.schemas.admin import AdminJobRead, AdminLogRead, AdminUserRead, AnalyticsRead, StorageSummary
from app.services.log_service import write_system_log
from app.services.media_service import delete_media
from app.services.report_service import analytics, render_report, report_payload, storage_summary

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/analytics", response_model=AnalyticsRead)
async def admin_analytics(session: AsyncSession = Depends(get_db)):
    return await analytics(session)


@router.get("/users", response_model=list[AdminUserRead])
async def admin_users(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars())


async def get_admin_user(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found", "USER_NOT_FOUND")
    return user


@router.patch("/users/{user_id}/activate", response_model=AdminUserRead)
async def activate_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    user = await get_admin_user(session, user_id)
    user.is_active = True
    await write_system_log(session, "admin.user_activate", {"user_id": str(user_id)})
    await session.commit()
    await session.refresh(user)
    return user


@router.patch("/users/{user_id}/deactivate", response_model=AdminUserRead)
async def deactivate_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    user = await get_admin_user(session, user_id)
    user.is_active = False
    await write_system_log(session, "admin.user_deactivate", {"user_id": str(user_id)})
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    user = await get_admin_user(session, user_id)
    
    # Delete all projects belonging to the user to trigger file deletion and job cancellation
    from app.models.project import Project
    from app.services.project_service import delete_project
    result = await session.execute(select(Project).where(Project.owner_id == user.user_id, Project.deleted_at.is_(None)))
    for project in result.scalars():
        await delete_project(session, user, project.project_id)
        
    await write_system_log(session, "admin.user_delete", {"user_id": str(user_id)})
    await session.delete(user)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_file(
    file_id: uuid.UUID,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(select(MediaFile).options(selectinload(MediaFile.project)).where(MediaFile.file_id == file_id))
    media = result.scalar_one_or_none()
    if media is None:
        raise NotFoundError("File not found", "FILE_NOT_FOUND")
    owner = await session.get(User, media.project.owner_id)
    await delete_media(session, owner, file_id)
    await write_system_log(session, "admin.file_delete", {"file_id": str(file_id)}, actor_id=admin_user.user_id)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/jobs", response_model=list[AdminJobRead])
async def admin_jobs(session: AsyncSession = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)):
    result = await session.execute(select(Job).order_by(Job.created_at.desc()).limit(limit))
    return list(result.scalars())


@router.get("/logs", response_model=list[AdminLogRead])
async def admin_logs(
    level: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    query = select(SystemLog)
    if level:
        query = query.where(SystemLog.level == level.upper())
    result = await session.execute(query.order_by(SystemLog.ts.desc()).limit(limit))
    return list(result.scalars())


@router.get("/storage", response_model=StorageSummary)
async def admin_storage(session: AsyncSession = Depends(get_db)):
    return await storage_summary(session)


@router.get("/reports/export")
async def admin_report(format: str = Query(pattern="^(csv|json)$"), session: AsyncSession = Depends(get_db)):
    payload = await report_payload(session)
    try:
        body, media_type, filename = render_report(payload, format)
    except ValueError:
        raise BadRequestError("Unsupported report format", "UNSUPPORTED_REPORT_FORMAT") from None
    return FastAPIResponse(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
