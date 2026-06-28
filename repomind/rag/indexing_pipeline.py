"""
repomind.rag.indexing_pipeline
===============================
Provides the service to ingest a repository, chunk it, embed it, and persist it to the vector store.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Dict

from repomind.ingestion.pipeline import ingest_repository
from repomind.models.chunk_schema import ChunkMetadata
from repomind.rag.embedding_engine import EmbeddingEngine
from repomind.rag.indexer import Indexer

logger = logging.getLogger(__name__)


@dataclass
class IndexingReport:
    """
    Detailed summary returned after indexing a repository.
    """
    repo_name: str
    """The last segment of the repository root path."""

    files_indexed: List[str] = field(default_factory=list)
    """Paths of successfully indexed files (relative to repository root)."""

    chunks_created: int = 0
    """Total count of ChunkMetadata objects generated and indexed."""

    skipped_files: List[str] = field(default_factory=list)
    """Paths of files skipped due to being binary or too large."""

    languages_detected: Set[str] = field(default_factory=set)
    """Set of language labels detected during ingestion."""

    index_location: str = ""
    """The location or path of the vector store backend used."""


def index_repository(repo_path: str) -> IndexingReport:
    """
    Ingest a repository, generate embeddings, and index chunks into the local vector store.

    Args:
        repo_path (str): Absolute path to the repository directory.

    Returns:
        IndexingReport: Complete details about the indexing process.
    """
    start_time = time.time()
    path_obj = Path(repo_path).resolve()
    repo_name = path_obj.name

    logger.info("Starting indexing pipeline for repository: %s", repo_path)

    # 1. Scan and chunk the repository
    # ingest_repository scans, loads, and chunks documents, returning List[ChunkMetadata]
    chunks: List[ChunkMetadata] = ingest_repository(repo_path=str(path_obj))

    # Calculate report fields
    files_indexed_set = {chunk.file_path for chunk in chunks}
    languages = {chunk.language for chunk in chunks}

    # Since RepositoryScanner processes all files but returns content=None for skipped ones,
    # we need to find skipped files by scanning again or comparing.
    # To keep it efficient, we can fetch scanned documents from scan_repository.
    from repomind.ingestion.repository_scanner import scan_repository
    scanned_docs = scan_repository(repo_path=str(path_obj))
    
    skipped_files = [
        doc.relative_path for doc in scanned_docs if doc.content is None
    ]

    # 2. Initialize embedding engine and embed chunks
    logger.info("Generating embeddings for %d chunks...", len(chunks))
    embed_engine = EmbeddingEngine()
    embeddings: List[List[float]] = []
    
    for idx, chunk in enumerate(chunks):
        if idx % 100 == 0 and idx > 0:
            logger.info("Embedded %d/%d chunks...", idx, len(chunks))
        embeddings.append(embed_engine.embed_text(chunk.content))

    # 3. Initialize indexer and store vectors
    logger.info("Storing vectors in the local vector store...")
    indexer = Indexer()
    indexer.index_chunks(chunks=chunks, embeddings=embeddings)

    # Fetch index location from settings if available
    indexer_vs_comp = indexer.vector_store_component
    db_type = indexer_vs_comp._settings.vectorstore.database
    if db_type == "qdrant":
        index_location = indexer_vs_comp._settings.qdrant.path or "qdrant"
    else:
        index_location = db_type

    report = IndexingReport(
        repo_name=repo_name,
        files_indexed=sorted(list(files_indexed_set)),
        chunks_created=len(chunks),
        skipped_files=sorted(skipped_files),
        languages_detected=languages,
        index_location=f"{db_type} ({index_location})",
    )

    duration = time.time() - start_time
    logger.info(
        "Successfully indexed repo %s in %.2f seconds. Created %d chunks.",
        repo_name, duration, len(chunks)
    )

    return report
