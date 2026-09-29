import asyncio
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from app.core.config import get_settings


def uses_r2() -> bool:
    return get_settings().storage_backend.lower() == "r2"


@lru_cache(maxsize=1)
def _client():
    settings = get_settings()
    if not settings.r2_endpoint_url or not settings.r2_bucket:
        raise RuntimeError("R2_ENDPOINT_URL and R2_BUCKET are required when STORAGE_BACKEND=r2")
    if not settings.r2_access_key_id or not settings.r2_secret_access_key:
        raise RuntimeError("R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY are required when STORAGE_BACKEND=r2")
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name=settings.r2_region,
    )


def _bucket() -> str:
    return get_settings().r2_bucket


async def upload_file(source: Path, key: str) -> None:
    if uses_r2():
        await asyncio.to_thread(_client().upload_file, str(source), _bucket(), key)
    else:
        destination = Path(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.copyfile, source, destination)


async def download_file(key: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if uses_r2():
        await asyncio.to_thread(_client().download_file, _bucket(), key, str(destination))
    else:
        await asyncio.to_thread(shutil.copyfile, Path(key), destination)


async def delete_file(key: str) -> None:
    if uses_r2():
        await asyncio.to_thread(_client().delete_object, Bucket=_bucket(), Key=key)
    else:
        await asyncio.to_thread(shutil.rmtree, Path(key).parent, True)


async def get_file_size(key: str) -> int:
    if uses_r2():
        response = await asyncio.to_thread(_client().head_object, Bucket=_bucket(), Key=key)
        return int(response["ContentLength"])
    return await asyncio.to_thread(lambda: Path(key).stat().st_size)


def iter_file_range(key: str, start: int, end: int) -> Iterator[bytes]:
    if uses_r2():
        response = _client().get_object(Bucket=_bucket(), Key=key, Range=f"bytes={start}-{end}")
        body = response["Body"]
        try:
            while chunk := body.read(1024 * 1024):
                yield chunk
        finally:
            body.close()
        return
    with Path(key).open("rb") as source:
        source.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = source.read(min(1024 * 1024, remaining))
            if not chunk:
                return
            remaining -= len(chunk)
            yield chunk


async def download_to_temporary_file(key: str, suffix: str) -> Path:
    import tempfile

    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    path = Path(handle.name)
    handle.close()
    await download_file(key, path)
    return path
