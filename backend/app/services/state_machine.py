from datetime import UTC, datetime

from app.core.errors import ConflictError
from app.models.enums import ProcessingStatus

TRANSITIONS: dict[ProcessingStatus | None, dict[str, ProcessingStatus]] = {
    None: {"createProject": ProcessingStatus.QUEUED},
    ProcessingStatus.QUEUED: {
        "startProcessing": ProcessingStatus.PROCESSING,
        "deleteProject": ProcessingStatus.QUEUED,
    },
    ProcessingStatus.PROCESSING: {
        "processingCompleted": ProcessingStatus.COMPLETED,
        "failProcessing": ProcessingStatus.FAILED,
        "pauseProcessing": ProcessingStatus.PAUSED,
        "resumeProcessing": ProcessingStatus.PROCESSING,
        "deleteProject": ProcessingStatus.PROCESSING,
    },
    ProcessingStatus.COMPLETED: {
        "pauseProcessing": ProcessingStatus.PAUSED,
        "exportSubtitles": ProcessingStatus.COMPLETED,
        "deleteProject": ProcessingStatus.COMPLETED,
    },
    ProcessingStatus.PAUSED: {
        "resumeProcessing": ProcessingStatus.COMPLETED,
        "deleteProject": ProcessingStatus.PAUSED,
    },
    ProcessingStatus.FAILED: {
        "retryProcessing": ProcessingStatus.QUEUED,
        "deleteProject": ProcessingStatus.FAILED,
    },
}


def transition(project, event: str, *, unfinished_job: bool = False):
    current = getattr(project, "status", None)
    next_status = TRANSITIONS.get(current, {}).get(event)
    if current == ProcessingStatus.PAUSED and event == "resumeProcessing" and unfinished_job:
        next_status = ProcessingStatus.PROCESSING
    if next_status is None:
        current_label = current.value if current else "start"
        raise ConflictError(f"Illegal transition {event} from {current_label}", "ILLEGAL_TRANSITION")
    if event == "deleteProject":
        project.deleted_at = datetime.now(UTC)
        return project
    project.status = next_status
    return project
