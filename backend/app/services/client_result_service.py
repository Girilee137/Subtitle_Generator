import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.core.config import get_settings
from app.core.errors import BadRequestError, ConflictError, ForbiddenError, NotFoundError, PayloadTooLargeError
from app.ml.aligner import cleanup_words
from app.ml.segmenter import segment_words
from app.models.enums import JobMode, JobStage, ProcessingStatus, TrackKind
from app.models.job import Job
from app.models.media_file import MediaFile
from app.models.project import Project
from app.models.subtitle_segment import SubtitleSegment
from app.models.subtitle_track import SubtitleTrack
from app.models.user import User
from app.services.log_service import write_system_log
from app.services.processing_service import publish_job_event
from app.services.state_machine import transition


def validate_client_words(words: list, duration_seconds: float | None) -> list[dict]:
    settings = get_settings()
    if len(words) > settings.client_result_max_words:
        raise PayloadTooLargeError("Client result has too many words", "CLIENT_RESULT_TOO_LARGE")
    clean: list[dict] = []
    previous_start = -1.0
    max_end = (duration_seconds or 0) + 1.0 if duration_seconds is not None else None
    for item in words:
        word = item.word.strip()
        if not word:
            raise BadRequestError("Word text cannot be empty", "INVALID_CLIENT_WORD")
        if item.start < previous_start:
            raise BadRequestError("Word starts must be non-decreasing", "NON_MONOTONIC_WORDS")
        if item.start >= item.end:
            raise BadRequestError("Word end must be after start", "INVALID_WORD_TIMING")
        if max_end is not None and item.end > max_end:
            raise BadRequestError("Word end exceeds media duration", "WORD_BEYOND_DURATION")
        clean.append({"word": word, "start": item.start, "end": item.end, "prob": item.prob if item.prob is not None else 0.9})
        previous_start = item.start
    return clean


async def get_browser_media(session: AsyncSession, current_user: User, file_id: uuid.UUID) -> MediaFile:
    result = await session.execute(
        select(MediaFile)
        .options(selectinload(MediaFile.project))
        .join(Project)
        .where(MediaFile.file_id == file_id, Project.deleted_at.is_(None))
    )
    media = result.scalar_one_or_none()
    if media is None:
        raise NotFoundError("File not found", "FILE_NOT_FOUND")
    if media.project.owner_id != current_user.user_id:
        raise ForbiddenError("File belongs to another user", "FILE_FORBIDDEN")
    return media


async def accept_client_result(
    current_user: User,
    file_id: uuid.UUID,
    language: str,
    model: str,
    words: list,
) -> Job:
    from app.db.session import async_session
    
    async with async_session() as session:
        media = await get_browser_media(session, current_user, file_id)
        project = media.project
        if project.status not in {ProcessingStatus.QUEUED, ProcessingStatus.FAILED}:
            raise ConflictError("Project cannot accept client result in its current state", "PROJECT_NOT_READY")
        clean_words = validate_client_words(words, media.duration_seconds)
        if project.status == ProcessingStatus.FAILED:
            transition(project, "retryProcessing")
        transition(project, "startProcessing")
        
        job = Job(
            project_id=project.project_id,
            file_id=media.file_id,
            mode=JobMode.BROWSER,
            status=ProcessingStatus.PROCESSING,
            stage=JobStage.ALIGN,
            progress=80,
            priority=5,
            chunks_total=1,
            chunks_done=1,
            started_at=datetime.now(UTC),
        )
        session.add(job)
        await session.commit()
        job_id = job.job_id
        project_id = project.project_id

    # Outside transaction: Do expensive Tanglish transliteration if needed
    drafts = segment_words(cleanup_words(clean_words), language)
    tanglish_texts = []
    if language == "ta":
        from app.ml.gemini import transliterate_tanglish_texts
        # Transliterate in batches of 40
        BATCH_SIZE = 40
        for start in range(0, len(drafts), BATCH_SIZE):
            batch = drafts[start : start + BATCH_SIZE]
            tanglish_texts.extend(await transliterate_tanglish_texts([d.text for d in batch]))

    # Open new transaction to save results
    async with async_session() as session:
        result = await session.execute(
            select(Job).options(selectinload(Job.project)).where(Job.job_id == job_id)
        )
        job = result.scalar_one()
        
        track = SubtitleTrack(
            file_id=file_id,
            language=language,
            source_language=language,
            is_translated=False,
            kind=TrackKind.ORIGINAL,
        )
        session.add(track)
        await session.flush()
        
        for draft in drafts:
            session.add(
                SubtitleSegment(
                    track_id=track.track_id,
                    idx=draft.idx,
                    start_time=draft.start_time,
                    end_time=draft.end_time,
                    text=draft.text,
                    confidence=draft.confidence,
                )
            )
            
        if language == "ta":
            tanglish = SubtitleTrack(
                file_id=file_id,
                language="ta-Latn",
                source_language="ta",
                is_translated=True,
                kind=TrackKind.TRANSLITERATION,
            )
            session.add(tanglish)
            await session.flush()
            for draft, text in zip(drafts, tanglish_texts, strict=True):
                session.add(
                    SubtitleSegment(
                        track_id=tanglish.track_id,
                        idx=draft.idx,
                        start_time=draft.start_time,
                        end_time=draft.end_time,
                        text=text,
                        confidence=draft.confidence,
                    )
                )

        transition(job.project, "processingCompleted")
        job.status = ProcessingStatus.COMPLETED
        job.stage = JobStage.DONE
        job.progress = 100
        job.completed_at = datetime.now(UTC)
        await write_system_log(
            session,
            "job.client_result",
            {"job_id": str(job.job_id), "model": model, "word_count": len(clean_words)},
            actor_id=current_user.user_id,
        )
        await publish_job_event(session, job)
        await session.commit()
        await session.refresh(job)
        return job
