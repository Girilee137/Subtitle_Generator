import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, UploadFile, status
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.errors import BadRequestError, NotFoundError
from app.models.user import User
from app.schemas.hybrid import ClientResultRequest, MetadataFileCreate
from app.schemas.job import JobRead
from app.schemas.project import MediaFileRead
from app.services.client_result_service import accept_client_result
from app.services.media_service import create_metadata_file, delete_media, get_media, list_media, save_upload

router = APIRouter(tags=["files"])


@router.post("/projects/{project_id}/files", response_model=MediaFileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    project_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await save_upload(session, current_user, project_id, file)


@router.post("/projects/{project_id}/files/metadata", response_model=MediaFileRead, status_code=status.HTTP_201_CREATED)
async def create_file_metadata(
    project_id: uuid.UUID,
    payload: MetadataFileCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await create_metadata_file(
        session,
        current_user,
        project_id,
        payload.file_name,
        payload.file_type,
        payload.size_bytes,
        payload.duration_seconds,
    )


@router.get("/projects/{project_id}/files", response_model=list[MediaFileRead])
async def list_files(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await list_media(session, current_user, project_id)


@router.get("/files/{file_id}", response_model=MediaFileRead)
async def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_media(session, current_user, file_id)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await delete_media(session, current_user, file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/files/{file_id}/client-result", response_model=JobRead)
async def client_result(
    file_id: uuid.UUID,
    payload: ClientResultRequest,
    current_user: User = Depends(get_current_user),
):
    return await accept_client_result(
        current_user,
        file_id,
        payload.language,
        payload.model,
        payload.words,
    )


def parse_range(range_header: str | None, size: int) -> tuple[int, int] | None:
    if not range_header:
        return None
    unit, _, value = range_header.partition("=")
    if unit.lower() != "bytes" or "-" not in value:
        raise BadRequestError("Invalid range header", "INVALID_RANGE")
    start_raw, _, end_raw = value.partition("-")
    try:
        if start_raw:
            start = int(start_raw)
            end = int(end_raw) if end_raw else size - 1
        else:
            suffix = int(end_raw)
            start = max(0, size - suffix)
            end = size - 1
    except ValueError:
        raise BadRequestError("Invalid range header", "INVALID_RANGE") from None
    if start < 0 or end < start or start >= size:
        raise BadRequestError("Invalid range header", "INVALID_RANGE")
    return start, min(end, size - 1)


def iter_file(path: Path, start: int, end: int):
    with path.open("rb") as media:
        media.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = media.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@router.get("/files/{file_id}/stream")
async def stream_file(
    file_id: uuid.UUID,
    range_header: str | None = Header(default=None, alias="Range"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    media = await get_media(session, current_user, file_id)
    if not media.storage_path:
        raise NotFoundError("Stored media not available", "MEDIA_NOT_STORED")
    from app.services.object_storage import get_file_size, iter_file_range, uses_r2

    if uses_r2():
        try:
            size = await get_file_size(media.storage_path)
        except Exception as exc:
            raise NotFoundError("Stored media missing", "MEDIA_MISSING") from exc
        path = None
    else:
        path = Path(media.storage_path)
        if not path.exists():
            raise NotFoundError("Stored media missing", "MEDIA_MISSING")
        size = os.path.getsize(path)
    byte_range = parse_range(range_header, size)
    headers = {"Accept-Ranges": "bytes"}
    if byte_range is None:
        if path is not None:
            return FileResponse(path, media_type=media.file_type, headers=headers)
        headers["Content-Length"] = str(size)
        start, end = 0, max(0, size - 1)
    else:
        start, end = byte_range
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        headers["Content-Length"] = str(end - start + 1)
    if path is not None:
        return StreamingResponse(
            iter_file(path, start, end),
            status_code=status.HTTP_206_PARTIAL_CONTENT if byte_range is not None else status.HTTP_200_OK,
            media_type=media.file_type,
            headers=headers,
        )
    return StreamingResponse(
        iter_file_range(media.storage_path, start, end),
        status_code=status.HTTP_206_PARTIAL_CONTENT if byte_range is not None else status.HTTP_200_OK,
        media_type=media.file_type,
        headers=headers,
    )
