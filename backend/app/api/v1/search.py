from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services.search_service import search_projects_and_segments, suggest_projects

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/suggest")
async def suggest(q: str = Query(min_length=1), current_user: User = Depends(get_current_user)):
    return {"items": suggest_projects(current_user.user_id, q)}


@router.get("")
async def search(
    q: str = Query(min_length=1),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return {"items": await search_projects_and_segments(session, current_user.user_id, q)}
