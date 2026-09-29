import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.models.media_file import MediaFile
from app.models.project import Project
from app.models.subtitle_segment import SubtitleSegment
from app.models.subtitle_track import SubtitleTrack
from app.models.user import User
from app.services.log_service import write_system_log


def validate_timing(start_time: float, end_time: float) -> None:
    if end_time <= start_time:
        raise BadRequestError("Segment end_time must be greater than start_time", "INVALID_SEGMENT_TIMING")


def validate_no_overlap(segments: list[SubtitleSegment]) -> None:
    ordered = sorted(segments, key=lambda item: item.idx)
    for previous, current in zip(ordered, ordered[1:]):
        validate_timing(previous.start_time, previous.end_time)
        validate_timing(current.start_time, current.end_time)
        if current.start_time < previous.end_time:
            raise BadRequestError("Subtitle segments cannot overlap", "SEGMENT_OVERLAP")


def normalize_indexes(segments: list[SubtitleSegment]) -> None:
    for idx, segment in enumerate(sorted(segments, key=lambda item: (item.start_time, item.end_time, item.idx))):
        segment.idx = idx


async def get_track_for_user(session: AsyncSession, current_user: User, track_id: uuid.UUID) -> SubtitleTrack:
    result = await session.execute(
        select(SubtitleTrack)
        .options(
            selectinload(SubtitleTrack.segments),
            selectinload(SubtitleTrack.media_file).selectinload(MediaFile.project),
        )
        .join(MediaFile)
        .join(Project)
        .where(SubtitleTrack.track_id == track_id, Project.deleted_at.is_(None))
    )
    track = result.scalar_one_or_none()
    if track is None:
        raise NotFoundError("Track not found", "TRACK_NOT_FOUND")
    if track.media_file.project.owner_id != current_user.user_id:
        raise ForbiddenError("Track belongs to another user", "TRACK_FORBIDDEN")
    return track


async def get_segment_for_user(session: AsyncSession, current_user: User, segment_id: uuid.UUID) -> SubtitleSegment:
    result = await session.execute(
        select(SubtitleSegment)
        .options(
            selectinload(SubtitleSegment.track).selectinload(SubtitleTrack.segments),
            selectinload(SubtitleSegment.track)
            .selectinload(SubtitleTrack.media_file)
            .selectinload(MediaFile.project),
        )
        .join(SubtitleTrack)
        .join(MediaFile)
        .join(Project)
        .where(SubtitleSegment.segment_id == segment_id, Project.deleted_at.is_(None))
    )
    segment = result.scalar_one_or_none()
    if segment is None:
        raise NotFoundError("Segment not found", "SEGMENT_NOT_FOUND")
    if segment.track.media_file.project.owner_id != current_user.user_id:
        raise ForbiddenError("Segment belongs to another user", "SEGMENT_FORBIDDEN")
    return segment


async def list_file_tracks(session: AsyncSession, current_user: User, file_id: uuid.UUID) -> list[SubtitleTrack]:
    result = await session.execute(
        select(SubtitleTrack)
        .options(selectinload(SubtitleTrack.media_file).selectinload(MediaFile.project))
        .join(MediaFile)
        .join(Project)
        .where(MediaFile.file_id == file_id, Project.deleted_at.is_(None))
        .order_by(SubtitleTrack.created_at)
    )
    tracks = list(result.scalars())
    if not tracks:
        owner_result = await session.execute(
            select(MediaFile).options(selectinload(MediaFile.project)).join(Project).where(MediaFile.file_id == file_id)
        )
        media = owner_result.scalar_one_or_none()
        if media is None:
            raise NotFoundError("File not found", "FILE_NOT_FOUND")
        if media.project.owner_id != current_user.user_id:
            raise ForbiddenError("File belongs to another user", "FILE_FORBIDDEN")
    else:
        if tracks[0].media_file.project.owner_id != current_user.user_id:
            raise ForbiddenError("File belongs to another user", "FILE_FORBIDDEN")
    return tracks


async def get_track_with_segments(session: AsyncSession, current_user: User, track_id: uuid.UUID) -> SubtitleTrack:
    track = await get_track_for_user(session, current_user, track_id)
    validate_no_overlap(list(track.segments))
    return track


async def update_segment(
    session: AsyncSession,
    current_user: User,
    segment_id: uuid.UUID,
    text: str | None,
    start_time: float | None,
    end_time: float | None,
) -> SubtitleSegment:
    segment = await get_segment_for_user(session, current_user, segment_id)
    if text is not None:
        segment.text = text.strip()
    if start_time is not None:
        segment.start_time = start_time
    if end_time is not None:
        segment.end_time = end_time
    validate_no_overlap(list(segment.track.segments))
    await write_system_log(session, "segment.edit", {"segment_id": str(segment_id)}, actor_id=current_user.user_id)
    await session.commit()
    await session.refresh(segment)
    return segment


async def split_segment(
    session: AsyncSession,
    current_user: User,
    segment_id: uuid.UUID,
    at_time: float,
    at_char: int,
) -> SubtitleSegment:
    segment = await get_segment_for_user(session, current_user, segment_id)
    if at_time <= segment.start_time or at_time >= segment.end_time:
        raise BadRequestError("Split time must be inside the segment", "INVALID_SPLIT_TIME")
    if at_char >= len(segment.text):
        raise BadRequestError("Split character must be inside the segment text", "INVALID_SPLIT_CHAR")
    left_text = segment.text[:at_char].strip()
    right_text = segment.text[at_char:].strip()
    if not left_text or not right_text:
        raise BadRequestError("Split must leave text on both sides", "INVALID_SPLIT_TEXT")
    track = segment.track
    for item in track.segments:
        if item.idx > segment.idx:
            item.idx += 1
    new_segment = SubtitleSegment(
        track_id=track.track_id,
        idx=segment.idx + 1,
        start_time=at_time,
        end_time=segment.end_time,
        text=right_text,
        confidence=segment.confidence,
    )
    segment.end_time = at_time
    segment.text = left_text
    session.add(new_segment)
    validate_no_overlap(list(track.segments) + [new_segment])
    await write_system_log(session, "segment.split", {"segment_id": str(segment_id)}, actor_id=current_user.user_id)
    await session.commit()
    await session.refresh(new_segment)
    return new_segment


async def merge_segments(
    session: AsyncSession,
    current_user: User,
    track_id: uuid.UUID,
    segment_a: uuid.UUID,
    segment_b: uuid.UUID,
) -> SubtitleSegment:
    first = await get_segment_for_user(session, current_user, segment_a)
    if first.track_id != track_id:
        raise NotFoundError("Segment not found on requested track", "SEGMENT_NOT_FOUND")
    second = next((item for item in first.track.segments if item.segment_id == segment_b), None)
    if second is None:
        raise NotFoundError("Second segment not found on same track", "SEGMENT_NOT_FOUND")
    if abs(first.idx - second.idx) != 1:
        raise BadRequestError("Only adjacent segments can be merged", "SEGMENTS_NOT_ADJACENT")
    left, right = sorted([first, second], key=lambda item: item.idx)
    left.text = f"{left.text.rstrip()} {right.text.lstrip()}".strip()
    left.end_time = right.end_time
    left.confidence = (left.confidence + right.confidence) / 2
    await session.delete(right)
    remaining = [item for item in first.track.segments if item.segment_id != right.segment_id]
    normalize_indexes(remaining)
    validate_no_overlap(remaining)
    await write_system_log(session, "segment.merge", {"segment_a": str(segment_a), "segment_b": str(segment_b)}, actor_id=current_user.user_id)
    await session.commit()
    await session.refresh(left)
    return left


async def shift_track(
    session: AsyncSession,
    current_user: User,
    track_id: uuid.UUID,
    offset: float,
    from_idx: int | None,
) -> SubtitleTrack:
    track = await get_track_for_user(session, current_user, track_id)
    for segment in track.segments:
        if from_idx is None or segment.idx >= from_idx:
            segment.start_time += offset
            segment.end_time += offset
            if segment.start_time < 0:
                raise BadRequestError("Shift would move a segment before 0", "NEGATIVE_SEGMENT_TIME")
    validate_no_overlap(list(track.segments))
    await write_system_log(session, "track.shift", {"track_id": str(track_id), "offset": offset}, actor_id=current_user.user_id)
    await session.commit()
    await session.refresh(track)
    return track


async def delete_segment(session: AsyncSession, current_user: User, segment_id: uuid.UUID) -> None:
    segment = await get_segment_for_user(session, current_user, segment_id)
    track = segment.track
    await session.delete(segment)
    remaining = [item for item in track.segments if item.segment_id != segment.segment_id]
    normalize_indexes(remaining)
    await write_system_log(session, "segment.delete", {"segment_id": str(segment_id)}, actor_id=current_user.user_id)
    await session.commit()


async def delete_track(session: AsyncSession, current_user: User, track_id: uuid.UUID) -> None:
    track = await get_track_for_user(session, current_user, track_id)
    await session.delete(track)
    await write_system_log(session, "track.delete", {"track_id": str(track_id)}, actor_id=current_user.user_id)
    await session.commit()
