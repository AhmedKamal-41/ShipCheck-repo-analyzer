"""Complexity analysis: radon for Python, tree-sitter for JS/TS. Read-only, no execution."""

from __future__ import annotations

import warnings
from typing import Any

_EMPTY_PY: dict[str, Any] = {
    "functions": [],
    "file_metrics": {"loc": 0, "comments": 0, "blanks": 0, "max_complexity": 0, "avg_complexity": 0.0},
}
_EMPTY_JS: dict[str, Any] = {"function_count": 0, "functions": [], "any_count": 0}

_JS_FUNCTION_NODES = frozenset({
    "function_declaration", "function_expression", "arrow_function",
    "method_definition", "generator_function_declaration", "generator_function",
})
_JS_NESTING_NODES = frozenset({
    "if_statement", "for_statement", "for_in_statement", "for_of_statement",
    "while_statement", "do_statement", "switch_statement", "try_statement", "catch_clause",
})


def parse_python_complexity(file_path: str, content: str) -> dict[str, Any]:
    """Cyclomatic complexity + raw metrics for one Python file. Empty dict on failure."""
    try:
        from radon.complexity import cc_visit
        from radon.raw import analyze
    except Exception:
        return _EMPTY_PY
    if not content or not content.strip():
        return _EMPTY_PY

    try:
        cc_blocks = cc_visit(content)
    except Exception:
        cc_blocks = []

    functions, complexities = [], []
    for block in cc_blocks or []:
        cx = int(getattr(block, "complexity", 0) or 0)
        start = int(getattr(block, "lineno", 0) or 0)
        end = int(getattr(block, "endline", start) or start)
        functions.append({
            "name": getattr(block, "name", "") or "",
            "complexity": cx,
            "lines": max(0, end - start + 1) if start else 0,
            "start_line": start,
        })
        complexities.append(cx)

    try:
        raw = analyze(content)
        loc = int(getattr(raw, "loc", 0) or 0)
        comments = int(getattr(raw, "comments", 0) or 0)
        blanks = int(getattr(raw, "blank", 0) or 0)
    except Exception:
        loc, comments, blanks = 0, 0, 0

    max_cx = max(complexities) if complexities else 0
    avg_cx = (sum(complexities) / len(complexities)) if complexities else 0.0
    return {
        "functions": functions,
        "file_metrics": {
            "loc": loc, "comments": comments, "blanks": blanks,
            "max_complexity": max_cx, "avg_complexity": round(avg_cx, 2),
        },
    }


def _walk(node: Any):
    yield node
    for child in getattr(node, "children", []) or []:
        yield from _walk(child)


def _node_text(node: Any, src: bytes) -> str:
    try:
        return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
    except Exception:
        return ""


def _function_name(node: Any, src: bytes) -> str:
    try:
        nf = node.child_by_field_name("name")
    except Exception:
        nf = None
    if nf is not None:
        return _node_text(nf, src)
    parent = getattr(node, "parent", None)
    if parent is not None and parent.type in {"variable_declarator", "assignment_expression", "pair", "method_definition"}:
        try:
            lhs = parent.child_by_field_name("name") or parent.child_by_field_name("key")
        except Exception:
            lhs = None
        if lhs is not None:
            return _node_text(lhs, src)
    return "<anonymous>"


def _max_nesting(node: Any) -> int:
    def helper(n: Any, depth: int) -> int:
        best = depth
        for child in getattr(n, "children", []) or []:
            if child.type in _JS_FUNCTION_NODES and child is not node:
                continue
            d = depth + 1 if child.type in _JS_NESTING_NODES else depth
            best = max(best, helper(child, d))
        return best
    return helper(node, 0)


def _has_any_keyword(node: Any) -> bool:
    for n in _walk(node):
        if n.type == "any":
            return True
        if n.type == "predefined_type":
            for c in getattr(n, "children", []) or []:
                if c.type == "any":
                    return True
    return False


def _count_any_types(root: Any, src: bytes) -> int:
    count = 0
    for n in _walk(root):
        if n.type == "type_annotation" and "any" in _node_text(n, src) and _has_any_keyword(n):
            count += 1
        elif n.type in {"as_expression", "type_assertion"} and _has_any_keyword(n):
            count += 1
    return count


def parse_js_complexity(file_path: str, content: str, language: str) -> dict[str, Any]:
    """JS/TS function metrics via tree-sitter. Empty dict on failure."""
    if not content:
        return _EMPTY_JS
    lang = (language or "").lower()
    if lang not in {"javascript", "typescript", "tsx"}:
        return _EMPTY_JS
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from tree_sitter_languages import get_parser
            parser = get_parser(lang)
    except Exception:
        return _EMPTY_JS
    try:
        src = content.encode("utf-8", errors="replace")
        tree = parser.parse(src)
    except Exception:
        return _EMPTY_JS

    functions = []
    for node in _walk(tree.root_node):
        if node.type not in _JS_FUNCTION_NODES:
            continue
        s, e = node.start_point[0] + 1, node.end_point[0] + 1
        functions.append({
            "name": _function_name(node, src),
            "lines": max(1, e - s + 1),
            "max_nesting": _max_nesting(node),
            "start_line": s,
        })

    any_count = 0
    if lang in {"typescript", "tsx"}:
        try:
            any_count = _count_any_types(tree.root_node, src)
        except Exception:
            any_count = 0
    return {"function_count": len(functions), "functions": functions, "any_count": any_count}
