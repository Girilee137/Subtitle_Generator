import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError
from app.models.enums import ProcessingStatus
from app.models.media_file import MediaFile
from app.models.project import Project
from app.models.user import User
from app.services import search_service
from app.services.log_service import write_system_log
from app.services.state_machine import transition


async def create_project(session: AsyncSession, owner: User, title: str) -> Project:
    project = Project(owner_id=owner.user_id, title=title.strip())
    transition(project, "createProject")
    session.add(project)
    await session.flush()
    search_service.project_created(owner.user_id, project.title)
    await write_system_log(session, "project.create", {"project_id": str(project.project_id)}, actor_id=owner.user_id)
    await session.commit()
    await session.refresh(project)
    return project


async def list_projects(
    session: AsyncSession,
    owner: User,
    status: ProcessingStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Project], int]:
    filters = [Project.owner_id == owner.user_id, Project.deleted_at.is_(None)]
    if status is not None:
        filters.append(Project.status == status)
    total = await session.scalar(select(func.count()).select_from(Project).where(*filters))
    result = await session.execute(
        select(Project).where(*filters).order_by(Project.updated_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars()), int(total or 0)


async def get_project(session: AsyncSession, owner: User, project_id: uuid.UUID) -> Project:
    result = await session.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalar_one_or_none()
    if project is None or project.deleted_at is not None:
        raise NotFoundError("Project not found", "PROJECT_NOT_FOUND")
    if project.owner_id != owner.user_id:
        raise ForbiddenError("Project belongs to another user", "PROJECT_FORBIDDEN")
    return project


async def rename_project(session: AsyncSession, owner: User, project_id: uuid.UUID, title: str | None) -> Project:
    project = await get_project(session, owner, project_id)
    if title is not None and title.strip() != project.title:
        old_title = project.title
        project.title = title.strip()
        project.updated_at = datetime.now(UTC)
        search_service.project_renamed(owner.user_id, old_title, project.title)
        await write_system_log(session, "project.rename", {"project_id": str(project.project_id)}, actor_id=owner.user_id)
        await session.commit()
        await session.refresh(project)
    return project


async def delete_project(session: AsyncSession, owner: User, project_id: uuid.UUID) -> Project:
    project = await get_project(session, owner, project_id)

    result = await session.execute(select(MediaFile).where(MediaFile.project_id == project.project_id))
    for media in result.scalars():
        if media.storage_path:
            from app.services.object_storage import delete_file
            await delete_file(media.storage_path)
        owner.storage_used = max(0, owner.storage_used - media.size_bytes)
    transition(project, "deleteProject")
    search_service.project_deleted(owner.user_id, project.title)
    await write_system_log(session, "project.delete", {"project_id": str(project.project_id)}, actor_id=owner.user_id)
    await session.commit()
    return project


async def apply_project_event(session: AsyncSession, owner: User, project_id: uuid.UUID, event: str) -> Project:
    project = await get_project(session, owner, project_id)
    transition(project, event)
    await write_system_log(
        session,
        f"project.{event}",
        {"project_id": str(project.project_id), "status": project.status.value},
        actor_id=owner.user_id,
    )
    await session.commit()
    await session.refresh(project)
    return project
