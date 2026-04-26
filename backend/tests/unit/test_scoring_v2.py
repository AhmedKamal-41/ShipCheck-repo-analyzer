"""Unit tests for the categorical scoring system (severity x confidence x scope_factor)."""

import pytest

from app.services.analyzer import (
    CATEGORY_WEIGHTS,
    CHECK_CATEGORY,
    POINTS_FAIL,
    POINTS_PASS,
    SEV_HIGH,
    SEV_LOW,
    SEV_MEDIUM,
    AnalyzerError,
    CheckResult,
    analyze,
    compute_categorical_score,
    compute_scope_factor,
)


def _good_fetch():
    return {
        "owner": "o", "name": "r", "default_branch": "main",
        "key_files": [
            {"path": "README.md", "found": True,
             "snippet": "## Setup\n\nInstall: `npm install`. Run: `npm run dev`.\n\n## Usage\n\nDocs.\n\n## Installation\n\nSteps." * 5,
             "size": 2500, "truncated": False},
            {"path": "Dockerfile", "found": True, "snippet": "FROM node:20", "size": 50, "truncated": False},
            {"path": ".env.example", "found": True, "snippet": "API_KEY=", "size": 20, "truncated": False},
            {"path": "package.json", "found": True,
             "snippet": '{"scripts": {"lint": "eslint .", "format": "prettier --write ."}}', "size": 80, "truncated": False},
            {"path": "package-lock.json", "found": True, "snippet": "{}", "size": 100, "truncated": False},
        ],
        "workflows": [{"path": ".github/workflows/ci.yml", "snippet": "run: npm test", "size": 50, "truncated": False}],
        "test_folders_detected": ["tests"],
    }


def _poor_fetch():
    return {
        "owner": "o", "name": "r", "default_branch": "main",
        "key_files": [
            {"path": "README.md", "found": True, "snippet": "tiny", "size": 4, "truncated": False},
        ],
        "workflows": [],
        "test_folders_detected": [],
    }


def test_default_weighting_preserves_old_relative_ordering():
    """If repo A is clearly better than repo B, new math must agree."""
    a = analyze(_good_fetch())
    b = analyze(_poor_fetch())
    assert a.overall_score > b.overall_score


def test_severity_lowers_score():
    """A HIGH-severity FAIL drags the score lower than a LOW-severity FAIL."""
    high_fail = [
        CheckResult(id="x_high", name="x", status="fail", evidence={}, recommendation="",
                    points=POINTS_FAIL, severity=SEV_HIGH, category="Runability"),
        CheckResult(id="x_pass", name="y", status="pass", evidence={}, recommendation="",
                    points=POINTS_PASS, severity=SEV_HIGH, category="Runability"),
    ]
    low_fail = [
        CheckResult(id="x_low", name="x", status="fail", evidence={}, recommendation="",
                    points=POINTS_FAIL, severity=SEV_LOW, category="Runability"),
        CheckResult(id="x_pass", name="y", status="pass", evidence={}, recommendation="",
                    points=POINTS_PASS, severity=SEV_HIGH, category="Runability"),
    ]
    high_overall, _ = compute_categorical_score(high_fail)
    low_overall, _ = compute_categorical_score(low_fail)
    assert high_overall < low_overall


def test_scope_factor_linear_interp():
    assert compute_scope_factor(0) == 0.2
    assert compute_scope_factor(1) == 0.2
    assert compute_scope_factor(5) == pytest.approx(0.6, abs=0.05)
    assert compute_scope_factor(10) == 1.0
    assert compute_scope_factor(100) == 1.0


def test_category_weights_sum_to_one():
    total = sum(CATEGORY_WEIGHTS.values())
    assert total == pytest.approx(1.0, abs=1e-9)


def test_every_check_id_has_a_category():
    """Every check produced by analyze() resolves to a known category."""
    fetch = _good_fetch()
    report = analyze(fetch)
    for section in report.sections:
        for check in section.checks:
            in_map = check.id in CHECK_CATEGORY
            has_explicit = check.category and check.category != "__unset__"
            assert in_map or has_explicit, f"check {check.id!r} has no category route"


def test_empty_category_scores_100():
    """A category with no relevant checks scores 100 (neutral, no penalty)."""
    only_runability = [
        CheckResult(id="r1", name="x", status="pass", evidence={}, recommendation="",
                    points=POINTS_PASS, category="Runability"),
    ]
    overall, cats = compute_categorical_score(only_runability)
    for empty_cat in ("Testing & CI", "Security & Deps", "Maintainability", "Architecture", "Documentation"):
        assert cats[empty_cat] == 100
    assert cats["Runability"] == 100
    assert overall == 100


def test_overall_score_clamped():
    """Synthetic checks shouldn't be able to push overall outside [0, 100]."""
    all_fail = [
        CheckResult(id=f"f_{cat.replace(' ', '_')}", name="x", status="fail", evidence={}, recommendation="",
                    points=POINTS_FAIL, severity=SEV_HIGH, category=cat)
        for cat in CATEGORY_WEIGHTS
    ]
    overall_low, _ = compute_categorical_score(all_fail)
    assert 0 <= overall_low <= 100
    assert overall_low == 0

    all_pass = [
        CheckResult(id=f"p_{cat.replace(' ', '_')}", name="x", status="pass", evidence={}, recommendation="",
                    points=POINTS_PASS, severity=SEV_HIGH, category=cat)
        for cat in CATEGORY_WEIGHTS
    ]
    overall_high, _ = compute_categorical_score(all_pass)
    assert overall_high == 100


def test_unknown_check_raises():
    """A check with an id not in CHECK_CATEGORY and no explicit category raises AnalyzerError."""
    orphan = [
        CheckResult(id="not_a_real_id", name="x", status="pass", evidence={}, recommendation="",
                    points=POINTS_PASS),  # no category set, id not in map
    ]
    with pytest.raises(AnalyzerError):
        compute_categorical_score(orphan)
