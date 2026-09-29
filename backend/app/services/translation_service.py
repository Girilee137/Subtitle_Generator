import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ConflictError
from app.ml.gemini import translate_texts, transliterate_tanglish_texts
from app.models.enums import TrackKind
from app.models.subtitle_segment import SubtitleSegment
from app.models.subtitle_track import SubtitleTrack
from app.models.user import User
from app.services.log_service import write_system_log
from app.services.subtitle_service import get_track_for_user

BATCH_SIZE = 40


def opposite_language(source_language: str) -> str:
    if source_language == "en":
        return "ta"
    if source_language == "ta":
        return "en"
    raise BadRequestError("Only English and Tamil tracks can be translated", "UNSUPPORTED_TRANSLATION_SOURCE")


async def create_track_from_texts(
    session: AsyncSession,
    source_track: SubtitleTrack,
    texts: list[str],
    language: str,
    kind: TrackKind,
    is_translated: bool = True,
    source_segments: list[SubtitleSegment] | None = None,
) -> SubtitleTrack:
    segments_to_use = source_segments if source_segments is not None else source_track.segments
    ordered_segments = sorted(segments_to_use, key=lambda item: item.idx)
    new_track = SubtitleTrack(
        file_id=source_track.file_id,
        language=language,
        source_language=source_track.language,
        is_translated=is_translated,
        kind=kind,
    )
    session.add(new_track)
    await session.flush()
    for source, text in zip(ordered_segments, texts, strict=True):
        session.add(
            SubtitleSegment(
                track_id=new_track.track_id,
                idx=source.idx,
                start_time=source.start_time,
                end_time=source.end_time,
                text=text,
                confidence=source.confidence,
            )
        )
    return new_track


async def translate_track(
    session: AsyncSession,
    current_user: User,
    track_id: uuid.UUID,
    target_language: str,
) -> SubtitleTrack:
    source_track = await get_track_for_user(session, current_user, track_id)
    if target_language == source_track.language:
        raise ConflictError("Target language must differ from source language", "SAME_LANGUAGE")
    if opposite_language(source_track.language) != target_language:
        raise BadRequestError("Only en-to-ta and ta-to-en translation is supported", "UNSUPPORTED_TRANSLATION_DIRECTION")
    ordered_segments = sorted(source_track.segments, key=lambda item: item.idx)
    translated: list[str] = []
    for start in range(0, len(ordered_segments), BATCH_SIZE):
        batch = ordered_segments[start : start + BATCH_SIZE]
        translated.extend(await translate_texts([segment.text for segment in batch], source_track.language, target_language))
    new_track = await create_track_from_texts(
        session,
        source_track,
        translated,
        target_language,
        TrackKind.TRANSLATION,
    )
    await write_system_log(
        session,
        "track.translate",
        {"source_track_id": str(track_id), "target_language": target_language},
        actor_id=current_user.user_id,
    )
    await session.commit()
    await session.refresh(new_track)
    return new_track


async def transliterate_track(
    session: AsyncSession,
    current_user: User,
    track_id: uuid.UUID,
) -> SubtitleTrack:
    source_track = await get_track_for_user(session, current_user, track_id)
    if source_track.language != "ta":
        raise BadRequestError("Only Tamil tracks can be transliterated", "UNSUPPORTED_TRANSLITERATION_SOURCE")
    new_track = await transliterate_loaded_tamil_track(session, source_track)
    await write_system_log(session, "track.transliterate", {"source_track_id": str(track_id)}, actor_id=current_user.user_id)
    await session.commit()
    await session.refresh(new_track)
    return new_track


async def transliterate_loaded_tamil_track(
    session: AsyncSession, source_track: SubtitleTrack, segments: list[SubtitleSegment] | None = None
) -> SubtitleTrack:
    segments_to_use = segments if segments is not None else source_track.segments
    ordered_segments = sorted(segments_to_use, key=lambda item: item.idx)
    output: list[str] = []
    for start in range(0, len(ordered_segments), BATCH_SIZE):
        batch = ordered_segments[start : start + BATCH_SIZE]
        output.extend(await transliterate_tanglish_texts([segment.text for segment in batch]))
    return await create_track_from_texts(
        session,
        source_track,
        texts=output,
        language="ta-Latn",
        kind=TrackKind.TRANSLITERATION,
        source_segments=segments_to_use,
    )
