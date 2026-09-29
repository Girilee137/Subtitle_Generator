import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.enums import ProcessingStatus
from app.models.user import User
from app.schemas.job import JobRead
from app.schemas.project import ProjectCreate, ProjectList, ProjectRead, ProjectUpdate
from app.services.project_service import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    rename_project,
)
from app.services.processing_service import pause_job, resume_job, retry_job

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await create_project(session, current_user, payload.title)


@router.get("", response_model=ProjectList)
async def list_(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    project_status: ProcessingStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = await list_projects(session, current_user, project_status, limit, offset)
    return ProjectList(items=items, total=total)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_project(session, current_user, project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
async def patch_(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await rename_project(session, current_user, project_id, payload.title)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await delete_project(session, current_user, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/pause", response_model=JobRead)
async def pause(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await pause_job(session, current_user, project_id)


@router.post("/{project_id}/resume", response_model=JobRead)
async def resume(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await resume_job(session, current_user, project_id)


@router.post("/{project_id}/retry", response_model=JobRead)
async def retry(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await retry_job(session, current_user, project_id)
