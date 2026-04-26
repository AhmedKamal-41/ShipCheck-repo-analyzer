"""Rules-based analyzer: fetch_result -> ReportResult (sections, checks, overall_score)."""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Literal

EVIDENCE_SNIPPET_MAX = 200
POINTS_PASS = 10
POINTS_WARN = 5
POINTS_FAIL = 0

SEV_LOW = 0.3
SEV_MEDIUM = 0.6
SEV_HIGH = 1.0

CATEGORY_WEIGHTS: dict[str, float] = {
    "Runability":      0.20,
    "Testing & CI":    0.20,
    "Security & Deps": 0.20,
    "Maintainability": 0.15,
    "Architecture":    0.15,
    "Documentation":   0.10,
}

CHECK_CATEGORY: dict[str, str] = {
    "runability_readme_install_run": "Runability",
    "runability_docker":             "Runability",
    "engineering_tests":             "Testing & CI",
    "engineering_ci":                "Testing & CI",
    "engineering_lint_format":       "Maintainability",
    "engineering_pinning":           "Security & Deps",
    "secrets_env_example":           "Security & Deps",
    "secrets_possible_secrets":      "Security & Deps",
    "documentation_readme_length":   "Documentation",
    "documentation_readme_sections": "Documentation",
    "code_summary":                  "Maintainability",
    "code_frameworks":               "Maintainability",
    "code_endpoints":                "Maintainability",
    "code_quality":                  "Maintainability",
    "code_security":                 "Security & Deps",
    "complexity_summary":            "Maintainability",
    "complexity_any_types":          "Maintainability",
    "smells_summary":                "Maintainability",
    "smells_dangerous":              "Maintainability",
    "dependencies_unused":           "Security & Deps",
    "dependencies_missing":          "Security & Deps",
    "architecture_circular":         "Architecture",
    "architecture_god_modules":      "Architecture",
    "architecture_orphans":          "Architecture",
    # code_finding_{i} entries route via CheckResult.category set by the emitter.
}

# Sentinel: when category equals this, fall back to CHECK_CATEGORY[id] lookup.
_CATEGORY_UNSET = "__unset__"


class AnalyzerError(Exception):
    """Raised when the analyzer cannot resolve a check to a known category."""


@dataclass
class Recommendation:
    """Structured recommendation: what was found, where, why it matters, how to fix.

    All four fields must be non-empty strings. to_legacy_string() collapses
    the structured form to a flat sentence for the legacy findings_json shape.
    """
    what: str
    where: str
    why: str
    how: str

    def to_legacy_string(self) -> str:
        """Render to a flat string for findings_json backward compat: '{what} {how}'."""
        return f"{self.what} {self.how}"


def _rec(what: str, where: str, why: str, how: str) -> Recommendation:
    """Compact constructor for inline recommendations."""
    return Recommendation(what=what, where=where, why=why, how=how)


@dataclass
class CheckResult:
    id: str
    name: str
    status: Literal["pass", "warn", "fail"]
    evidence: dict[str, Any]  # file, snippet; optional start_line, end_line for code analysis
    recommendation: Recommendation
    points: int = 0
    severity: float = 1.0
    confidence: float = 1.0
    scope_factor: float = 1.0
    category: str = _CATEGORY_UNSET


@dataclass
class SectionResult:
    name: str
    checks: list[CheckResult] = field(default_factory=list)
    score: int = 0


@dataclass
class ReportResult:
    overall_score: int
    sections: list[SectionResult] = field(default_factory=list)
    interview_pack: list[str] = field(default_factory=list)
    category_scores: dict[str, int] = field(default_factory=dict)


def compute_scope_factor(occurrences: int) -> float:
    """Linear interp from 1 occurrence (0.2) to 10+ occurrences (1.0).

    Below 1 returns 0.2 (no negative scope). At/above 10 returns 1.0.
    """
    if occurrences <= 1:
        return 0.2
    if occurrences >= 10:
        return 1.0
    # Linear: x=1 -> 0.2, x=10 -> 1.0; slope = 0.8/9
    return round(0.2 + (occurrences - 1) * (0.8 / 9), 4)


def _category_for(check: CheckResult) -> str:
    if check.category and check.category != _CATEGORY_UNSET:
        return check.category
    cat = CHECK_CATEGORY.get(check.id)
    if cat is None:
        raise AnalyzerError(
            f"Check id {check.id!r} has no category: not in CHECK_CATEGORY and no explicit category set"
        )
    return cat


def compute_categorical_score(
    checks: list[CheckResult],
) -> tuple[int, dict[str, int]]:
    """Compute weighted overall score and per-category scores.

    Returns (overall_score, category_scores). Empty categories score 100
    (neutral, no penalty). Overall is clamped to [0, 100].
    """
    category_scores: dict[str, int] = {}
    by_cat: dict[str, list[CheckResult]] = {c: [] for c in CATEGORY_WEIGHTS}
    for check in checks:
        cat = _category_for(check)
        if cat not in by_cat:
            # Category named on a check but not in CATEGORY_WEIGHTS — accept and warn via dict.
            by_cat[cat] = []
        by_cat[cat].append(check)

    for cat in CATEGORY_WEIGHTS:
        relevant = by_cat.get(cat) or []
        if not relevant:
            category_scores[cat] = 100
            continue
        weighted_earned = sum(
            c.points * c.severity * c.confidence * c.scope_factor for c in relevant
        )
        weighted_max = sum(
            POINTS_PASS * c.severity * c.confidence * c.scope_factor for c in relevant
        )
        category_scores[cat] = (
            round(100 * weighted_earned / weighted_max) if weighted_max > 0 else 100
        )

    overall = sum(category_scores[c] * CATEGORY_WEIGHTS[c] for c in CATEGORY_WEIGHTS)
    return (max(0, min(100, round(overall))), category_scores)


def _truncate(s: str, n: int = EVIDENCE_SNIPPET_MAX) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n] + "..."


def _tree_paths(fetch_result: dict[str, Any]) -> list[str]:
    """All blob paths from full tree (full repo scan)."""
    return list(fetch_result.get("tree_paths") or [])


def _find_path(fetch_result: dict[str, Any], predicate: Any) -> str | None:
    """First path in tree_paths matching predicate(path)."""
    for path in _tree_paths(fetch_result):
        if predicate(path):
            return path
    return None


def _find_paths(fetch_result: dict[str, Any], predicate: Any) -> list[str]:
    """All paths in tree_paths matching predicate(path)."""
    return [p for p in _tree_paths(fetch_result) if predicate(p)]


def _get_content_for_path(
    fetch_result: dict[str, Any], content_by_path: dict[str, str] | None, path: str
) -> str:
    """Content for path: content_by_path first, else key_files snippet (backward compat)."""
    if content_by_path and path in content_by_path:
        return content_by_path[path] or ""
    key_files = fetch_result.get("key_files") or []
    for e in key_files:
        if e.get("path") == path:
            if e.get("skipped"):
                return ""
            return e.get("snippet") or ""
    return ""


def _get_key_file(fetch_result: dict[str, Any], path: str) -> dict[str, Any] | None:
    key_files = fetch_result.get("key_files") or []
    for e in key_files:
        if e.get("path") == path:
            return e
    return None


def _readme_path_and_content(
    fetch_result: dict[str, Any], content_by_path: dict[str, str] | None
) -> tuple[str | None, str, bool]:
    """Return (path, snippet, exists). Uses tree_paths for README* anywhere."""
    def is_readme(p: str) -> bool:
        base = os.path.basename(p).upper()
        return base.startswith("README")
    paths = _find_paths(fetch_result, is_readme)
    if not paths:
        return None, "", False
    path = paths[0]
    content = _get_content_for_path(fetch_result, content_by_path, path)
    return path, content, True


def _readme(fetch_result: dict[str, Any]) -> tuple[str, bool]:
    """Return (snippet, exists). Backward compat: root README.md only if no tree_paths."""
    tree_paths = _tree_paths(fetch_result)
    if tree_paths:
        path, content, exists = _readme_path_and_content(fetch_result, None)
        return content, exists
    e = _get_key_file(fetch_result, "README.md")
    if not e:
        return "", False
    if e.get("skipped"):
        return "(skipped)", True
    return e.get("snippet") or "", True


def _workflows(fetch_result: dict[str, Any]) -> list[dict[str, Any]]:
    return fetch_result.get("workflows") or []


def _runability_checks(
    fetch_result: dict[str, Any], content_by_path: dict[str, str] | None = None
) -> list[CheckResult]:
    results: list[CheckResult] = []
    readme_path, readme_snippet, readme_exists = _readme_path_and_content(
        fetch_result, content_by_path
    )
    if not readme_exists:
        readme_snippet, readme_exists = _readme(fetch_result)
        readme_path = "README.md" if readme_exists else None
    run_keywords = ["install", "run", "docker", "uvicorn", "npm run"]
    has_run_hint = any(kw in (readme_snippet or "").lower() for kw in run_keywords)
    ev_file = readme_path or "—"

    if not readme_exists:
        results.append(CheckResult(
            id="runability_readme_install_run",
            name="README install/run",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No README file was found anywhere in the repository.",
                where="Repository root",
                why="Without a README, new contributors and reviewers cannot tell what the project does or how to run it. Onboarding stalls and the repo gets a low first impression.",
                how="Add a README.md at the repository root with a one-paragraph description, install instructions, and a single command to run the app locally.",
            ),
            points=POINTS_FAIL,
        ))
    elif has_run_hint:
        results.append(CheckResult(
            id="runability_readme_install_run",
            name="README install/run",
            status="pass",
            evidence={"file": ev_file, "snippet": _truncate(readme_snippet or "")},
            recommendation=_rec(
                what="README contains install or run instructions.",
                where=ev_file,
                why="A reader can clone this repo and get it running without asking the team for help — the cheapest possible onboarding cost.",
                how="Keep the install and run commands current as dependencies and entrypoints change so the README stays a source of truth.",
            ),
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="runability_readme_install_run",
            name="README install/run",
            status="warn",
            evidence={"file": ev_file, "snippet": _truncate(readme_snippet or "")},
            recommendation=_rec(
                what="README exists but lacks install or run instructions.",
                where=ev_file,
                why="A reader has to dig through code to figure out how to start the app. That's a multi-minute friction tax on every new contributor and every reviewer.",
                how="Add a short 'Getting started' section with the exact install command (e.g. `pip install -r requirements.txt`, `npm install`) and the run command (e.g. `uvicorn app.main:app`, `npm run dev`).",
            ),
            points=POINTS_WARN,
        ))

    docker_path = _find_path(fetch_result, lambda p: p.endswith("Dockerfile"))
    compose_path = _find_path(
        fetch_result,
        lambda p: p.endswith("docker-compose.yml") or p.endswith("docker-compose.yaml"),
    )
    if not docker_path and _get_key_file(fetch_result, "Dockerfile"):
        docker_path = "Dockerfile"
    if not compose_path and _get_key_file(fetch_result, "docker-compose.yml"):
        compose_path = "docker-compose.yml"
    has_docker = bool(docker_path or compose_path)
    ev_file = docker_path or compose_path or "—"
    ev_snip = ""
    if docker_path:
        ev_snip = _truncate(_get_content_for_path(fetch_result, content_by_path, docker_path)) or f"Found: {docker_path}"
    elif compose_path:
        ev_snip = _truncate(_get_content_for_path(fetch_result, content_by_path, compose_path)) or f"Found: {compose_path}"
    if not ev_snip and has_docker:
        ev_snip = f"Found: {ev_file}"

    if has_docker:
        results.append(CheckResult(
            id="runability_docker",
            name="Docker",
            status="pass",
            evidence={"file": ev_file, "snippet": ev_snip},
            recommendation=_rec(
                what="Docker configuration is present in the repository.",
                where=ev_file,
                why="A reproducible container removes the 'works on my machine' class of bugs and gives reviewers a one-command path to a running app.",
                how="Periodically rebuild from a clean cache to confirm the Dockerfile still builds, and keep the base image pinned to a specific version rather than `latest`.",
            ),
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="runability_docker",
            name="Docker",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No Dockerfile or docker-compose.yml found in the repository.",
                where="Repository root",
                why="Reviewers and CI have to set up a Python or Node environment by hand to run this code. That's a per-contributor cost and a source of environment drift.",
                how="Add a Dockerfile that installs dependencies and exposes the app's run command. For multi-service apps, add a docker-compose.yml that wires up dependencies (db, redis, etc.).",
            ),
            points=POINTS_FAIL,
        ))

    return results


def _engineering_checks(
    fetch_result: dict[str, Any], content_by_path: dict[str, str] | None = None
) -> list[CheckResult]:
    results: list[CheckResult] = []
    tree_paths = _tree_paths(fetch_result)
    test_prefixes = ("tests/", "__tests__/", "src/test/", "src/tests/")
    test_paths = [p for p in tree_paths if any(p.startswith(pr) for pr in test_prefixes)]
    test_folders = fetch_result.get("test_folders_detected") or []
    workflows = _workflows(fetch_result)
    test_in_workflows = False
    wf_ev_path, wf_ev_snip = "—", ""
    for w in workflows:
        snip = (w.get("snippet") or "").lower()
        if any(x in snip for x in ["test", "pytest", "jest", "vitest"]):
            test_in_workflows = True
            wf_ev_path = w.get("path") or "—"
            wf_ev_snip = _truncate(w.get("snippet") or "")
            break

    has_tests = bool(test_paths or test_folders)
    ev_test = (test_paths[0] if test_paths else test_folders[0]) if has_tests else "—"
    if has_tests:
        results.append(CheckResult(
            id="engineering_tests",
            name="Tests",
            status="pass",
            evidence={"file": ev_test, "snippet": f"Found: {ev_test}"},
            recommendation=_rec(
                what="A test directory is present in the repository.",
                where=ev_test,
                why="Tests are the cheapest way to catch regressions before production. Their presence means the team treats correctness as part of 'done'.",
                how="Run the test suite in CI on every PR, and watch coverage trends — adding code without adding tests is the most common way coverage erodes.",
            ),
            points=POINTS_PASS,
        ))
    elif test_in_workflows:
        results.append(CheckResult(
            id="engineering_tests",
            name="Tests",
            status="warn",
            evidence={"file": wf_ev_path, "snippet": wf_ev_snip},
            recommendation=_rec(
                what="CI references a test command but no test directory was found.",
                where=wf_ev_path,
                why="The CI step is either failing silently or running on an empty suite. Either way, the team is paying for CI minutes without getting test coverage in return.",
                how="Add a `tests/` (Python) or `__tests__/` (JS) directory with at least smoke tests for the critical paths — a single happy-path test per route is a cheap starting point.",
            ),
            points=POINTS_WARN,
        ))
    else:
        results.append(CheckResult(
            id="engineering_tests",
            name="Tests",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No tests or test directory found anywhere in the repository.",
                where="Repository root",
                why="Every change ships untested. Regressions land in production unnoticed and refactors become high-risk because there's no safety net.",
                how="Add `tests/` (Python, with pytest) or `__tests__/` (JS, with jest/vitest), and start with one happy-path test per public entrypoint — that already catches most import-time and wiring bugs.",
            ),
            points=POINTS_FAIL,
        ))

    ci_paths = _find_paths(
        fetch_result,
        lambda p: p.startswith(".github/workflows/") and (p.endswith(".yml") or p.endswith(".yaml")),
    )
    has_ci = bool(ci_paths or workflows)
    ci_ev_path = ci_paths[0] if ci_paths else (workflows[0].get("path") if workflows else "—")
    ci_ev_snip = _get_content_for_path(fetch_result, content_by_path, ci_ev_path) if ci_ev_path != "—" else (workflows[0].get("snippet") if workflows else "")
    if has_ci:
        results.append(CheckResult(
            id="engineering_ci",
            name="CI",
            status="pass",
            evidence={"file": ci_ev_path, "snippet": _truncate(ci_ev_snip or f"Found: {ci_ev_path}")},
            recommendation=_rec(
                what="A CI workflow is configured for this repository.",
                where=ci_ev_path,
                why="Automated checks on every PR catch broken builds before merge, so reviewers can focus on the change itself rather than environment setup.",
                how="Make sure the workflow runs tests and lint on PRs against the default branch, and add a status check requirement so failing CI blocks merge.",
            ),
            points=POINTS_PASS,
            severity=SEV_MEDIUM,
        ))
    else:
        results.append(CheckResult(
            id="engineering_ci",
            name="CI",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No CI workflow files found under .github/workflows/.",
                where=".github/workflows/",
                why="Every PR depends on humans running tests locally. Broken main branches are a matter of when, not if, and reviewers spend cycles reproducing setup issues.",
                how="Create `.github/workflows/ci.yml` that installs dependencies and runs your test command on push and pull_request events targeting the default branch.",
            ),
            points=POINTS_FAIL,
            severity=SEV_MEDIUM,
        ))

    lint_patterns = (".prettierrc", ".eslintrc", "eslint.config", "ruff.toml", "pyproject.toml", "mypy.ini", "tox.ini")
    lint_paths = [p for p in tree_paths if any(os.path.basename(p).lower().startswith(x) or x in p for x in lint_patterns)]
    scripts_snip = ""
    py_snip = ""
    req_snip = ""
    for path in ["package.json", "pyproject.toml", "requirements.txt"]:
        content = _get_content_for_path(fetch_result, content_by_path, path)
        if path == "package.json":
            scripts_snip = content
        elif path == "pyproject.toml":
            py_snip = content
        else:
            req_snip = content
    for p in tree_paths:
        if p.endswith("package.json") and not scripts_snip:
            scripts_snip = _get_content_for_path(fetch_result, content_by_path, p)
        if p.endswith("pyproject.toml") and not py_snip:
            py_snip = _get_content_for_path(fetch_result, content_by_path, p)
        if "requirements" in p and p.endswith(".txt") and not req_snip:
            req_snip = _get_content_for_path(fetch_result, content_by_path, p)
    lint_in_scripts = any(x in scripts_snip.lower() for x in ["eslint", "prettier", "lint", "format"])
    lint_in_py = any(x in py_snip.lower() for x in ["ruff", "black", "mypy", "flake8"])
    lint_in_reqs = any(x in req_snip.lower() for x in ["ruff", "black", "mypy", "flake8"])
    has_lint = bool(lint_paths) or lint_in_scripts or lint_in_py or lint_in_reqs
    ev_lint = lint_paths[0] if lint_paths else ("package.json" if lint_in_scripts else ("pyproject.toml" if lint_in_py else "requirements.txt"))
    ev_lint_snip = _truncate(_get_content_for_path(fetch_result, content_by_path, ev_lint) if ev_lint else (scripts_snip or py_snip or req_snip)) or f"Found: {ev_lint}"

    if has_lint:
        results.append(CheckResult(
            id="engineering_lint_format",
            name="Lint/format",
            status="pass",
            evidence={"file": ev_lint, "snippet": ev_lint_snip},
            recommendation=_rec(
                what="Lint or format configuration is present.",
                where=ev_lint,
                why="A consistent style means PR reviews focus on logic rather than whitespace, and machine-enforced rules catch common bugs (unused imports, undefined names) before they ship.",
                how="Run the linter in CI as a required check, and consider a pre-commit hook so issues are caught locally before push.",
            ),
            points=POINTS_PASS,
        ))
    elif scripts_snip or py_snip or req_snip:
        results.append(CheckResult(
            id="engineering_lint_format",
            name="Lint/format",
            status="warn",
            evidence={"file": ev_lint, "snippet": ev_lint_snip},
            recommendation=_rec(
                what="A package manifest exists but no lint or format tool is configured.",
                where=ev_lint,
                why="Style drift is a slow tax on every reviewer and makes diffs noisy. Without a linter, simple bugs (unused imports, dead code, undefined names) ship to production.",
                how="Add `ruff` and `black` for Python (configure in `pyproject.toml`) or `eslint` and `prettier` for JS/TS (add `lint`/`format` scripts to `package.json`), and run them in CI.",
            ),
            points=POINTS_WARN,
        ))
    else:
        results.append(CheckResult(
            id="engineering_lint_format",
            name="Lint/format",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No lint or format configuration found anywhere in the repository.",
                where="Repository root",
                why="The codebase has no automated style or correctness gate. Whatever pattern emerges is whatever the most recent contributor felt like — review fatigue and inconsistent code follow.",
                how="Pick one tool per language (`ruff` for Python, `eslint` for JS/TS) and add a config file plus a CI job that fails on lint errors.",
            ),
            points=POINTS_FAIL,
        ))

    lockfile_names = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock")
    lock_paths = [p for p in tree_paths if any(p.endswith(lf) for lf in lockfile_names)]
    if not lock_paths:
        for lf in lockfile_names:
            if _get_key_file(fetch_result, lf):
                lock_paths = [lf]
                break
    has_lock = bool(lock_paths)
    reqs_path = _find_path(fetch_result, lambda p: "requirements" in p and p.endswith(".txt"))
    if not reqs_path and _get_key_file(fetch_result, "requirements.txt"):
        reqs_path = "requirements.txt"
    reqs_content = _get_content_for_path(fetch_result, content_by_path, reqs_path or "") if reqs_path else ""
    pinned_reqs = "==" in reqs_content
    has_reqs = bool(reqs_path or _get_key_file(fetch_result, "requirements.txt"))

    if has_lock or pinned_reqs:
        ev_pin = lock_paths[0] if lock_paths else (reqs_path or "requirements.txt")
        ev_pin_snip = _truncate(_get_content_for_path(fetch_result, content_by_path, ev_pin)) or f"Found: {ev_pin}"
        results.append(CheckResult(
            id="engineering_pinning",
            name="Dependency pinning",
            status="pass",
            evidence={"file": ev_pin, "snippet": ev_pin_snip},
            recommendation=_rec(
                what="Dependencies are pinned via a lockfile or exact-version specifiers.",
                where=ev_pin,
                why="Builds are reproducible and supply-chain compromises in transitive deps don't silently update overnight. Yesterday's green build still builds today.",
                how="Keep the lockfile committed and refresh it intentionally (e.g. `npm ci` in CI, scheduled Renovate or Dependabot PRs for updates rather than ad-hoc bumps).",
            ),
            points=POINTS_PASS,
        ))
    elif has_reqs:
        ev_pin_snip = _truncate(reqs_content)
        results.append(CheckResult(
            id="engineering_pinning",
            name="Dependency pinning",
            status="warn",
            evidence={"file": reqs_path or "requirements.txt", "snippet": ev_pin_snip},
            recommendation=_rec(
                what="A requirements file exists but versions are not pinned with `==`.",
                where=reqs_path or "requirements.txt",
                why="A new transitive release tonight can break the build tomorrow with no code change. Reproducing yesterday's bug from yesterday's commit is no longer reliable.",
                how="Replace `>=` and unspecified versions with exact `==` pins, or add a lockfile (`pip-compile` -> `requirements.lock` for pip, or migrate to Poetry/uv with their lockfiles).",
            ),
            points=POINTS_WARN,
        ))
    else:
        results.append(CheckResult(
            id="engineering_pinning",
            name="Dependency pinning",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No lockfile or pinned-version manifest found.",
                where="Repository root",
                why="Every install pulls whatever is current on the registry. Builds are non-reproducible, and a malicious typo-squatted package can land without anyone noticing.",
                how="Commit a lockfile from your package manager (`package-lock.json`, `poetry.lock`, `Pipfile.lock`, `uv.lock`), and have CI use the lockfile-respecting install command (`npm ci`, `poetry install --no-root --sync`).",
            ),
            points=POINTS_FAIL,
        ))

    return results


def _secrets_checks(
    fetch_result: dict[str, Any], content_by_path: dict[str, str] | None = None
) -> list[CheckResult]:
    results: list[CheckResult] = []
    env_ex_path = _find_path(fetch_result, lambda p: ".env.example" in p or p.endswith(".env.example"))
    env_ex_content = _get_content_for_path(fetch_result, content_by_path, env_ex_path or "") if env_ex_path else ""
    if not env_ex_path:
        k = _get_key_file(fetch_result, ".env.example")
        env_ex_path = ".env.example" if k else None
        env_ex_content = (k.get("snippet") or "") if k else ""
    if env_ex_path:
        results.append(CheckResult(
            id="secrets_env_example",
            name=".env.example",
            status="pass",
            evidence={"file": env_ex_path, "snippet": _truncate(env_ex_content) or f"Found: {env_ex_path}"},
            recommendation=_rec(
                what="A `.env.example` template is present.",
                where=env_ex_path,
                why="New contributors know exactly which environment variables the app needs without having to grep the codebase or message the team.",
                how="Keep `.env.example` in sync as new env vars are introduced — a missing key here is a guaranteed onboarding failure.",
            ),
            points=POINTS_PASS,
            severity=SEV_LOW,
        ))
    else:
        results.append(CheckResult(
            id="secrets_env_example",
            name=".env.example",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No `.env.example` template found.",
                where="Repository root",
                why="There's no documented list of environment variables this app expects, so first-time setup involves trial-and-error against runtime errors.",
                how="Add a `.env.example` listing every required env var (with placeholder values, never real secrets), and reference it from the README's setup section.",
            ),
            points=POINTS_FAIL,
            severity=SEV_LOW,
        ))

    patterns = [
        (r"(?:api_key|secret|password)\s*=\s*['\"]?[a-zA-Z0-9_\-]{20,}", "possible secret"),
        (r"=ghp_[a-zA-Z0-9]+", "GitHub token"),
        (r"=sk-[a-zA-Z0-9]+", "API key"),
        (r"Bearer\s+[a-zA-Z0-9_\-]{20,}", "Bearer token"),
    ]
    scans: list[tuple[str, str]] = []
    paths_to_scan: list[tuple[str, str]] = []
    if content_by_path:
        for path, content in content_by_path.items():
            paths_to_scan.append((path, content))
    for e in fetch_result.get("key_files") or []:
        path = e.get("path") or ""
        if e.get("skipped"):
            continue
        paths_to_scan.append((path, e.get("snippet") or ""))
    for w in _workflows(fetch_result):
        paths_to_scan.append((w.get("path") or "workflow", w.get("snippet") or ""))
    for path, snip in paths_to_scan:
        for pat, label in patterns:
            if re.search(pat, snip, re.IGNORECASE):
                scans.append((path, label))
                break

    if not scans:
        results.append(CheckResult(
            id="secrets_possible_secrets",
            name="Possible secrets",
            status="pass",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No high-confidence secret patterns matched in sampled files.",
                where="Sampled repository contents",
                why="The first line of credential hygiene is holding — committed code is unlikely to leak tokens or keys to anyone who clones the repo.",
                how="Add a pre-commit hook (`detect-secrets`, `gitleaks`) so this stays true even as the codebase grows, and rotate any secret that ever lands in a commit (even a reverted one).",
            ),
            points=POINTS_PASS,
        ))
    else:
        f, _ = scans[0]
        results.append(CheckResult(
            id="secrets_possible_secrets",
            name="Possible secrets",
            status="warn",
            evidence={"file": f, "snippet": "possible secret – review recommended"},
            recommendation=_rec(
                what="A pattern matching a possible secret (token, key, or password) was detected.",
                where=f,
                why="If this is a real credential, anyone with read access to the repo can use it. Even a since-removed secret in git history is compromised — git remembers everything.",
                how="Treat any matched secret as compromised: rotate it now, then remove from the file (move the value to environment variables and `.env`), and use `git filter-repo` or BFG to scrub history if it was ever committed.",
            ),
            points=POINTS_WARN,
        ))

    return results


def _documentation_checks(
    fetch_result: dict[str, Any], content_by_path: dict[str, str] | None = None
) -> list[CheckResult]:
    results: list[CheckResult] = []
    readme_path, readme_snippet, readme_exists = _readme_path_and_content(
        fetch_result, content_by_path
    )
    if not readme_exists:
        readme_snippet, readme_exists = _readme(fetch_result)
        readme_path = "README.md" if readme_exists else None
    n = len(readme_snippet or "")
    section_markers = ["## usage", "## setup", "## installation", "## getting started"]
    has_section = any(m in (readme_snippet or "").lower() for m in section_markers)
    doc_ev_file = readme_path or "—"

    doc_paths = _find_paths(
        fetch_result,
        lambda p: (
            os.path.basename(p).upper().startswith("README")
            or p.startswith("docs/")
            or os.path.basename(p).upper().startswith("CONTRIBUTING")
            or os.path.basename(p).upper().startswith("SECURITY")
            or os.path.basename(p).upper().startswith("CHANGELOG")
            or os.path.basename(p).upper().startswith("LICENSE")
        ),
    )
    has_doc = bool(doc_paths) or readme_exists

    if not has_doc:
        results.append(CheckResult(
            id="documentation_readme_length",
            name="README length",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No README or `docs/` directory found.",
                where="Repository root",
                why="The project has no written context. New contributors and stakeholders have to read the source to learn what the code does, which doesn't scale past one or two people.",
                how="Add a README.md with at least: a one-paragraph project description, a `## Usage` or `## Setup` section, and a working run command.",
            ),
            points=POINTS_FAIL,
        ))
    elif n >= 500:
        results.append(CheckResult(
            id="documentation_readme_length",
            name="README length",
            status="pass",
            evidence={"file": doc_ev_file, "snippet": f"length={n}"},
            recommendation=_rec(
                what=f"README is substantive ({n} characters).",
                where=doc_ev_file,
                why="There's enough context here for a new contributor to orient themselves without having to ping the team. That's the whole job of a README.",
                how="Review the README quarterly — outdated install steps or wrong run commands hurt more than a short README, because the reader trusts what they see.",
            ),
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="documentation_readme_length",
            name="README length",
            status="warn",
            evidence={"file": doc_ev_file, "snippet": f"length={n}"},
            recommendation=_rec(
                what=f"README is short ({n} characters; under the 500-character threshold).",
                where=doc_ev_file,
                why="A terse README signals 'this isn't where you find answers.' Readers learn to skip it, and the next person to update it doesn't bother either.",
                how="Expand to at least cover: what the project is (one paragraph), how to install (one code block), how to run (one code block), and where to ask questions.",
            ),
            points=POINTS_WARN,
        ))

    if not has_doc:
        results.append(CheckResult(
            id="documentation_readme_sections",
            name="README sections",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation=_rec(
                what="No README or docs to evaluate for structure.",
                where="Repository root",
                why="Without any structured documentation, the project's onboarding cost scales linearly with team size — every new person asks the same questions.",
                how="Add a README.md that includes at minimum a `## Usage`, `## Setup`, or `## Installation` heading so readers can find the run command without reading every paragraph.",
            ),
            points=POINTS_FAIL,
        ))
    elif has_section:
        results.append(CheckResult(
            id="documentation_readme_sections",
            name="README sections",
            status="pass",
            evidence={"file": doc_ev_file, "snippet": _truncate(readme_snippet or "") or f"Found: {doc_ev_file}"},
            recommendation=_rec(
                what="README is organized with usage, setup, or installation headings.",
                where=doc_ev_file,
                why="Readers can skim to the section they need. That's the difference between docs people use and docs people skim past.",
                how="Keep adding headings as the project grows (e.g. `## Architecture`, `## Contributing`) so the README scales with the codebase.",
            ),
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="documentation_readme_sections",
            name="README sections",
            status="warn",
            evidence={"file": doc_ev_file, "snippet": _truncate(readme_snippet or "") or f"Found: {doc_ev_file}"},
            recommendation=_rec(
                what="README has prose but no `## Usage`, `## Setup`, or `## Installation` heading.",
                where=doc_ev_file,
                why="Readers have to read top-to-bottom to find install or run commands. That's a friction tax every time someone returns to this project.",
                how="Add a `## Setup` or `## Getting started` heading near the top of the README, with the install and run commands directly under it.",
            ),
            points=POINTS_WARN,
        ))

    return results


def _detect_stack(
    fetch_result: dict[str, Any], content_by_path: dict[str, str] | None = None
) -> dict[str, bool]:
    """Deterministic stack and gaps from fetch_result. Uses tree_paths and content."""
    workflows = _workflows(fetch_result)
    tree_paths = _tree_paths(fetch_result)
    test_prefixes = ("tests/", "__tests__/", "src/test/", "src/tests/")
    test_folders = [p for p in tree_paths if any(p.startswith(pr) for pr in test_prefixes)] or fetch_result.get("test_folders_detected") or []
    test_in_wf = False
    for w in workflows:
        snip = (w.get("snippet") or "").lower()
        if any(x in snip for x in ["test", "pytest", "jest", "vitest"]):
            test_in_wf = True
            break

    scripts_snip = ""
    py_snip = ""
    req_snip = ""
    for p in tree_paths:
        if p.endswith("package.json"):
            scripts_snip = _get_content_for_path(fetch_result, content_by_path, p).lower()
            break
    for p in tree_paths:
        if p.endswith("pyproject.toml"):
            py_snip = _get_content_for_path(fetch_result, content_by_path, p).lower()
            break
    for p in tree_paths:
        if "requirements" in p and p.endswith(".txt"):
            req_snip = _get_content_for_path(fetch_result, content_by_path, p).lower()
            break
    if not scripts_snip:
        pkg = _get_key_file(fetch_result, "package.json")
        scripts_snip = (pkg.get("snippet") or "").lower() if pkg else ""
    if not py_snip:
        pyproject = _get_key_file(fetch_result, "pyproject.toml")
        py_snip = (pyproject.get("snippet") or "").lower() if pyproject else ""
    if not req_snip:
        reqs = _get_key_file(fetch_result, "requirements.txt")
        req_snip = (reqs.get("snippet") or "").lower() if reqs else ""
    lint_kw = ["eslint", "prettier", "lint", "format", "ruff", "black", "mypy", "flake8"]
    has_lint = any(kw in scripts_snip or kw in py_snip or kw in req_snip for kw in lint_kw)

    readme_path, readme_snippet, readme_exists = _readme_path_and_content(fetch_result, content_by_path)
    if not readme_exists:
        readme_snippet, readme_exists = _readme(fetch_result)
    section_markers = ["## usage", "## setup", "## installation", "## getting started"]
    has_section = any(m in (readme_snippet or "").lower() for m in section_markers)
    readme_ok = readme_exists and len(readme_snippet or "") >= 500 and has_section

    has_node = bool(_find_path(fetch_result, lambda p: p.endswith("package.json")))
    has_python = bool(_find_path(fetch_result, lambda p: p.endswith("pyproject.toml") or ("requirements" in p and p.endswith(".txt"))))
    has_fastapi = has_python and ("fastapi" in req_snip or "fastapi" in py_snip)
    has_next = has_node and "next" in scripts_snip

    has_docker = bool(
        _find_path(fetch_result, lambda p: p.endswith("Dockerfile"))
        or _find_path(fetch_result, lambda p: p.endswith("docker-compose.yml") or p.endswith("docker-compose.yaml"))
    )
    has_ci = bool(_find_paths(fetch_result, lambda p: p.startswith(".github/workflows/") and (p.endswith(".yml") or p.endswith(".yaml")))) or len(workflows) > 0
    env_ex = _find_path(fetch_result, lambda p: ".env.example" in p or p.endswith(".env.example")) or _get_key_file(fetch_result, ".env.example")

    return {
        "has_docker": has_docker,
        "has_ci": has_ci,
        "has_tests": len(test_folders) > 0 or test_in_wf,
        "has_node": has_node,
        "has_python": has_python,
        "has_fastapi": has_fastapi,
        "has_next": has_next,
        "has_lint": has_lint,
        "has_env_example": bool(env_ex),
        "readme_ok": readme_ok,
    }


def _generate_interview_pack(
    fetch_result: dict[str, Any], stack: dict[str, bool]
) -> list[str]:
    """Build up to 10 tailored interview questions. Deterministic, no LLM."""
    out: list[str] = []
    generic = [
        "How would you improve production readiness of this project?",
        "What would you add first to make this codebase easier for new contributors?",
        "How do you approach dependency upgrades and security patches?",
        "Describe how you'd structure environment-specific configuration.",
        "What monitoring or observability would you add for production?",
    ]

    rules: list[tuple[bool, str]] = [
        (stack["has_docker"], "Why did you choose Docker for containerization? How do you structure Dockerfile vs docker-compose for local dev and production?"),
        (not stack["has_tests"], "How would you test the critical paths in this application? Where would you start?"),
        (stack["has_fastapi"], "How do you use dependency injection in FastAPI? Where would you add middleware?"),
        (stack["has_next"], "How do you decide between SSR and CSR in Next.js? How is routing organized?"),
        (stack["has_ci"], "Walk me through your CI pipeline. What runs on PR vs main? What would you add?"),
        (not stack["has_env_example"], "How do you manage secrets across environments? What would you document in .env.example?"),
        (not stack["has_docker"], "How would you containerize this app for local dev and production?"),
        (not stack["has_ci"], "How would you add CI? What stages would you include (test, lint, build, deploy)?"),
        (stack["has_lint"], "How is linting and formatting integrated? Pre-commit hooks vs CI, or both?"),
        (not stack["readme_ok"], "How would you improve the README for onboarding new developers?"),
    ]

    for cond, q in rules:
        if cond and len(out) < 10:
            out.append(q)
    i = 0
    while len(out) < 10 and i < len(generic):
        out.append(generic[i])
        i += 1
    return out[:10]


def _code_analysis_checks(
    content_by_path: dict[str, str] | None, stats: dict[str, Any] | None = None
) -> list[CheckResult]:
    """Build Code Analysis section from content_by_path. No code execution."""
    from app.analyzers.code import run_code_analysis

    files = content_by_path or {}
    stats = stats or {}
    if not files:
        return []

    code_analysis = run_code_analysis(files, stats)
    checks: list[CheckResult] = []

    # Summary bullet as first check
    bullets = code_analysis.get("summary_bullets") or []
    summary_text = "; ".join(bullets)[:500] if bullets else "No code analysis summary."
    if bullets:
        summary_rec = _rec(
            what="Static analysis produced a summary of languages, frameworks, and endpoints.",
            where="Sampled repository contents",
            why="A read-only summary is the cheapest way for a reviewer to grasp the shape of the codebase before clicking into specific files.",
            how="Use the bullets below as the entry point into deeper review — start with the most-used language and the framework that owns the request path.",
        )
    else:
        summary_rec = _rec(
            what="Static analysis produced no summary signals.",
            where="Sampled repository contents",
            why="Either the sampled files are too few to tell, or the repo uses languages/frameworks the analyzer doesn't recognize. Either way, reviewer gets no orienting view.",
            how="Increase the file sample (raise MAX_FILES_FETCH) or add a language/framework detector for whatever is actually in this repo.",
        )
    checks.append(
        CheckResult(
            id="code_summary",
            name="Code analysis summary",
            status="pass" if bullets else "warn",
            evidence={"file": "—", "snippet": summary_text},
            recommendation=summary_rec,
            points=POINTS_PASS if bullets else POINTS_WARN,
        )
    )

    # Frameworks detected
    frameworks = code_analysis.get("frameworks_detected") or []
    if frameworks:
        fw_rec = _rec(
            what=f"Detected frameworks: {', '.join(frameworks)}.",
            where="Sampled repository contents",
            why="Knowing the framework tells a reviewer which conventions to expect (e.g. FastAPI dependency injection, Next.js routing) and where to look for the request path.",
            how="If the list is missing a framework you actually use, raise the file sample limit or add a detector — the rest of the analysis depends on this signal.",
        )
    else:
        fw_rec = _rec(
            what="No web framework detected in scanned files.",
            where="Sampled repository contents",
            why="Either this is a library, a script, or the framework isn't recognized. Endpoint discovery and architecture analysis don't have an anchor without it.",
            how="If this should be a web service, confirm `fastapi`, `express`, `next`, or similar is present in your manifest and being imported. Otherwise this is informational.",
        )
    checks.append(
        CheckResult(
            id="code_frameworks",
            name="Frameworks detected",
            status="pass" if frameworks else "warn",
            evidence={"file": "—", "snippet": ", ".join(frameworks) if frameworks else "None"},
            recommendation=fw_rec,
            points=POINTS_PASS if frameworks else POINTS_WARN,
        )
    )

    # Endpoint count
    endpoints = code_analysis.get("endpoints") or []
    ep_count = len(endpoints)
    if ep_count:
        ep_rec = _rec(
            what=f"Static endpoint discovery found {ep_count} route(s).",
            where="Detected route definitions in sampled files",
            why="Endpoints are the public contract. Knowing what's exposed is the first step to reviewing auth, input validation, and rate limiting on each one.",
            how="Cross-check the discovered list against your routing tests — anything in the list that isn't tested is a candidate for a smoke test.",
        )
    else:
        ep_rec = _rec(
            what="No route decorators or API endpoints found in scanned files.",
            where="Sampled repository contents",
            why="Either this isn't a web service, or the framework's routing convention isn't recognized. Reviewers can't audit the public surface from this analysis alone.",
            how="If endpoints exist, confirm the analyzer covers your framework's routing style (FastAPI/APIRouter decorators, Next.js `pages/api/`, or Express `router.get`).",
        )
    checks.append(
        CheckResult(
            id="code_endpoints",
            name="Endpoints",
            status="pass" if ep_count > 0 else "warn",
            evidence={"file": "—", "snippet": f"{ep_count} endpoint(s) discovered"},
            recommendation=ep_rec,
            points=POINTS_PASS if ep_count > 0 else POINTS_WARN,
        )
    )

    # Code quality (lint/format/typecheck/test from code analyzers)
    quality_signals = code_analysis.get("quality_signals") or {}
    has_lint = bool(quality_signals.get("lint_format"))
    has_typecheck = bool(quality_signals.get("typecheck"))
    has_tests = bool(quality_signals.get("test_dirs") or quality_signals.get("test_config"))
    quality_ok = has_lint or has_tests
    if quality_ok:
        quality_rec = _rec(
            what=f"Quality signals detected (lint: {has_lint}, typecheck: {has_typecheck}, tests: {has_tests}).",
            where="Repository configuration files",
            why="The team has set up at least one of the standard quality gates. Code health is a stated value, not just an aspiration.",
            how="Make sure each detected gate runs in CI as a required check — a config file that nobody enforces is just decoration.",
        )
    else:
        quality_rec = _rec(
            what=f"Few quality signals: lint={has_lint}, typecheck={has_typecheck}, tests={has_tests}.",
            where="Repository configuration files",
            why="Without lint, typecheck, or tests, every change ships unreviewed by any automated tool. The cost is paid in production bugs and review fatigue.",
            how="Pick the cheapest one to add first — usually `ruff`/`eslint` for lint — and wire it into CI as a required check before tackling typecheck or tests.",
        )
    checks.append(
        CheckResult(
            id="code_quality",
            name="Code quality signals",
            status="pass" if quality_ok else "warn",
            evidence={"file": "—", "snippet": f"Lint/format: {has_lint}; Typecheck: {has_typecheck}; Tests: {has_tests}"},
            recommendation=quality_rec,
            points=POINTS_PASS if quality_ok else POINTS_WARN,
        )
    )

    # Code security (secrets + dangerous patterns)
    security_signals = code_analysis.get("security_signals") or {}
    secret_count = security_signals.get("secret_findings", 0) or 0
    danger_count = security_signals.get("danger_findings", 0) or 0
    security_ok = secret_count == 0 and danger_count == 0
    if security_ok:
        sec_rec = _rec(
            what="Static security scan found no high-confidence secrets or dangerous patterns.",
            where="Sampled repository contents",
            why="Surface-level credential and dangerous-call hygiene is in place — committed code isn't leaking tokens or shelling out to user input on the obvious paths.",
            how="Add a pre-commit secret scanner (`gitleaks`, `detect-secrets`) so this stays true as the codebase grows, and run a deeper SAST tool periodically for the non-obvious paths.",
        )
    elif secret_count > 0:
        sec_rec = _rec(
            what=f"Static scan flagged {secret_count} possible secret(s) and {danger_count} dangerous pattern(s).",
            where="Sampled repository contents (see individual findings below)",
            why="If even one of the secret matches is real, that credential is compromised. Anyone with read access to the repo (or its git history) can use it.",
            how="Treat every flagged secret as compromised: rotate it, then move the value to environment variables. Review each dangerous pattern (`eval`, `subprocess shell=True`, `pickle.loads`) for untrusted input.",
        )
    else:
        sec_rec = _rec(
            what=f"Static scan flagged {danger_count} dangerous code pattern(s).",
            where="Sampled repository contents (see individual findings below)",
            why="Dangerous patterns (`eval`, `exec`, `subprocess shell=True`, `pickle.loads`) are remote code execution paths if their input is ever attacker-controlled.",
            how="Review each flagged call. Ensure the input is fully trusted (literal string, internal config) — if not, replace with a safe alternative (`subprocess.run(args)` instead of `shell=True`, structured deserializers instead of `pickle`).",
        )
    checks.append(
        CheckResult(
            id="code_security",
            name="Code security",
            status="fail" if secret_count > 0 else ("warn" if danger_count > 0 else "pass"),
            evidence={"file": "—", "snippet": f"Possible secrets: {secret_count}; Dangerous patterns: {danger_count}"},
            recommendation=sec_rec,
            points=POINTS_FAIL if secret_count > 0 else (POINTS_WARN if danger_count > 0 else POINTS_PASS),
        )
    )

    # Individual findings with evidence (path, line range, snippet)
    for i, f in enumerate((code_analysis.get("findings") or [])[:15]):
        ev = f.get("evidence") or {}
        path = ev.get("path") or "—"
        snippet = (ev.get("snippet") or "")[:EVIDENCE_SNIPPET_MAX]
        start_line = ev.get("start_line")
        end_line = ev.get("end_line")
        evidence_dict: dict[str, Any] = {"file": path, "snippet": snippet}
        if start_line is not None:
            evidence_dict["start_line"] = start_line
        if end_line is not None:
            evidence_dict["end_line"] = end_line
        sev_str = (f.get("severity") or "info").lower()
        status = "fail" if sev_str == "high" else ("warn" if sev_str == "medium" else "pass")
        points = POINTS_FAIL if sev_str == "high" else (POINTS_WARN if sev_str == "medium" else POINTS_PASS)
        sev_value = SEV_HIGH if sev_str == "high" else (SEV_MEDIUM if sev_str == "medium" else SEV_LOW)
        title = f.get("title") or "Finding"
        title_lower = title.lower()
        is_security = title_lower.startswith("possible secret") or title_lower.startswith("dangerous pattern")
        category = "Security & Deps" if is_security else "Maintainability"
        description = f.get("description") or ""
        # Build a structured recommendation. The analyzer-supplied `description`
        # is the closest thing to a "how" we have; the rest is severity- and
        # category-shaped so the why is honest about cost.
        where_str = path
        if start_line is not None and end_line is not None and start_line == end_line:
            where_str = f"{path}:{start_line}"
        elif start_line is not None and end_line is not None:
            where_str = f"{path}:{start_line}-{end_line}"
        if is_security and sev_str == "high":
            why_text = "If this match is a real credential, it's compromised — anyone with repo read access (or git history) can use it. Even removed secrets in history are leaked."
        elif is_security:
            why_text = "Dangerous code patterns (eval, subprocess shell=True, pickle.loads) become RCE paths the moment their input is attacker-controlled."
        else:
            why_text = "Maintainability findings don't break prod today, but they accumulate into the kind of code that takes longer to change safely."
        finding_rec = _rec(
            what=title,
            where=where_str,
            why=why_text,
            how=description or "Review the flagged location and apply the smallest change that resolves the underlying issue.",
        )
        checks.append(
            CheckResult(
                id=f"code_finding_{i}",
                name=title,
                status=status,
                evidence=evidence_dict,
                recommendation=finding_rec,
                points=points,
                severity=sev_value,
                category=category,
            )
        )

    return checks


_COMPLEXITY_HIGH = 10
_COMPLEXITY_VERY_HIGH = 20
_GOD_MODULE_FAN_IN = 20


def _file_language(path: str) -> str:
    """Map a file extension to a tree-sitter language string. Empty if unsupported."""
    pl = path.lower()
    if pl.endswith(".tsx"):
        return "tsx"
    if pl.endswith(".ts"):
        return "typescript"
    if pl.endswith((".js", ".jsx", ".mjs", ".cjs")):
        return "javascript"
    return ""


def _complexity_checks(content_by_path: dict[str, str]) -> list[CheckResult]:
    """Surface high-complexity functions and TS `: any` density."""
    from app.analyzers.code.complexity import (
        parse_js_complexity,
        parse_python_complexity,
    )

    results: list[CheckResult] = []
    if not content_by_path:
        return results

    high_funcs: list[tuple[str, str, int, int]] = []  # path, name, complexity, line
    very_high_funcs: list[tuple[str, str, int, int]] = []
    any_total = 0
    ts_files_scanned = 0

    for path, content in content_by_path.items():
        if path.endswith(".py"):
            res = parse_python_complexity(path, content or "")
            for fn in res.get("functions") or []:
                cx = int(fn.get("complexity") or 0)
                if cx >= _COMPLEXITY_VERY_HIGH:
                    very_high_funcs.append((path, fn.get("name") or "", cx, int(fn.get("start_line") or 0)))
                elif cx >= _COMPLEXITY_HIGH:
                    high_funcs.append((path, fn.get("name") or "", cx, int(fn.get("start_line") or 0)))
        else:
            lang = _file_language(path)
            if not lang:
                continue
            res = parse_js_complexity(path, content or "", lang)
            if lang in ("typescript", "tsx"):
                ts_files_scanned += 1
                any_total += int(res.get("any_count") or 0)

    total_complex = len(high_funcs) + len(very_high_funcs)
    if total_complex == 0:
        results.append(CheckResult(
            id="complexity_summary",
            name="Cyclomatic complexity",
            status="pass",
            evidence={"file": "—", "snippet": "No functions exceeded complexity threshold."},
            recommendation=_rec(
                what="No Python functions exceeded the cyclomatic complexity threshold.",
                where="Sampled Python files",
                why="Low complexity means each function fits in a reviewer's head and is easier to test in isolation. That keeps refactor cost down.",
                how="Keep complexity in mind when adding code — when a function grows past ~10 branches, that's the moment to split it rather than after.",
            ),
            points=POINTS_PASS,
            severity=SEV_LOW,
            confidence=0.9,
            scope_factor=0.2,
        ))
    else:
        first = (very_high_funcs or high_funcs)[0]
        path, name, cx, line = first
        is_fail = bool(very_high_funcs)
        sev = SEV_HIGH if is_fail else SEV_MEDIUM
        results.append(CheckResult(
            id="complexity_summary",
            name="Cyclomatic complexity",
            status="fail" if is_fail else "warn",
            evidence={"file": f"{path}:{line}" if line else path, "snippet": f"{name} complexity={cx}"},
            recommendation=_rec(
                what=f"{total_complex} function(s) exceed the complexity threshold (>= {_COMPLEXITY_HIGH}); {len(very_high_funcs)} are very high (>= {_COMPLEXITY_VERY_HIGH}).",
                where=f"e.g. {path}:{line} ({name}, complexity={cx})",
                why="Highly branchy functions are hard to reason about, hard to test, and hard to change without regressions. They become the slowest part of every PR review touching them.",
                how="Extract guard clauses to early returns, pull each branch into a named helper, and add a test per branch as you split — the test surface grows with the design, not after.",
            ),
            points=POINTS_FAIL if is_fail else POINTS_WARN,
            severity=sev,
            confidence=0.9,
            scope_factor=compute_scope_factor(total_complex),
        ))

    if ts_files_scanned > 0:
        if any_total == 0:
            results.append(CheckResult(
                id="complexity_any_types",
                name="TypeScript `any` usage",
                status="pass",
                evidence={"file": "—", "snippet": f"any usages: 0 across {ts_files_scanned} TS file(s)"},
                recommendation=_rec(
                    what=f"No `: any` or `as any` usages were detected across {ts_files_scanned} TypeScript file(s).",
                    where="Sampled TypeScript files",
                    why="Avoiding `any` keeps the type system useful — refactors stay safe and IDE tooling can catch mistakes before they ship.",
                    how="Keep enforcing this with a `no-explicit-any` rule in eslint/tsconfig so a slip in a future PR fails CI rather than landing silently.",
                ),
                points=POINTS_PASS,
                severity=SEV_LOW,
                confidence=0.85,
                scope_factor=0.2,
            ))
        else:
            results.append(CheckResult(
                id="complexity_any_types",
                name="TypeScript `any` usage",
                status="warn",
                evidence={"file": "—", "snippet": f"any usages: {any_total} across {ts_files_scanned} TS file(s)"},
                recommendation=_rec(
                    what=f"{any_total} `: any` or `as any` usage(s) detected across {ts_files_scanned} TypeScript file(s).",
                    where="Sampled TypeScript files",
                    why="Each `any` is a hole the type system can't see through. Refactors silently break consumers and the tooling can't help catch the mistake at edit time.",
                    how="Replace each with the concrete type, a generic, or `unknown` plus a narrow check. Add an eslint `no-explicit-any` rule so new instances fail CI.",
                ),
                points=POINTS_WARN,
                severity=SEV_MEDIUM,
                confidence=0.85,
                scope_factor=compute_scope_factor(any_total),
            ))

    return results


def _smells_checks(content_by_path: dict[str, str]) -> list[CheckResult]:
    """Surface code smells (empty except, eval, console.log, etc.)."""
    from app.analyzers.code.smells import detect_js_smells, detect_python_smells

    results: list[CheckResult] = []
    if not content_by_path:
        return results

    high_smells: list[tuple[str, dict[str, Any]]] = []
    low_smells: list[tuple[str, dict[str, Any]]] = []

    for path, content in content_by_path.items():
        if path.endswith(".py"):
            for s in detect_python_smells(path, content or ""):
                (high_smells if s.get("severity") == "high" else low_smells).append((path, s))
        elif path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
            for s in detect_js_smells(path, content or ""):
                (high_smells if s.get("severity") == "high" else low_smells).append((path, s))

    total = len(high_smells) + len(low_smells)
    if total == 0:
        results.append(CheckResult(
            id="smells_summary",
            name="Code smells",
            status="pass",
            evidence={"file": "—", "snippet": "No code smells detected."},
            recommendation=_rec(
                what="No code smells (empty except, eval, console.log in prod, magic numbers) detected in scanned files.",
                where="Sampled repository contents",
                why="The obvious quality gates are clean — no swallowed exceptions, no `eval`, no debug logging shipping to production.",
                how="Keep enforcing this via lint rules so a regression fails CI rather than landing silently.",
            ),
            points=POINTS_PASS,
            severity=SEV_LOW,
            confidence=0.85,
            scope_factor=0.2,
        ))
    else:
        results.append(CheckResult(
            id="smells_summary",
            name="Code smells",
            status="warn" if not high_smells else "fail",
            evidence={
                "file": (high_smells or low_smells)[0][0],
                "snippet": f"{total} smell(s); {len(high_smells)} high-severity",
            },
            recommendation=_rec(
                what=f"{total} code smell(s) detected; {len(high_smells)} are high-severity.",
                where=f"e.g. {(high_smells or low_smells)[0][0]}:{(high_smells or low_smells)[0][1].get('line', '')}",
                why="Smells like empty `except`, `eval`, and console logging in production code don't break the build but hide bugs and leak debug noise to users.",
                how="Address high-severity smells first (empty except, eval) — they hide real failures. Then tighten lint rules to prevent regressions.",
            ),
            points=POINTS_FAIL if high_smells else POINTS_WARN,
            severity=SEV_HIGH if high_smells else SEV_LOW,
            confidence=0.9,
            scope_factor=compute_scope_factor(total),
        ))

    if high_smells:
        path, smell = high_smells[0]
        line = smell.get("line") or 0
        smell_type = smell.get("type") or "smell"
        results.append(CheckResult(
            id="smells_dangerous",
            name=f"Dangerous smell: {smell_type}",
            status="fail",
            evidence={
                "file": f"{path}:{line}" if line else path,
                "snippet": (smell.get("snippet") or "")[:EVIDENCE_SNIPPET_MAX],
                "start_line": line if line else None,
                "end_line": line if line else None,
            },
            recommendation=_rec(
                what=f"High-severity smell: {smell_type}.",
                where=f"{path}:{line}" if line else path,
                why="Empty `except` swallows real failures and `eval` is a remote-code-execution path the moment its input is attacker-controlled.",
                how="Replace `except: pass` with explicit handling (log + re-raise, or catch the specific exception class). Replace `eval` with a parser or explicit dispatch table.",
            ),
            points=POINTS_FAIL,
            severity=SEV_HIGH,
            confidence=0.9,
            scope_factor=compute_scope_factor(len(high_smells)),
        ))

    # Strip None-valued evidence keys so the dataclass stays JSON-clean.
    for r in results:
        r.evidence = {k: v for k, v in r.evidence.items() if v is not None}

    return results


def _dependency_checks(content_by_path: dict[str, str]) -> list[CheckResult]:
    """Surface unused / missing declared dependencies."""
    from app.analyzers.code.dependencies import check_js_deps, check_python_deps

    results: list[CheckResult] = []
    if not content_by_path:
        return results

    py_dep = check_python_deps(content_by_path)
    js_dep = check_js_deps(content_by_path)

    unused = (py_dep.get("unused") or []) + (js_dep.get("unused") or [])
    missing = (py_dep.get("missing") or []) + (js_dep.get("missing") or [])

    has_manifest = bool(py_dep.get("declared")) or bool(js_dep.get("declared"))
    if not has_manifest:
        return results

    if unused:
        results.append(CheckResult(
            id="dependencies_unused",
            name="Unused dependencies",
            status="warn",
            evidence={
                "file": "requirements.txt" if py_dep.get("unused") else "package.json",
                "snippet": ", ".join(unused[:10]),
            },
            recommendation=_rec(
                what=f"{len(unused)} declared dependency/dependencies appear unused in source: {', '.join(unused[:5])}{'…' if len(unused) > 5 else ''}.",
                where="requirements.txt or package.json",
                why="Unused deps inflate install size, broaden the supply-chain attack surface, and confuse new contributors about what's actually load-bearing.",
                how="Remove each from the manifest, run a clean install, and run the test suite. If a dep is needed at runtime via dynamic import, document that explicitly.",
            ),
            points=POINTS_WARN,
            severity=SEV_LOW,
            confidence=0.7,
            scope_factor=compute_scope_factor(len(unused)),
        ))
    else:
        results.append(CheckResult(
            id="dependencies_unused",
            name="Unused dependencies",
            status="pass",
            evidence={"file": "—", "snippet": "All declared dependencies appear used."},
            recommendation=_rec(
                what="All declared dependencies appear to be imported somewhere.",
                where="requirements.txt and package.json",
                why="No dead weight in the dependency manifest — install size and supply-chain surface are minimized.",
                how="Run a check like `depcheck` or `pip-check` periodically to keep this true as code is removed.",
            ),
            points=POINTS_PASS,
            severity=SEV_LOW,
            confidence=0.7,
            scope_factor=0.2,
        ))

    if missing:
        results.append(CheckResult(
            id="dependencies_missing",
            name="Missing dependencies",
            status="fail",
            evidence={
                "file": "requirements.txt or package.json",
                "snippet": ", ".join(missing[:10]),
            },
            recommendation=_rec(
                what=f"{len(missing)} import(s) reference packages not declared in any manifest: {', '.join(missing[:5])}{'…' if len(missing) > 5 else ''}.",
                where="requirements.txt and package.json",
                why="A fresh clone won't install these packages. The first runtime import will crash with ModuleNotFoundError — a guaranteed onboarding break.",
                how="Add each missing package to the manifest with an exact version pin. If one is meant to be optional, gate the import behind a try/except with a clear error message.",
            ),
            points=POINTS_FAIL,
            severity=SEV_HIGH,
            confidence=0.8,
            scope_factor=compute_scope_factor(len(missing)),
        ))
    else:
        results.append(CheckResult(
            id="dependencies_missing",
            name="Missing dependencies",
            status="pass",
            evidence={"file": "—", "snippet": "All imports resolve to declared dependencies."},
            recommendation=_rec(
                what="Every external import resolves to a declared dependency.",
                where="requirements.txt and package.json",
                why="Fresh clones install successfully — no surprise `ModuleNotFoundError` at runtime.",
                how="Keep the manifest in sync as imports are added; consider a CI check (`pip check`, `npm ls`) that fails on unresolved imports.",
            ),
            points=POINTS_PASS,
            severity=SEV_MEDIUM,
            confidence=0.8,
            scope_factor=0.2,
        ))

    return results


def _architecture_checks(content_by_path: dict[str, str]) -> list[CheckResult]:
    """Surface circular imports, god modules, orphan modules from the import graph."""
    from app.analyzers.code.architecture import (
        build_import_graph,
        find_circular_imports,
        find_god_modules,
        find_orphan_modules,
    )

    results: list[CheckResult] = []
    if not content_by_path:
        return results

    graph = build_import_graph(content_by_path)
    if graph.number_of_nodes() == 0:
        return results

    cycles = find_circular_imports(graph)
    gods = find_god_modules(graph, threshold=_GOD_MODULE_FAN_IN)
    orphans = find_orphan_modules(graph)

    if cycles:
        first = cycles[0]
        results.append(CheckResult(
            id="architecture_circular",
            name="Circular imports",
            status="fail",
            evidence={"file": first[0] if first else "—", "snippet": " -> ".join(first)[:EVIDENCE_SNIPPET_MAX]},
            recommendation=_rec(
                what=f"{len(cycles)} circular import chain(s) detected.",
                where=f"e.g. {' -> '.join(first)}",
                why="Circular imports trigger import-time errors, force lazy-import workarounds, and signal that the module boundaries don't match the actual data flow.",
                how="Pull the shared types or constants out into a leaf module that both sides import from. Or merge the two modules if they really do belong together.",
            ),
            points=POINTS_FAIL,
            severity=SEV_HIGH,
            confidence=0.9,
            scope_factor=compute_scope_factor(len(cycles)),
        ))
    else:
        results.append(CheckResult(
            id="architecture_circular",
            name="Circular imports",
            status="pass",
            evidence={"file": "—", "snippet": "No circular imports detected."},
            recommendation=_rec(
                what="No circular imports detected in the import graph.",
                where="Sampled repository contents",
                why="Module boundaries are clean — refactors don't have to chase phantom import-time errors.",
                how="Keep it that way by treating new circular-import errors as a design signal, not a thing to work around with lazy imports.",
            ),
            points=POINTS_PASS,
            severity=SEV_MEDIUM,
            confidence=0.9,
            scope_factor=0.2,
        ))

    if gods:
        results.append(CheckResult(
            id="architecture_god_modules",
            name="God modules",
            status="warn",
            evidence={"file": gods[0], "snippet": f"fan_in > {_GOD_MODULE_FAN_IN}: {', '.join(gods[:5])}"},
            recommendation=_rec(
                what=f"{len(gods)} module(s) imported by more than {_GOD_MODULE_FAN_IN} other files.",
                where=f"e.g. {gods[0]}",
                why="A module that's depended on by half the codebase is a change-blast-radius hazard: every edit risks breaking a long tail of consumers.",
                how="Split the module along internal seams (one file per coherent responsibility), or freeze its public surface and route changes through a stable adapter.",
            ),
            points=POINTS_WARN,
            severity=SEV_MEDIUM,
            confidence=0.8,
            scope_factor=compute_scope_factor(len(gods)),
        ))
    else:
        results.append(CheckResult(
            id="architecture_god_modules",
            name="God modules",
            status="pass",
            evidence={"file": "—", "snippet": f"No modules exceed fan_in={_GOD_MODULE_FAN_IN}."},
            recommendation=_rec(
                what="No god modules: no file is imported by more than the threshold.",
                where="Sampled repository contents",
                why="The blast radius of a typical change is bounded — no single file holds the whole codebase hostage.",
                how="Watch fan-in over time as the codebase grows; the same threshold becomes informative again at a larger scale.",
            ),
            points=POINTS_PASS,
            severity=SEV_LOW,
            confidence=0.8,
            scope_factor=0.2,
        ))

    if orphans:
        # Only warn when there are multiple orphans — a single orphan is often legitimate (script, types-only file).
        many = len(orphans) >= 3
        results.append(CheckResult(
            id="architecture_orphans",
            name="Orphan modules",
            status="warn" if many else "pass",
            evidence={"file": orphans[0], "snippet": f"{len(orphans)} orphan(s): {', '.join(orphans[:5])}"},
            recommendation=_rec(
                what=f"{len(orphans)} module(s) are not imported by any non-entry-point file.",
                where=f"e.g. {orphans[0]}",
                why="An orphan module either is dead code or relies on dynamic loading. Either case is worth flagging before a refactor wastes effort on unused branches.",
                how="For each orphan, decide: delete (dead code), wire it into the codebase explicitly (live but disconnected), or document the dynamic-load path.",
            ),
            points=POINTS_WARN if many else POINTS_PASS,
            severity=SEV_LOW,
            confidence=0.6,
            scope_factor=compute_scope_factor(len(orphans)) if many else 0.2,
        ))
    else:
        results.append(CheckResult(
            id="architecture_orphans",
            name="Orphan modules",
            status="pass",
            evidence={"file": "—", "snippet": "No orphan modules detected."},
            recommendation=_rec(
                what="No orphan modules: every non-entry-point file has at least one importer.",
                where="Sampled repository contents",
                why="The codebase has no dead-code candidates hiding in plain sight — every file is on a live import path.",
                how="Re-run this check after large refactors to surface any newly-disconnected modules.",
            ),
            points=POINTS_PASS,
            severity=SEV_LOW,
            confidence=0.6,
            scope_factor=0.2,
        ))

    return results


def analyze(
    fetch_result: dict[str, Any],
    ingested: dict[str, Any] | None = None,
    content_by_path: dict[str, str] | None = None,
) -> ReportResult:
    fetch_result = fetch_result or {}
    content = content_by_path
    if content is None and ingested:
        content = ingested.get("files") or {}
    sections: list[SectionResult] = []

    run_checks = _runability_checks(fetch_result, content)
    run_score = sum(c.points for c in run_checks)
    sections.append(SectionResult(name="Runability", checks=run_checks, score=run_score))

    eng_checks = _engineering_checks(fetch_result, content)
    eng_score = sum(c.points for c in eng_checks)
    sections.append(SectionResult(name="Engineering Quality", checks=eng_checks, score=eng_score))

    sec_checks = _secrets_checks(fetch_result, content)
    sec_score = sum(c.points for c in sec_checks)
    sections.append(SectionResult(name="Secrets Safety", checks=sec_checks, score=sec_score))

    doc_checks = _documentation_checks(fetch_result, content)
    doc_score = sum(c.points for c in doc_checks)
    sections.append(SectionResult(name="Documentation", checks=doc_checks, score=doc_score))

    code_checks: list[CheckResult] = []
    code_score = 0
    arch_checks: list[CheckResult] = []
    if content:
        code_stats = (ingested.get("stats") or {}) if ingested else {}
        base_code_checks = _code_analysis_checks(content, code_stats)
        complexity_checks = _complexity_checks(content)
        smells_checks = _smells_checks(content)
        deps_checks = _dependency_checks(content)
        arch_checks = _architecture_checks(content)
        code_checks = base_code_checks + complexity_checks + smells_checks + deps_checks
        code_score = sum(c.points for c in code_checks)
        sections.append(SectionResult(name="Code Analysis", checks=code_checks, score=code_score))
        if arch_checks:
            arch_score = sum(c.points for c in arch_checks)
            sections.append(SectionResult(name="Architecture", checks=arch_checks, score=arch_score))

    all_checks = run_checks + eng_checks + sec_checks + doc_checks + code_checks + arch_checks
    overall_score, category_scores = compute_categorical_score(all_checks)

    stack = _detect_stack(fetch_result, content)
    interview_pack = _generate_interview_pack(fetch_result, stack)

    return ReportResult(
        overall_score=overall_score,
        sections=sections,
        interview_pack=interview_pack,
        category_scores=category_scores,
    )
