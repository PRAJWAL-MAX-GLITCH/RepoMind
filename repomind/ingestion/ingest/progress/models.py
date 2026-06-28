from pydantic import BaseModel
from enum import Enum
from contextlib import contextmanager
from typing import Protocol, ClassVar

class ProgressStep(str, Enum):
    pass

class ProgressStatus(BaseModel):
    progress: float
    message: str | None = None

class NotifyProtocol(Protocol):
    def __call__(self, progress: float, message: str = "") -> None:
        ...

@contextmanager
def notify_progress(*args, **kwargs):
    yield


class IngestionProgressSteps(ProgressStep):
    """Possible steps for the ingestion progress."""

    VALIDATION = "Validation"
    PARSE = "Parse"
    STORAGE = "Storage"


class ValidationProgressStatus(ProgressStatus):
    current_step: ClassVar[IngestionProgressSteps] = IngestionProgressSteps.VALIDATION


class ParseProgressStatus(ProgressStatus):
    current_step: ClassVar[IngestionProgressSteps] = IngestionProgressSteps.PARSE


class StorageProgressStatus(ProgressStatus):
    current_step: ClassVar[IngestionProgressSteps] = IngestionProgressSteps.STORAGE
