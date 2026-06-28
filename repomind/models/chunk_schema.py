"""
repomind.models.chunk_schema
==============================
Single source of truth for the metadata attached to every indexed chunk
in RepoMind.  All pipeline stages — chunking, ingestion, vector store, and
retrieval — must use :class:`ChunkMetadata` to guarantee consistent metadata
throughout the system.

Schema fields
-------------
repo_name    Repository name (last segment of the repo path, e.g. "my-app").
file_path    Path relative to the repository root (e.g. "src/auth/login.py").
file_name    Bare filename including extension (e.g. "login.py").
extension    Lowercase file extension (e.g. ".py").
language     Human-readable language label (e.g. "Python", "TypeScript").
chunk_id     Stable UUID4 string, unique across a session / store.
chunk_type   Structural classification: "function", "class", "module",
             "export", "section", "paragraph", "block".
start_line   1-indexed first line of the chunk in the source file.
end_line     1-indexed last line of the chunk (inclusive).
symbol_name  Name of the captured symbol (function/class name), or None.
content      Raw source text of the chunk.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """
    Pydantic model describing a single indexed code or text chunk.

    This is the canonical data contract shared by the ingestion pipeline,
    vector store, and retrieval layer.  All fields are documented to aid
    LLM-assisted query routing (e.g. "where is auth implemented?").
    """

    # -- Origin ----------------------------------------------------------
    repo_name: str = Field(
        description="Repository name, e.g. 'my-app'. Derived from the last "
                    "segment of the repo root path."
    )
    file_path: str = Field(
        description="File path relative to the repository root, "
                    "e.g. 'src/auth/login.py'."
    )
    file_name: str = Field(
        description="Bare filename with extension, e.g. 'login.py'."
    )
    extension: str = Field(
        description="Lowercase file extension including leading dot, e.g. '.py'."
    )
    language: str = Field(
        description="Human-readable language label, e.g. 'Python', 'TypeScript'."
    )

    # -- Identity --------------------------------------------------------
    chunk_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Stable UUID4 string, unique per chunk within a session.",
    )

    # -- Structure -------------------------------------------------------
    chunk_type: str = Field(
        description="Structural type: 'function', 'class', 'module', 'export', "
                    "'section', 'paragraph', or 'block'."
    )
    start_line: int = Field(
        description="1-indexed line number where this chunk starts."
    )
    end_line: int = Field(
        description="1-indexed line number where this chunk ends (inclusive)."
    )
    symbol_name: Optional[str] = Field(
        default=None,
        description="Name of the extracted symbol (function/class) if available.",
    )

    # -- Content ---------------------------------------------------------
    content: str = Field(
        description="The raw source or documentation text of this chunk."
    )

    # -- Helpers ---------------------------------------------------------
    @classmethod
    def from_parts(
        cls,
        *,
        repo_root: str,
        file_path: str,
        language: str,
        chunk_type: str,
        start_line: int,
        end_line: int,
        content: str,
        symbol_name: Optional[str] = None,
    ) -> "ChunkMetadata":
        """
        Convenience constructor that derives ``repo_name``, ``file_name``,
        and ``extension`` automatically from *repo_root* and *file_path*.

        Args:
            repo_root:   Absolute path to the repository root.
            file_path:   Relative (or absolute) path to the file.
            language:    Language label from the scanner.
            chunk_type:  Structural type string.
            start_line:  1-indexed start line.
            end_line:    1-indexed end line (inclusive).
            content:     Raw chunk text.
            symbol_name: Extracted function/class name, or None.

        Returns:
            A fully populated :class:`ChunkMetadata` instance.
        """
        p = Path(file_path)
        repo_name = Path(repo_root).name
        return cls(
            repo_name=repo_name,
            file_path=str(file_path),
            file_name=p.name,
            extension=p.suffix.lower(),
            language=language,
            chunk_type=chunk_type,
            start_line=start_line,
            end_line=end_line,
            content=content,
            symbol_name=symbol_name,
        )

    def location_summary(self) -> str:
        """
        Returns a short human-readable location string suitable for citations.

        Example: ``'login.py:45-78 [function authenticate]'``
        """
        symbol = f" [{self.chunk_type} {self.symbol_name}]" if self.symbol_name else ""
        return f"{self.file_name}:{self.start_line}-{self.end_line}{symbol}"

    class Config:
        populate_by_name = True
