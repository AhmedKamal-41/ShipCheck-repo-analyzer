"""Shared fixtures for API tests."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.main import app
from app.models import Report


def _mock_fetch_result():
    return {
        "owner": "owner",
        "name": "repo",
        "default_branch": "main",
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session):
    db.query(Report).delete()
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.api.reports.fetch_repo", return_value=_mock_fetch_result()):
        with patch("app.api.reports.check_analyze_rate_limit"):
            yield TestClient(app)

    app.dependency_overrides.clear()
