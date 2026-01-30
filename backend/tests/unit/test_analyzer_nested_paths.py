"""Unit tests for analyzer using full tree_paths (nested paths)."""

from app.services.analyzer import analyze


def test_analyze_docker_pass_with_nested_compose():
    """Repo with docker-compose.yml under infra/ -> Docker check PASS with actual path."""
    fetch = {
        "owner": "o",
        "name": "n",
        "default_branch": "main",
        "tree_blobs": [],
        "tree_paths": ["infra/docker-compose.yml", "src/main.py"],
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }
    content_by_path = {
        "infra/docker-compose.yml": "services:\n  app:\n    build: .",
    }
    result = analyze(fetch, content_by_path=content_by_path)
    run_section = next((s for s in result.sections if s.name == "Runability"), None)
    assert run_section is not None
    docker_check = next((c for c in run_section.checks if c.id == "runability_docker"), None)
    assert docker_check is not None
    assert docker_check.status == "pass"
    assert "infra/docker-compose.yml" in (docker_check.evidence.get("file") or "")


def test_analyze_docs_pass_with_nested_readme():
    """Repo with README under backend/ -> docs PASS with actual path."""
    fetch = {
        "owner": "o",
        "name": "n",
        "default_branch": "main",
        "tree_blobs": [],
        "tree_paths": ["backend/README.md", "backend/app.py"],
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }
    content_by_path = {
        "backend/README.md": "## Setup\nInstall: `pip install -r requirements.txt`. Run: `uvicorn app:app`.\n\n## Usage\nSee docs.",
    }
    result = analyze(fetch, content_by_path=content_by_path)
    doc_section = next((s for s in result.sections if s.name == "Documentation"), None)
    assert doc_section is not None
    length_check = next((c for c in doc_section.checks if "length" in c.id), None)
    assert length_check is not None
    assert "backend/README.md" in (length_check.evidence.get("file") or "")


def test_analyze_ci_pass_with_workflows_path():
    """Repo with workflows under .github/workflows -> CI PASS."""
    fetch = {
        "owner": "o",
        "name": "n",
        "default_branch": "main",
        "tree_blobs": [],
        "tree_paths": [".github/workflows/ci.yml", "src/foo.js"],
        "key_files": [],
        "workflows": [{"path": ".github/workflows/ci.yml", "snippet": "name: CI"}],
        "test_folders_detected": [],
    }
    content_by_path = {".github/workflows/ci.yml": "name: CI\non: push"}
    result = analyze(fetch, content_by_path=content_by_path)
    eng_section = next((s for s in result.sections if s.name == "Engineering Quality"), None)
    assert eng_section is not None
    ci_check = next((c for c in eng_section.checks if c.id == "engineering_ci"), None)
    assert ci_check is not None
    assert ci_check.status == "pass"


def test_analyze_lockfile_pass_with_nested_lockfile():
    """Repo with lockfile under frontend/ -> lockfile PASS with actual path."""
    fetch = {
        "owner": "o",
        "name": "n",
        "default_branch": "main",
        "tree_blobs": [],
        "tree_paths": ["frontend/package-lock.json", "frontend/package.json"],
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }
    content_by_path = {"frontend/package-lock.json": "{}", "frontend/package.json": "{}"}
    result = analyze(fetch, content_by_path=content_by_path)
    eng_section = next((s for s in result.sections if s.name == "Engineering Quality"), None)
    assert eng_section is not None
    pin_check = next((c for c in eng_section.checks if c.id == "engineering_pinning"), None)
    assert pin_check is not None
    assert pin_check.status == "pass"
    assert "frontend/package-lock.json" in (pin_check.evidence.get("file") or "")
