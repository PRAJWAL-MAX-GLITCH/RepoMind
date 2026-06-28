"""
repomind.parsers.text_chunker
==============================
Generic text chunker for documentation files such as README.md, YAML
configs, and JSON manifests that have no structural code boundaries.

All chunks are returned as :class:`repomind.models.chunk_schema.ChunkMetadata`
instances — the canonical metadata contract for the entire pipeline.

Chunking strategy:
  - Markdown: chunk by heading sections (## headings), then by paragraph if
    a section is too long.
  - Everything else: sliding line-window with configurable size and overlap.

Usage::

    from repomind.parsers.text_chunker import chunk_text_file

    chunks = chunk_text_file(
        repo_root="/path/to/repo",
        file_path="README.md",
        language="Markdown",
        content=open("README.md").read(),
    )
    for chunk in chunks:
        print(chunk.location_summary())
"""

from __future__ import annotations

import re
from typing import List, Optional

from repomind.models.chunk_schema import ChunkMetadata




# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

DEFAULT_WINDOW: int = 50       # lines per fallback window chunk
DEFAULT_OVERLAP: int = 10      # overlap lines between adjacent window chunks
MAX_SECTION_LINES: int = 150   # section chunks longer than this get sub-split


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def chunk_text_file(
    repo_root: str,
    file_path: str,
    language: str,
    content: str,
    window: int = DEFAULT_WINDOW,
    overlap: int = DEFAULT_OVERLAP,
    max_section_lines: int = MAX_SECTION_LINES,
) -> List[ChunkMetadata]:
    """
    Split *content* into :class:`ChunkMetadata` objects appropriate for
    documentation-style files.

    Markdown files are chunked by heading sections; all other text files use
    a sliding line-window.

    Args:
        repo_root:         Absolute path to the repository root.
        file_path:         Source file path relative to *repo_root*.
        language:          Language label (e.g. ``'Markdown'``, ``'YAML'``).
        content:           Raw UTF-8 text of the file.
        window:            Lines per fallback window chunk (default 50).
        overlap:           Overlap lines between window chunks (default 10).
        max_section_lines: Max lines in a Markdown section before sub-splitting
                           it into paragraphs (default 150).

    Returns:
        A non-empty list of :class:`ChunkMetadata` objects.
    """
    if not content or not content.strip():
        return []

    if language == "Markdown":
        chunks = _chunk_markdown(
            repo_root, file_path, language, content, max_section_lines, window, overlap
        )
    else:
        chunks = _chunk_line_window(repo_root, file_path, language, content, window, overlap)

    return chunks if chunks else _chunk_line_window(
        repo_root, file_path, language, content, window, overlap
    )


# ---------------------------------------------------------------------------
# Markdown chunker (section-based)
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")


def _chunk_markdown(
    repo_root: str,
    file_path: str,
    language: str,
    content: str,
    max_section_lines: int,
    window: int,
    overlap: int,
) -> List[ChunkMetadata]:
    """
    Split Markdown into sections delimited by ATX headings (# through ######).

    Sections that exceed *max_section_lines* are further sub-split by
    paragraph boundaries.  Content before the first heading is emitted as its
    own 'block' chunk.
    """
    lines = content.splitlines()
    total = len(lines)
    chunks: List[ChunkMetadata] = []

    # Collect heading positions
    heading_positions: list[tuple[int, str]] = []  # (line_idx, heading_text)
    for idx, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m:
            heading_positions.append((idx, m.group(2).strip()))

    if not heading_positions:
        # No headings found – fall through to line-window
        return []

    # Helper to emit a section (may sub-split by paragraph)
    def emit_section(
        start_idx: int,
        end_idx: int,
        title: Optional[str],
        ctype: str,
    ) -> None:
        section_lines = lines[start_idx:end_idx + 1]
        if len(section_lines) <= max_section_lines:
            text = "\n".join(section_lines)
            if text.strip():
                chunks.append(
                    ChunkMetadata.from_parts(
                        repo_root=repo_root,
                        file_path=file_path,
                        language=language,
                        chunk_type=ctype,
                        content=text,
                        start_line=start_idx + 1,
                        end_line=end_idx + 1,
                        symbol_name=title,
                    )
                )
        else:
            # Sub-split by paragraph (blank-line boundaries)
            para_chunks = _split_paragraphs(
                repo_root, file_path, language, section_lines, start_idx, title
            )
            chunks.extend(para_chunks)

    # Preamble before the first heading
    first_heading_idx = heading_positions[0][0]
    if first_heading_idx > 0:
        emit_section(0, first_heading_idx - 1, None, "block")

    # Sections
    for pos, (h_idx, title) in enumerate(heading_positions):
        if pos + 1 < len(heading_positions):
            next_h_idx = heading_positions[pos + 1][0]
            section_end = next_h_idx - 1
        else:
            section_end = total - 1

        emit_section(h_idx, section_end, title, "section")

    return chunks


def _split_paragraphs(
    repo_root: str,
    file_path: str,
    language: str,
    section_lines: list[str],
    base_idx: int,
    section_title: Optional[str],
) -> List[ChunkMetadata]:
    """
    Split a list of lines into paragraph-based chunks (blank line separators).
    """
    chunks: List[ChunkMetadata] = []
    para_start: Optional[int] = None

    for local_idx, line in enumerate(section_lines):
        if line.strip():
            if para_start is None:
                para_start = local_idx
        else:
            if para_start is not None:
                text = "\n".join(section_lines[para_start:local_idx])
                if text.strip():
                    chunks.append(
                        ChunkMetadata.from_parts(
                            repo_root=repo_root,
                            file_path=file_path,
                            language=language,
                            chunk_type="paragraph",
                            content=text,
                            start_line=base_idx + para_start + 1,
                            end_line=base_idx + local_idx,
                            symbol_name=section_title,
                        )
                    )
                para_start = None

    # Flush last paragraph
    if para_start is not None:
        text = "\n".join(section_lines[para_start:])
        if text.strip():
            chunks.append(
                ChunkMetadata.from_parts(
                    repo_root=repo_root,
                    file_path=file_path,
                    language=language,
                    chunk_type="paragraph",
                    content=text,
                    start_line=base_idx + para_start + 1,
                    end_line=base_idx + len(section_lines),
                    symbol_name=section_title,
                )
            )

    return chunks


# ---------------------------------------------------------------------------
# Generic fallback: sliding line-window
# ---------------------------------------------------------------------------

def _chunk_line_window(
    repo_root: str,
    file_path: str,
    language: str,
    content: str,
    window: int,
    overlap: int,
) -> List[ChunkMetadata]:
    """
    Chunk *content* with a sliding line window.

    Args:
        window:  Number of lines per chunk.
        overlap: Number of lines shared between consecutive chunks.
    """
    lines = content.splitlines()
    total = len(lines)
    chunks: List[ChunkMetadata] = []
    step = max(1, window - overlap)

    start = 0
    while start < total:
        end = min(start + window, total)
        text = "\n".join(lines[start:end])
        if text.strip():
            chunks.append(
                ChunkMetadata.from_parts(
                    repo_root=repo_root,
                    file_path=file_path,
                    language=language,
                    chunk_type="block",
                    content=text,
                    start_line=start + 1,
                    end_line=end,
                    symbol_name=None,
                )
            )
        start += step

    return chunks
