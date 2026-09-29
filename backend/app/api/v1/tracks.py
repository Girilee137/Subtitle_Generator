import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.subtitle import TrackMergeRequest, TrackRead, TrackShiftRequest, TrackWithSegments
from app.services.subtitle_service import (
    delete_track,
    get_track_with_segments,
    list_file_tracks,
    merge_segments,
    shift_track,
)

router = APIRouter(tags=["tracks"])


@router.get("/files/{file_id}/tracks", response_model=list[TrackRead])
async def file_tracks(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await list_file_tracks(session, current_user, file_id)


@router.get("/tracks/{track_id}", response_model=TrackWithSegments)
async def get_track(
    track_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_track_with_segments(session, current_user, track_id)


@router.post("/tracks/{track_id}/shift", response_model=TrackWithSegments)
async def shift(
    track_id: uuid.UUID,
    payload: TrackShiftRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await shift_track(session, current_user, track_id, payload.offset, payload.from_idx)


@router.post("/tracks/{track_id}/merge", response_model=TrackWithSegments)
async def merge(
    track_id: uuid.UUID,
    payload: TrackMergeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    merged = await merge_segments(session, current_user, track_id, payload.segment_a, payload.segment_b)
    return await get_track_with_segments(session, current_user, merged.track_id)


@router.delete("/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track_route(
    track_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await delete_track(session, current_user, track_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
