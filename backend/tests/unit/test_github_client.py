"""Unit tests for GitHub client URL parsing and error handling."""

import pytest
from unittest.mock import patch, Mock

from app.services.github_client import (
    InvalidRepoUrlError,
    RepoNotFoundError,
    GitHubRateLimitError,
    GitHubAPIError,
    _parse_repo_url,
    fetch_repo,
    parse_repo_url,
)


def test_parse_repo_url_valid():
    """Test valid GitHub URL parsing."""
    owner, name = _parse_repo_url("https://github.com/owner/repo")
    assert owner == "owner"
    assert name == "repo"


def test_parse_repo_url_with_git_suffix():
    """Test URL with .git suffix."""
    owner, name = _parse_repo_url("https://github.com/owner/repo.git")
    assert owner == "owner"
    assert name == "repo"


def test_parse_repo_url_with_trailing_slash():
    """Test URL with trailing slash."""
    owner, name = _parse_repo_url("https://github.com/owner/repo/")
    assert owner == "owner"
    assert name == "repo"


def test_parse_repo_url_empty():
    """Test empty URL raises error."""
    with pytest.raises(InvalidRepoUrlError, match="URL is required"):
        _parse_repo_url("")


def test_parse_repo_url_non_github():
    """Test non-GitHub URL raises error."""
    with pytest.raises(InvalidRepoUrlError, match="github.com"):
        _parse_repo_url("https://gitlab.com/owner/repo")


def test_parse_repo_url_no_scheme():
    """Test URL without http/https raises error."""
    with pytest.raises(InvalidRepoUrlError, match="http or https"):
        _parse_repo_url("github.com/owner/repo")


def test_parse_repo_url_incomplete():
    """Test URL without owner/repo raises error."""
    with pytest.raises(InvalidRepoUrlError):
        _parse_repo_url("https://github.com/owner")


def test_parse_repo_url_whitespace():
    """Test URL with whitespace is trimmed."""
    owner, name = _parse_repo_url("  https://github.com/owner/repo  ")
    assert owner == "owner"
    assert name == "repo"


def test_parse_repo_url_public_returns_dict():
    """Test public parse_repo_url returns dict with owner, repo, ref optional."""
    out = parse_repo_url("https://github.com/owner/repo")
    assert out["owner"] == "owner"
    assert out["repo"] == "repo"
    assert out.get("ref") is None


def test_parse_repo_url_with_tree_ref():
    """Test parse_repo_url extracts ref from .../tree/branch."""
    out = parse_repo_url("https://github.com/owner/repo/tree/main")
    assert out["owner"] == "owner"
    assert out["repo"] == "repo"
    assert out.get("ref") == "main"


def test_parse_repo_url_with_blob_ref():
    """Test parse_repo_url extracts ref from .../blob/branch/path."""
    out = parse_repo_url("https://github.com/owner/repo/blob/develop/src/foo.py")
    assert out["owner"] == "owner"
    assert out["repo"] == "repo"
    assert out.get("ref") == "develop"


@patch("app.services.github_client._fetch_repo_impl")
def test_fetch_repo_success(mock_fetch):
    """Test successful repo fetch."""
    mock_fetch.return_value = {
        "owner": "test",
        "name": "repo",
        "default_branch": "main",
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }
    result = fetch_repo("https://github.com/test/repo")
    assert result["owner"] == "test"
    assert result["name"] == "repo"


@patch("app.services.github_client._parse_repo_url")
def test_fetch_repo_invalid_url(mock_parse):
    """Test invalid URL raises error."""
    mock_parse.side_effect = InvalidRepoUrlError("Invalid URL")
    with pytest.raises(InvalidRepoUrlError):
        fetch_repo("invalid-url")


@patch("app.services.github_client._fetch_repo_impl")
def test_fetch_repo_not_found(mock_fetch):
    """Test 404 raises RepoNotFoundError."""
    mock_fetch.side_effect = RepoNotFoundError("Repository not found")
    with pytest.raises(RepoNotFoundError):
        fetch_repo("https://github.com/nonexistent/repo")


@patch("app.services.github_client._fetch_repo_impl")
def test_fetch_repo_rate_limit(mock_fetch):
    """Test rate limit raises GitHubRateLimitError."""
    mock_fetch.side_effect = GitHubRateLimitError("Rate limit exceeded", retry_after=60)
    with pytest.raises(GitHubRateLimitError) as exc_info:
        fetch_repo("https://github.com/test/repo")
    assert exc_info.value.retry_after == 60


@patch("app.services.github_client._fetch_repo_impl")
def test_fetch_repo_api_error(mock_fetch):
    """Test API error raises GitHubAPIError."""
    mock_fetch.side_effect = GitHubAPIError("API unavailable")
    with pytest.raises(GitHubAPIError):
        fetch_repo("https://github.com/test/repo")
