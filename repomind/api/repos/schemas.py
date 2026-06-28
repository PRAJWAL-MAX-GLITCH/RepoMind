"""
repomind.api.repos.schemas
===========================
Pydantic request/response models for all /repos endpoints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared / common
# ---------------------------------------------------------------------------

class SourceChunk(BaseModel):
    """A single retrieved code chunk returned alongside an answer."""
    file_path: str
    file_name: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str
    symbol_name: Optional[str] = None
    content: str


# ---------------------------------------------------------------------------
# POST /repos/scan
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    """Request body for scanning a repository without indexing."""
    repo_path: str = Field(
        ...,
        description="Absolute path to the local repository root.",
        examples=[r"C:\projects\my-app"],
    )

    @field_validator("repo_path")
    @classmethod
    def path_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("repo_path must not be empty.")
        return v.strip()


class ScanResponse(BaseModel):
    """Metadata returned after scanning a repository (no indexing performed)."""
    repo_name: str
    repo_path: str
    total_files: int
    languages: Dict[str, int]
    estimated_chunks: int
    sample_files: List[str]


# ---------------------------------------------------------------------------
# POST /repos/index
# ---------------------------------------------------------------------------

class IndexRequest(BaseModel):
    """Request body for indexing a repository."""
    repo_path: str = Field(
        ...,
        description="Absolute path to the local repository root.",
        examples=[r"C:\projects\my-app"],
    )

    @field_validator("repo_path")
    @classmethod
    def path_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("repo_path must not be empty.")
        return v.strip()


class IndexResponse(BaseModel):
    """Response returned after a successful indexing operation."""
    status: str = "success"
    repo_name: str
    files_indexed: List[str]
    chunks_created: int
    skipped_files: List[str]
    languages_detected: List[str]
    index_location: str


# ---------------------------------------------------------------------------
# POST /repos/query
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """Request body for querying an indexed repository."""
    repo_name: str = Field(
        ...,
        description="Name of the already-indexed repository.",
        examples=["my-app"],
    )
    question: str = Field(
        ...,
        description="Natural-language question about the codebase.",
        examples=["Where is authentication implemented?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of context chunks to retrieve (1-20).",
    )

    @field_validator("repo_name", "question")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v.strip()


class QueryResponse(BaseModel):
    """Response containing the answer and the supporting source chunks."""
    status: str = "success"
    repo_name: str
    question: str
    answer: str
    source_chunks: List[SourceChunk]


# ---------------------------------------------------------------------------
# GET /repos/{repo_name}/summary
# ---------------------------------------------------------------------------

class ImportantFileGroups(BaseModel):
    auth: List[str] = Field(default_factory=list)
    database: List[str] = Field(default_factory=list)
    api: List[str] = Field(default_factory=list)
    ml: List[str] = Field(default_factory=list)
    config: List[str] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    """Developer onboarding summary for a repository."""
    status: str = "success"
    repo_name: str
    what_it_does: str
    major_modules: List[str]
    tech_stack: List[str]
    entry_files: List[str]
    important_files: ImportantFileGroups
    needs_review: List[str]
    architecture_notes: List[str]


# ---------------------------------------------------------------------------
# GET /repos/{repo_name}/architecture
# ---------------------------------------------------------------------------

class ArchitectureResponse(BaseModel):
    """Structured architectural analysis of a repository."""
    status: str = "success"
    repo_name: str
    project_summary: str
    languages: List[str]
    main_modules: List[str]
    entry_points: List[str]
    important_files: List[str]
    architecture_notes: List[str]
    # Enhanced fields
    categorized_files: Dict[str, List[str]] = Field(default_factory=dict)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    directory_tree: List[Dict[str, Any]] = Field(default_factory=list)
    file_count: int = 0
    has_db: bool = False
    has_auth: bool = False
    has_api: bool = False
    has_ml: bool = False


# ---------------------------------------------------------------------------
# Error wrapper (used consistently across all endpoints)
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /repos/{repo_name}/hotspots
# ---------------------------------------------------------------------------

class HotspotItem(BaseModel):
    file_path: str
    reason: str
    priority: str

class HotspotsResponse(BaseModel):
    """List of identified code hotspots."""
    status: str = "success"
    repo_name: str
    hotspots: List[HotspotItem]
