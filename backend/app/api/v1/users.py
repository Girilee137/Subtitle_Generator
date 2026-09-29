from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.deps import get_current_user, get_db
from app.core.config import get_settings
from app.models.enums import JobMode
from app.models.job import Job
from app.models.project import Project
from app.models.user import User
from app.schemas.hybrid import UserQuotaRead
from app.schemas.auth import MessageResponse, ProfileUpdate, UserRead
from app.services.auth_service import update_profile
from app.services.log_service import write_system_log

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
async def patch_me(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> User:
    return await update_profile(session, current_user, payload.name, payload.password)


@router.post("/me/consent/server-processing", response_model=MessageResponse)
async def consent_server_processing(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    current_user.server_processing_consent_at = datetime.now(UTC)
    await write_system_log(session, "user.server_processing_consent", {}, actor_id=current_user.user_id)
    await session.commit()
    return MessageResponse(detail="Server processing consent recorded.")


@router.get("/me/quota", response_model=UserQuotaRead)
async def quota(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserQuotaRead:
    from datetime import UTC, datetime, time

    settings = get_settings()
    midnight = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
    used = await session.scalar(
        select(func.count())
        .select_from(Job)
        .where(
            Job.mode == JobMode.SERVER,
            Job.created_at >= midnight,
            Job.project_id.in_(select(Project.project_id).where(Project.owner_id == current_user.user_id)),
        )
    )
    return UserQuotaRead(
        server_jobs_used=int(used or 0),
        server_jobs_limit=settings.server_jobs_per_day,
        storage_used=current_user.storage_used,
        storage_quota=settings.user_quota_mb * 1024 * 1024,
    )
