"""Quality signals: lint/format/typecheck/test config presence. No execution."""

from typing import Any

LINT_CONFIG_PATHS = frozenset({
    "ruff.toml",
    ".ruff.toml",
    "pyproject.toml",
    "mypy.ini",
    ".mypy.ini",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.json",
    ".eslintrc.yml",
    "eslint.config.js",
    ".prettierrc",
    ".prettierrc.js",
    ".prettierrc.json",
    "prettier.config.js",
})
TEST_DIR_PREFIXES = ("tests/", "__tests__/", "src/test/", "src/tests/")
TEST_CONFIG_NAMES = frozenset({
    "pytest.ini",
    "pyproject.toml",
    "jest.config.js",
    "jest.config.ts",
    "vitest.config.js",
    "vitest.config.ts",
})


def run_quality_analysis(files: dict[str, str]) -> dict[str, Any]:
    """Detect lint/format/typecheck/test presence. Returns quality_signals and findings."""
    paths = set(files.keys())
    paths_lower = {p.replace("\\", "/").lower() for p in paths}

    lint_format: list[str] = []
    typecheck: list[str] = []
    test_dirs: list[str] = []
    test_config: list[str] = []

    for p in paths_lower:
        base = p.split("/")[-1] if "/" in p else p
        if base in LINT_CONFIG_PATHS or p in LINT_CONFIG_PATHS:
            if "mypy" in p or "mypy" in base:
                typecheck.append(p)
            else:
                lint_format.append(p)
        if base in TEST_CONFIG_NAMES:
            test_config.append(p)

    for prefix in TEST_DIR_PREFIXES:
        if any(p == prefix.rstrip("/") or p.startswith(prefix) for p in paths_lower):
            test_dirs.append(prefix.rstrip("/"))

    # Pyproject may contain both [tool.ruff] and [tool.mypy]
    if "pyproject.toml" in paths:
        content = files.get("pyproject.toml") or ""
        if "[tool.mypy]" in content or "mypy" in content.lower():
            if "pyproject.toml" not in typecheck:
                typecheck.append("pyproject.toml")
        if "[tool.ruff]" in content or "black" in content.lower() or "ruff" in content.lower():
            if "pyproject.toml" not in lint_format:
                lint_format.append("pyproject.toml")

    quality_signals = {
        "lint_format": lint_format,
        "typecheck": typecheck,
        "test_dirs": test_dirs,
        "test_config": test_config,
    }

    findings: list[dict[str, Any]] = []
    for p in lint_format[:5]:
        findings.append({
            "title": "Lint/format config",
            "severity": "info",
            "description": "Lint or format configuration detected.",
            "evidence": {"path": p, "snippet": "", "start_line": None, "end_line": None},
        })
    for p in typecheck[:3]:
        findings.append({
            "title": "Typecheck config",
            "severity": "info",
            "description": "Type checker configuration detected.",
            "evidence": {"path": p, "snippet": "", "start_line": None, "end_line": None},
        })
    for d in test_dirs[:3]:
        findings.append({
            "title": "Test directory",
            "severity": "info",
            "description": "Test directory detected.",
            "evidence": {"path": d, "snippet": "", "start_line": None, "end_line": None},
        })

    return {
        "quality_signals": quality_signals,
        "findings": findings,
    }
