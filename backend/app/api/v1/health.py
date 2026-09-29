from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import async_session

router = APIRouter(tags=["health"])


def gpu_available(device: str) -> bool:
    if device.lower() == "cpu":
        return False
    try:
        import torch
    except ImportError:
        return False
    return torch.cuda.is_available()


async def check_db() -> bool:
    try:
        async with async_session() as session:
            await session.execute(text("select 1"))
        return True
    except Exception:
        return False


@router.get("/health")
async def health() -> dict[str, bool | str]:
    settings = get_settings()
    db_ok = await check_db()
    storage_ok = settings.storage_backend == "local" or all(
        (
            settings.r2_endpoint_url,
            settings.r2_bucket,
            settings.r2_access_key_id,
            settings.r2_secret_access_key,
        )
    )
    gpu_enabled = gpu_available(settings.whisper_device)
    return {
        "status": "ok" if db_ok and storage_ok else "degraded",
        "db": db_ok,
        "postgres_queue": db_ok,
        "storage": storage_ok,
        "gpu": gpu_enabled,
    }
