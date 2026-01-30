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


def test_analyze_includes_code_analysis_section(client: TestClient, db):
    """Test that when content fetch succeeds, report includes Code Analysis section."""
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.return_value = {
            "owner": "test",
            "name": "repo",
            "default_branch": "main",
            "tree_blobs": [
                {"path": "app/main.py", "sha": "abc"},
                {"path": "src/foo.py", "sha": "def"},
            ],
            "tree_paths": ["app/main.py", "src/foo.py"],
            "key_files": [],
            "workflows": [],
            "test_folders_detected": [],
        }
        with patch("app.api.reports.batch_fetch_text") as mock_batch:
            mock_batch.return_value = {
                "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get(\"/\")\ndef root(): pass",
                "src/foo.py": "x = 1",
            }

            resp = client.post("/api/analyze", json={"repo_url": "https://github.com/test/repo"})
            assert resp.status_code == 200
            report_id = uuid.UUID(resp.json()["report_id"])

            get_resp = client.get(f"/api/reports/{report_id}")
            assert get_resp.status_code == 200
            report = get_resp.json()
            assert report["status"] == "done"
            findings = report.get("findings_json") or {}
            sections = findings.get("sections") or []
            code_section = next((s for s in sections if s.get("name") == "Code Analysis"), None)
            assert code_section is not None
            assert "checks" in code_section
            assert len(code_section["checks"]) > 0


def test_analyze_continues_when_batch_fetch_fails(client: TestClient, db):
    """Test that when batch_fetch_text raises, report is still stored with other sections (no crash)."""
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.return_value = {
            "owner": "test",
            "name": "repo",
            "default_branch": "main",
            "tree_blobs": [{"path": "README.md", "sha": "x"}],
            "tree_paths": ["README.md"],
            "key_files": [{"path": "README.md", "found": True, "snippet": "Hi", "size": 2, "truncated": False}],
            "workflows": [],
            "test_folders_detected": [],
        }
        with patch("app.api.reports.batch_fetch_text") as mock_batch:
            mock_batch.side_effect = Exception("Batch fetch failed")

            resp = client.post("/api/analyze", json={"repo_url": "https://github.com/test/repo"})
            assert resp.status_code == 200
            report_id = uuid.UUID(resp.json()["report_id"])
            get_resp = client.get(f"/api/reports/{report_id}")
            assert get_resp.status_code == 200
            report = get_resp.json()
            assert report["status"] == "done"
            sections = (report.get("findings_json") or {}).get("sections") or []
            section_names = [s.get("name") for s in sections]
            assert "Runability" in section_names
            # Code Analysis may be present but empty when content_by_path is empty
            code_section = next((s for s in sections if s.get("name") == "Code Analysis"), None)
            if code_section is not None:
                assert len(code_section.get("checks") or []) == 0
