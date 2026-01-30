"""Rules-based analyzer: fetch_result -> ReportResult (sections, checks, overall_score)."""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Literal

EVIDENCE_SNIPPET_MAX = 200
POINTS_PASS = 10
POINTS_WARN = 5
POINTS_FAIL = 0


@dataclass
class CheckResult:
    id: str
    name: str
    status: Literal["pass", "warn", "fail"]
    evidence: dict[str, Any]  # file, snippet; optional start_line, end_line for code analysis
    recommendation: str
    points: int = 0


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
            recommendation="Add README with install/run instructions.",
            points=POINTS_FAIL,
        ))
    elif has_run_hint:
        results.append(CheckResult(
            id="runability_readme_install_run",
            name="README install/run",
            status="pass",
            evidence={"file": ev_file, "snippet": _truncate(readme_snippet or "")},
            recommendation="README has install/run instructions.",
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="runability_readme_install_run",
            name="README install/run",
            status="warn",
            evidence={"file": ev_file, "snippet": _truncate(readme_snippet or "")},
            recommendation="Add install/run/docker/uvicorn/npm run instructions to README.",
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
            recommendation="Docker support present.",
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="runability_docker",
            name="Docker",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation="Add Dockerfile or docker-compose.yml.",
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
            recommendation="Tests detected.",
            points=POINTS_PASS,
        ))
    elif test_in_workflows:
        results.append(CheckResult(
            id="engineering_tests",
            name="Tests",
            status="warn",
            evidence={"file": wf_ev_path, "snippet": wf_ev_snip},
            recommendation="Tests mentioned in CI but no test folder; add tests/ or __tests__/.",
            points=POINTS_WARN,
        ))
    else:
        results.append(CheckResult(
            id="engineering_tests",
            name="Tests",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation="Add tests and/or test folder (tests/, __tests__/).",
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
            recommendation="CI present.",
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="engineering_ci",
            name="CI",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation="Add .github/workflows.",
            points=POINTS_FAIL,
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
            recommendation="Lint/format present.",
            points=POINTS_PASS,
        ))
    elif scripts_snip or py_snip or req_snip:
        results.append(CheckResult(
            id="engineering_lint_format",
            name="Lint/format",
            status="warn",
            evidence={"file": ev_lint, "snippet": ev_lint_snip},
            recommendation="Add lint/format scripts or config (eslint, prettier, ruff, black).",
            points=POINTS_WARN,
        ))
    else:
        results.append(CheckResult(
            id="engineering_lint_format",
            name="Lint/format",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation="Add lint/format scripts or config.",
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
            recommendation="Dependencies pinned.",
            points=POINTS_PASS,
        ))
    elif has_reqs:
        ev_pin_snip = _truncate(reqs_content)
        results.append(CheckResult(
            id="engineering_pinning",
            name="Dependency pinning",
            status="warn",
            evidence={"file": reqs_path or "requirements.txt", "snippet": ev_pin_snip},
            recommendation="Use lockfiles or pin versions (==) in requirements.txt.",
            points=POINTS_WARN,
        ))
    else:
        results.append(CheckResult(
            id="engineering_pinning",
            name="Dependency pinning",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation="Use lockfiles or pin versions.",
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
            recommendation="Has .env.example.",
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="secrets_env_example",
            name=".env.example",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation="Add .env.example.",
            points=POINTS_FAIL,
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
            recommendation="No obvious secret patterns in sampled files.",
            points=POINTS_PASS,
        ))
    else:
        f, _ = scans[0]
        results.append(CheckResult(
            id="secrets_possible_secrets",
            name="Possible secrets",
            status="warn",
            evidence={"file": f, "snippet": "possible secret – review recommended"},
            recommendation="Remove secrets from repo; use .env and .env.example.",
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
            recommendation="Add a README.",
            points=POINTS_FAIL,
        ))
    elif n >= 500:
        results.append(CheckResult(
            id="documentation_readme_length",
            name="README length",
            status="pass",
            evidence={"file": doc_ev_file, "snippet": f"length={n}"},
            recommendation="README sufficient.",
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="documentation_readme_length",
            name="README length",
            status="warn",
            evidence={"file": doc_ev_file, "snippet": f"length={n}"},
            recommendation="Expand README (e.g. ≥500 chars).",
            points=POINTS_WARN,
        ))

    if not has_doc:
        results.append(CheckResult(
            id="documentation_readme_sections",
            name="README sections",
            status="fail",
            evidence={"file": "—", "snippet": ""},
            recommendation="Add README with Usage/Setup/Installation.",
            points=POINTS_FAIL,
        ))
    elif has_section:
        results.append(CheckResult(
            id="documentation_readme_sections",
            name="README sections",
            status="pass",
            evidence={"file": doc_ev_file, "snippet": _truncate(readme_snippet or "") or f"Found: {doc_ev_file}"},
            recommendation="README has structure.",
            points=POINTS_PASS,
        ))
    else:
        results.append(CheckResult(
            id="documentation_readme_sections",
            name="README sections",
            status="warn",
            evidence={"file": doc_ev_file, "snippet": _truncate(readme_snippet or "") or f"Found: {doc_ev_file}"},
            recommendation="Add Usage/Setup/Installation section.",
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
    checks.append(
        CheckResult(
            id="code_summary",
            name="Code analysis summary",
            status="pass" if bullets else "warn",
            evidence={"file": "—", "snippet": summary_text},
            recommendation="Summary from static analysis (read-only, no execution).",
            points=POINTS_PASS if bullets else POINTS_WARN,
        )
    )

    # Frameworks detected
    frameworks = code_analysis.get("frameworks_detected") or []
    checks.append(
        CheckResult(
            id="code_frameworks",
            name="Frameworks detected",
            status="pass" if frameworks else "warn",
            evidence={"file": "—", "snippet": ", ".join(frameworks) if frameworks else "None"},
            recommendation="Frameworks inferred from code structure." if frameworks else "No framework detected in scanned files.",
            points=POINTS_PASS if frameworks else POINTS_WARN,
        )
    )

    # Endpoint count
    endpoints = code_analysis.get("endpoints") or []
    ep_count = len(endpoints)
    checks.append(
        CheckResult(
            id="code_endpoints",
            name="Endpoints",
            status="pass" if ep_count > 0 else "warn",
            evidence={"file": "—", "snippet": f"{ep_count} endpoint(s) discovered"},
            recommendation=f"Static endpoint discovery (FastAPI/Next/Express)." if ep_count else "No route decorators or API routes found in scanned files.",
            points=POINTS_PASS if ep_count > 0 else POINTS_WARN,
        )
    )

    # Code quality (lint/format/typecheck/test from code analyzers)
    quality_signals = code_analysis.get("quality_signals") or {}
    has_lint = bool(quality_signals.get("lint_format"))
    has_typecheck = bool(quality_signals.get("typecheck"))
    has_tests = bool(quality_signals.get("test_dirs") or quality_signals.get("test_config"))
    quality_ok = has_lint or has_tests
    checks.append(
        CheckResult(
            id="code_quality",
            name="Code quality signals",
            status="pass" if quality_ok else "warn",
            evidence={"file": "—", "snippet": f"Lint/format: {has_lint}; Typecheck: {has_typecheck}; Tests: {has_tests}"},
            recommendation="Lint/format or test config detected in repo." if quality_ok else "Add lint/format or test config for better quality signals.",
            points=POINTS_PASS if quality_ok else POINTS_WARN,
        )
    )

    # Code security (secrets + dangerous patterns)
    security_signals = code_analysis.get("security_signals") or {}
    secret_count = security_signals.get("secret_findings", 0) or 0
    danger_count = security_signals.get("danger_findings", 0) or 0
    security_ok = secret_count == 0 and danger_count == 0
    checks.append(
        CheckResult(
            id="code_security",
            name="Code security",
            status="fail" if secret_count > 0 else ("warn" if danger_count > 0 else "pass"),
            evidence={"file": "—", "snippet": f"Possible secrets: {secret_count}; Dangerous patterns: {danger_count}"},
            recommendation="No high-confidence secrets or dangerous patterns." if security_ok else "Review flagged secrets and dangerous patterns.",
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
        severity = (f.get("severity") or "info").lower()
        status = "fail" if severity == "high" else ("warn" if severity == "medium" else "pass")
        points = POINTS_FAIL if severity == "high" else (POINTS_WARN if severity == "medium" else POINTS_PASS)
        checks.append(
            CheckResult(
                id=f"code_finding_{i}",
                name=f.get("title") or "Finding",
                status=status,
                evidence=evidence_dict,
                recommendation=f.get("description") or "",
                points=points,
            )
        )

    return checks


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
    if content:
        code_stats = (ingested.get("stats") or {}) if ingested else {}
        code_checks = _code_analysis_checks(content, code_stats)
        code_score = sum(c.points for c in code_checks)
        sections.append(SectionResult(name="Code Analysis", checks=code_checks, score=code_score))

    total = run_score + eng_score + sec_score + doc_score + code_score
    all_checks = run_checks + eng_checks + sec_checks + doc_checks + code_checks
    max_possible = 10 * len(all_checks) if all_checks else 1
    overall_score = round(100 * total / max_possible) if max_possible else 0
    overall_score = min(100, max(0, overall_score))

    stack = _detect_stack(fetch_result, content)
    interview_pack = _generate_interview_pack(fetch_result, stack)

    return ReportResult(
        overall_score=overall_score,
        sections=sections,
        interview_pack=interview_pack,
    )
