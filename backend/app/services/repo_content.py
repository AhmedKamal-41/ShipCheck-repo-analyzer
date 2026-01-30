"""Selective content fetch by blob SHA with caching. Read-only, no code execution."""

from typing import Any

from app.core.repo_limits import MAX_FILES_FETCH, MAX_TOTAL_BYTES, should_skip_path
from app.services.github_client import get_blob_text


def fetch_blob_text(owner: str, repo: str, sha: str) -> str:
    """Fetch blob by SHA, decode to text. Truncates to MAX_FILE_BYTES (in github_client)."""
    return get_blob_text(owner, repo, sha)


def batch_fetch_text(
    owner: str,
    repo: str,
    blobs: list[dict[str, Any]],
    max_files: int = MAX_FILES_FETCH,
    max_total_bytes: int = MAX_TOTAL_BYTES,
) -> dict[str, str]:
    """Fetch content for prioritized blobs until limits. Returns {path: decoded_text}.
    In-memory sha->text cache per request. Skips paths that should_skip_path.
    """
    cache: dict[str, str] = {}
    result: dict[str, str] = {}
    total_bytes = 0

    for b in blobs:
        if len(result) >= max_files or total_bytes >= max_total_bytes:
            break
        path = b.get("path") or ""
        if should_skip_path(path):
            continue
        sha = b.get("sha")
        if not sha:
            continue
        if sha in cache:
            text = cache[sha]
        else:
            try:
                text = get_blob_text(owner, repo, sha)
                cache[sha] = text
            except Exception:
                continue
        n = len(text.encode("utf-8"))
        if total_bytes + n > max_total_bytes:
            take = max_total_bytes - total_bytes
            if take > 0:
                text = text.encode("utf-8")[:take].decode("utf-8", errors="replace")
                n = len(text.encode("utf-8"))
            total_bytes += n
            result[path] = text
            break
        total_bytes += n
        result[path] = text

    return result
