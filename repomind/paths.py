from pathlib import Path

from repomind.constants import REPOMIND_HOME, PROJECT_ROOT_PATH
from repomind.core.settings.settings import settings


def resolve_data_path(path: str) -> Path:
    """Resolve a data path, handling absolute paths and paths relative to REPOMIND_HOME."""
    p = Path(path).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (REPOMIND_HOME / p).resolve()


models_path: Path = REPOMIND_HOME / "models"
models_cache_path: Path = models_path / "cache"
docs_path: Path = PROJECT_ROOT_PATH / "docs"
local_data_path: Path = resolve_data_path(settings().data.local_data_folder)

prompt_templates_path: Path = (
    Path(__file__).resolve().parent / "components" / "prompts" / "templates"
)
