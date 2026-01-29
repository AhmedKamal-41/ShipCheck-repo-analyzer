"""Unit tests for analyzer detection logic (README, CI, Docker, etc.)."""

from app.services.analyzer import analyze, ReportResult


def _get_check(report: ReportResult, section_name: str, check_id: str):
    """Helper to find a check by section and ID."""
    for s in report.sections:
        if s.name == section_name:
            for c in s.checks:
                if c.id == check_id:
                    return c
    return None


def _base_fetch_result():
    return {
        "owner": "owner",
        "name": "repo",
        "default_branch": "main",
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }


def test_detector_readme_missing():
    """Test README detection when missing."""
    fetch = _base_fetch_result()
    report = analyze(fetch)
    check = _get_check(report, "Runability", "runability_readme_install_run")
    assert check is not None
    assert check.status == "fail"


def test_detector_readme_with_install_hints():
    """Test README detection with install/run keywords."""
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "README.md", "found": True, "snippet": "## Setup\n\nInstall: `npm install`. Run: `npm run dev`.", "size": 100, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Runability", "runability_readme_install_run")
    assert check.status == "pass"


def test_detector_dockerfile_present():
    """Test Docker detection when Dockerfile exists."""
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "Dockerfile", "found": True, "snippet": "FROM node:20", "size": 50, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Runability", "runability_docker")
    assert check.status == "pass"


def test_detector_docker_compose_present():
    """Test Docker detection when docker-compose.yml exists."""
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "docker-compose.yml", "found": True, "snippet": "services:", "size": 50, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Runability", "runability_docker")
    assert check.status == "pass"


def test_detector_ci_workflow_present():
    """Test CI detection when workflow exists."""
    fetch = _base_fetch_result()
    fetch["workflows"] = [
        {"path": ".github/workflows/ci.yml", "snippet": "name: CI", "size": 50, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Engineering Quality", "engineering_ci")
    assert check.status == "pass"


def test_detector_tests_folder_present():
    """Test test detection when test folder exists."""
    fetch = _base_fetch_result()
    fetch["test_folders_detected"] = ["tests"]
    report = analyze(fetch)
    check = _get_check(report, "Engineering Quality", "engineering_tests")
    assert check.status == "pass"


def test_detector_tests_in_workflow():
    """Test test detection when tests mentioned in CI workflow."""
    fetch = _base_fetch_result()
    fetch["workflows"] = [
        {"path": ".github/workflows/ci.yml", "snippet": "run: npm test", "size": 50, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Engineering Quality", "engineering_tests")
    assert check.status == "warn"  # Tests in CI but no folder


def test_detector_env_example_present():
    """Test .env.example detection."""
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": ".env.example", "found": True, "snippet": "API_KEY=", "size": 20, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Secrets Safety", "secrets_env_example")
    assert check.status == "pass"


def test_detector_lint_in_package_json():
    """Test lint detection in package.json scripts."""
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "package.json", "found": True, "snippet": '{"scripts": {"lint": "eslint ."}}', "size": 50, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Engineering Quality", "engineering_lint_format")
    assert check.status == "pass"


def test_detector_large_file_skipped():
    """Test that files >200KB are skipped."""
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "README.md", "found": True, "skipped": True, "reason": "exceeds 200KB", "size": 250000},
    ]
    report = analyze(fetch)
    # When README is skipped, analyzer treats it as missing (no snippet)
    # This results in a "warn" status (README exists but no install hints)
    check = _get_check(report, "Runability", "runability_readme_install_run")
    # The analyzer logic: if README exists but no install hints, it's "warn"
    assert check.status in ("fail", "warn")  # Either is acceptable for skipped file
