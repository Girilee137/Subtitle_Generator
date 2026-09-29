from enum import StrEnum


class Role(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class ProcessingStatus(StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class JobMode(StrEnum):
    SERVER = "SERVER"
    BROWSER = "BROWSER"


class JobStage(StrEnum):
    EXTRACT = "extract"
    DETECT_LANG = "detect_lang"
    VAD = "vad"
    CHUNK = "chunk"
    SCHEDULE = "schedule"
    ASR = "asr"
    ALIGN = "align"
    SEGMENT = "segment"
    TANGLISH = "tanglish"
    DONE = "done"


class TrackKind(StrEnum):
    ORIGINAL = "ORIGINAL"
    TRANSLATION = "TRANSLATION"
    TRANSLITERATION = "TRANSLITERATION"


class ExportFormat(StrEnum):
    SRT = "srt"
    VTT = "vtt"
    TXT = "txt"
    HTML = "html"
