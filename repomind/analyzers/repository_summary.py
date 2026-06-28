"""
repomind.analyzers.repository_summary
=======================================
Generates a developer onboarding summary for an indexed repository.

Builds on top of the architecture analyzer's heuristic file-system scan and
semantic retrieval, then composes an opinionated, human-readable summary dict
that answers the most common "where do I start?" questions for a new developer.

Output schema::

    {
        "repo_name":        str,
        "what_it_does":     str,
        "major_modules":    [str, ...],
        "tech_stack":       [str, ...],
        "entry_files":      [str, ...],
        "important_files":  {
            "auth":    [str, ...],
            "database":[str, ...],
            "api":     [str, ...],
            "ml":      [str, ...],
            "config":  [str, ...],
        },
        "needs_review":     [str, ...],
        "architecture_notes":[str, ...],
    }
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
# Regex classifiers  (intentionally generic — not hardcoded to one project)
# ---------------------------------------------------------------------------

_ENTRY_RE = re.compile(
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
    r"(^|[/\\])(auth|authentication|authoriz|login|logout|jwt|oauth|token|password|session)"
    r".*\.(py|js|ts|java)$"
    r"|(^|[/\\])(auth|security|permissions)[/\\]",
    re.IGNORECASE,
)
_API_RE = re.compile(
    r"(^|[/\\])(routes?|router|endpoint|controller|handler|views?|api)\.(py|js|ts|java)$"
    r"|(^|[/\\])(routes?|endpoints?|controllers?|views?|api)[/\\]",
    re.IGNORECASE,
)
_ML_RE = re.compile(
    r"(^|[/\\])(train|predict|inference|embedding|vector|dataset|feature|ml_pipeline)"
    r".*\.(py|ipynb)$"
    r"|(^|[/\\])(models|ml|ai|training|inference|embeddings)[/\\]",
    re.IGNORECASE,
)

# Files/patterns that often need manual review
_REVIEW_RE = re.compile(
    r"(TODO|FIXME|HACK|XXX|DEPRECATED|legacy|stub|placeholder)",
    re.IGNORECASE,
)
_REVIEW_FILES_RE = re.compile(
    r"(^|[/\\])(CHANGELOG|SECURITY|LICENSE|NOTICE|CONTRIBUTING|ROADMAP)\.(md|txt|rst)?$"
    r"|(^|[/\\])(temp|tmp|scratch|wip|experiment|test_manual)[/\\]",
    re.IGNORECASE,
)

# Extension → language
_EXT_LANG: Dict[str, str] = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript", ".tsx": "TypeScript (TSX)", ".java": "Java",
    ".cpp": "C++", ".c": "C", ".cs": "C#", ".go": "Go", ".rb": "Ruby",
    ".rs": "Rust", ".kt": "Kotlin", ".swift": "Swift",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".sh": "Shell", ".sql": "SQL", ".html": "HTML", ".css": "CSS",
    ".ipynb": "Jupyter Notebook",
}

# Technology fingerprints based on special files/directories
_TECH_FINGERPRINTS: List[tuple[re.Pattern, str]] = [
    (re.compile(r"requirements.*\.txt$|pyproject\.toml$|setup\.py$"), "Python"),
    (re.compile(r"package\.json$"), "Node.js"),
    (re.compile(r"Dockerfile"), "Docker"),
    (re.compile(r"docker-compose"), "Docker Compose"),
    (re.compile(r"\.github[/\\]workflows"), "GitHub Actions CI/CD"),
    (re.compile(r"tsconfig"), "TypeScript"),
    (re.compile(r"fastapi|uvicorn", re.IGNORECASE), "FastAPI"),
    (re.compile(r"django", re.IGNORECASE), "Django"),
    (re.compile(r"flask", re.IGNORECASE), "Flask"),
    (re.compile(r"nextjs|next\.config", re.IGNORECASE), "Next.js"),
    (re.compile(r"react", re.IGNORECASE), "React"),
    (re.compile(r"pytest", re.IGNORECASE), "Pytest"),
    (re.compile(r"qdrant", re.IGNORECASE), "Qdrant (Vector Store)"),
    (re.compile(r"langchain|llamaindex|llama.index", re.IGNORECASE), "LlamaIndex / LangChain"),
    (re.compile(r"sqlalchemy|alembic", re.IGNORECASE), "SQLAlchemy / Alembic"),
    (re.compile(r"pydantic", re.IGNORECASE), "Pydantic"),
    (re.compile(r"celery", re.IGNORECASE), "Celery"),
    (re.compile(r"redis", re.IGNORECASE), "Redis"),
    (re.compile(r"postgres|postgresql", re.IGNORECASE), "PostgreSQL"),
    (re.compile(r"mongodb|motor", re.IGNORECASE), "MongoDB"),
    (re.compile(r"torch|pytorch", re.IGNORECASE), "PyTorch"),
    (re.compile(r"tensorflow|keras", re.IGNORECASE), "TensorFlow / Keras"),
    (re.compile(r"transformers|huggingface", re.IGNORECASE), "Hugging Face Transformers"),
]

_IGNORED_DIRS: Set[str] = {
    "node_modules", ".git", "__pycache__", "build", "dist",
    ".venv", "venv", ".mypy_cache", ".pytest_cache", ".tox",
}


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

class ImportantFileGroups(BaseModel):
    auth: List[str] = Field(default_factory=list)
    database: List[str] = Field(default_factory=list)
    api: List[str] = Field(default_factory=list)
    ml: List[str] = Field(default_factory=list)
    config: List[str] = Field(default_factory=list)


class RepositorySummary(BaseModel):
    repo_name: str
    what_it_does: str
    major_modules: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    entry_files: List[str] = Field(default_factory=list)
    important_files: ImportantFileGroups = Field(default_factory=ImportantFileGroups)
    needs_review: List[str] = Field(default_factory=list)
    architecture_notes: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def _walk(repo_path: Path):
    """Yield relative path strings for every non-ignored file under repo_path."""
    for root, dirs, files in os.walk(str(repo_path)):
        dirs[:] = [d for d in dirs if d not in _IGNORED_DIRS and not d.startswith(".")]
        rel_root = Path(root).relative_to(repo_path)
        for f in files:
            yield str(rel_root / f)


def _scan_filesystem(repo_path: Path) -> Dict[str, Any]:
    """
    Walk repo_path and classify files into structured buckets.
    Returns a rich dict consumed by generate_repository_summary.
    """
    languages: Set[str] = set()
    modules: Set[str] = set()
    entry_files: List[str] = []
    tech_hints: Set[str] = set()
    important: Dict[str, List[str]] = {
        "auth": [], "database": [], "api": [], "ml": [], "config": [],
    }
    needs_review: List[str] = []
    all_files: List[str] = []

    for rel in _walk(repo_path):
        all_files.append(rel)
        rel_path = Path(rel)
        parts = rel_path.parts

        # Top-level module
        if len(parts) >= 2:
            modules.add(parts[0])

        # Language from extension
        ext = rel_path.suffix.lower()
        lang = _EXT_LANG.get(ext)
        if lang:
            languages.add(lang)

        # Entry point
        if _ENTRY_RE.search(rel):
            entry_files.append(rel)

        # Technology fingerprints (filename / path level)
        for pattern, tech in _TECH_FINGERPRINTS:
            if pattern.search(rel):
                tech_hints.add(tech)

        # Classification into important_files groups
        if _AUTH_RE.search(rel):
            important["auth"].append(rel)
        if _DATABASE_RE.search(rel):
            important["database"].append(rel)
        if _API_RE.search(rel):
            important["api"].append(rel)
        if _ML_RE.search(rel):
            important["ml"].append(rel)
        if _CONFIG_RE.search(rel_path.name) or _CONFIG_RE.search(rel):
            important["config"].append(rel)

        # Needs-review candidates
        if _REVIEW_FILES_RE.search(rel):
            needs_review.append(rel)

    # Scan file *contents* for TODO/FIXME markers (top 200 lines only, lightweight)
    _scan_for_review_markers(repo_path, all_files, needs_review)

    return {
        "languages": languages,
        "modules": modules,
        "entry_files": entry_files,
        "tech_hints": tech_hints,
        "important": important,
        "needs_review": needs_review,
        "all_files": all_files,
    }


def _scan_for_review_markers(repo_path: Path, all_files: List[str], bucket: List[str]):
    """Scan first 200 lines of text files for TODO/FIXME markers."""
    already = set(bucket)
    for rel in all_files:
        if rel in already:
            continue
        fp = repo_path / rel
        if fp.suffix.lower() not in {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".md"}:
            continue
        try:
            with fp.open("r", encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh):
                    if i > 200:
                        break
                    if _REVIEW_RE.search(line):
                        bucket.append(rel)
                        break
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Semantic retrieval helpers
# ---------------------------------------------------------------------------

def _retrieve_bulk(repo_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """Fire multiple semantic queries and return bucketed chunk lists."""
    retriever = RepositoryRetriever()
    queries = {
        "what_it_does": "what does this project do main purpose overview",
        "entry":        "main application entry point start server",
        "config":       "configuration settings environment variables",
        "database":     "database model connection migration",
        "auth":         "authentication login security token",
        "api":          "API route endpoint controller",
        "ml":           "machine learning AI embedding model training",
        "tech":         "framework library dependencies technology stack",
    }
    result: Dict[str, List[Dict[str, Any]]] = {}
    seen: Set = set()
    for key, q in queries.items():
        chunks = retriever.retrieve(query=q, repo_name=repo_name, top_k=4)
        deduped = []
        for c in chunks:
            cid = c.get("chunk_id", hash(c.get("content", "")))
            if cid not in seen:
                seen.add(cid)
                deduped.append(c)
        result[key] = deduped
    return result


def _enrich_tech_from_chunks(
    chunks: List[Dict[str, Any]], tech_hints: Set[str]
) -> None:
    """Scan chunk text for technology fingerprints."""
    for c in chunks:
        text = c.get("content", "")
        for pattern, tech in _TECH_FINGERPRINTS:
            if pattern.search(text):
                tech_hints.add(tech)


# ---------------------------------------------------------------------------
# Optional LLM enrichment
# ---------------------------------------------------------------------------

def _try_llm(chunks: List[Dict[str, Any]], question: str) -> Optional[str]:
    """Try LLM completion; return None silently for mock / failures."""
    if not chunks:
        return None
    context = "\n\n".join(
        f"File: {c.get('file_path', '?')}\n{c.get('content', '')[:500]}"
        for c in chunks[:6]
    )
    prompt = (
        "You are an expert software engineer generating a brief technical summary of a repository. "
        "Using ONLY the code context below, output a highly concise, 2-3 sentence overview of what the project does. "
        "Avoid generic fluff (e.g. 'This project is a...'). Focus on the domain, stack, and primary purpose.\n\n"
        f"Question: {question}\n\nContext:\n{context}\n\nAnswer:"
    )
    try:
        from repomind.core.di import get_global_injector
        from repomind.models.llm.llm_component import LLMComponent

        llm = get_global_injector().get(LLMComponent).get_llm()
        response = str(llm.complete(prompt)).strip()
        if "You are a senior software engineer" in response or len(response) > 3000:
            return None  # mock echo
        return response or None
    except Exception as e:
        logger.debug("LLM enrichment skipped: %s", e)
        return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_repository_summary(
    repo_name: str,
    repo_path: Optional[str] = None,
) -> dict:
    """
    Generate a developer onboarding summary for an indexed repository.

    Args:
        repo_name:  Name used when the repository was indexed (Qdrant filter key).
        repo_path:  Optional path to the local repository root. When provided,
                    a full filesystem walk is performed for richer analysis.

    Returns:
        dict matching the :class:`RepositorySummary` schema.
    """
    logger.info("Generating repository summary for '%s'", repo_name)

    # ------------------------------------------------------------------
    # Phase 1: Filesystem scan
    # ------------------------------------------------------------------
    fs: Dict[str, Any] = {
        "languages": set(), "modules": set(), "entry_files": [],
        "tech_hints": set(), "important": {
            "auth": [], "database": [], "api": [], "ml": [], "config": [],
        },
        "needs_review": [], "all_files": [],
    }

    if repo_path:
        rp = Path(repo_path)
        if rp.exists() and rp.is_dir():
            logger.info("Running filesystem scan of '%s'", repo_path)
            fs = _scan_filesystem(rp)

    # ------------------------------------------------------------------
    # Phase 2: Semantic retrieval
    # ------------------------------------------------------------------
    query_chunks = _retrieve_bulk(repo_name)

    # Collect all unique chunks for language/tech enrichment
    all_chunks: List[Dict[str, Any]] = [
        c for bucket in query_chunks.values() for c in bucket
    ]

    # Supplement language detection from chunk metadata
    for c in all_chunks:
        lang = c.get("language", "")
        if lang and lang.lower() not in ("unknown", "text", ""):
            fs["languages"].add(lang.capitalize())

    # Supplement module detection from chunk file paths
    for c in all_chunks:
        fp = c.get("file_path", "")
        if fp:
            parts = Path(fp).parts
            if len(parts) >= 2:
                fs["modules"].add(parts[0])

    # Supplement tech hints from chunk content
    _enrich_tech_from_chunks(all_chunks, fs["tech_hints"])

    # Supplement important files from chunk metadata
    for c in all_chunks:
        fp = c.get("file_path", "")
        if not fp:
            continue
        if _AUTH_RE.search(fp) and fp not in fs["important"]["auth"]:
            fs["important"]["auth"].append(fp)
        if _DATABASE_RE.search(fp) and fp not in fs["important"]["database"]:
            fs["important"]["database"].append(fp)
        if _API_RE.search(fp) and fp not in fs["important"]["api"]:
            fs["important"]["api"].append(fp)
        if _ML_RE.search(fp) and fp not in fs["important"]["ml"]:
            fs["important"]["ml"].append(fp)

    # ------------------------------------------------------------------
    # Phase 3: "what_it_does" — LLM first, heuristic fallback
    # ------------------------------------------------------------------
    what_it_does = _try_llm(
        query_chunks.get("what_it_does", []) + query_chunks.get("entry", []),
        "What does this project do? Describe its main purpose and architecture briefly.",
    )

    if not what_it_does:
        langs = ", ".join(sorted(fs["languages"])) or "unknown"
        mods  = ", ".join(sorted(fs["modules"]))  or "undetermined"
        file_count = len(fs["all_files"]) or len(set(
            c.get("file_path", "") for c in all_chunks if c.get("file_path")
        ))
        what_it_does = (
            f"This repository ('{repo_name}') appears to be a {langs} project "
            f"with {len(fs['modules'])} top-level module(s): {mods}. "
            f"Analysed {file_count} file(s) across {len(all_chunks)} indexed chunks."
        )

    # ------------------------------------------------------------------
    # Phase 4: Architecture notes
    # ------------------------------------------------------------------
    arch_notes: List[str] = []

    if fs["entry_files"]:
        arch_notes.append(
            f"Entry point(s) detected: {', '.join(fs['entry_files'][:5])}"
        )
    if fs["important"]["database"]:
        arch_notes.append("Database layer present — check models/migrations for schema details.")
    if fs["important"]["auth"]:
        arch_notes.append("Authentication layer detected — review token and session handling.")
    if fs["important"]["api"]:
        arch_notes.append("API routing files found — explore routes for endpoint definitions.")
    if fs["important"]["ml"]:
        arch_notes.append("ML/AI components detected — review embedding and inference pipelines.")
    if fs["needs_review"]:
        arch_notes.append(
            f"{len(fs['needs_review'])} file(s) contain TODO/FIXME markers or are flagged for review."
        )

    llm_note = _try_llm(
        query_chunks.get("tech", []) + query_chunks.get("what_it_does", []),
        "What are the key architectural patterns or design decisions a new developer should know about?",
    )
    if llm_note:
        arch_notes.insert(0, llm_note)

    # ------------------------------------------------------------------
    # Phase 5: Tech stack — fingerprints + language labels
    # ------------------------------------------------------------------
    tech_stack = sorted(fs["tech_hints"])
    # Ensure detected languages appear in the tech stack if not already there
    for lang in sorted(fs["languages"]):
        if not any(lang.lower() in t.lower() for t in tech_stack):
            tech_stack.append(lang)

    # ------------------------------------------------------------------
    # Assemble and return
    # ------------------------------------------------------------------
    summary = RepositorySummary(
        repo_name=repo_name,
        what_it_does=what_it_does,
        major_modules=sorted(fs["modules"]),
        tech_stack=tech_stack,
        entry_files=sorted(set(fs["entry_files"])),
        important_files=ImportantFileGroups(
            auth=sorted(set(fs["important"]["auth"])),
            database=sorted(set(fs["important"]["database"])),
            api=sorted(set(fs["important"]["api"])),
            ml=sorted(set(fs["important"]["ml"])),
            config=sorted(set(fs["important"]["config"])),
        ),
        needs_review=sorted(set(fs["needs_review"]))[:20],  # cap at 20 items
        architecture_notes=arch_notes,
    )

    logger.info("Repository summary complete for '%s'", repo_name)
    return summary.model_dump()
