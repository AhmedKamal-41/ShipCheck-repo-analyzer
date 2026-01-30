"""Prioritized blob selection for content fetch. No code execution."""

import fnmatch
import os
from typing import Any

from app.core.repo_limits import is_text_candidate, should_skip_path

# Priority buckets: A (docs/config) -> B (CI) -> C (manifests) -> D (entry) -> E (security) -> F (code)
MAX_BUCKET_F = 150  # cap bucket F so A-E get room

DOC_PATTERNS = ("README*", "CONTRIBUTING*", "SECURITY*", "CHANGELOG*", "LICENSE*")
MANIFEST_NAMES = frozenset({
    "package.json", "pyproject.toml", "Pipfile", "poetry.lock",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Pipfile.lock",
})
MANIFEST_PREFIXES = ("requirements", "requirements-")
ENTRY_NAMES = ("main.py", "app.py", "server.py", "server.js", "server.ts", "index.js", "index.ts", "index.tsx")
ENTRY_PATH_PREFIXES = ("app/", "src/", "api/", "routes/", "routers/", "backend/", "services/")
CODE_PREFIXES = ("src/", "app/", "backend/", "api/", "services/", "routes/", "routers/")


def _path_matches_doc(path: str) -> bool:
    base = os.path.basename(path).upper()
    for pat in DOC_PATTERNS:
        if fnmatch.fnmatch(base, pat.upper()):
            return True
    return False


def _path_matches_manifest(path: str) -> bool:
    base = os.path.basename(path).lower()
    if base in {x.lower() for x in MANIFEST_NAMES}:
        return True
    if base.endswith(".txt") and any(base.startswith(p) for p in MANIFEST_PREFIXES):
        return True
    return False


def _path_matches_entry(path: str) -> bool:
    path_n = path.replace("\\", "/").lower()
    base = os.path.basename(path_n).lower()
    if base in {x.lower() for x in ENTRY_NAMES}:
        return True
    for prefix in ENTRY_PATH_PREFIXES:
        if path_n.startswith(prefix) and "/" in path_n:
            return True
    return False


def _path_matches_security(path: str) -> bool:
    base = os.path.basename(path).lower()
    if base.startswith(".env") or base == ".env":
        return True
    if base.startswith("config.") and is_text_candidate(path):
        return True
    return False


def _bucket(path: str) -> int:
    """Return bucket 0=A, 1=B, 2=C, 3=D, 4=E, 5=F, -1=skip."""
    path_n = path.replace("\\", "/")
    base = os.path.basename(path_n)
    if _path_matches_doc(path_n):
        return 0
    if path_n.startswith(".github/workflows/") and (path_n.endswith(".yml") or path_n.endswith(".yaml")):
        return 1
    if _path_matches_manifest(path_n):
        return 2
    if _path_matches_entry(path_n):
        return 3
    if _path_matches_security(path_n):
        return 4
    for prefix in CODE_PREFIXES:
        if path_n.startswith(prefix):
            return 5
    return -1


def select_candidates(tree_blobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return prioritized list of blobs to fetch. Order: A then B then C then D then E then F.
    Skips paths that should_skip_path. Caps bucket F at MAX_BUCKET_F.
    """
    buckets: list[list[dict[str, Any]]] = [[] for _ in range(6)]
    for b in tree_blobs:
        path = b.get("path") or ""
        if not path or should_skip_path(path) or not is_text_candidate(path):
            continue
        sha = b.get("sha")
        if not sha:
            continue
        bucket = _bucket(path)
        if bucket < 0:
            continue
        buckets[bucket].append(b)

    for lst in buckets:
        lst.sort(key=lambda x: (x.get("path") or ""))

    out: list[dict[str, Any]] = []
    for i in range(5):
        out.extend(buckets[i])
    f_list = buckets[5]
    if len(f_list) > MAX_BUCKET_F:
        f_list = f_list[:MAX_BUCKET_F]
    out.extend(f_list)
    return out
