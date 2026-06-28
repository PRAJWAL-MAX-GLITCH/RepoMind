"""
repomind.ingestion.repository_scanner
======================================
Scans a local project repository and collects metadata and raw content
for all supported source code and documentation files.

Usage:
    from repomind.ingestion.repository_scanner import scan_repository

    files = scan_repository("/path/to/my/project")
    for f in files:
        print(f.relative_path, f.language, f.size_bytes)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Supported extensions and their language labels
# ---------------------------------------------------------------------------

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py":   "Python",
    ".js":   "JavaScript",
    ".jsx":  "JavaScript (JSX)",
    ".ts":   "TypeScript",
    ".tsx":  "TypeScript (TSX)",
    ".java": "Java",
    ".cpp":  "C++",
    ".c":    "C",
    ".h":    "C/C++ Header",
    ".md":   "Markdown",
    ".json": "JSON",
    ".yml":  "YAML",
    ".yaml": "YAML",
}

# ---------------------------------------------------------------------------
# Directories to skip during traversal
# ---------------------------------------------------------------------------

IGNORED_DIRS: set[str] = {
    "node_modules",
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    "venv",
    "env",
    ".env",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "target",       # Rust / Java Maven / Gradle
    "out",          # Java / others
    ".idea",
    ".vscode",
}

# Maximum file size to read into memory (default: 1 MB)
MAX_FILE_SIZE_BYTES: int = 1 * 1024 * 1024


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class FileDocument:
    """Represents a single scanned source file inside a repository."""

    absolute_path: str
    """Absolute path to the file on disk."""

    relative_path: str
    """Path relative to the scanned repository root."""

    extension: str
    """File extension including the leading dot (e.g. '.py')."""

    language: str
    """Best-guess programming or markup language for this file."""

    size_bytes: int
    """Size of the file in bytes."""

    content: Optional[str]
    """Raw UTF-8 text content of the file, or None if it could not be decoded."""

    metadata: dict = field(default_factory=dict)
    """Optional extra metadata (populated by downstream parsers)."""


# ---------------------------------------------------------------------------
# Core scanner
# ---------------------------------------------------------------------------

class RepositoryScanner:
    """
    Recursively scans a local project directory, collecting all supported
    source files while ignoring irrelevant directories and large binaries.
    """

    def __init__(
        self,
        repo_path: str | Path,
        max_file_size_bytes: int = MAX_FILE_SIZE_BYTES,
        extra_ignored_dirs: Optional[set[str]] = None,
    ) -> None:
        """
        Initialise the scanner.

        Args:
            repo_path:           Absolute or relative path to the repository root.
            max_file_size_bytes: Files larger than this will be skipped (default 1 MB).
            extra_ignored_dirs:  Additional directory names to skip beyond the defaults.
        """
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {self.repo_path}")
        if not self.repo_path.is_dir():
            raise NotADirectoryError(f"Expected a directory, got: {self.repo_path}")

        self.max_file_size_bytes = max_file_size_bytes
        self.ignored_dirs: set[str] = IGNORED_DIRS.copy()
        if extra_ignored_dirs:
            self.ignored_dirs.update(extra_ignored_dirs)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def scan(self) -> List[FileDocument]:
        """
        Traverse the repository and return a list of :class:`FileDocument` objects.

        Only files whose extensions appear in :data:`EXTENSION_LANGUAGE_MAP` are
        included. Files larger than ``max_file_size_bytes`` or non-UTF-8 binaries
        will have their ``content`` field set to ``None``.

        Returns:
            A list of :class:`FileDocument` instances, one per supported file found.
        """
        results: List[FileDocument] = []

        for root, dirs, files in os.walk(self.repo_path, topdown=True):
            # Prune ignored directories in-place so os.walk skips them entirely
            dirs[:] = [
                d for d in dirs
                if d not in self.ignored_dirs and not d.startswith(".")
            ]

            for filename in files:
                file_path = Path(root) / filename
                doc = self._process_file(file_path)
                if doc is not None:
                    results.append(doc)

        return results

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _process_file(self, file_path: Path) -> Optional[FileDocument]:
        """
        Attempt to read and package a single file as a :class:`FileDocument`.

        Args:
            file_path: Absolute path to the candidate file.

        Returns:
            A :class:`FileDocument` if the file is supported, otherwise ``None``.
        """
        ext = file_path.suffix.lower()
        language = EXTENSION_LANGUAGE_MAP.get(ext)
        if language is None:
            return None  # Unsupported file type – skip silently

        try:
            size_bytes = file_path.stat().st_size
        except OSError:
            return None  # File disappeared or permission denied

        content: Optional[str] = None
        if size_bytes <= self.max_file_size_bytes:
            content = self._read_text(file_path)

        relative_path = str(file_path.relative_to(self.repo_path))

        return FileDocument(
            absolute_path=str(file_path),
            relative_path=relative_path,
            extension=ext,
            language=language,
            size_bytes=size_bytes,
            content=content,
        )

    @staticmethod
    def _read_text(file_path: Path) -> Optional[str]:
        """
        Read a file as UTF-8 text.

        Args:
            file_path: Path to the file.

        Returns:
            The file content as a string, or ``None`` if the file is binary or
            unreadable.
        """
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # File is not valid UTF-8 (binary or non-standard encoding) – skip content
            return None
        except OSError:
            return None


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def scan_repository(
    repo_path: str | Path,
    max_file_size_bytes: int = MAX_FILE_SIZE_BYTES,
    extra_ignored_dirs: Optional[set[str]] = None,
) -> List[FileDocument]:
    """
    Scan *repo_path* and return a list of supported :class:`FileDocument` objects.

    This is the primary public entry-point for the ingestion pipeline.

    Args:
        repo_path:           Path to the local repository root directory.
        max_file_size_bytes: Skip files larger than this many bytes (default 1 MB).
        extra_ignored_dirs:  Additional directory names to ignore.

    Returns:
        A list of :class:`FileDocument` instances for every supported source file
        found inside *repo_path*.

    Example::

        from repomind.ingestion.repository_scanner import scan_repository

        docs = scan_repository("/home/user/projects/my-app")
        for doc in docs:
            print(f"{doc.relative_path} ({doc.language}) - {doc.size_bytes} bytes")
    """
    scanner = RepositoryScanner(
        repo_path=repo_path,
        max_file_size_bytes=max_file_size_bytes,
        extra_ignored_dirs=extra_ignored_dirs,
    )
    return scanner.scan()
