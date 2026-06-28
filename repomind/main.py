"""FastAPI app creation, logger configuration and main API routes."""


from repomind.core.di import get_global_injector
from repomind.core.launcher import create_app

app = create_app(get_global_injector())
