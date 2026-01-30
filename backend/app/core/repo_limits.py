"""Repo filtering and limits for code ingestion. No code execution."""

import os

MAX_FILES = 500
MAX_FILES_FETCH = 250  # cap for how many blobs to fetch content for
MAX_TOTAL_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_FILE_BYTES = 200_000  # 200 KB, align with github_client

SKIP_DIRS = frozenset({
    "node_modules",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".tox",
    "target",
    "vendor",
    "coverage",
    ".coverage",
    "htmlcov",
    ".eggs",
    ".idea",
    ".vscode",
})

SKIP_EXTS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".xz", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pyc", ".pyo", ".pyd",
    ".class", ".jar", ".war",
    ".db", ".sqlite", ".sqlite3",
    ".mp3", ".mp4", ".webm", ".mov", ".avi",
})

# Path suffixes for minified / source-map files
SKIP_MINIFIED_SUFFIXES = (".min.js", ".min.css", ".min.mjs", ".map")


def should_skip_path(path: str) -> bool:
    """True if path should be skipped (skip dirs, binary exts, minified)."""
    if not path or not path.strip():
        return True
    path = path.replace("\\", "/").strip("/")
    parts = path.lower().split("/")
    for part in parts:
        if part in SKIP_DIRS:
            return True
        if part.endswith(".egg-info") or part == ".egg-info":
            return True
    base = os.path.basename(path).lower()
    _, ext = os.path.splitext(base)
    if ext in SKIP_EXTS:
        return True
    if base.endswith(SKIP_MINIFIED_SUFFIXES):
        return True
    return False


def is_text_candidate(path: str) -> bool:
    """True if path is a candidate for text/code (not binary, not minified, not in skip dirs)."""
    return not should_skip_path(path)
