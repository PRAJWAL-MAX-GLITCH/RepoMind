"""
repomind.analyzers.architecture_analyzer
=========================================
Generates a structured architectural understanding of an indexed repository.

The analyzer works in two complementary phases:

Phase 1 – **File-system scan** (primary): Walks the repository directory tree
    directly to detect modules (top-level folders), entry points, and
    important files using heuristic filename/path patterns. This is both
    reliable and fast because it does not depend on LLM availability.

Phase 2 – **Semantic enrichment** (optional): Pulls representative code chunks
    from the Qdrant vector index and, when a real LLM is configured, adds a
    natural-language ``project_summary`` and supplemental ``architecture_notes``.
    When the mock LLM is active the enrichment step is silently skipped and a
    clean heuristic summary is generated instead.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from repomind.rag.retriever import RepositoryRetriever

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns for heuristic classification
# ---------------------------------------------------------------------------

_ENTRY_POINT_RE = re.compile(
    r"(^|[/\\])(main|app|server|index|run|start|wsgi|asgi|manage|cli)\.(py|js|ts|jsx|tsx)$",
    re.IGNORECASE,
)
_CONFIG_RE = re.compile(
    r"(pyproject\.toml|setup\.py|setup\.cfg|package\.json|requirements.*\.txt"
    r"|Dockerfile(\..*)?|docker-compose.*|\.env(\..+)?"
    r"|config\.(py|js|ts|yaml|yml|json)"
    r"|settings\.(py|js|ts|yaml|yml)"
    r"|webpack\.config\..+|tsconfig.*\.json|jest\.config\..+"
    r"|Makefile|\.github/.*\.ya?ml)$",
    re.IGNORECASE,
)
_DATABASE_RE = re.compile(
    r"(^|[/\\])(models?|migration|schema|database|db|orm|repository|store|dao)\.(py|js|ts|java|sql)$"
    r"|(^|[/\\])(models|migrations|repositories|database)[/\\]",
    re.IGNORECASE,
)
_AUTH_RE = re.compile(
    r"(^|[/\\])(auth|authentication|authoriz|login|logout|jwt|oauth|token|password|session).*\.(py|js|ts|java)$"
    r"|(^|[/\\])(auth|security|permissions)[/\\]",
    re.IGNORECASE,
)
_API_RE = re.compile(
    r"(^|[/\\])(routes?|router|endpoint|controller|handler|views?|api)\.(py|js|ts|java)$"
    r"|(^|[/\\])(routes?|endpoints?|controllers?|views?|api)[/\\]",
    re.IGNORECASE,
)
_ML_RE = re.compile(
    r"(^|[/\\])(train|predict|inference|embedding|vector|dataset|feature|ml_pipeline).*\.(py|ipynb)$"
    r"|(^|[/\\])(models|ml|ai|training|inference|embeddings)[/\\]",
    re.IGNORECASE,
)

_EXT_TO_LANG: Dict[str, str] = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript", ".tsx": "TypeScript (TSX)", ".java": "Java",
    ".cpp": "C++", ".c": "C", ".cs": "C#", ".go": "Go", ".rb": "Ruby",
    ".rs": "Rust", ".kt": "Kotlin", ".swift": "Swift", ".md": "Markdown",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".sh": "Shell", ".sql": "SQL", ".html": "HTML", ".css": "CSS",
    ".ipynb": "Jupyter Notebook",
}

_IGNORED_DIRS: Set[str] = {
    "node_modules", ".git", "__pycache__", "build", "dist",
    ".venv", "venv", ".mypy_cache", ".pytest_cache", ".tox",
}


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

class ArchitectureSummary(BaseModel):
    project_summary: str = Field(..., description="High-level summary of the project")
    languages: List[str] = Field(..., description="Programming languages detected")
    main_modules: List[str] = Field(..., description="Major top-level folders / modules")
    entry_points: List[str] = Field(..., description="Probable entry-point files")
    important_files: List[str] = Field(
        ...,
        description="Config, database, auth, API-route, and ML files",
    )
    architecture_notes: List[str] = Field(
        ..., description="Key architectural observations"
    )


# ---------------------------------------------------------------------------
# File-system scanner helpers
# ---------------------------------------------------------------------------

def _walk_repo(repo_path: Path):
    """Yield (relative_str, is_dir) for every non-ignored item under repo_path."""
    for root, dirs, files in os.walk(str(repo_path)):
        dirs[:] = [d for d in dirs if d not in _IGNORED_DIRS and not d.startswith(".")]
        rel_root = Path(root).relative_to(repo_path)
        for f in files:
            rel = rel_root / f
            yield str(rel), False
        for d in dirs:
            rel = rel_root / d
            yield str(rel), True


def _scan_filesystem(repo_path: Path) -> Dict[str, Any]:
    """
    Walk the repository directory and classify files heuristically.

    Returns a dict with sets: languages, modules, entry_points, important_files,
    and a list of all file paths.
    """
    languages: Set[str] = set()
    modules: Set[str] = set()
    entry_points: List[str] = []
    important_files: List[str] = []
    all_files: List[str] = []
    has_db = has_auth = has_api = has_ml = False

    for rel, is_dir in _walk_repo(repo_path):
        rel_path = Path(rel)
        parts = rel_path.parts

        # Top-level folder → module
        if len(parts) >= 2 and is_dir and len(rel_path.parent.parts) == 0:
            modules.add(parts[0])
        elif not is_dir and len(parts) >= 2:
            modules.add(parts[0])

        if is_dir:
            continue

        all_files.append(rel)

        # Language detection
        ext = rel_path.suffix.lower()
        lang = _EXT_TO_LANG.get(ext)
        if lang:
            languages.add(lang)

        # Classification
        if _ENTRY_POINT_RE.search(rel):
            entry_points.append(rel)

        classified = False
        if _CONFIG_RE.search(str(rel_path.name)) or _CONFIG_RE.search(rel):
            important_files.append(rel)
            classified = True
        if _DATABASE_RE.search(rel):
            if not classified:
                important_files.append(rel)
            has_db = True
        if _AUTH_RE.search(rel):
            if rel not in important_files:
                important_files.append(rel)
            has_auth = True
        if _API_RE.search(rel):
            if rel not in important_files:
                important_files.append(rel)
            has_api = True
        if _ML_RE.search(rel):
            if rel not in important_files:
                important_files.append(rel)
            has_ml = True

    return {
        "languages": languages,
        "modules": modules,
        "entry_points": entry_points,
        "important_files": important_files,
        "all_files": all_files,
        "has_db": has_db,
        "has_auth": has_auth,
        "has_api": has_api,
        "has_ml": has_ml,
    }


# ---------------------------------------------------------------------------
# Optional LLM enrichment
# ---------------------------------------------------------------------------

def _try_llm_summary(chunks: List[Dict[str, Any]], question: str) -> Optional[str]:
    """Try LLM; silently return None if mock or error."""
    if not chunks:
        return None
    context = "\n\n".join(
        f"File: {c.get('file_path', '?')}\n{c.get('content', '')[:500]}"
        for c in chunks[:5]
    )
    prompt = (
        "You are a senior software architect. "
        "Provide a concise, highly technical 2-3 sentence summary using ONLY the code context below. "
        "Avoid conversational fluff. Focus strictly on architectural patterns, frameworks, and system boundaries.\n\n"
        f"Question: {question}\n\nContext:\n{context}\n\nAnswer:"
    )
    try:
        from repomind.core.di import get_global_injector
        from repomind.models.llm.llm_component import LLMComponent

        llm_component = get_global_injector().get(LLMComponent)
        llm = llm_component.get_llm()
        response = str(llm.complete(prompt)).strip()
        # Detect mock echo (returns the entire prompt back)
        if "You are a senior software architect" in response or len(response) > 3000:
            return None
        return response or None
    except Exception as e:
        logger.debug("LLM enrichment skipped: %s", e)
        return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def analyze_architecture(repo_name: str, repo_path: Optional[str] = None) -> dict:
    """
    Generate a structured architectural understanding of a repository.

    Args:
        repo_name:  Name of the indexed repository (used for Qdrant filtering).
        repo_path:  Optional path to the local repository root. When provided,
                    the filesystem walk gives much richer module / file data.

    Returns:
        dict matching the :class:`ArchitectureSummary` schema.
    """
    logger.info("Starting architecture analysis for repo '%s'", repo_name)

    # ------------------------------------------------------------------
    # Phase 1: Filesystem scan (if path available)
    # ------------------------------------------------------------------
    fs_data: Dict[str, Any] = {
        "languages": set(), "modules": set(), "entry_points": [],
        "important_files": [], "all_files": [],
        "has_db": False, "has_auth": False, "has_api": False, "has_ml": False,
    }

    categorized: Dict[str, List[str]] = {
        "auth": [], "database": [], "api": [], "ml": [], "config": [], "tests": []
    }
    dependencies: Dict[str, List[str]] = {}
    directory_tree: List[Dict] = []

    if repo_path:
        rp = Path(repo_path)
        if rp.exists() and rp.is_dir():
            logger.info("Performing filesystem scan of '%s'", repo_path)
            fs_data = _scan_filesystem(rp)

            # Build categorized files dict
            for f in fs_data["important_files"]:
                if _AUTH_RE.search(f):
                    categorized["auth"].append(f)
                if _DATABASE_RE.search(f):
                    categorized["database"].append(f)
                if _API_RE.search(f):
                    categorized["api"].append(f)
                if _ML_RE.search(f):
                    categorized["ml"].append(f)
                if _CONFIG_RE.search(Path(f).name) or _CONFIG_RE.search(f):
                    categorized["config"].append(f)

            # Test files
            for f in fs_data["all_files"]:
                if re.search(r"(test|spec|__tests__|tests)[/\\]", f, re.IGNORECASE) or \
                   re.search(r"(test_|_test|_spec)\.(py|js|ts)$", f, re.IGNORECASE):
                    categorized["tests"].append(f)

            # Deduplicate
            for k in categorized:
                categorized[k] = sorted(set(categorized[k]))

            # Dependencies from manifest files
            dep_files = {
                "Python": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
                "Node": ["package.json"],
                "Ruby": ["Gemfile"],
                "Go": ["go.mod"],
                "Rust": ["Cargo.toml"],
                "Java": ["pom.xml", "build.gradle"],
            }
            for lang, manifests in dep_files.items():
                for manifest in manifests:
                    manifest_path = rp / manifest
                    if manifest_path.exists():
                        try:
                            content = manifest_path.read_text(encoding="utf-8", errors="ignore")
                            deps = _extract_deps(manifest, content)
                            if deps:
                                dependencies[lang] = deps
                        except Exception:
                            pass

            # Build directory tree (top 2 levels)
            directory_tree = _build_tree(rp, max_depth=2)

        else:
            logger.warning("repo_path '%s' does not exist — skipping FS scan", repo_path)

    # ------------------------------------------------------------------
    # Phase 2: Semantic retrieval from vector store
    # ------------------------------------------------------------------
    retriever = RepositoryRetriever()
    semantic_queries = {
        "structure": "project structure modules packages",
        "entry_points": "main application entry point",
        "config": "configuration settings environment",
        "database": "database connection model migration",
        "auth": "authentication login security token",
        "api": "API routes endpoints controllers",
        "ml": "machine learning AI embedding model",
    }

    all_chunks: List[Dict[str, Any]] = []
    query_chunks: Dict[str, List[Dict[str, Any]]] = {}
    seen_ids: Set = set()

    for key, q in semantic_queries.items():
        chunks = retriever.retrieve(query=q, repo_name=repo_name, top_k=4)
        query_chunks[key] = chunks
        for c in chunks:
            cid = c.get("chunk_id", hash(c.get("content", "")))
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_chunks.append(c)

    # Supplement language + module detection from chunk metadata
    for c in all_chunks:
        lang = c.get("language", "")
        if lang and lang.lower() not in ("unknown", "text", ""):
            fs_data["languages"].add(lang.capitalize())

        fp = c.get("file_path", "")
        if fp:
            parts = Path(fp).parts
            if len(parts) >= 2:
                fs_data["modules"].add(parts[0])
            if _ENTRY_POINT_RE.search(fp) and fp not in fs_data["entry_points"]:
                fs_data["entry_points"].append(fp)
            for pat, key_name in [
                (_DATABASE_RE, "has_db"), (_AUTH_RE, "has_auth"),
                (_API_RE, "has_api"), (_ML_RE, "has_ml"),
            ]:
                if pat.search(fp):
                    fs_data[key_name] = True
                    if fp not in fs_data["important_files"]:
                        fs_data["important_files"].append(fp)

    # ------------------------------------------------------------------
    # Phase 3: Build architecture notes
    # ------------------------------------------------------------------
    arch_notes: List[str] = []

    if fs_data["entry_points"]:
        arch_notes.append(
            f"{len(fs_data['entry_points'])} probable entry point(s) detected: "
            + ", ".join(fs_data["entry_points"][:5])
        )
    if fs_data["has_db"]:
        arch_notes.append("Database-related files detected (models, migrations, or ORMs).")
    if fs_data["has_auth"]:
        arch_notes.append("Authentication / security files detected.")
    if fs_data["has_api"]:
        arch_notes.append("API routing files detected.")
    if fs_data["has_ml"]:
        arch_notes.append("Machine learning / AI files detected.")
    if fs_data["modules"]:
        arch_notes.append(
            f"Top-level modules: {', '.join(sorted(fs_data['modules']))}."
        )

    llm_pattern_note = _try_llm_summary(
        query_chunks.get("structure", []),
        "What are the major architectural patterns or design decisions in this codebase?",
    )
    if llm_pattern_note:
        arch_notes.insert(0, llm_pattern_note)

    if not all_chunks and not fs_data["all_files"]:
        arch_notes.append(
            "No data found. Run index_repository() first, and pass repo_path for richer analysis."
        )

    # ------------------------------------------------------------------
    # Phase 4: Project summary (LLM → fallback heuristic)
    # ------------------------------------------------------------------
    summary_text = _try_llm_summary(
        all_chunks,
        "What does this project do and what is its high-level architecture?",
    )

    if not summary_text:
        langs = ", ".join(sorted(fs_data["languages"])) or "unknown"
        mods = ", ".join(sorted(fs_data["modules"])) or "undetermined"
        file_count = len(fs_data["all_files"]) or len(set(
            c.get("file_path", "") for c in all_chunks if c.get("file_path")
        ))
        summary_text = (
            f"Repository '{repo_name}' appears to be written in {langs}. "
            f"Top-level modules: {mods}. "
            f"Analysed {file_count} files across {len(all_chunks)} indexed chunks."
        )

    result = ArchitectureSummary(
        project_summary=summary_text,
        languages=sorted(fs_data["languages"]),
        main_modules=sorted(fs_data["modules"]),
        entry_points=sorted(set(fs_data["entry_points"])),
        important_files=sorted(set(fs_data["important_files"])),
        architecture_notes=arch_notes,
    )

    logger.info("Architecture analysis complete for '%s'", repo_name)
    return {
        **result.model_dump(),
        "categorized_files": categorized,
        "dependencies": dependencies,
        "directory_tree": directory_tree,
        "file_count": len(fs_data["all_files"]),
        "has_db": fs_data["has_db"],
        "has_auth": fs_data["has_auth"],
        "has_api": fs_data["has_api"],
        "has_ml": fs_data["has_ml"],
    }
