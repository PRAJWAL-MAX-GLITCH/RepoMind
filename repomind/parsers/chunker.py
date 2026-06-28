"""
repomind.parsers.chunker
=========================
Unified chunking dispatcher.  Accepts file details and routes to the
appropriate chunker (code-aware or generic text) based on language.
All chunkers return :class:`repomind.models.chunk_schema.ChunkMetadata`.

This is the single entry point the ingestion/indexer pipeline calls.

Usage::

    from repomind.parsers.chunker import chunk_document
    from repomind.ingestion.repository_scanner import scan_repository

    docs = scan_repository("/path/to/repo")
    for doc in docs:
        chunks = chunk_document(
            repo_root="/path/to/repo",
            file_path=doc.relative_path,
            language=doc.language,
            content=doc.content,
        )
"""

from __future__ import annotations

from typing import List

from repomind.models.chunk_schema import ChunkMetadata
from repomind.parsers.code_chunker import chunk_code_file
from repomind.parsers.text_chunker import chunk_text_file

# Languages that get code-aware structural chunking
CODE_LANGUAGES = {
    "Python",
    "JavaScript",
    "JavaScript (JSX)",
    "TypeScript",
    "TypeScript (TSX)",
    "Java",
    "C",
    "C++",
    "C/C++ Header",
}

# Languages that get text/documentation chunking
TEXT_LANGUAGES = {
    "Markdown",
    "YAML",
    "JSON",
}


def chunk_document(
    repo_root: str,
    file_path: str,
    language: str,
    content: str,
) -> List[ChunkMetadata]:
    """
    Route a file to the appropriate chunker and return a list of
    :class:`ChunkMetadata` objects.

    Code files (Python, JS/TS, Java, C, C++) → :func:`chunk_code_file`
    (structural parsing with line-window fallback).

    Documentation files (Markdown, YAML, JSON) → :func:`chunk_text_file`
    (heading-section or line-window parsing).

    Args:
        repo_root:  Absolute path to the repository root (used for naming).
        file_path:  Source file path relative to *repo_root*.
        language:   Language label from the repository scanner.
        content:    Raw UTF-8 text of the file.

    Returns:
        A list of :class:`ChunkMetadata` instances.
        Returns an empty list if *content* is empty or None.
    """
    if not content:
        return []

    if language in CODE_LANGUAGES:
        return chunk_code_file(
            repo_root=repo_root,
            file_path=file_path,
            language=language,
            content=content,
        )

    # Text / documentation (and unknown) languages
    return chunk_text_file(
        repo_root=repo_root,
        file_path=file_path,
        language=language,
        content=content,
    )
