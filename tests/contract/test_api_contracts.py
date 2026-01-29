"""Contract tests - validate API responses match expected schemas."""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path

# Add both backend and project root to path
project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))

from tests.contract.schemas import (
    AnalyzeResponseSchema,
    ReportResponseSchema,
    ReportListItemSchema,
    ErrorResponseSchema,
)


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_analyze_response_contract(client):
    """Test POST /api/analyze response matches schema."""
    with patch("app.api.reports.fetch_repo") as mock_fetch:
        mock_fetch.return_value = {
            "owner": "test",
            "name": "repo",
            "default_branch": "main",
            "key_files": [],
            "workflows": [],
            "test_folders_detected": [],
        }
        with patch("app.api.reports.check_analyze_rate_limit"):
            resp = client.post("/api/analyze", json={"repo_url": "https://github.com/test/repo"})
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Validate against schema
    schema = AnalyzeResponseSchema(**data)
    assert schema.report_id is not None
    # Verify it's a valid UUID
    uuid.UUID(schema.report_id)


def test_report_response_contract(client):
    """Test GET /api/reports/{id} response matches schema."""
    from app.models import Report
    from app.core.database import SessionLocal
    
    # Create a report
    db = SessionLocal()
    report = Report(
        repo_url="https://github.com/test/repo",
        repo_owner="test",
        repo_name="repo",
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
    
    # Validate against schema
    schema = ReportResponseSchema(**data)
    assert schema.id == str(report.id)
    assert schema.repo_url == "https://github.com/test/repo"
    assert schema.status == "done"
    assert schema.overall_score == 85
    assert schema.status in ("pending", "done", "failed")
    
    db.close()


def test_report_list_response_contract(client):
    """Test GET /api/reports response matches schema."""
    from app.models import Report
    from app.core.database import SessionLocal
    
    # Create reports
    db = SessionLocal()
    for i in range(3):
        report = Report(
            repo_url=f"https://github.com/test/repo{i}",
            status="done",
            overall_score=80 + i,
        )
        db.add(report)
    db.commit()
    
    resp = client.get("/api/reports?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    
    # Validate each item
    assert isinstance(data, list)
    schema = ReportListResponseSchema(data)
    for item in schema.root:
        assert item.id is not None
        assert item.repo_url is not None
    
    db.close()


def test_error_response_contract(client):
    """Test error responses match schema."""
    # Invalid UUID
    resp = client.get("/api/reports/not-a-uuid")
    assert resp.status_code == 422
    
    # Non-existent report
    fake_id = uuid.uuid4()
    resp = client.get(f"/api/reports/{fake_id}")
    assert resp.status_code == 404
    data = resp.json()
    
    # Validate error schema
    schema = ErrorResponseSchema(**data)
    assert "detail" in schema.dict()
    assert len(schema.detail) > 0


def test_report_status_enum_validation(client):
    """Test that status field only accepts valid enum values."""
    from app.models import Report
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    report = Report(
        repo_url="https://github.com/test/repo",
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    resp = client.get(f"/api/reports/{report.id}")
    data = resp.json()
    
    schema = ReportResponseSchema(**data)
    assert schema.status in ("pending", "done", "failed")
    
    db.close()


def test_report_score_bounds(client):
    """Test that overall_score is between 0 and 100."""
    from app.models import Report
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    report = Report(
        repo_url="https://github.com/test/repo",
        status="done",
        overall_score=50,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    resp = client.get(f"/api/reports/{report.id}")
    data = resp.json()
    
    schema = ReportResponseSchema(**data)
    if schema.overall_score is not None:
        assert 0 <= schema.overall_score <= 100
    
    db.close()
