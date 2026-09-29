import uuid

from app.db.session import async_session
from app.models.user import User
from app.services.translation_service import translate_track, transliterate_track


async def translate_track_async(track_id: str, user_id: str, target_language: str) -> str:
    async with async_session() as session:
        user = await session.get(User, uuid.UUID(user_id))
        track = await translate_track(session, user, uuid.UUID(track_id), target_language)
        return str(track.track_id)


async def transliterate_track_async(track_id: str, user_id: str) -> str:
    async with async_session() as session:
        user = await session.get(User, uuid.UUID(user_id))
        track = await transliterate_track(session, user, uuid.UUID(track_id))
        return str(track.track_id)
