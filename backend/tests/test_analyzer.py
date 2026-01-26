"""Unit tests for app.services.analyzer."""

from app.services.analyzer import (
    ReportResult,
    analyze,
)


def _get_check(report: ReportResult, section_name: str, check_id: str):
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


def test_runability_readme_install_run_pass():
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "README.md", "found": True, "snippet": "## Setup\n\nInstall deps. Then `npm run dev` to run.", "size": 100, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Runability", "runability_readme_install_run")
    assert check is not None
    assert check.status == "pass"
    assert "README.md" in check.evidence.get("file", "")
    assert "install" in check.evidence.get("snippet", "").lower() or "npm run" in check.evidence.get("snippet", "").lower()


def test_runability_dockerfile_pass():
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": "Dockerfile", "found": True, "snippet": "FROM node:20\nWORKDIR /app", "size": 50, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Runability", "runability_docker")
    assert check is not None
    assert check.status == "pass"
    assert check.evidence.get("file") == "Dockerfile"


def test_engineering_tests_present_pass():
    fetch = _base_fetch_result()
    fetch["test_folders_detected"] = ["tests"]
    report = analyze(fetch)
    check = _get_check(report, "Engineering Quality", "engineering_tests")
    assert check is not None
    assert check.status == "pass"
    assert "tests" in check.evidence.get("file", "")


def test_engineering_ci_pass():
    fetch = _base_fetch_result()
    fetch["workflows"] = [
        {"path": ".github/workflows/ci.yml", "snippet": "run: build", "size": 100, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Engineering Quality", "engineering_ci")
    assert check is not None
    assert check.status == "pass"
    assert "workflows" in check.evidence.get("file", "")


def test_secrets_env_example_pass():
    fetch = _base_fetch_result()
    fetch["key_files"] = [
        {"path": ".env.example", "found": True, "snippet": "API_KEY=\nDB_URL=", "size": 30, "truncated": False},
    ]
    report = analyze(fetch)
    check = _get_check(report, "Secrets Safety", "secrets_env_example")
    assert check is not None
    assert check.status == "pass"
    assert ".env.example" in check.evidence.get("file", "")
