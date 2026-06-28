"""
repomind.analyzers.hotspot_finder
=================================
Identifies likely important or risky files in a repository based on heuristics.
"""
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from repomind.rag.retriever import RepositoryRetriever

logger = logging.getLogger(__name__)

# Heuristics Patterns
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|password|secret|token|credentials?|auth)[ \t]*[:=][ \t]*['\"][a-zA-Z0-9_\-]+['\"]"
)
_COMPLEXITY_MARKERS = re.compile(r"(?i)(TODO|FIXME|HACK|XXX)")
_CRITICAL_KEYWORDS = re.compile(r"(?i)(auth|config|db|database|api|security)")

# Extensions to check
_SOURCE_EXT = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".cs", ".go", ".rs", ".rb", ".php"}

def _scan_filesystem_for_hotspots(repo_path: Path) -> List[Dict[str, str]]:
    hotspots = []
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv", ".venv", "build", "dist"} and not d.startswith(".")]
        
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(repo_path).as_posix()
            
            # 1. Check size heuristic (e.g. > 1000 lines or > 100KB)
            try:
                size_bytes = file_path.stat().st_size
                if size_bytes > 200_000:  # > 200KB is usually a massive file or generated
                    if file_path.suffix in _SOURCE_EXT:
                        hotspots.append({
                            "file_path": rel_path,
                            "reason": f"Extremely large source file ({size_bytes//1024} KB). May be overly complex or generated.",
                            "priority": "medium"
                        })
            except Exception:
                pass
            
            # Scan text content for secrets / complexity
            if file_path.suffix in _SOURCE_EXT or file_path.name.endswith((".yaml", ".yml", ".json", ".toml", ".ini", ".env")):
                try:
                    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                        # 2. Check for hardcoded secrets
                        if _SECRET_RE.search(content):
                            hotspots.append({
                                "file_path": rel_path,
                                "reason": "Possible hardcoded secret, token, or password detected in plain text.",
                                "priority": "high"
                            })
                            
                        # 3. Check for complexity / technical debt markers
                        todos = len(_COMPLEXITY_MARKERS.findall(content))
                        if todos > 5:
                            hotspots.append({
                                "file_path": rel_path,
                                "reason": f"High density of technical debt markers ({todos} TODO/FIXME comments).",
                                "priority": "medium"
                            })
                            
                        # 4. Check for critical architectural keywords (if high density)
                        criticals = len(_CRITICAL_KEYWORDS.findall(content))
                        if criticals > 15:
                            hotspots.append({
                                "file_path": rel_path,
                                "reason": "High density of critical keywords (auth, db, config, api). Likely a central architectural component.",
                                "priority": "low"
                            })
                            
                except Exception:
                    pass
                
    return hotspots

def _scan_semantic_for_hotspots(repo_name: str) -> List[Dict[str, str]]:
    hotspots = []
    try:
        retriever = RepositoryRetriever()
        # Look for chunks with secrets or high security impact
        queries = ["hardcoded password secret token", "authentication authorization security middleware", "database connection pool schema"]
        
        seen = set()
        for query in queries:
            chunks = retriever.retrieve(query=query, repo_name=repo_name, top_k=5)
            for c in chunks:
                fp = c.get("file_path", "")
                if not fp or fp in seen:
                    continue
                    
                seen.add(fp)
                content = c.get("content", "")
                
                if _SECRET_RE.search(content):
                    hotspots.append({
                        "file_path": fp,
                        "reason": "Semantic search detected potential hardcoded credentials or critical security logic.",
                        "priority": "high"
                    })
                elif "auth" in query.lower():
                    hotspots.append({
                        "file_path": fp,
                        "reason": "Semantic search identified this as a core authentication or security module.",
                        "priority": "medium"
                    })
    except Exception as e:
        logger.warning(f"Semantic hotspot scan failed: {e}")
        
    return hotspots

def find_hotspots(repo_name: str, repo_path: str = None) -> List[Dict[str, str]]:
    """
    Find code hotspots in the repository based on heuristics and semantic search.
    """
    logger.info(f"Finding hotspots for repo '{repo_name}'")
    
    hotspots = []
    seen = set()
    
    # 1. Run filesystem scan if path provided
    if repo_path and Path(repo_path).exists():
        fs_hotspots = _scan_filesystem_for_hotspots(Path(repo_path))
        for h in fs_hotspots:
            key = f"{h['file_path']}-{h['reason']}"
            if key not in seen:
                seen.add(key)
                hotspots.append(h)
                
    # 2. Run semantic search
    sem_hotspots = _scan_semantic_for_hotspots(repo_name)
    for h in sem_hotspots:
        # Check if we already flagged this file as high priority to avoid spam
        key = f"{h['file_path']}-{h['reason']}"
        if key not in seen:
            seen.add(key)
            hotspots.append(h)
            
    # Sort by priority (high > medium > low)
    priority_map = {"high": 0, "medium": 1, "low": 2}
    hotspots.sort(key=lambda x: (priority_map.get(x.get("priority", "low"), 3), x.get("file_path", "")))
    
    return hotspots
