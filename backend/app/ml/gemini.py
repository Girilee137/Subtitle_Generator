import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable

from app.core.config import get_settings
from app.ml.tanglish import fake_tanglish
from app.services.db_cache import cache_get, cache_set, increment_counter


def cache_key(operation: str, text: str, source: str, target: str) -> str:
    digest = hashlib.sha256(f"{operation}|{source}|{target}|{text}".encode("utf-8")).hexdigest()
    return f"gemini:{digest}"


async def _cache_get(key: str) -> list[str] | None:
    return await cache_get(key)


async def _cache_set(key: str, value: list[str]) -> None:
    await cache_set(key, value, 60 * 60 * 24 * 30)


async def acquire_rate_limit() -> None:
    settings = get_settings()
    key = "gemini:rpm"
    if await increment_counter(key, 60) > settings.gemini_rpm:
        await asyncio.sleep(60 / max(1, settings.gemini_rpm))


async def with_backoff(call: Callable[[], Awaitable[list[str]]]) -> list[str]:
    delay = 2.0
    for attempt in range(10):
        try:
            return await call()
        except Exception as e:
            if attempt == 9:
                raise
            import logging
            logging.getLogger(__name__).warning("Gemini API error (attempt %d/10): %s", attempt + 1, e)
            await asyncio.sleep(delay)
            delay = min(60.0, delay * 2)
    return []


async def translate_texts(texts: list[str], source_language: str, target_language: str) -> list[str]:
    if get_settings().fake_gemini:
        return [f"[{target_language}] {text}" for text in texts]
    key = cache_key("translate", "\n".join(texts), source_language, target_language)
    cached = await _cache_get(key)
    if cached is not None:
        return cached

    async def call() -> list[str]:
        await acquire_rate_limit()
        from google import genai

        client = genai.Client(api_key=get_settings().gemini_api_key)
        payload = {
            "source_language": source_language,
            "target_language": target_language,
            "segments": [{"idx": idx, "text": text} for idx, text in enumerate(texts)],
        }
        response = client.models.generate_content(
            model=get_settings().gemini_model,
            contents=(
                "Translate only between English and Tamil. "
                "You must respond with ONLY a raw JSON array. "
                f"Return JSON array in the same order: {json.dumps(payload, ensure_ascii=False)}"
            ),
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        parsed = json.loads(raw_text.strip())
        results = []
        for item in parsed:
            if isinstance(item, dict) and "text" in item:
                results.append(str(item["text"]))
            else:
                results.append(str(item))
        return results

    translated = await with_backoff(call)
    await _cache_set(key, translated)
    return translated


async def transliterate_tanglish_texts(texts: list[str]) -> list[str]:
    if get_settings().fake_gemini:
        return [fake_tanglish(text) for text in texts]
    key = cache_key("tanglish", "\n".join(texts), "ta", "ta-Latn")
    cached = await _cache_get(key)
    if cached is not None:
        return cached

    async def call() -> list[str]:
        await acquire_rate_limit()
        from google import genai

        client = genai.Client(api_key=get_settings().gemini_api_key)
        payload = [{"idx": idx, "text": text} for idx, text in enumerate(texts)]
        response = client.models.generate_content(
            model=get_settings().gemini_model,
            contents=(
                "Transliterate Tamil script to Tanglish Roman letters. Preserve English words. "
                "You must respond with ONLY a raw JSON array. "
                f"Return JSON array in order: {json.dumps(payload, ensure_ascii=False)}"
            ),
        )
        # Strip potential markdown formatting
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        parsed = json.loads(raw_text.strip())
        results = []
        for item in parsed:
            if isinstance(item, dict) and "text" in item:
                results.append(str(item["text"]))
            else:
                results.append(str(item))
        return results

    output = await with_backoff(call)
    await _cache_set(key, output)
    return output
