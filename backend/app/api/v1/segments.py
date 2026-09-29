import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.subtitle import SegmentRead, SegmentSplitRequest, SegmentUpdate
from app.services.subtitle_service import delete_segment, split_segment, update_segment

router = APIRouter(prefix="/segments", tags=["segments"])


@router.patch("/{segment_id}", response_model=SegmentRead)
async def patch_segment(
    segment_id: uuid.UUID,
    payload: SegmentUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await update_segment(
        session,
        current_user,
        segment_id,
        payload.text,
        payload.start_time,
        payload.end_time,
    )


@router.post("/{segment_id}/split", response_model=SegmentRead)
async def split(
    segment_id: uuid.UUID,
    payload: SegmentSplitRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await split_segment(session, current_user, segment_id, payload.at_time, payload.at_char)


@router.delete("/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_segment_route(
    segment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await delete_segment(session, current_user, segment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
