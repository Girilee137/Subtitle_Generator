import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.job import JobRead, ProcessAccepted, ProcessRequest
from app.services.processing_service import get_job_for_user, get_latest_project_job, start_processing

router = APIRouter(tags=["jobs"])


@router.post("/files/{file_id}/process", response_model=ProcessAccepted, status_code=status.HTTP_202_ACCEPTED)
async def process_file(
    file_id: uuid.UUID,
    payload: ProcessRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProcessAccepted:
    job = await start_processing(session, current_user, file_id, payload.language, payload.priority)
    return ProcessAccepted(job_id=job.job_id)


@router.get("/jobs/{job_id}", response_model=JobRead)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_job_for_user(session, current_user, job_id)


@router.get("/projects/{project_id}/job", response_model=JobRead)
async def get_project_job(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_latest_project_job(session, current_user, project_id)
