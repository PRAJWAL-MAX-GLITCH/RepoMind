"""FastAPI app creation, logger configuration and main API routes."""
import asyncio
import concurrent
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import nest_asyncio  # type: ignore
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from injector import Injector
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.settings import Settings as LlamaIndexSettings

from repomind.models.embedding.embedding_component import EmbeddingComponent
from repomind.models.llm.llm_component import LLMComponent
from repomind.vector_store.node_store.node_store_component import NodeStoreComponent
from repomind.rag.prompts.prompt_builder import PromptBuilderService
from repomind.vector_store.vector_store.vector_store_component import (
    VectorStoreComponent,
)
from repomind.constants import PROJECT_ROOT_PATH
from repomind.core.di import set_global_injector
from repomind.docs import DESCRIPTION, TITLE, configure_openapi
from repomind.global_handler import (
    ExceptionMiddleware,
    request_validation_exception_adapter,
)
from repomind.core.initialize import initialize_globals, initialize_observability
from repomind.api.server.embeddings.embeddings_router import embeddings_router
from repomind.api.server.health.health_router import health_router
from repomind.api.server.ingest.ingest_router import ingest_router
from repomind.api.server.models.models_router import models_router
from repomind.api.server.primitives.primitives_router import primitives_router
from repomind.core.settings.settings import Settings
from repomind.utils.runner import get_version

logger = logging.getLogger(__name__)


def eager_loading(injector: Injector) -> None:
    """Eagerly load modules to avoid race conditions in multi-threaded environments."""
    logger.debug("Initializing mandatory dependencies")
    injector.get(Settings)

    # Models
    logger.debug("Initializing models")
    injector.get(LLMComponent)
    injector.get(EmbeddingComponent)

    # Stores
    logger.debug("Initializing stores")
    injector.get(NodeStoreComponent)
    injector.get(VectorStoreComponent)

    # Auxiliar
    logger.debug("Initializing auxiliar services")
    injector.get(PromptBuilderService)


def apply_migrations(injector: Injector) -> None:
    """Ensure that all migrations are applied."""
    logger.debug("Migrations skipped (persistence component removed)")


def create_app(root_injector: Injector) -> FastAPI:
    # Initialize global settings and dependencies
    initialize_globals()
    set_global_injector(root_injector)

    # Retrieve settings and server version
    settings = root_injector.get(Settings)
    version = get_version()

    # Initialize Observability module
    initialize_observability(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Lifespan context manager to initialize and clean up resources."""
        # Set nested loop
        nest_asyncio.apply()

        # Set default thread pool limit
        cpu_count = os.cpu_count() or 1
        executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(500, cpu_count * 50), thread_name_prefix="Stream-Pool"
        )
        asyncio.get_event_loop().set_default_executor(executor)

        # Set the global injector as loop injector.
        set_global_injector(root_injector)

        # Ensure migrations are applied
        apply_migrations(root_injector)

        # Eagerly load minimum components
        eager_loading(root_injector)

        # Set up global settings for LlamaIndex
        app.state.injector = root_injector

        # Yield control back to the FastAPI app
        yield

        # Clean up the thread pool executor
        executor.shutdown(wait=True)

        # Clean up resources if necessary
        logger.debug("Cleaning up resources")

    # Start the API
    app = FastAPI(
        # Enable debug mode in FastAPI
        debug=settings.server.debug_mode,
        # Allow to configure prefix for all routes
        root_path=settings.server.root_path,
        root_path_in_servers=True,
        servers=[{"url": settings.server.root_path}]
        if settings.server.root_path
        else None,
        # Use lifespan context manager for initialization
        lifespan=lifespan,
        # Configure Zylon info
        title=TITLE,
        description=DESCRIPTION,
        version=version,
        # Enable OpenAPI schema and Swagger UI
        docs_url=settings.server.api_doc.swagger_url
        if settings.server.api_doc.enabled
        else None,
        redoc_url=settings.server.api_doc.redoc_url
        if settings.server.api_doc.enabled
        else None,
        openapi_url=settings.server.api_doc.openapi_url
        if settings.server.api_doc.enabled
        else None,
    )

    # Disable health logs
    def filter_health_logs(record: Any) -> bool:
        return len(record.args) >= 3 and record.args[2] != "/health"

    logging.getLogger("uvicorn.access").addFilter(filter_health_logs)

    # Add a global exception handler
    app.add_middleware(ExceptionMiddleware)
    app.add_exception_handler(
        RequestValidationError, request_validation_exception_adapter
    )

    # Add a middleware than inject the injector to the request state
    @app.middleware("http")
    async def inject_injector_middleware(request: Request, call_next: Any) -> Any:
        """Middleware to inject the injector into the request state."""
        request.state.injector = (
            request.app.state.injector
            if hasattr(request.app, "state") and hasattr(request.app.state, "injector")
            else root_injector
        )
        response = await call_next(request)
        return response

    app.include_router(models_router)
    app.include_router(embeddings_router)
    app.include_router(ingest_router)
    app.include_router(primitives_router)
    app.include_router(health_router)
    
    from repomind.api.repos.router import router as repos_router
    app.include_router(repos_router)

    if settings.server.cors.enabled:
        logger.debug("Setting up CORS middleware")
        app.add_middleware(
            CORSMiddleware,
            allow_credentials=settings.server.cors.allow_credentials,
            allow_origins=settings.server.cors.allow_origins,
            allow_origin_regex=settings.server.cors.allow_origin_regex,
            allow_methods=settings.server.cors.allow_methods,
            allow_headers=settings.server.cors.allow_headers,
        )

    # Set global embedding model to Mock to prevent LlamaIndex to default to use OpenAI
    LlamaIndexSettings.embed_model = MockEmbedding(384)

    # Configure OpenAPI schema
    configure_openapi(app)

    return app
