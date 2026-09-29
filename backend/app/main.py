from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.files import router as files_router
from app.api.v1.export import router as export_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.projects import router as projects_router
from app.api.v1.search import router as search_router
from app.api.v1.segments import router as segments_router
from app.api.v1.tracks import router as tracks_router
from app.api.v1.translate import router as translate_router
from app.api.v1.users import router as users_router
from app.api.v1.ws import router as ws_router
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler, unhandled_error_handler
from app.core.logging import configure_logging, logger
from app.db.session import async_session
from app.services.auth_service import seed_admin

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    try:
        async with async_session() as session:
            await seed_admin(session, settings.admin_email, settings.admin_password)
        logger.info("admin_seed_complete", email=settings.admin_email)
    except SQLAlchemyError as exc:
        logger.error("admin_seed_failed", error=str(exc))
    yield


app = FastAPI(
    title="Privacy-First Subtitle Platform",
    version="0.1.0",
    lifespan=lifespan,
)
settings = get_settings()
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(tracks_router, prefix="/api/v1")
app.include_router(segments_router, prefix="/api/v1")
app.include_router(translate_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(ws_router)
app.include_router(admin_router, prefix="/api/v1")
