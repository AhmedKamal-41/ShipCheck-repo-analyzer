"""Unit tests for the structured Recommendation shape and to_legacy_string()."""

from app.services.analyzer import Recommendation, analyze


def _representative_fetch():
    """A fetch_result that exercises pass, warn, and fail paths across all sections."""
    return {
        "owner": "o", "name": "r", "default_branch": "main",
        "key_files": [
            {"path": "README.md", "found": True,
             "snippet": "## Setup\n\nInstall: `npm install`. Run: `npm run dev`.\n\n## Usage" * 20,
             "size": 2000, "truncated": False},
            {"path": "Dockerfile", "found": True, "snippet": "FROM node:20", "size": 50, "truncated": False},
            {"path": "package.json", "found": True,
             "snippet": '{"scripts": {"lint": "eslint ."}}', "size": 80, "truncated": False},
        ],
        "workflows": [{"path": ".github/workflows/ci.yml", "snippet": "run: npm test", "size": 50, "truncated": False}],
        "test_folders_detected": ["tests"],
    }


def test_recommendation_to_legacy_string_is_what_plus_how():
    rec = Recommendation(
        what="X is broken.",
        where="path/to/file.py:12",
        why="X is on the request path so this affects every user.",
        how="Replace X with Y and re-run the test suite.",
    )
    legacy = rec.to_legacy_string()
    assert legacy == "X is broken. Replace X with Y and re-run the test suite."
    assert rec.what in legacy
    assert rec.how in legacy
    # The 'where' and 'why' deliberately don't appear in the legacy collapse
    assert rec.where not in legacy
    assert rec.why not in legacy


def test_every_check_recommendation_has_all_four_nonempty_fields():
    """Every CheckResult produced by analyze() carries a fully-populated Recommendation."""
    report = analyze(_representative_fetch())
    seen_ids: set[str] = set()
    for section in report.sections:
        for check in section.checks:
            seen_ids.add(check.id)
            rec = check.recommendation
            assert isinstance(rec, Recommendation), (
                f"check {check.id!r} has recommendation of type {type(rec).__name__}, expected Recommendation"
            )
            for field_name in ("what", "where", "why", "how"):
                value = getattr(rec, field_name)
                assert isinstance(value, str), f"{check.id}.{field_name} must be a string"
                assert value.strip(), f"{check.id}.{field_name} must be non-empty"
    # Sanity check that we actually exercised multiple checks (not silently empty)
    assert len(seen_ids) >= 8, f"expected to see many check ids, got {seen_ids}"


def test_pass_warn_fail_all_produce_structured_recommendations():
    """Run analyze on a poor-quality repo so several checks fail; verify they still emit Recommendation."""
    poor = {"owner": "o", "name": "r", "default_branch": "main",
            "key_files": [], "workflows": [], "test_folders_detected": []}
    report = analyze(poor)
    statuses_seen = set()
    for section in report.sections:
        for check in section.checks:
            statuses_seen.add(check.status)
            assert isinstance(check.recommendation, Recommendation)
            # Even for fail-status checks, the four fields are non-empty.
            assert check.recommendation.what
            assert check.recommendation.where
            assert check.recommendation.why
            assert check.recommendation.how
    assert "fail" in statuses_seen, "fixture should produce at least one fail-status check"
