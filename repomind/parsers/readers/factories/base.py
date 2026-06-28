from abc import ABC, abstractmethod

from injector import Injector

from repomind.parsers.readers.base_reader import IngestionReader
from repomind.core.settings.settings import Settings


class ReaderFactory(ABC):
    def __init__(self, settings: Settings, injector: Injector) -> None:
        self.settings = settings
        self.injector = injector

    @abstractmethod
    def create_reader(self, extension: str | None = None) -> IngestionReader:
        pass
