"""Integration tests for GET /api/reports endpoints."""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models import Report


def test_get_report_by_id(client: TestClient, db):
    """Test getting a report by ID."""
    # Create a report directly in DB
    report = Report(
        repo_url="https://github.com/test/repo",
        status="done",
        overall_score=85,
        findings_json={"sections": [], "overall_score": 85},
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    resp = client.get(f"/api/reports/{report.id}")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["id"] == str(report.id)
    assert data["repo_url"] == "https://github.com/test/repo"
    assert data["status"] == "done"
    assert data["overall_score"] == 85


def test_get_report_not_found(client: TestClient):
    """Test getting non-existent report returns 404."""
    fake_id = uuid.uuid4()
    resp = client.get(f"/api/reports/{fake_id}")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_get_report_invalid_uuid(client: TestClient):
    """Test getting report with invalid UUID format."""
    resp = client.get("/api/reports/not-a-uuid")
    assert resp.status_code == 422  # Validation error


def test_list_reports_default_limit(client: TestClient, db):
    """Test listing reports with default limit."""
    # Create multiple reports
    for i in range(5):
        report = Report(
            repo_url=f"https://github.com/test/repo{i}",
            status="done",
            overall_score=80 + i,
        )
        db.add(report)
    db.commit()
    
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    data = resp.json()
    
    assert isinstance(data, list)
    assert len(data) == 5
    assert all("id" in item and "repo_url" in item for item in data)


def test_list_reports_with_limit(client: TestClient, db):
    """Test listing reports with custom limit."""
    # Create 10 reports
    for i in range(10):
        report = Report(
            repo_url=f"https://github.com/test/repo{i}",
            status="done",
            overall_score=80,
        )
        db.add(report)
    db.commit()
    
    resp = client.get("/api/reports?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3


def test_list_reports_ordered_by_created_at(client: TestClient, db):
    """Test that reports are ordered by created_at descending."""
    # Create reports with different timestamps
    for i in range(3):
        report = Report(
            repo_url=f"https://github.com/test/repo{i}",
            status="done",
            overall_score=80,
        )
        db.add(report)
        db.flush()  # Get IDs assigned
    db.commit()
    
    resp = client.get("/api/reports?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    
    # Should be ordered newest first
    assert len(data) >= 3
    created_dates = [item.get("created_at") for item in data[:3] if item.get("created_at")]
    if len(created_dates) > 1:
        # Verify descending order (newest first)
        assert created_dates[0] >= created_dates[1]


def test_list_reports_limit_bounds(client: TestClient):
    """Test limit parameter bounds."""
    # Test limit too high
    resp = client.get("/api/reports?limit=200")
    assert resp.status_code == 422  # Should fail validation (max 100)

    # Test limit too low
    resp = client.get("/api/reports?limit=0")
    assert resp.status_code == 422  # Should fail validation (min 1)


def test_get_report_v2_returns_structured_recommendations(client: TestClient, db):
    """GET /api/reports/{id}?v=2 returns the structured shape; v=1 (default) returns flat strings."""
    structured_findings = {
        "overall_score": 80,
        "sections": [
            {
                "name": "Runability",
                "score": 10,
                "checks": [
                    {
                        "id": "runability_readme_install_run",
                        "name": "README install/run",
                        "status": "pass",
                        "evidence": {"file": "README.md", "snippet": "Install: ..."},
                        "recommendation": {
                            "what": "README contains install or run instructions.",
                            "where": "README.md",
                            "why": "Reviewers can clone and run quickly.",
                            "how": "Keep instructions current.",
                        },
                        "points": 10,
                    },
                ],
            },
        ],
        "interview_pack": [],
        "category_scores": {},
    }
    legacy_findings = {
        "overall_score": 80,
        "sections": [
            {
                "name": "Runability",
                "score": 10,
                "checks": [
                    {
                        "id": "runability_readme_install_run",
                        "name": "README install/run",
                        "status": "pass",
                        "evidence": {"file": "README.md", "snippet": "Install: ..."},
                        "recommendation": "README contains install or run instructions. Keep instructions current.",
                        "points": 10,
                    },
                ],
            },
        ],
        "interview_pack": [],
    }
    report = Report(
        repo_url="https://github.com/test/repo",
        status="done",
        overall_score=80,
        findings_json=legacy_findings,
        findings_v2=structured_findings,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # v=1 (default): flat-string recommendation
    resp_v1 = client.get(f"/api/reports/{report.id}")
    assert resp_v1.status_code == 200
    rec_v1 = resp_v1.json()["findings_json"]["sections"][0]["checks"][0]["recommendation"]
    assert isinstance(rec_v1, str)
    assert "Keep instructions current" in rec_v1

    # v=2: structured recommendation dict
    resp_v2 = client.get(f"/api/reports/{report.id}?v=2")
    assert resp_v2.status_code == 200
    rec_v2 = resp_v2.json()["findings_json"]["sections"][0]["checks"][0]["recommendation"]
    assert isinstance(rec_v2, dict)
    assert set(rec_v2.keys()) == {"what", "where", "why", "how"}
    for key in ("what", "where", "why", "how"):
        assert rec_v2[key], f"{key} must be non-empty"


def test_get_report_v2_falls_back_to_legacy_when_v2_missing(client: TestClient, db):
    """A row written before this prompt has no findings_v2; v=2 should fall back to findings_json."""
    legacy_only = {
        "overall_score": 50,
        "sections": [],
        "interview_pack": [],
    }
    report = Report(
        repo_url="https://github.com/test/legacy",
        status="done",
        overall_score=50,
        findings_json=legacy_only,
        findings_v2=None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    resp = client.get(f"/api/reports/{report.id}?v=2")
    assert resp.status_code == 200
    # Falls back to findings_json since findings_v2 is None
    assert resp.json()["findings_json"] == legacy_only
