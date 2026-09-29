import asyncio
import json
import mimetypes
import shutil
import subprocess
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import BadRequestError, ForbiddenError, NotFoundError, PayloadTooLargeError
from app.models.enums import ProcessingStatus
from app.models.media_file import MediaFile
from app.models.project import Project
from app.models.user import User
from app.services.log_service import write_system_log

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mp4", ".mkv", ".mov", ".webm"}
CHUNK_SIZE = 1024 * 1024


def storage_dir(user_id: uuid.UUID, project_id: uuid.UUID, file_id: uuid.UUID) -> Path:
    return get_settings().storage_root / str(user_id) / str(project_id) / str(file_id)


async def probe_media(path: Path) -> tuple[str, float | None]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=format_name,duration:stream=codec_type",
        "-of",
        "json",
        str(path),
    ]
    proc = await asyncio.to_thread(subprocess.run, command, capture_output=True, check=False)
    if proc.returncode != 0:
        raise BadRequestError("Unsupported or corrupt media file", "INVALID_MEDIA")
    payload = json.loads(proc.stdout.decode("utf-8") or "{}")
    
    streams = payload.get("streams", [])
    if not any(s.get("codec_type") == "audio" for s in streams):
        raise BadRequestError("The uploaded file does not contain an audio track.", "NO_AUDIO_TRACK")
    fmt = payload.get("format", {})
    duration_raw = fmt.get("duration")
    duration = float(duration_raw) if duration_raw not in (None, "N/A") else None
    return str(fmt.get("format_name") or "application/octet-stream"), duration


async def get_project_for_upload(session: AsyncSession, owner: User, project_id: uuid.UUID) -> Project:
    result = await session.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalar_one_or_none()
    if project is None or project.deleted_at is not None:
        raise NotFoundError("Project not found", "PROJECT_NOT_FOUND")
    if project.owner_id != owner.user_id:
        raise ForbiddenError("Project belongs to another user", "PROJECT_FORBIDDEN")
    return project


async def save_upload(session: AsyncSession, owner: User, project_id: uuid.UUID, upload: UploadFile) -> MediaFile:
    project = await get_project_for_upload(session, owner, project_id)
    original_name = Path(upload.filename or "upload").name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise BadRequestError("Unsupported file extension", "UNSUPPORTED_MEDIA_TYPE")
    file_id = uuid.uuid4()
    target_dir = storage_dir(owner.user_id, project.project_id, file_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"original{extension}"
    storage_key = f"users/{owner.user_id}/projects/{project.project_id}/files/{file_id}/original{extension}"
    size = 0
    try:
        async with aiofiles.open(target, "wb") as out:
            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > get_settings().max_upload_mb * 1024 * 1024:
                    raise PayloadTooLargeError("File exceeds upload size limit", "UPLOAD_TOO_LARGE")
                if owner.storage_used + size > get_settings().user_quota_mb * 1024 * 1024:
                    raise PayloadTooLargeError("Storage quota exceeded", "QUOTA_EXCEEDED")
                await out.write(chunk)
        probed_type, duration = await probe_media(target)
        from app.services.object_storage import uses_r2, upload_file

        if uses_r2():
            await upload_file(target, storage_key)
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise
    from app.services.object_storage import uses_r2

    stored_path = storage_key if uses_r2() else str(target)
    if uses_r2():
        shutil.rmtree(target_dir, ignore_errors=True)
    media = MediaFile(
        file_id=file_id,
        project_id=project.project_id,
        file_name=original_name,
        file_type=upload.content_type or mimetypes.guess_type(original_name)[0] or probed_type,
        size_bytes=size,
        duration_seconds=duration,
        is_stored=True,
        storage_path=stored_path,
    )
    owner.storage_used += size
    session.add(media)
    await write_system_log(session, "media.upload", {"file_id": str(file_id), "size_bytes": size}, actor_id=owner.user_id)
    await session.commit()
    await session.refresh(media)
    return media


async def create_metadata_file(
    session: AsyncSession,
    owner: User,
    project_id: uuid.UUID,
    file_name: str,
    file_type: str,
    size_bytes: int,
    duration_seconds: float | None,
) -> MediaFile:
    project = await get_project_for_upload(session, owner, project_id)
    media = MediaFile(
        project_id=project.project_id,
        file_name=Path(file_name).name,
        file_type=file_type,
        size_bytes=size_bytes,
        duration_seconds=duration_seconds,
        is_stored=False,
        storage_path=None,
        audio_path=None,
    )
    session.add(media)
    await write_system_log(session, "media.metadata", {"project_id": str(project.project_id)}, actor_id=owner.user_id)
    await session.commit()
    await session.refresh(media)
    return media


async def list_media(session: AsyncSession, owner: User, project_id: uuid.UUID) -> list[MediaFile]:
    project = await get_project_for_upload(session, owner, project_id)
    result = await session.execute(select(MediaFile).where(MediaFile.project_id == project.project_id))
    return list(result.scalars())


async def get_media(session: AsyncSession, owner: User, file_id: uuid.UUID) -> MediaFile:
    result = await session.execute(
        select(MediaFile)
        .options(selectinload(MediaFile.project))
        .join(Project)
        .where(MediaFile.file_id == file_id, Project.deleted_at.is_(None))
    )
    media = result.scalar_one_or_none()
    if media is None:
        raise NotFoundError("File not found", "FILE_NOT_FOUND")
    if media.project.owner_id != owner.user_id:
        raise ForbiddenError("File belongs to another user", "FILE_FORBIDDEN")
    return media


async def delete_media(session: AsyncSession, owner: User, file_id: uuid.UUID) -> None:
    media = await get_media(session, owner, file_id)

    if media.storage_path:
        from app.services.object_storage import delete_file

        await delete_file(media.storage_path)
    owner.storage_used = max(0, owner.storage_used - media.size_bytes)
    await write_system_log(session, "media.delete", {"file_id": str(file_id)}, actor_id=owner.user_id)
    await session.delete(media)
    await session.commit()
