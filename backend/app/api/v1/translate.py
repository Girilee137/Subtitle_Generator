import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.subtitle import TrackWithSegments
from app.schemas.translation import TranslateRequest
from app.services.subtitle_service import get_track_with_segments
from app.services.translation_service import translate_track, transliterate_track

router = APIRouter(prefix="/tracks", tags=["translate"])


@router.post("/{track_id}/translate", response_model=TrackWithSegments, status_code=status.HTTP_201_CREATED)
async def translate(
    track_id: uuid.UUID,
    payload: TranslateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    new_track = await translate_track(session, current_user, track_id, payload.target_language)
    return await get_track_with_segments(session, current_user, new_track.track_id)


@router.post("/{track_id}/transliterate", response_model=TrackWithSegments, status_code=status.HTTP_201_CREATED)
async def transliterate(
    track_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    new_track = await transliterate_track(session, current_user, track_id)
    return await get_track_with_segments(session, current_user, new_track.track_id)
