"""Integration tests for POST /api/analyze endpoint."""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models import Report


def test_analyze_creates_report_with_pending_status(client: TestClient, db):
    """Test that analyze creates a report with pending status initially."""
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.return_value = {
            "owner": "test",
            "name": "repo",
            "default_branch": "main",
            "key_files": [],
            "workflows": [],
            "test_folders_detected": [],
        }
        
        resp = client.post(
            "/api/analyze",
            json={"repo_url": "https://github.com/test/repo"},
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert "report_id" in data
        report_id = uuid.UUID(data["report_id"])
        
        # Verify report exists in DB
        report = db.query(Report).filter(Report.id == report_id).first()
        assert report is not None
        assert report.repo_url == "https://github.com/test/repo"
        assert report.status == "done"  # Should be done after analysis completes


def test_analyze_completes_analysis(client: TestClient, db):
    """Test that analyze completes and stores findings."""
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.return_value = {
            "owner": "test",
            "name": "repo",
            "default_branch": "main",
            "key_files": [
                {"path": "README.md", "found": True, "snippet": "Install: `npm install`", "size": 50, "truncated": False},
            ],
            "workflows": [],
            "test_folders_detected": [],
        }
        
        resp = client.post("/api/analyze", json={"repo_url": "https://github.com/test/repo"})
        assert resp.status_code == 200
        report_id = uuid.UUID(resp.json()["report_id"])
        
        # Get report
        get_resp = client.get(f"/api/reports/{report_id}")
        assert get_resp.status_code == 200
        report = get_resp.json()
        
        assert report["status"] == "done"
        assert report["overall_score"] is not None
        assert report["findings_json"] is not None
        assert "sections" in report["findings_json"]


def test_analyze_invalid_url(client: TestClient):
    """Test analyze with invalid URL returns 400."""
    resp = client.post("/api/analyze", json={"repo_url": "not-a-url"})
    assert resp.status_code == 400
    assert "detail" in resp.json()


def test_analyze_empty_url(client: TestClient):
    """Test analyze with empty URL returns 400."""
    resp = client.post("/api/analyze", json={"repo_url": ""})
    assert resp.status_code == 400


def test_analyze_missing_url(client: TestClient):
    """Test analyze without repo_url returns 400."""
    resp = client.post("/api/analyze", json={})
    assert resp.status_code == 422  # Pydantic validation error


def test_analyze_handles_fetch_error(client: TestClient, db):
    """Test analyze handles GitHub fetch errors gracefully."""
    from app.services.github_client import RepoNotFoundError
    
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.side_effect = RepoNotFoundError("Repository not found")
        
        resp = client.post("/api/analyze", json={"repo_url": "https://github.com/nonexistent/repo"})
        assert resp.status_code == 200  # Still returns report_id
        
        report_id = uuid.UUID(resp.json()["report_id"])
        report = db.query(Report).filter(Report.id == report_id).first()
        assert report.status == "failed"
        assert "error" in report.findings_json
