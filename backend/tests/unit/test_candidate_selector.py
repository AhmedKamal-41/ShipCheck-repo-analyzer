"""Unit tests for candidate_selector: priority buckets A-F, skip paths."""

from app.services.candidate_selector import select_candidates


def test_select_candidates_order_a_then_b_then_c():
    """Output order: docs (A), then CI (B), then manifests (C)."""
    blobs = [
        {"path": "package.json", "sha": "s1"},
        {"path": "README.md", "sha": "s2"},
        {"path": ".github/workflows/ci.yml", "sha": "s3"},
    ]
    out = select_candidates(blobs)
    paths = [b["path"] for b in out]
    assert paths.index("README.md") < paths.index(".github/workflows/ci.yml")
    assert paths.index(".github/workflows/ci.yml") < paths.index("package.json")


def test_select_candidates_skips_node_modules():
    """Paths under node_modules are excluded."""
    blobs = [
        {"path": "node_modules/foo/index.js", "sha": "s1"},
        {"path": "src/index.js", "sha": "s2"},
    ]
    out = select_candidates(blobs)
    paths = [b["path"] for b in out]
    assert "node_modules/foo/index.js" not in paths
    assert "src/index.js" in paths


def test_select_candidates_skips_minified():
    """Minified and .map files are excluded."""
    blobs = [
        {"path": "dist/bundle.min.js", "sha": "s1"},
        {"path": "src/main.js", "sha": "s2"},
    ]
    out = select_candidates(blobs)
    paths = [b["path"] for b in out]
    assert "dist/bundle.min.js" not in paths
    assert "src/main.js" in paths


def test_select_candidates_includes_docs_anywhere():
    """README and CONTRIBUTING anywhere are in bucket A."""
    blobs = [
        {"path": "docs/README.md", "sha": "s1"},
        {"path": "CONTRIBUTING.md", "sha": "s2"},
    ]
    out = select_candidates(blobs)
    paths = [b["path"] for b in out]
    assert "docs/README.md" in paths
    assert "CONTRIBUTING.md" in paths
