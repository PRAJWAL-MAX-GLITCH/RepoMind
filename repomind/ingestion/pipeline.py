"""
repomind.ingestion.pipeline
============================
The top-level ingestion pipeline for RepoMind.

Orchestrates the full flow:
    1. Scan the repository (RepositoryScanner)
    2. Load file contents   (FileLoader)
    3. Chunk each file      (chunk_document dispatcher)
    4. Return chunks ready for vector indexing

Usage::

    from repomind.ingestion.pipeline import ingest_repository

    chunks = ingest_repository("/path/to/my-project")
    print(f"Produced {len(chunks)} chunks ready for indexing.")
"""

from __future__ import annotations

import logging
from typing import List, Union

from repomind.ingestion.repository_scanner import FileDocument, scan_repository
from repomind.models.chunk_schema import ChunkMetadata
from repomind.parsers.chunker import chunk_document

logger = logging.getLogger(__name__)


def ingest_repository(
    repo_path: str,
    max_file_size_bytes: int = 1 * 1024 * 1024,
    extra_ignored_dirs: set[str] | None = None,
) -> List[ChunkMetadata]:
    """
    Run the full ingestion pipeline for a local repository.

    Steps:
        1. Recursively scan *repo_path* for supported source files.
        2. Chunk each file using language-aware code or text chunking.
        3. Return all chunks as a flat list.

    Args:
        repo_path:           Absolute path to the repository root.
        max_file_size_bytes: Files larger than this are scanned but not chunked.
        extra_ignored_dirs:  Extra directory names to skip during scanning.

    Returns:
        A flat list of :class:`ChunkMetadata` objects suitable
        for embedding and vector indexing.
    """
    logger.info("Scanning repository: %s", repo_path)
    docs: List[FileDocument] = scan_repository(
        repo_path=repo_path,
        max_file_size_bytes=max_file_size_bytes,
        extra_ignored_dirs=extra_ignored_dirs,
    )
    logger.info("Scanner found %d supported files.", len(docs))

    all_chunks: List[ChunkMetadata] = []
    skipped = 0

    for doc in docs:
        if doc.content is None:
            skipped += 1
            continue  # Binary or oversized file

        chunks = chunk_document(
            repo_root=repo_path,
            file_path=doc.relative_path,
            language=doc.language,
            content=doc.content,
        )
        all_chunks.extend(chunks)

    logger.info(
        "Ingestion complete: %d chunks from %d files (%d files skipped).",
        len(all_chunks),
        len(docs) - skipped,
        skipped,
    )
    return all_chunks
