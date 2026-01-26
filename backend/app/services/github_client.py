import base64
import re
from typing import Any
from urllib.parse import urlparse

import requests

from app.core.config import GITHUB_TOKEN

API_BASE = "https://api.github.com"
MAX_FILE_BYTES = 200_000
SNIPPET_CHARS = 4096
TIMEOUT = 20

KEY_FILES_ROOT = [
    "README.md",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Dockerfile",
    "docker-compose.yml",
    "Makefile",
    ".env.example",
]

TEST_FOLDER_PREFIXES = ("tests/", "__tests__/", "src/test/", "src/tests/")


class InvalidRepoUrlError(ValueError):
    pass


class RepoNotFoundError(Exception):
    pass


class GitHubRateLimitError(Exception):
    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class GitHubAPIError(Exception):
    pass


def _parse_repo_url(url: str) -> tuple[str, str]:
    s = (url or "").strip()
    if not s:
        raise InvalidRepoUrlError("URL is required")
    parsed = urlparse(s)
    if parsed.scheme not in ("http", "https"):
        raise InvalidRepoUrlError("URL must use http or https")
    netloc = (parsed.netloc or "").lower()
    if netloc != "github.com":
        raise InvalidRepoUrlError("URL must point to github.com")
    path = (parsed.path or "").strip("/")
    path = re.sub(r"\.git$", "", path, flags=re.IGNORECASE)
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise InvalidRepoUrlError("URL must contain owner and repo name (e.g. github.com/owner/name)")
    owner, name = parts[0], parts[1]
    if not owner or not name:
        raise InvalidRepoUrlError("Invalid owner or repo name")
    return owner, name


def _session() -> requests.Session:
    sess = requests.Session()
    sess.headers["Accept"] = "application/vnd.github.v3+json"
    if GITHUB_TOKEN:
        sess.headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return sess


def _parse_retry_after(resp: requests.Response) -> int | None:
    retry = resp.headers.get("Retry-After")
    if not retry:
        return None
    try:
        return int(retry)
    except ValueError:
        return None


def _rate_limit_message(retry_after: int | None) -> str:
    if retry_after is not None:
        return f"GitHub API rate limit exceeded. Try again in {retry_after} seconds."
    return (
        "GitHub API rate limit exceeded. Try again later, or set GITHUB_TOKEN "
        "for higher limits."
    )


def _check_response(resp: requests.Response) -> None:
    if resp.status_code == 404:
        raise RepoNotFoundError("Repository not found")
    if resp.status_code == 429:
        retry_after = _parse_retry_after(resp)
        raise GitHubRateLimitError(
            _rate_limit_message(retry_after), retry_after=retry_after
        )
    if resp.status_code == 403:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining is not None and remaining.strip() == "0":
            retry_after = _parse_retry_after(resp)
            raise GitHubRateLimitError(
                _rate_limit_message(retry_after), retry_after=retry_after
            )
        try:
            body = resp.json()
            msg = body.get("message", "") or ""
        except Exception:
            msg = resp.text or ""
        if "rate limit" in msg.lower():
            retry_after = _parse_retry_after(resp)
            raise GitHubRateLimitError(
                _rate_limit_message(retry_after), retry_after=retry_after
            )
        raise GitHubAPIError(f"GitHub API error: {msg or 'Forbidden'}")
    if resp.status_code >= 500:
        raise GitHubAPIError("GitHub API is unavailable")
    resp.raise_for_status()


def fetch_repo(url: str) -> dict[str, Any]:
    owner, name = _parse_repo_url(url)
    sess = _session()

    try:
        return _fetch_repo_impl(sess, owner, name)
    except (
        InvalidRepoUrlError,
        RepoNotFoundError,
        GitHubRateLimitError,
        GitHubAPIError,
    ):
        raise
    except requests.RequestException as e:
        raise GitHubAPIError("GitHub API request failed") from e


def _fetch_repo_impl(sess: requests.Session, owner: str, name: str) -> dict[str, Any]:
    repo_url = f"{API_BASE}/repos/{owner}/{name}"
    r = sess.get(repo_url, timeout=TIMEOUT)
    _check_response(r)
    repo = r.json()
    default_branch = repo.get("default_branch")
    ref = default_branch or "HEAD"

    tree_url = f"{API_BASE}/repos/{owner}/{name}/git/trees/{ref}?recursive=1"
    r = sess.get(tree_url, timeout=TIMEOUT)
    _check_response(r)
    data = r.json()
    tree = data.get("tree") or []

    paths_set = {n["path"] for n in tree}
    workflows: list[str] = []
    for n in tree:
        p = n.get("path") or ""
        if p.startswith(".github/workflows/") and n.get("type") == "blob":
            if p.endswith(".yml") or p.endswith(".yaml"):
                workflows.append(p)
    workflows = workflows[:3]

    test_folders_detected: list[str] = []
    for prefix in TEST_FOLDER_PREFIXES:
        if any(p == prefix.rstrip("/") or p.startswith(prefix) for p in paths_set):
            test_folders_detected.append(prefix.rstrip("/"))

    key_files: list[dict[str, Any]] = []
    to_fetch: list[str] = []
    for f in KEY_FILES_ROOT:
        if f in paths_set:
            to_fetch.append(f)

    for path in to_fetch:
        contents_url = f"{API_BASE}/repos/{owner}/{name}/contents/{path}?ref={ref}"
        r = sess.get(contents_url, timeout=TIMEOUT)
        if r.status_code == 404:
            continue
        _check_response(r)
        obj = r.json()
        if isinstance(obj, list):
            continue
        size = obj.get("size") or 0
        if size > MAX_FILE_BYTES:
            key_files.append({
                "path": path,
                "found": True,
                "skipped": True,
                "reason": "exceeds 200KB",
                "size": size,
            })
            continue
        raw = obj.get("content")
        if not raw:
            key_files.append({"path": path, "found": True, "snippet": "", "size": size, "truncated": False})
            continue
        try:
            decoded = base64.b64decode(raw).decode("utf-8", errors="replace")
        except Exception:
            decoded = ""
        truncated = len(decoded) > SNIPPET_CHARS
        snippet = decoded[:SNIPPET_CHARS] if truncated else decoded
        key_files.append({
            "path": path,
            "found": True,
            "snippet": snippet,
            "size": size,
            "truncated": truncated,
        })

    workflow_entries: list[dict[str, Any]] = []
    for path in workflows:
        contents_url = f"{API_BASE}/repos/{owner}/{name}/contents/{path}?ref={ref}"
        r = sess.get(contents_url, timeout=TIMEOUT)
        if r.status_code == 404:
            continue
        _check_response(r)
        obj = r.json()
        if isinstance(obj, list):
            continue
        size = obj.get("size") or 0
        if size > MAX_FILE_BYTES:
            workflow_entries.append({
                "path": path,
                "found": True,
                "skipped": True,
                "reason": "exceeds 200KB",
                "size": size,
            })
            continue
        raw = obj.get("content")
        if not raw:
            workflow_entries.append({"path": path, "snippet": "", "size": size, "truncated": False})
            continue
        try:
            decoded = base64.b64decode(raw).decode("utf-8", errors="replace")
        except Exception:
            decoded = ""
        truncated = len(decoded) > SNIPPET_CHARS
        snippet = decoded[:SNIPPET_CHARS] if truncated else decoded
        workflow_entries.append({
            "path": path,
            "snippet": snippet,
            "size": size,
            "truncated": truncated,
        })

    return {
        "owner": owner,
        "name": name,
        "default_branch": default_branch,
        "key_files": key_files,
        "workflows": workflow_entries,
        "test_folders_detected": test_folders_detected,
    }
