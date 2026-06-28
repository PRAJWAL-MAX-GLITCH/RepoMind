from repomind.parsers.readers.base_reader import IngestionReader
from repomind.ingestion.ingest.utils import FileInfo
from llama_index.core.schema import BaseNode
from typing import Any, AsyncIterable

class ExtractionUnsuccessfulError(RuntimeError):
    pass

class DoclingApiReader(IngestionReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()

    async def lazy_load_data(
        self,
        file_info: FileInfo,
        extra_info: dict[str, Any] | None = None,
        execute_transformations: bool = True,
        *args: Any,
        **load_kwargs: Any,
    ) -> AsyncIterable[BaseNode]:
        if False:
            yield
