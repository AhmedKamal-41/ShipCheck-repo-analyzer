"""Integration tests for database CRUD operations."""

import uuid
from datetime import datetime

import pytest

from app.models import Report


def test_create_report(db):
    """Test creating a report in database."""
    report = Report(
        repo_url="https://github.com/test/repo",
        repo_owner="test",
        repo_name="repo",
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    assert report.id is not None
    assert report.repo_url == "https://github.com/test/repo"
    assert report.status == "pending"
    assert report.created_at is not None


def test_read_report(db):
    """Test reading a report from database."""
    report = Report(
        repo_url="https://github.com/test/repo",
        status="done",
        overall_score=85,
        findings_json={"sections": []},
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    found = db.query(Report).filter(Report.id == report.id).first()
    assert found is not None
    assert found.repo_url == "https://github.com/test/repo"
    assert found.overall_score == 85


def test_update_report(db):
    """Test updating a report in database."""
    report = Report(
        repo_url="https://github.com/test/repo",
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Update status
    report.status = "done"
    report.overall_score = 90
    db.commit()
    db.refresh(report)
    
    assert report.status == "done"
    assert report.overall_score == 90


def test_delete_report(db):
    """Test deleting a report from database."""
    report = Report(
        repo_url="https://github.com/test/repo",
        status="done",
    )
    db.add(report)
    db.commit()
    report_id = report.id
    
    db.delete(report)
    db.commit()
    
    found = db.query(Report).filter(Report.id == report_id).first()
    assert found is None


def test_report_timestamps(db):
    """Test that created_at and updated_at are set correctly."""
    report = Report(
        repo_url="https://github.com/test/repo",
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    assert report.created_at is not None
    assert report.updated_at is not None
    assert report.created_at == report.updated_at
    
    # Update and check updated_at changes
    original_updated = report.updated_at
    report.status = "done"
    db.commit()
    db.refresh(report)
    
    assert report.updated_at >= original_updated


def test_report_findings_json_storage(db):
    """Test that findings_json is stored correctly as JSONB."""
    findings = {
        "overall_score": 85,
        "sections": [
            {"name": "Runability", "checks": [], "score": 20},
        ],
        "interview_pack": ["Question 1", "Question 2"],
    }
    
    report = Report(
        repo_url="https://github.com/test/repo",
        status="done",
        overall_score=85,
        findings_json=findings,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    assert report.findings_json == findings
    assert report.findings_json["overall_score"] == 85
    assert len(report.findings_json["sections"]) == 1


def test_query_reports_by_status(db):
    """Test querying reports by status."""
    # Clean up any existing reports first
    db.query(Report).delete()
    db.commit()
    
    # Create reports with different statuses
    for status in ["pending", "done", "failed"]:
        report = Report(
            repo_url=f"https://github.com/test/repo-{status}",
            status=status,
        )
        db.add(report)
    db.commit()
    
    # Query pending reports
    pending = db.query(Report).filter(Report.status == "pending").all()
    assert len(pending) == 1
    assert pending[0].status == "pending"
    
    # Query done reports
    done = db.query(Report).filter(Report.status == "done").all()
    assert len(done) == 1
    assert done[0].status == "done"
