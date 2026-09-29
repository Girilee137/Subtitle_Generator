import hashlib

from app.services.db_cache import cache_get, cache_set


def cache_key(chunk_pcm: bytes, model: str, language: str) -> str:
    digest = hashlib.sha256(chunk_pcm).hexdigest()
    return f"asr:{digest}:{model}:{language}"


async def get_cached_words(key: str):
    return await cache_get(key)


async def set_cached_words(key: str, words: list[dict]) -> None:
    await cache_set(key, words, 60 * 60 * 24)
