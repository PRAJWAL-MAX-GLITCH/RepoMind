"""
repomind.parsers.code_chunker
==============================
Language-aware code chunker that extracts semantic chunks aligned with
structural boundaries (functions, classes, exports) using regex-based
structural detection. Falls back to a sliding line-window when structural
detection fails or yields zero chunks.

All chunks are returned as :class:`repomind.models.chunk_schema.ChunkMetadata`
instances — the canonical metadata contract for the entire pipeline.

Supported languages:
    Python, JavaScript, TypeScript (JSX/TSX), Java, C, C++

Usage::

    from repomind.parsers.code_chunker import chunk_code_file

    chunks = chunk_code_file(
        repo_root="/path/to/repo",
        file_path="src/auth.py",
        language="Python",
        content=open("src/auth.py").read(),
    )
    for chunk in chunks:
        print(chunk.location_summary())
"""

from __future__ import annotations

import re
from typing import List, Optional

from repomind.models.chunk_schema import ChunkMetadata




# ---------------------------------------------------------------------------
# Language-specific structural patterns
# ---------------------------------------------------------------------------

# Each entry maps to a list of (chunk_type, compiled_regex) pairs.
# The regex must capture the first line of a structural boundary; we then
# detect the block's extent via indentation or brace counting.

_PYTHON_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("class",    re.compile(r"^(class\s+(\w+).*:)")),
    ("function", re.compile(r"^((?:async\s+)?def\s+(\w+)\s*\()")),
]

_JS_TS_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("class",    re.compile(r"^((?:export\s+)?(?:default\s+)?class\s+(\w+))")),
    ("function", re.compile(r"^((?:export\s+)?(?:default\s+)?(?:async\s+)?function[\s*]+(\w+)\s*\()")),
    ("function", re.compile(r"^((?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(.*\)\s*=>)")),
    ("export",   re.compile(r"^(export\s+(?:default\s+)?(?:const|let|var|type|interface)\s+(\w+))")),
]

_JAVA_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("class",    re.compile(r"^((?:public|private|protected|abstract|final|\s)*class\s+(\w+))")),
    ("function", re.compile(r"^(\s*(?:public|private|protected|static|final|synchronized|\s)*[\w<>\[\]]+\s+(\w+)\s*\()")),
]

_C_CPP_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("function", re.compile(r"^([\w\s\*]+\s+(\w+)\s*\([^)]*\)\s*\{?)")),
    ("class",    re.compile(r"^((?:class|struct)\s+(\w+))")),
]

_PATTERNS_BY_LANGUAGE: dict[str, list[tuple[str, re.Pattern]]] = {
    "Python":               _PYTHON_PATTERNS,
    "JavaScript":           _JS_TS_PATTERNS,
    "JavaScript (JSX)":     _JS_TS_PATTERNS,
    "TypeScript":           _JS_TS_PATTERNS,
    "TypeScript (TSX)":     _JS_TS_PATTERNS,
    "Java":                 _JAVA_PATTERNS,
    "C":                    _C_CPP_PATTERNS,
    "C++":                  _C_CPP_PATTERNS,
    "C/C++ Header":         _C_CPP_PATTERNS,
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def chunk_code_file(
    repo_root: str,
    file_path: str,
    language: str,
    content: str,
    fallback_window: int = 60,
    fallback_overlap: int = 10,
) -> List[ChunkMetadata]:
    """
    Split *content* into semantically-aware :class:`ChunkMetadata` objects.

    Attempts language-specific structural chunking first.  If the language is
    not recognised, or if structural chunking returns zero chunks, falls back to
    sliding line-window chunking.

    Args:
        repo_root:         Absolute path to the repository root (for naming).
        file_path:         Source file path relative to *repo_root*.
        language:          Language label as returned by the repository scanner.
        content:           Raw UTF-8 text of the file.
        fallback_window:   Number of lines per fallback chunk.
        fallback_overlap:  Overlap in lines between consecutive fallback chunks.

    Returns:
        A non-empty list of :class:`ChunkMetadata` objects.
    """
    if not content or not content.strip():
        return []

    patterns = _PATTERNS_BY_LANGUAGE.get(language)
    chunks: List[ChunkMetadata] = []

    if patterns:
        if language == "Python":
            chunks = _chunk_python(repo_root, file_path, language, content, patterns)
        else:
            chunks = _chunk_brace_based(repo_root, file_path, language, content, patterns)

    if not chunks:
        # Fallback: line-window chunking
        chunks = _chunk_line_window(
            repo_root, file_path, language, content,
            window=fallback_window,
            overlap=fallback_overlap,
        )

    return chunks


# ---------------------------------------------------------------------------
# Python chunker (indentation-based block detection)
# ---------------------------------------------------------------------------

def _chunk_python(
    repo_root: str,
    file_path: str,
    language: str,
    content: str,
    patterns: list[tuple[str, re.Pattern]],
) -> List[ChunkMetadata]:
    """
    Extract Python top-level and class-level definitions using indentation
    to determine block boundaries.
    """
    lines = content.splitlines()
    total = len(lines)
    chunks: List[ChunkMetadata] = []
    starts: list[tuple[int, str, Optional[str]]] = []  # (line_idx, chunk_type, name)

    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        for chunk_type, pattern in patterns:
            m = pattern.match(stripped)
            if m:
                name = m.group(2) if m.lastindex and m.lastindex >= 2 else None
                starts.append((idx, chunk_type, name))
                break

    # Determine block extents by finding where the next same-or-lower indent begins
    for pos, (start_idx, chunk_type, name) in enumerate(starts):
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
        # End is just before the next structural start at same/lower indent, or EOF
        if pos + 1 < len(starts):
            next_start = starts[pos + 1][0]
            end_idx = next_start - 1
        else:
            end_idx = total - 1

        # Trim trailing blank lines
        while end_idx > start_idx and not lines[end_idx].strip():
            end_idx -= 1

        chunk_text = "\n".join(lines[start_idx:end_idx + 1])
        chunks.append(
            ChunkMetadata.from_parts(
                repo_root=repo_root,
                file_path=file_path,
                language=language,
                chunk_type=chunk_type,
                content=chunk_text,
                start_line=start_idx + 1,
                end_line=end_idx + 1,
                symbol_name=name,
            )
        )

    # Capture any module-level code before the first definition
    if starts and starts[0][0] > 0:
        preamble = "\n".join(lines[: starts[0][0]])
        if preamble.strip():
            chunks.insert(
                0,
                ChunkMetadata.from_parts(
                    repo_root=repo_root,
                    file_path=file_path,
                    language=language,
                    chunk_type="module",
                    content=preamble,
                    start_line=1,
                    end_line=starts[0][0],
                    symbol_name=None,
                ),
            )

    return chunks


# ---------------------------------------------------------------------------
# Brace-based chunker (JS/TS/Java/C/C++)
# ---------------------------------------------------------------------------

def _chunk_brace_based(
    repo_root: str,
    file_path: str,
    language: str,
    content: str,
    patterns: list[tuple[str, re.Pattern]],
) -> List[ChunkMetadata]:
    """
    Extract structural chunks from brace-delimited languages using brace
    counting to find closing braces.
    """
    lines = content.splitlines()
    total = len(lines)
    chunks: List[ChunkMetadata] = []

    idx = 0
    while idx < total:
        line = lines[idx].lstrip()
        matched = False
        for chunk_type, pattern in patterns:
            m = pattern.match(line)
            if m:
                name = m.group(2) if m.lastindex and m.lastindex >= 2 else None
                start_idx = idx
                # Count braces to find block end
                depth = 0
                end_idx = idx
                for scan in range(idx, total):
                    depth += lines[scan].count("{") - lines[scan].count("}")
                    if scan > idx and depth <= 0:
                        end_idx = scan
                        break
                    end_idx = scan  # fallback: reached EOF inside block

                chunk_text = "\n".join(lines[start_idx:end_idx + 1])
                chunks.append(
                    ChunkMetadata.from_parts(
                        repo_root=repo_root,
                        file_path=file_path,
                        language=language,
                        chunk_type=chunk_type,
                        content=chunk_text,
                        start_line=start_idx + 1,
                        end_line=end_idx + 1,
                        symbol_name=name,
                    )
                )
                idx = end_idx + 1
                matched = True
                break

        if not matched:
            idx += 1

    return chunks


# ---------------------------------------------------------------------------
# Fallback: sliding line-window chunker
# ---------------------------------------------------------------------------

def _chunk_line_window(
    repo_root: str,
    file_path: str,
    language: str,
    content: str,
    window: int = 60,
    overlap: int = 10,
) -> List[ChunkMetadata]:
    """
    Chunk *content* using a sliding line window.  Used as fallback when
    structural parsing yields no results.

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
        chunk_text = "\n".join(lines[start:end])
        if chunk_text.strip():
            chunks.append(
                ChunkMetadata.from_parts(
                    repo_root=repo_root,
                    file_path=file_path,
                    language=language,
                    chunk_type="block",
                    content=chunk_text,
                    start_line=start + 1,
                    end_line=end,
                    symbol_name=None,
                )
            )
        start += step

    return chunks
