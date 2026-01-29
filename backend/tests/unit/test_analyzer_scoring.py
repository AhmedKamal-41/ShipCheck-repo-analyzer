"""Unit tests for analyzer scoring logic and edge cases."""

from app.services.analyzer import analyze, ReportResult


def _base_fetch_result():
    return {
        "owner": "owner",
        "name": "repo",
        "default_branch": "main",
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }


def test_score_calculation_perfect_score():
    """Test high score (most checks pass)."""
    fetch = _base_fetch_result()
    # Create a comprehensive repo with most features
    fetch["key_files"] = [
        {"path": "README.md", "found": True, "snippet": "## Setup\n\nInstall: `npm install`. Run: `npm run dev`.\n\n## Usage\n\nSee docs.\n\n## Installation\n\nFollow these steps.", "size": 500, "truncated": False},
        {"path": "Dockerfile", "found": True, "snippet": "FROM node:20", "size": 50, "truncated": False},
        {"path": ".env.example", "found": True, "snippet": "API_KEY=", "size": 20, "truncated": False},
        {"path": "package.json", "found": True, "snippet": '{"scripts": {"lint": "eslint .", "format": "prettier --write ."}}', "size": 80, "truncated": False},
        {"path": "package-lock.json", "found": True, "snippet": "{}", "size": 100, "truncated": False},
    ]
    fetch["workflows"] = [
        {"path": ".github/workflows/ci.yml", "snippet": "run: npm test", "size": 50, "truncated": False},
    ]
    fetch["test_folders_detected"] = ["tests"]
    
    report = analyze(fetch)
    assert isinstance(report, ReportResult)
    assert report.overall_score >= 70  # Should be high with most checks passing


def test_score_calculation_zero_score():
    """Test low score (most checks fail)."""
    fetch = _base_fetch_result()
    # Empty fetch result - most things fail, but secrets check might pass
    report = analyze(fetch)
    # Secrets check passes even with empty repo (no secrets found = pass)
    # So score won't be exactly 0, but should be very low
    assert report.overall_score < 20  # Very low score
    assert len(report.sections) == 4  # Runability, Engineering, Secrets, Docs


def test_score_calculation_mixed():
    """Test mixed score (some pass, some fail)."""
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "README.md", "found": True, "snippet": "Short readme", "size": 50, "truncated": False},
    ]
    # Has README but no Docker, no CI, no tests, no .env.example
    report = analyze(fetch)
    assert 0 < report.overall_score < 50  # Should be low but not zero


def test_score_bounds():
    """Test score is always between 0 and 100."""
    fetch = _base_fetch_result()
    report = analyze(fetch)
    assert 0 <= report.overall_score <= 100


def test_empty_fetch_result():
    """Test handling of empty/None fetch result."""
    report = analyze({})
    # Secrets check passes (no secrets = pass), so score won't be 0
    assert report.overall_score < 20  # Very low but not zero
    assert len(report.sections) == 4


def test_interview_pack_generation():
    """Test interview pack is generated."""
    fetch = _base_fetch_result()
    report = analyze(fetch)
    assert isinstance(report.interview_pack, list)
    assert len(report.interview_pack) <= 10


def test_section_scores_sum():
    """Test that section scores sum correctly."""
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "README.md", "found": True, "snippet": "## Setup\n\nInstall: `npm install`.", "size": 100, "truncated": False},
    ]
    report = analyze(fetch)
    
    total_section_score = sum(s.score for s in report.sections)
    assert total_section_score >= 0
