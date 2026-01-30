"""Shared fixtures for API tests."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATABASE_URL
from app.core.database import get_db
from app.main import app
from app.models import Base, Report

# Use SQLite in-memory for tests if TESTING is set
TESTING = os.getenv("TESTING", "0").lower() in ("1", "true", "yes")
if TESTING and "sqlite" not in DATABASE_URL.lower():
    # Override DATABASE_URL for tests to use SQLite
    test_db_url = "sqlite:///:memory:"
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
else:
    from app.core.database import engine, SessionLocal as TestSessionLocal


def _mock_fetch_result():
    return {
        "owner": "owner",
        "name": "repo",
        "default_branch": "main",
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }


def _load_github_fixture(name: str) -> dict:
    """Load a GitHub API fixture JSON file."""
    fixture_path = Path(__file__).parent / "fixtures" / "github" / f"{name}.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="function")
def db() -> Session:
    """Create a test database session."""
    if TESTING and "sqlite" not in DATABASE_URL.lower():
        # Create tables in SQLite test DB
        Base.metadata.create_all(bind=test_engine)
    
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        if TESTING and "sqlite" not in DATABASE_URL.lower():
            Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db: Session):
    """Create a test client with database override."""
    db.query(Report).delete()
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.api.reports.fetch_repo", return_value=_mock_fetch_result()):
        with patch("app.api.reports.batch_fetch_text", return_value={}):
            with patch("app.api.reports.check_analyze_rate_limit"):
                yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def github_fixture():
    """Fixture loader for GitHub API responses."""
    return _load_github_fixture
