import uuid

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media_file import MediaFile
from app.models.project import Project
from app.models.subtitle_segment import SubtitleSegment
from app.models.subtitle_track import SubtitleTrack
from app.utils.trie import Trie

_project_tries: dict[uuid.UUID, Trie] = {}


def _trie_for_user(user_id: uuid.UUID) -> Trie:
    return _project_tries.setdefault(user_id, Trie())


def project_created(user_id: uuid.UUID, title: str) -> None:
    _trie_for_user(user_id).insert(title)


def project_renamed(user_id: uuid.UUID, old_title: str, new_title: str) -> None:
    trie = _trie_for_user(user_id)
    trie.delete(old_title)
    trie.insert(new_title)


def project_deleted(user_id: uuid.UUID, title: str) -> None:
    _trie_for_user(user_id).delete(title)


def suggest_projects(user_id: uuid.UUID, prefix: str, limit: int = 8) -> list[str]:
    return _trie_for_user(user_id).prefix_search(prefix, limit)


async def search_projects_and_segments(session: AsyncSession, user_id: uuid.UUID, query: str, limit: int = 20) -> list[dict]:
    ts_query = text("websearch_to_tsquery('simple', :query)")
    result = await session.execute(
        select(Project.project_id, Project.title, SubtitleSegment.segment_id, SubtitleSegment.text)
        .outerjoin(MediaFile, MediaFile.project_id == Project.project_id)
        .outerjoin(SubtitleTrack, SubtitleTrack.file_id == MediaFile.file_id)
        .outerjoin(SubtitleSegment, SubtitleSegment.track_id == SubtitleTrack.track_id)
        .where(
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
            or_(
                Project.search_vector.op("@@")(ts_query),
                SubtitleSegment.search_vector.op("@@")(ts_query),
                Project.title.ilike(f"%{query}%"),
                SubtitleSegment.text.ilike(f"%{query}%"),
            ),
        )
        .limit(limit)
        .params(query=query)
    )
    items = []
    for row in result:
        items.append(
            {
                "project_id": str(row.project_id),
                "title": row.title,
                "segment_id": str(row.segment_id) if row.segment_id else None,
                "text": row.text,
            }
        )
    return items
