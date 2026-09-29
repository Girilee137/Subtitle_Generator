import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.errors import BadRequestError
from app.models.enums import ExportFormat
from app.models.export_record import ExportRecord
from app.models.user import User
from app.services.export_service import render_export
from app.services.subtitle_service import get_track_with_segments

router = APIRouter(prefix="/tracks", tags=["export"])


@router.get("/{track_id}/export")
async def export_track(
    track_id: uuid.UUID,
    format: str = Query(pattern="^(srt|vtt|txt|html)$"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    track = await get_track_with_segments(session, current_user, track_id)
    try:
        body, media_type = render_export(list(track.segments), format)
    except ValueError:
        raise BadRequestError("Unsupported export format", "UNSUPPORTED_EXPORT_FORMAT") from None
    session.add(ExportRecord(track_id=track.track_id, user_id=current_user.user_id, format=ExportFormat(format)))
    await session.commit()
    filename = f"track-{track.track_id}.{format}"
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
