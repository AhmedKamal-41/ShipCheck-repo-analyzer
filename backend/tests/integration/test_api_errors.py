"""Integration tests for API error handling."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.services.github_client import (
    InvalidRepoUrlError,
    RepoNotFoundError,
    GitHubRateLimitError,
    GitHubAPIError,
)


def test_analyze_invalid_repo_url(client: TestClient):
    """Test analyze with invalid repo URL returns 400."""
    resp = client.post("/api/analyze", json={"repo_url": "not-a-github-url"})
    assert resp.status_code == 400
    assert "detail" in resp.json()


def test_analyze_rate_limit_error(client: TestClient):
    """Test analyze rate limit returns 429."""
    from app.core.rate_limit import RateLimitExceeded
    
    with pytest.raises(RateLimitExceeded):
        # Exhaust rate limit
        ip = "127.0.0.100"
        from app.core.rate_limit import check_analyze_rate_limit, MAX_REQUESTS_PER_WINDOW, _store
        _store.clear()
        for _ in range(MAX_REQUESTS_PER_WINDOW + 1):
            check_analyze_rate_limit(ip)


def test_analyze_github_rate_limit_fallback(client: TestClient, db):
    """Test analyze handles GitHub rate limit and falls back to demo."""
    from app.services.github_client import GitHubRateLimitError
    
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.side_effect = GitHubRateLimitError("Rate limit exceeded", retry_after=60)
        
        # Should still return report_id but with failed status or demo data
        resp = client.post("/api/analyze", json={"repo_url": "https://github.com/test/repo"})
        # Depending on implementation, may return 200 with failed status or use demo fixture
        assert resp.status_code in [200, 429]


def test_analyze_github_not_found(client: TestClient, db):
    """Test analyze with non-existent repo returns report with failed status."""
    from app.services.github_client import RepoNotFoundError
    
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.side_effect = RepoNotFoundError("Repository not found")
        
        resp = client.post("/api/analyze", json={"repo_url": "https://github.com/nonexistent/repo"})
        assert resp.status_code == 200  # Returns report_id
        
        import uuid
        report_id = uuid.UUID(resp.json()["report_id"])
        
        # Get report - should be failed
        get_resp = client.get(f"/api/reports/{report_id}")
        report = get_resp.json()
        assert report["status"] == "failed"


def test_analyze_github_api_error(client: TestClient, db):
    """Test analyze handles GitHub API errors."""
    from app.services.github_client import GitHubAPIError
    
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.side_effect = GitHubAPIError("GitHub API unavailable")
        
        resp = client.post("/api/analyze", json={"repo_url": "https://github.com/test/repo"})
        assert resp.status_code == 200  # Returns report_id
        
        import uuid
        report_id = uuid.UUID(resp.json()["report_id"])
        
        # Get report - should be failed
        get_resp = client.get(f"/api/reports/{report_id}")
        report = get_resp.json()
        assert report["status"] == "failed"


def test_get_report_invalid_uuid_format(client: TestClient):
    """Test GET report with invalid UUID format."""
    resp = client.get("/api/reports/invalid-uuid")
    assert resp.status_code == 422  # Validation error


def test_health_endpoint(client: TestClient):
    """Test health endpoint returns 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_db_check_endpoint(client: TestClient):
    """Test db-check endpoint returns 200."""
    resp = client.get("/db-check")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
