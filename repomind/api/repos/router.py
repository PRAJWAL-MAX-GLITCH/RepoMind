"""
repomind.api.repos.router
==========================
FastAPI router for all /repos endpoints.

Endpoints
---------
POST   /repos/index                    – Index a local repository
POST   /repos/query                    – Ask a semantic question about a repo
GET    /repos/{repo_name}/summary      – Developer onboarding summary
GET    /repos/{repo_name}/architecture – Structural architecture analysis
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from repomind.api.repos.schemas import (
    ArchitectureResponse,
    ErrorResponse,
    ImportantFileGroups,
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
    ScanRequest,
    ScanResponse,
    SourceChunk,
    SummaryResponse,
    HotspotItem,
    HotspotsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["Repository"])


# ---------------------------------------------------------------------------
# Helper: convert Set → sorted List for JSON serialisation
# ---------------------------------------------------------------------------

def _set_to_list(value) -> List[str]:
    if isinstance(value, set):
        return sorted(value)
    return list(value) if value else []


# ---------------------------------------------------------------------------
# POST /repos/scan
# ---------------------------------------------------------------------------

@router.post(
    "/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan a local repository without indexing",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or non-existent path"},
    },
)
async def scan_repository_endpoint(request: ScanRequest) -> ScanResponse:
    """
    Scan a local repository directory and return metadata — file count,
    detected languages, and an estimated chunk count — without embedding
    or storing anything. Used to preview a repo before indexing.
    """
    from repomind.ingestion.repository_scanner import RepositoryScanner
    from collections import Counter

    repo_path = Path(request.repo_path)
    if not repo_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path does not exist: {request.repo_path}",
        )
    if not repo_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path is not a directory: {request.repo_path}",
        )

    scanner = RepositoryScanner(repo_path)
    docs = scanner.scan()

    lang_counter: Counter = Counter()
    total_lines = 0
    for doc in docs:
        lang_counter[doc.language] += 1
        if doc.content:
            total_lines += doc.content.count("\n") + 1

    # Estimate: ~1 chunk per 40 lines of code
    estimated_chunks = max(1, total_lines // 40)

    return ScanResponse(
        repo_name=repo_path.name,
        repo_path=str(repo_path),
        total_files=len(docs),
        languages=dict(lang_counter),
        estimated_chunks=estimated_chunks,
        sample_files=[doc.relative_path for doc in docs[:20]],
    )


# ---------------------------------------------------------------------------
# POST /repos/index
# ---------------------------------------------------------------------------

@router.post(
    "/index",
    response_model=IndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Index a local repository",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or non-existent path"},
        500: {"model": ErrorResponse, "description": "Internal indexing error"},
    },
)
async def index_repository_endpoint(request: IndexRequest) -> IndexResponse:
    """
    Scan, chunk, embed, and store a local repository into the vector index.

    Accepts an absolute path to the repository root.  Returns an indexing
    report detailing how many files and chunks were processed.
    """
    repo_path = Path(request.repo_path)

    # Validate path
    if not repo_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path does not exist: {request.repo_path}",
        )
    if not repo_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path is not a directory: {request.repo_path}",
        )

    try:
        from repomind.rag.indexing_pipeline import index_repository, IndexingReport

        report: IndexingReport = index_repository(repo_path=str(repo_path))

        return IndexResponse(
            repo_name=report.repo_name,
            files_indexed=sorted(report.files_indexed),
            chunks_created=report.chunks_created,
            skipped_files=sorted(report.skipped_files),
            languages_detected=_set_to_list(report.languages_detected),
            index_location=report.index_location,
        )
    except Exception as exc:
        logger.exception("Indexing failed for '%s'", request.repo_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# POST /repos/query
# ---------------------------------------------------------------------------

@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a semantic question about a repository",
    responses={
        404: {"model": ErrorResponse, "description": "No indexed data for this repo"},
        500: {"model": ErrorResponse, "description": "Query execution error"},
    },
)
async def query_repository_endpoint(request: QueryRequest) -> QueryResponse:
    """
    Retrieve relevant code chunks and generate an answer using the RAG pipeline.

    Returns the answer string and the source chunks with file paths and line
    ranges so the caller can surface citations.
    """
    try:
        from repomind.rag.retriever import RepositoryRetriever
        from repomind.rag.query_service import query_repo

        # Check that at least some chunks exist for this repo
        retriever = RepositoryRetriever()
        chunks = retriever.retrieve(
            query=request.question,
            repo_name=request.repo_name,
            top_k=request.top_k,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No indexed data found for repository '{request.repo_name}'. "
                    "Please index the repository first via POST /repos/index."
                ),
            )

        # Build answer via full RAG query service
        answer = query_repo(question=request.question, repo_name=request.repo_name)

        # Map raw chunk dicts → SourceChunk models
        source_chunks: List[SourceChunk] = []
        for c in chunks:
            source_chunks.append(
                SourceChunk(
                    file_path=c.get("file_path", ""),
                    file_name=c.get("file_name", Path(c.get("file_path", "")).name),
                    language=c.get("language", "unknown"),
                    start_line=c.get("start_line", 0),
                    end_line=c.get("end_line", 0),
                    chunk_type=c.get("chunk_type", "block"),
                    symbol_name=c.get("symbol_name"),
                    content=c.get("content", ""),
                )
            )

        return QueryResponse(
            repo_name=request.repo_name,
            question=request.question,
            answer=answer,
            source_chunks=source_chunks,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Query failed for repo '%s'", request.repo_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# GET /repos/{repo_name}/summary
# ---------------------------------------------------------------------------

@router.get(
    "/{repo_name}/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a developer onboarding summary",
    responses={
        500: {"model": ErrorResponse, "description": "Analysis error"},
    },
)
async def get_repository_summary(
    repo_name: str,
    repo_path: Optional[str] = Query(
        default=None,
        description=(
            "Optional local filesystem path to the repository root. "
            "When provided, enables richer file-level analysis."
        ),
    ),
) -> SummaryResponse:
    """
    Generate a developer-facing onboarding summary for an indexed repository.

    Covers: what the project does, major modules, tech stack, entry points,
    auth/DB/API/ML files, files needing review, and key architectural notes.

    Pass `repo_path` as a query parameter for fuller filesystem-level analysis.
    """
    try:
        from repomind.analyzers.repository_summary import generate_repository_summary

        data = generate_repository_summary(
            repo_name=repo_name,
            repo_path=repo_path,
        )

        return SummaryResponse(
            repo_name=data["repo_name"],
            what_it_does=data["what_it_does"],
            major_modules=data["major_modules"],
            tech_stack=data["tech_stack"],
            entry_files=data["entry_files"],
            important_files=ImportantFileGroups(**data["important_files"]),
            needs_review=data["needs_review"],
            architecture_notes=data["architecture_notes"],
        )
    except Exception as exc:
        logger.exception("Summary generation failed for '%s'", repo_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# GET /repos/{repo_name}/architecture
# ---------------------------------------------------------------------------

@router.get(
    "/{repo_name}/architecture",
    response_model=ArchitectureResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a structural architecture analysis",
    responses={
        500: {"model": ErrorResponse, "description": "Analysis error"},
    },
)
async def get_repository_architecture(
    repo_name: str,
    repo_path: Optional[str] = Query(
        default=None,
        description="Optional local filesystem path for richer filesystem-level analysis.",
    ),
) -> ArchitectureResponse:
    """
    Generate a structured architectural analysis of an indexed repository.

    Identifies: languages, modules, entry points, important files
    (config, DB, auth, API, ML), and key architectural observations.

    Pass `repo_path` as a query parameter for fuller filesystem-level analysis.
    """
    try:
        from repomind.analyzers.architecture_analyzer import analyze_architecture

        data = analyze_architecture(
            repo_name=repo_name,
            repo_path=repo_path,
        )

        return ArchitectureResponse(
            repo_name=repo_name,
            project_summary=data["project_summary"],
            languages=data["languages"],
            main_modules=data["main_modules"],
            entry_points=data["entry_points"],
            important_files=data["important_files"],
            architecture_notes=data["architecture_notes"],
        )
    except Exception as exc:
        logger.exception("Architecture analysis failed for '%s'", repo_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Architecture analysis failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# GET /repos/{repo_name}/hotspots
# ---------------------------------------------------------------------------

@router.get(
    "/{repo_name}/hotspots",
    response_model=HotspotsResponse,
    status_code=status.HTTP_200_OK,
    summary="Identify risky or central code hotspots",
    responses={
        500: {"model": ErrorResponse, "description": "Analysis error"},
    },
)
async def get_repository_hotspots(
    repo_name: str,
    repo_path: Optional[str] = Query(
        default=None,
        description="Optional local filesystem path for richer filesystem-level scanning.",
    ),
) -> HotspotsResponse:
    """
    Identifies code hotspots based on heuristics like large file sizes,
    high density of technical debt markers, hardcoded secrets, and
    semantic detection of critical files (auth, db, API).
    """
    try:
        from repomind.analyzers.hotspot_finder import find_hotspots

        hotspots_raw = find_hotspots(
            repo_name=repo_name,
            repo_path=repo_path,
        )

        return HotspotsResponse(
            repo_name=repo_name,
            hotspots=[HotspotItem(**h) for h in hotspots_raw],
        )
    except Exception as exc:
        logger.exception("Hotspots analysis failed for '%s'", repo_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hotspots analysis failed: {exc}",
        ) from exc
