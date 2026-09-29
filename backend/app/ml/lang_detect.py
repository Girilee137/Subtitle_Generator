import asyncio
import json
import re

from app.core.config import SUPPORTED_LANGUAGES, get_settings


def normalize_language(language: str) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language
    if language == "auto":
        return "auto"
    raise ValueError("Only English and Tamil are supported")


def detect_language(audio_path: str, requested: str) -> str:
    requested = normalize_language(requested)
    if requested != "auto":
        return requested
    if get_settings().fake_asr:
        return "en"
    try:
        from faster_whisper import WhisperModel
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        model = WhisperModel(get_settings().whisper_model, device=device, compute_type=compute_type)
        segments, info = model.transcribe(audio_path, language=None, beam_size=1, without_timestamps=True)
        detected = info.language if info.language in SUPPORTED_LANGUAGES else None
        if detected:
            return detected
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Language detection failed: {e}")
        return "en"
    return "en"


async def detect_language_for_processing(audio_path: str, requested: str) -> str:
    requested = normalize_language(requested)
    if requested != "auto":
        return requested
    settings = get_settings()
    if settings.fake_asr:
        return "en"
    if settings.asr_provider.lower() != "gemini":
        return await asyncio.to_thread(detect_language, audio_path, requested)
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is required when ASR_PROVIDER=gemini")
    from app.ml.gemini import acquire_rate_limit

    await acquire_rate_limit()

    def call() -> str:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        uploaded = client.files.upload(file=audio_path)
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    uploaded,
                    "Identify the primary spoken language. Return only JSON with language set to "
                    '"en" for English or "ta" for Tamil. Do not return any other language code.',
                ],
            )
            return response.text or ""
        finally:
            client.files.delete(name=uploaded.name)

    raw = await asyncio.to_thread(call)
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("Gemini did not identify the audio language as English or Tamil")
    try:
        language = json.loads(match.group(0)).get("language")
    except (json.JSONDecodeError, AttributeError) as exc:
        raise ValueError("Gemini returned an invalid language response") from exc
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("Only English and Tamil audio are supported")
    return language
