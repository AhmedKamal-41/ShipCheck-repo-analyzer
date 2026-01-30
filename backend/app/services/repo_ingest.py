"""Code ingestion: list tree, filter, download blobs. Read-only, no code execution."""

from app.core.repo_limits import (
    MAX_FILES,
    MAX_TOTAL_BYTES,
    is_text_candidate,
    should_skip_path,
)
from app.services.github_client import (
    GitHubAPIError,
    GitHubRateLimitError,
    InvalidRepoUrlError,
    RepoNotFoundError,
    get_blob_text,
    get_default_branch,
    get_tree_recursive,
    parse_repo_url,
)

PREFER_PREFIXES = ("src/", "app/", "backend/", "api/", "pages/", "routers/", "services/")


def _prefer_score(path: str) -> int:
    """Higher = prefer when hitting limits. 0 = no preference."""
    path_n = path.replace("\\", "/").lower()
    for i, prefix in enumerate(PREFER_PREFIXES):
        if path_n.startswith(prefix) or f"/{prefix}" in path_n:
            return len(PREFER_PREFIXES) - i
    return 0


def ingest_repo(url: str) -> dict:
    """Ingest repo source files up to limits. Returns {files: {path: content}, stats: {...}}.
    Raises InvalidRepoUrlError, RepoNotFoundError, GitHubRateLimitError, GitHubAPIError on failure.
    """
    parsed = parse_repo_url(url)
    owner = parsed["owner"]
    repo = parsed["repo"]
    ref = parsed.get("ref")
    if not ref:
        ref = get_default_branch(owner, repo)

    tree = get_tree_recursive(owner, repo, ref)
    candidates: list[dict] = []
    for node in tree:
        path = node.get("path") or ""
        if not path or not is_text_candidate(path):
            continue
        sha = node.get("sha")
        if not sha:
            continue
        size = node.get("size")
        candidates.append({
            "path": path,
            "sha": sha,
            "size": size if size is not None else 0,
        })

    # Prefer src/app/backend/api/pages/routers/services
    candidates.sort(key=lambda n: (-_prefer_score(n["path"]), n["path"]))

    files: dict[str, str] = {}
    total_bytes = 0
    truncated = False

    for node in candidates:
        if len(files) >= MAX_FILES:
            truncated = True
            break
        if total_bytes >= MAX_TOTAL_BYTES:
            truncated = True
            break
        path = node["path"]
        sha = node["sha"]
        try:
            content = get_blob_text(owner, repo, sha)
        except Exception:
            continue
        content_bytes = len(content.encode("utf-8"))
        if total_bytes + content_bytes > MAX_TOTAL_BYTES:
            truncated = True
            # Optionally add truncated content; plan says partial results
            remaining = MAX_TOTAL_BYTES - total_bytes
            if remaining > 0 and content_bytes > remaining:
                content = content[:remaining]
                content_bytes = remaining
            total_bytes += content_bytes
            files[path] = content
            break
        total_bytes += content_bytes
        files[path] = content

    stats = {
        "total_files": len(files),
        "total_bytes": total_bytes,
        "truncated": truncated,
    }
    return {"files": files, "stats": stats}
