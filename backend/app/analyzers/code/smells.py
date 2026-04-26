"""Code smell detection: empty excepts, TODOs, prints, magic numbers, console.log, eval, http URLs."""

from __future__ import annotations

import ast
import re
from typing import Any

_TODO_RE = re.compile(r"\b(TODO|FIXME|XXX)\b")
_PY_PRINT_RE = re.compile(r"^\s*print\s*\(")
_JS_CONSOLE_RE = re.compile(r"\bconsole\.(log|warn|error|info|debug)\s*\(")
_JS_EVAL_RE = re.compile(r"\beval\s*\(")
_HTTP_URL_RE = re.compile(r"['\"`](http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^'\"`\s]+)['\"`]")

_PY_TEST_DIR_PREFIXES = ("tests/", "test/", "src/test/", "src/tests/")
_JS_TEST_PATTERNS = ("/tests/", "/__tests__/", ".test.", ".spec.")


def _is_python_script_file(path: str) -> bool:
    pn = path.replace("\\", "/").lower()
    return pn.startswith("scripts/") or "/scripts/" in pn or pn.endswith(("_cli.py", "/cli.py"))


def _is_python_test_file(path: str) -> bool:
    pn = path.replace("\\", "/").lower()
    base = pn.rsplit("/", 1)[-1]
    if base.startswith("test_") or base.endswith("_test.py") or base == "conftest.py":
        return True
    return any(pn.startswith(p) or f"/{p}" in pn for p in _PY_TEST_DIR_PREFIXES)


def _is_js_test_file(path: str) -> bool:
    pn = path.replace("\\", "/").lower()
    return any(p in pn for p in _JS_TEST_PATTERNS) or pn.startswith("tests/")


def _line_text(lines: list[str], lineno: int) -> str:
    return lines[lineno - 1].rstrip() if 1 <= lineno <= len(lines) else ""


def _empty_except_smells(tree: ast.AST, lines: list[str]) -> list[dict[str, Any]]:
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        body = node.body or []
        only_pass = len(body) == 1 and isinstance(body[0], ast.Pass)
        only_ellipsis = (
            len(body) == 1 and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant) and body[0].value.value is Ellipsis
        )
        if only_pass or only_ellipsis:
            ln = node.lineno
            out.append({"type": "empty_except", "line": ln, "snippet": _line_text(lines, ln)[:200], "severity": "high"})
    return out


def _todo_smells(lines: list[str]) -> list[dict[str, Any]]:
    return [
        {"type": "todo", "line": i, "snippet": line.strip()[:200], "severity": "low"}
        for i, line in enumerate(lines, start=1) if _TODO_RE.search(line)
    ]


def _print_smells(file_path: str, lines: list[str]) -> list[dict[str, Any]]:
    if _is_python_script_file(file_path):
        return []
    return [
        {"type": "print_statement", "line": i, "snippet": line.strip()[:200], "severity": "low"}
        for i, line in enumerate(lines, start=1) if _PY_PRINT_RE.match(line)
    ]


def _magic_number_smells(file_path: str, tree: ast.AST, lines: list[str]) -> list[dict[str, Any]]:
    if _is_python_test_file(file_path):
        return []
    constant_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isupper():
                    constant_lines.add(node.lineno)
                    break
    out, seen = [], set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            continue
        ln = getattr(node, "lineno", 0) or 0
        if ln in constant_lines:
            continue
        if isinstance(node.value, int) and node.value in (0, 1, -1, 2):
            continue
        if isinstance(node.value, float) and node.value in (0.0, 1.0):
            continue
        key = (ln, repr(node.value))
        if key in seen:
            continue
        seen.add(key)
        out.append({"type": "magic_number", "line": ln, "snippet": _line_text(lines, ln)[:200] or repr(node.value), "severity": "low"})
    return out


def detect_python_smells(file_path: str, content: str) -> list[dict[str, Any]]:
    """Return list of smells for one Python file. Empty list on parse failure (regex-only fallback)."""
    if not content:
        return []
    lines = content.splitlines()
    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return _todo_smells(lines) + _print_smells(file_path, lines)
    out = []
    out.extend(_empty_except_smells(tree, lines))
    out.extend(_todo_smells(lines))
    out.extend(_print_smells(file_path, lines))
    out.extend(_magic_number_smells(file_path, tree, lines))
    return out


def detect_js_smells(file_path: str, content: str) -> list[dict[str, Any]]:
    """Return list of smells for one JS/TS file."""
    if not content:
        return []
    lines = content.splitlines()
    is_test = _is_js_test_file(file_path)
    out = []
    for i, line in enumerate(lines, start=1):
        if not is_test and _JS_CONSOLE_RE.search(line):
            out.append({"type": "console_log", "line": i, "snippet": line.strip()[:200], "severity": "low"})
        if _JS_EVAL_RE.search(line):
            out.append({"type": "eval_use", "line": i, "snippet": line.strip()[:200], "severity": "high"})
        if _TODO_RE.search(line):
            out.append({"type": "todo", "line": i, "snippet": line.strip()[:200], "severity": "low"})
        if _HTTP_URL_RE.search(line):
            out.append({"type": "http_url", "line": i, "snippet": line.strip()[:200], "severity": "medium"})
    return out
