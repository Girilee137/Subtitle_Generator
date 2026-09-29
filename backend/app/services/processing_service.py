import logging
import uuid
from datetime import UTC, datetime, time
from pathlib import Path
import tempfile

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import BadRequestError, ConflictError, DailyLimitError, ForbiddenError, NotFoundError
from app.db.session import async_session
from app.ml.aligner import cleanup_words
from app.ml.asr import transcribe_chunk
from app.ml.audio import extract_audio
from app.ml.chunker import chunk_intervals
from app.ml.lang_detect import detect_language_for_processing, normalize_language
from app.ml.segmenter import segment_words
from app.ml.vad import detect_speech_intervals
from app.models.enums import JobMode, JobStage, ProcessingStatus, Role, TrackKind
from app.models.job import Job
from app.models.job_chunk import JobChunk
from app.models.media_file import MediaFile
from app.models.project import Project
from app.models.subtitle_segment import SubtitleSegment
from app.models.subtitle_track import SubtitleTrack
from app.models.user import User
from app.services.log_service import write_system_log
from app.services.media_service import get_media
from app.services.state_machine import transition
from app.services.queue_service import enqueue_task

logger = logging.getLogger(__name__)


async def publish_job_event(session: AsyncSession, job: Job) -> None:
    await session.flush()


async def set_job_progress(
    session: AsyncSession,
    job: Job,
    stage: JobStage,
    progress: float,
    status: ProcessingStatus | None = None,
) -> None:
    job.stage = stage
    job.progress = progress
    if status is not None:
        job.status = status
    await session.flush()
    await publish_job_event(session, job)


async def cleanup_completed_server_media(session: AsyncSession, job: Job) -> None:
    media = job.media_file
    if (
        job.status != ProcessingStatus.COMPLETED
        or job.mode != JobMode.SERVER
        or not media.is_stored
        or not media.storage_path
    ):
        return

    storage_path = media.storage_path
    try:
        from app.services.object_storage import delete_file

        await delete_file(storage_path)
    except Exception as exc:
        try:
            await write_system_log(
                session,
                "media.auto_delete_after_transcription.failed",
                {"file_id": str(media.file_id), "job_id": str(job.job_id), "error": str(exc)},
                level="ERROR",
                actor_id=job.project.owner_id,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not log media cleanup failure for completed job %s", job.job_id)
        else:
            logger.error("Could not delete source media for completed job %s: %s", job.job_id, exc)
        return

    try:
        owner = await session.get(User, job.project.owner_id)
        media.storage_path = None
        media.audio_path = None
        media.is_stored = False
        if owner is not None:
            owner.storage_used = max(0, owner.storage_used - media.size_bytes)
        await write_system_log(
            session,
            "media.auto_delete_after_transcription",
            {"file_id": str(media.file_id), "job_id": str(job.job_id)},
            actor_id=job.project.owner_id,
        )
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception("Could not persist media cleanup metadata for completed job %s", job.job_id)


async def is_paused(job_id: uuid.UUID) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Job.status, Project.deleted_at)
            .join(Project, Project.project_id == Job.project_id)
            .where(Job.job_id == job_id)
        )
        row = result.one_or_none()
    return row is None or row.status == ProcessingStatus.PAUSED or row.deleted_at is not None


async def get_job_for_user(session: AsyncSession, current_user: User, job_id: uuid.UUID) -> Job:
    result = await session.execute(
        select(Job)
        .options(selectinload(Job.project), selectinload(Job.media_file))
        .where(Job.job_id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("Job not found", "JOB_NOT_FOUND")
    if job.project.owner_id != current_user.user_id:
        raise ForbiddenError("Job belongs to another user", "JOB_FORBIDDEN")
    return job


async def get_latest_project_job(session: AsyncSession, current_user: User, project_id: uuid.UUID) -> Job:
    result = await session.execute(
        select(Job)
        .join(Project)
        .where(Job.project_id == project_id, Project.owner_id == current_user.user_id)
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("Job not found", "JOB_NOT_FOUND")
    return job


async def start_processing(
    session: AsyncSession,
    current_user: User,
    file_id: uuid.UUID,
    language: str,
    priority: int,
) -> Job:
    normalize_language(language)
    media = await get_media(session, current_user, file_id)
    if not media.is_stored or not media.storage_path:
        raise BadRequestError("Server processing requires a stored media file", "MEDIA_NOT_STORED")
    if current_user.role != Role.ADMIN:
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
        if int(used or 0) >= get_settings().server_jobs_per_day:
            raise DailyLimitError()
    project = media.project
    if project.status != ProcessingStatus.QUEUED:
        raise ConflictError("Project is not queued for processing", "PROJECT_NOT_QUEUED")
    transition(project, "startProcessing")
    job = Job(
        project_id=project.project_id,
        file_id=media.file_id,
        mode=JobMode.SERVER,
        status=ProcessingStatus.PROCESSING,
        stage=JobStage.EXTRACT,
        progress=0,
        priority=priority,
        chunks_total=0,
        chunks_done=0,
        started_at=datetime.now(UTC),
    )
    session.add(job)
    await session.flush()
    await write_system_log(session, "job.start", {"job_id": str(job.job_id)}, actor_id=current_user.user_id)
    enqueue_task(
        session,
        "process_job",
        {"job_id": str(job.job_id), "language": language},
        priority=priority,
        queue_name="default",
    )
    await session.commit()
    await session.refresh(job)
    return job


async def pause_job(session: AsyncSession, current_user: User, project_id: uuid.UUID) -> Job:
    job = await get_latest_project_job(session, current_user, project_id)
    if job.status != ProcessingStatus.PROCESSING:
        raise ConflictError("Only processing jobs can be paused", "JOB_NOT_PROCESSING")
    transition(job.project, "pauseProcessing")
    job.status = ProcessingStatus.PAUSED
    await publish_job_event(session, job)
    await session.commit()
    return job


async def resume_job(session: AsyncSession, current_user: User, project_id: uuid.UUID) -> Job:
    job = await get_latest_project_job(session, current_user, project_id)
    if job.status != ProcessingStatus.PAUSED:
        raise ConflictError("Only paused jobs can be resumed", "JOB_NOT_PAUSED")
    unfinished = job.chunks_done < job.chunks_total
    transition(job.project, "resumeProcessing", unfinished_job=unfinished)
    job.status = ProcessingStatus.PROCESSING if unfinished else ProcessingStatus.COMPLETED
    await session.commit()
    if unfinished:
        enqueue_task(
            session,
            "process_job",
            {"job_id": str(job.job_id), "language": "auto"},
            priority=job.priority,
            queue_name="default",
        )
        await session.commit()
    return job


async def retry_job(session: AsyncSession, current_user: User, project_id: uuid.UUID) -> Job:
    job = await get_latest_project_job(session, current_user, project_id)
    if job.status != ProcessingStatus.FAILED:
        raise ConflictError("Only failed jobs can be retried", "JOB_NOT_FAILED")
    transition(job.project, "retryProcessing")
    job.status = ProcessingStatus.QUEUED
    job.error = None
    await session.commit()
    return await start_processing(session, current_user, job.file_id, "auto", job.priority)


async def process_chunk_async(job_chunk_id: str, language: str, audio_path: str | None = None) -> None:
    async with async_session() as session:
        result = await session.execute(select(JobChunk).where(JobChunk.chunk_id == uuid.UUID(job_chunk_id)))
        chunk = result.scalar_one()
        if await is_paused(chunk.job_id):
            chunk.status = "PAUSED"
            await session.commit()
            return
        job = await session.get(Job, chunk.job_id)
        media = await session.get(MediaFile, job.file_id)
        words = await transcribe_chunk(audio_path or media.audio_path or media.storage_path, language, chunk.start_s, chunk.end_s)
        chunk.result = {"words": cleanup_words(words, offset=chunk.start_s)}
        chunk.status = "DONE"
        job.chunks_done += 1
        job.progress = min(85.0, (job.chunks_done / max(1, job.chunks_total)) * 85.0)
        await publish_job_event(session, job)
        await session.commit()


async def finalize_job_async(job_id: str, language: str) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(Job)
            .options(selectinload(Job.chunks), selectinload(Job.project), selectinload(Job.media_file))
            .where(Job.job_id == uuid.UUID(job_id))
        )
        job = result.scalar_one()
        await set_job_progress(session, job, JobStage.ALIGN, 88.0)
        words: list[dict] = []
        for chunk in sorted(job.chunks, key=lambda item: item.idx):
            words.extend((chunk.result or {}).get("words", []))
        words = cleanup_words(words)
        await set_job_progress(session, job, JobStage.SEGMENT, 92.0)
        drafts = segment_words(words, language)
    
    tanglish_texts = []
    if language == "ta":
        from app.ml.gemini import transliterate_tanglish_texts
        BATCH_SIZE = 40
        for start in range(0, len(drafts), BATCH_SIZE):
            batch = drafts[start : start + BATCH_SIZE]
            tanglish_texts.extend(await transliterate_tanglish_texts([d.text for d in batch]))

    async with async_session() as session:
        result = await session.execute(
            select(Job).options(selectinload(Job.project), selectinload(Job.media_file)).where(Job.job_id == uuid.UUID(job_id))
        )
        job = result.scalar_one()
        
        track = SubtitleTrack(
            file_id=job.file_id,
            language=language,
            source_language=language,
            is_translated=False,
            kind=TrackKind.ORIGINAL,
        )
        session.add(track)
        await session.flush()
        for draft in drafts:
            segment = SubtitleSegment(
                track_id=track.track_id,
                idx=draft.idx,
                start_time=draft.start_time,
                end_time=draft.end_time,
                text=draft.text,
                confidence=draft.confidence,
            )
            session.add(segment)
            
        if language == "ta":
            t_track = SubtitleTrack(
                file_id=job.file_id,
                language="ta-Latn",
                source_language=language,
                is_translated=True,
                kind=TrackKind.TRANSLITERATION,
            )
            session.add(t_track)
            await session.flush()
            for draft, t_text in zip(drafts, tanglish_texts, strict=True):
                session.add(
                    SubtitleSegment(
                        track_id=t_track.track_id,
                        idx=draft.idx,
                        start_time=draft.start_time,
                        end_time=draft.end_time,
                        text=t_text,
                        confidence=draft.confidence,
                    )
                )

        transition(job.project, "processingCompleted")
        job.status = ProcessingStatus.COMPLETED
        job.stage = JobStage.DONE
        job.progress = 100
        job.completed_at = datetime.now(UTC)
        await write_system_log(session, "job.completed", {"job_id": str(job.job_id)})
        await publish_job_event(session, job)
        await session.commit()
        await cleanup_completed_server_media(session, job)


async def run_job_pipeline(job_id: str, requested_language: str) -> None:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Job)
                .options(selectinload(Job.project), selectinload(Job.media_file), selectinload(Job.chunks))
                .where(Job.job_id == uuid.UUID(job_id))
            )
            job = result.scalar_one()
            if await is_paused(job.job_id):
                job.status = ProcessingStatus.PAUSED
                await session.commit()
                return
            await set_job_progress(session, job, JobStage.EXTRACT, 5.0)
            
            file_name = job.media_file.file_name
            storage_path = job.media_file.storage_path
            media_audio_path = job.media_file.audio_path
            duration_seconds = job.media_file.duration_seconds

        from app.services.object_storage import download_file, uses_r2

        with tempfile.TemporaryDirectory(prefix="subtitle-job-") as working_dir:
            if uses_r2():
                extension = Path(file_name).suffix or ".media"
                media_path = str(Path(working_dir) / f"original{extension}")
                await download_file(storage_path, Path(media_path))
            else:
                media_path = storage_path
                
            audio_path = (
                media_audio_path
                if media_audio_path and not uses_r2()
                else str(Path(working_dir) / "audio.wav")
                if uses_r2()
                else str(Path(storage_path).parent / "audio.wav")
            )
            
            if get_settings().fake_asr:
                audio_path = media_path
            elif not media_audio_path or uses_r2():
                await extract_audio(media_path, audio_path)
                if not uses_r2():
                    async with async_session() as session:
                        result = await session.execute(select(Job).options(selectinload(Job.media_file)).where(Job.job_id == uuid.UUID(job_id)))
                        job = result.scalar_one()
                        job.media_file.audio_path = audio_path
                        await session.commit()
                        
            async with async_session() as session:
                result = await session.execute(select(Job).where(Job.job_id == uuid.UUID(job_id)))
                job = result.scalar_one()
                await set_job_progress(session, job, JobStage.DETECT_LANG, 12.0)
                
            detection_path = audio_path
            if get_settings().fake_asr and uses_r2():
                await extract_audio(media_path, str(Path(working_dir) / "detect.wav"))
                detection_path = str(Path(working_dir) / "detect.wav")
                
            language = await detect_language_for_processing(detection_path, requested_language)
            logger.info("Language detected, opening session for VAD progress...")
            
            async with async_session() as session:
                result = await session.execute(select(Job).where(Job.job_id == uuid.UUID(job_id)))
                job = result.scalar_one()
                await set_job_progress(session, job, JobStage.VAD, 18.0)
            logger.info("VAD progress saved. Running detect_speech_intervals...")
                
            intervals = detect_speech_intervals(audio_path, duration_seconds)
            logger.info("Speech intervals detected. Opening session for chunks...")
            
            async with async_session() as session:
                result = await session.execute(select(Job).options(selectinload(Job.chunks)).where(Job.job_id == uuid.UUID(job_id)))
                job = result.scalar_one()
                await set_job_progress(session, job, JobStage.CHUNK, 24.0)
                chunks = list(job.chunks)
                if not chunks:
                    for idx, (start, end) in enumerate(chunk_intervals(intervals)):
                        chunk = JobChunk(job_id=job.job_id, idx=idx, start_s=start, end_s=end, status="PENDING")
                        session.add(chunk)
                        chunks.append(chunk)
                    job.chunks_total = len(chunks)
                    await session.flush()
                await set_job_progress(session, job, JobStage.SCHEDULE, 30.0)
                await session.commit()
                chunks_info = [(str(c.chunk_id), c.status) for c in chunks]

            for chunk_id_str, chunk_status in chunks_info:
                if chunk_status != "DONE":
                    logger.info(f"Processing chunk {chunk_id_str}")
                    await process_chunk_async(chunk_id_str, language, audio_path)

            logger.info("Chunks done. Calling finalize_job_async...")
            await finalize_job_async(job_id, language)
            logger.info("Finalize done.")

    except Exception as exc:
        logger.exception(f"Error in run_job_pipeline: {exc}")
        async with async_session() as session:
            result = await session.execute(select(Job).options(selectinload(Job.project)).where(Job.job_id == uuid.UUID(job_id)))
            job = result.scalar_one()
            try:
                transition(job.project, "failProcessing")
            except Exception as transition_exc:
                logger.error(f"Failed to transition project to failed: {transition_exc}")
            job.status = ProcessingStatus.FAILED
            job.error = str(exc)
            await write_system_log(session, "job.failed", {"job_id": job_id, "error": str(exc)}, level="ERROR")
            await publish_job_event(session, job)
            await session.commit()
