"""Parameterized coverage tests for every (check_id, status) branch.

Each fixture is shaped to drive one specific check toward one specific
status (pass / warn / fail). For each parametrize row, we run analyze()
on the fixture and assert that:

- the named check appears with the expected status
- its recommendation has all four required fields populated
- severity / confidence / scope_factor are within valid ranges

This recovers the coverage drop from adding the structured-recommendation
code paths in every branch of every static check.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.analyzer import Recommendation, analyze


def _flatten_checks(report) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for section in report.sections:
        for check in section.checks:
            out[check.id] = check
    return out


def _readme(snippet: str) -> dict[str, Any]:
    return {"path": "README.md", "found": True, "snippet": snippet, "size": len(snippet), "truncated": False}


def _fetch_empty() -> dict[str, Any]:
    return {"owner": "o", "name": "r", "default_branch": "main",
            "key_files": [], "workflows": [], "test_folders_detected": []}


def _fetch_full_pass() -> dict[str, Any]:
    long_readme = "## Setup\n\nInstall: `npm install`. Run: `npm run dev`.\n\n## Usage\n\nDocs.\n\n## Installation" * 10
    return {
        "owner": "o", "name": "r", "default_branch": "main",
        "key_files": [
            _readme(long_readme),
            {"path": "Dockerfile", "found": True, "snippet": "FROM node:20", "size": 12, "truncated": False},
            {"path": ".env.example", "found": True, "snippet": "API_KEY=", "size": 8, "truncated": False},
            {"path": "package.json", "found": True,
             "snippet": '{"scripts": {"lint": "eslint ."}}', "size": 30, "truncated": False},
            {"path": "package-lock.json", "found": True, "snippet": "{}", "size": 2, "truncated": False},
        ],
        "workflows": [{"path": ".github/workflows/ci.yml", "snippet": "run: npm test", "size": 20, "truncated": False}],
        "test_folders_detected": ["tests"],
    }


def _fetch_readme_no_run_hint() -> dict[str, Any]:
    return {
        **_fetch_empty(),
        "key_files": [_readme("This is a project description with no setup commands but enough text. " * 10)],
    }


def _fetch_ci_only_no_tests() -> dict[str, Any]:
    return {
        "owner": "o", "name": "r", "default_branch": "main",
        "key_files": [],
        "workflows": [{"path": ".github/workflows/ci.yml", "snippet": "run: pytest tests/", "size": 20, "truncated": False}],
        "test_folders_detected": [],
    }


def _fetch_lint_warn_no_config() -> dict[str, Any]:
    return {
        **_fetch_empty(),
        "key_files": [{"path": "package.json", "found": True,
                       "snippet": '{"name": "x"}', "size": 10, "truncated": False}],
    }


def _fetch_pinning_warn_unpinned_reqs() -> dict[str, Any]:
    return {
        **_fetch_empty(),
        "key_files": [{"path": "requirements.txt", "found": True,
                       "snippet": "fastapi>=0.109\nrequests\n", "size": 30, "truncated": False}],
    }


def _fetch_secrets_possible() -> dict[str, Any]:
    return {
        **_fetch_empty(),
        "key_files": [{"path": "config.py", "found": True,
                       "snippet": 'api_key = "sk-1234567890abcdefghijabcdef"', "size": 40, "truncated": False}],
    }


def _fetch_docs_short_readme() -> dict[str, Any]:
    return {**_fetch_empty(), "key_files": [_readme("Tiny readme.")]}


def _fetch_readme_no_sections() -> dict[str, Any]:
    return {**_fetch_empty(), "key_files": [_readme("This project does X. " * 50)]}


# (check_id, expected_status, fixture_factory)
_PARAMS = [
    # Runability — README install/run
    ("runability_readme_install_run", "fail", _fetch_empty),
    ("runability_readme_install_run", "warn", _fetch_readme_no_run_hint),
    ("runability_readme_install_run", "pass", _fetch_full_pass),
    # Runability — Docker
    ("runability_docker", "fail", _fetch_empty),
    ("runability_docker", "pass", _fetch_full_pass),
    # Engineering — Tests
    ("engineering_tests", "fail", _fetch_empty),
    ("engineering_tests", "warn", _fetch_ci_only_no_tests),
    ("engineering_tests", "pass", _fetch_full_pass),
    # Engineering — CI
    ("engineering_ci", "fail", _fetch_empty),
    ("engineering_ci", "pass", _fetch_full_pass),
    # Engineering — Lint/format
    ("engineering_lint_format", "fail", _fetch_empty),
    ("engineering_lint_format", "warn", _fetch_lint_warn_no_config),
    ("engineering_lint_format", "pass", _fetch_full_pass),
    # Engineering — Pinning
    ("engineering_pinning", "fail", _fetch_empty),
    ("engineering_pinning", "warn", _fetch_pinning_warn_unpinned_reqs),
    ("engineering_pinning", "pass", _fetch_full_pass),
    # Secrets — env example
    ("secrets_env_example", "fail", _fetch_empty),
    ("secrets_env_example", "pass", _fetch_full_pass),
    # Secrets — possible secrets
    ("secrets_possible_secrets", "pass", _fetch_empty),
    ("secrets_possible_secrets", "warn", _fetch_secrets_possible),
    # Documentation — readme length
    ("documentation_readme_length", "fail", _fetch_empty),
    ("documentation_readme_length", "warn", _fetch_docs_short_readme),
    ("documentation_readme_length", "pass", _fetch_full_pass),
    # Documentation — readme sections
    ("documentation_readme_sections", "fail", _fetch_empty),
    ("documentation_readme_sections", "warn", _fetch_readme_no_sections),
    ("documentation_readme_sections", "pass", _fetch_full_pass),
]


@pytest.mark.parametrize("check_id,expected_status,fixture_factory", _PARAMS)
def test_check_branch_emits_structured_recommendation(check_id, expected_status, fixture_factory):
    """Every (check, status) row produces a fully-populated structured rec."""
    report = analyze(fixture_factory())
    checks = _flatten_checks(report)
    assert check_id in checks, f"check {check_id!r} not produced for fixture {fixture_factory.__name__}"
    check = checks[check_id]
    assert check.status == expected_status, (
        f"{check_id} on {fixture_factory.__name__}: expected {expected_status}, got {check.status}"
    )

    rec = check.recommendation
    assert isinstance(rec, Recommendation), (
        f"{check_id} returned {type(rec).__name__}, expected Recommendation"
    )
    for field in ("what", "where", "why", "how"):
        value = getattr(rec, field)
        assert isinstance(value, str) and value.strip(), (
            f"{check_id}.{field} must be a non-empty string"
        )

    assert 0.0 < check.severity <= 1.0
    assert 0.0 < check.confidence <= 1.0
    assert 0.2 <= check.scope_factor <= 1.0


def test_complexity_warn_branch_emits_structured_rec():
    """A high-complexity Python function fires the warn/fail branch of complexity_summary."""
    branchy = (
        "def big(x, y):\n"
        "    if x > 0:\n"
        "        if y > 0:\n"
        "            if x > y: return 1\n"
        "            return 2\n"
        "        elif y < 0: return 3\n"
        "        return 4\n"
        "    elif x < 0:\n"
        "        if y > 0: return 5\n"
        "        return 6\n"
        "    elif y > 0: return 7\n"
        "    elif y < 0: return 8\n"
        "    return 0\n"
    )
    fetch = _fetch_empty()
    content = {"app/big.py": branchy}
    report = analyze(fetch, content_by_path=content)
    checks = _flatten_checks(report)
    assert "complexity_summary" in checks
    rec = checks["complexity_summary"].recommendation
    assert isinstance(rec, Recommendation)
    assert rec.what and rec.where and rec.why and rec.how


def test_smells_dangerous_branch_emits_structured_rec():
    """An empty `except` block fires the smells_dangerous fail branch."""
    src = (
        "def f():\n"
        "    try:\n"
        "        do()\n"
        "    except Exception:\n"
        "        pass\n"
    )
    report = analyze(_fetch_empty(), content_by_path={"app/x.py": src})
    checks = _flatten_checks(report)
    assert "smells_dangerous" in checks
    assert checks["smells_dangerous"].status == "fail"
    rec = checks["smells_dangerous"].recommendation
    assert isinstance(rec, Recommendation)
    assert rec.how


def test_dependencies_missing_branch_emits_structured_rec():
    """An import that's not in requirements.txt fires the dependencies_missing fail branch."""
    content = {
        "requirements.txt": "fastapi==0.109.0\n",
        "app/main.py": "import requests\nimport fastapi\n",
    }
    report = analyze(_fetch_empty(), content_by_path=content)
    checks = _flatten_checks(report)
    assert "dependencies_missing" in checks
    assert checks["dependencies_missing"].status == "fail"
    rec = checks["dependencies_missing"].recommendation
    assert isinstance(rec, Recommendation)
    assert "requests" in rec.what or "missing" in rec.what.lower()


def test_architecture_circular_branch_emits_structured_rec():
    """A circular import triggers the architecture_circular fail branch."""
    content = {
        "pkg/__init__.py": "",
        "pkg/a.py": "from pkg import b\n",
        "pkg/b.py": "from pkg import a\n",
    }
    report = analyze(_fetch_empty(), content_by_path=content)
    checks = _flatten_checks(report)
    assert "architecture_circular" in checks
    assert checks["architecture_circular"].status == "fail"
    rec = checks["architecture_circular"].recommendation
    assert isinstance(rec, Recommendation)
    assert rec.where


def test_architecture_god_module_warn_branch_emits_structured_rec():
    """A module imported by >20 files triggers the architecture_god_modules warn branch."""
    content = {f"app/m{i}.py": "from app import shared\n" for i in range(25)}
    content["app/shared.py"] = "VALUE = 1\n"
    content["app/__init__.py"] = ""
    report = analyze(_fetch_empty(), content_by_path=content)
    checks = _flatten_checks(report)
    assert "architecture_god_modules" in checks
    assert checks["architecture_god_modules"].status == "warn"
    rec = checks["architecture_god_modules"].recommendation
    assert isinstance(rec, Recommendation)
    assert "shared" in rec.where or "shared" in rec.what


def test_complexity_any_types_warn_branch():
    """A TS file with several `: any` annotations triggers complexity_any_types warn."""
    ts_src = (
        "function f(x: any): any {\n"
        "  const y: any = x;\n"
        "  return y as any;\n"
        "}\n"
    )
    report = analyze(_fetch_empty(), content_by_path={"src/x.ts": ts_src})
    checks = _flatten_checks(report)
    assert "complexity_any_types" in checks
    assert checks["complexity_any_types"].status == "warn"
    rec = checks["complexity_any_types"].recommendation
    assert isinstance(rec, Recommendation)
    assert "any" in rec.what


def test_dependencies_unused_warn_branch():
    """A declared-but-not-imported package triggers dependencies_unused warn."""
    content = {
        "requirements.txt": "fastapi==0.109.0\nrich==13.0.0\n",
        "app/main.py": "import fastapi\n",
    }
    report = analyze(_fetch_empty(), content_by_path=content)
    checks = _flatten_checks(report)
    assert "dependencies_unused" in checks
    assert checks["dependencies_unused"].status == "warn"
    rec = checks["dependencies_unused"].recommendation
    assert isinstance(rec, Recommendation) and "rich" in rec.what


def test_architecture_orphan_modules_warn_branch():
    """Three orphan modules trigger the architecture_orphans warn branch."""
    content = {
        "app/__init__.py": "",
        "app/main.py": "",  # entrypoint
        "app/orphan1.py": "x = 1\n",
        "app/orphan2.py": "y = 2\n",
        "app/orphan3.py": "z = 3\n",
        "app/orphan4.py": "w = 4\n",
    }
    report = analyze(_fetch_empty(), content_by_path=content)
    checks = _flatten_checks(report)
    assert "architecture_orphans" in checks
    assert checks["architecture_orphans"].status == "warn"
