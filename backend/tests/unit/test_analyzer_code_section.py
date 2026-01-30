"""Unit tests for analyzer Code Analysis section when ingested is provided."""

from app.services.analyzer import analyze


def test_analyze_with_ingested_adds_code_analysis_section():
    """When ingested has files, report includes Code Analysis section."""
    fetch = {
        "owner": "o",
        "name": "n",
        "default_branch": "main",
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }
    ingested = {
        "files": {
            "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get(\"/\")\ndef root(): pass",
        },
        "stats": {"truncated": False},
    }
    result = analyze(fetch, ingested=ingested)
    code_section = next((s for s in result.sections if s.name == "Code Analysis"), None)
    assert code_section is not None
    assert len(code_section.checks) > 0
    check_names = [c.name for c in code_section.checks]
    assert "Code analysis summary" in check_names or "Frameworks detected" in check_names


def test_analyze_without_ingested_no_code_analysis_section():
    """When ingested is None, no Code Analysis section."""
    fetch = {
        "owner": "o",
        "name": "n",
        "default_branch": "main",
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }
    result = analyze(fetch, ingested=None)
    code_section = next((s for s in result.sections if s.name == "Code Analysis"), None)
    assert code_section is None


def test_analyze_with_empty_ingested_no_code_analysis_section():
    """When ingested has no files, no Code Analysis section."""
    fetch = {
        "owner": "o",
        "name": "n",
        "default_branch": "main",
        "key_files": [],
        "workflows": [],
        "test_folders_detected": [],
    }
    ingested = {"files": {}, "stats": {}}
    result = analyze(fetch, ingested=ingested)
    code_section = next((s for s in result.sections if s.name == "Code Analysis"), None)
    assert code_section is None
