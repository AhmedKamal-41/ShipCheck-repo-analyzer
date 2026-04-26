"""Import-graph based architecture metrics: cycles, fan-in/out, god/orphan modules."""

from __future__ import annotations

import ast
import os
import re

import networkx as nx

_JS_IMPORT_RE = re.compile(r"""(?:import\s+(?:[^'"]*?\s+from\s+)?|require\s*\(\s*|import\s*\(\s*)['"]([^'"]+)['"]""")
_JS_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
_PY_ENTRYPOINTS = frozenset({"main.py", "app.py", "__main__.py", "manage.py", "wsgi.py", "asgi.py"})
_JS_ENTRYPOINTS = frozenset({"index.ts", "index.tsx", "index.js", "index.jsx", "main.ts", "main.js"})


def _normalize(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def _resolve_python_module(module: str, repo_paths: set[str]) -> str | None:
    if not module:
        return None
    base = "/".join(module.split("."))
    if (f := f"{base}.py") in repo_paths:
        return f
    if (f := f"{base}/__init__.py") in repo_paths:
        return f
    return None


def _resolve_relative_import(file_path: str, level: int, module: str | None, repo_paths: set[str]) -> str | None:
    parts = [p for p in os.path.dirname(file_path).replace("\\", "/").split("/") if p]
    if level > len(parts) + 1:
        return None
    base = parts[: max(0, len(parts) - (level - 1))]
    if module:
        target = "/".join(base + module.split("."))
    else:
        target = "/".join(base)
    for cand in (f"{target}.py", f"{target}/__init__.py"):
        if cand in repo_paths:
            return cand
    return None


def _python_edges(file_path: str, content: str, repo_paths: set[str]) -> list[str]:
    edges: list[str] = []
    try:
        tree = ast.parse(content or "")
    except (SyntaxError, ValueError):
        return edges
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                r = _resolve_python_module(alias.name or "", repo_paths)
                if r and r != file_path:
                    edges.append(r)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level or 0
            for alias in node.names or []:
                name = alias.name or ""
                resolved = None
                if level > 0:
                    if name and name != "*":
                        sub = f"{module}.{name}" if module else name
                    else:
                        sub = module
                    resolved = _resolve_relative_import(file_path, level, sub, repo_paths)
                    if not resolved:
                        resolved = _resolve_relative_import(file_path, level, module, repo_paths)
                else:
                    if name and name != "*":
                        resolved = _resolve_python_module(f"{module}.{name}" if module else name, repo_paths)
                    if not resolved:
                        resolved = _resolve_python_module(module, repo_paths)
                if resolved and resolved != file_path:
                    edges.append(resolved)
    return edges


def _resolve_js_specifier(spec: str, file_path: str, repo_paths: set[str]) -> str | None:
    if not spec.startswith((".", "/")):
        return None
    file_dir = os.path.dirname(file_path).replace("\\", "/")
    if spec.startswith("/"):
        base = spec.lstrip("/")
    else:
        base = os.path.normpath(os.path.join(file_dir, spec)).replace("\\", "/").lstrip("./")
    candidates = []
    if "." in os.path.basename(base):
        candidates.append(base)
    candidates.extend(base + ext for ext in _JS_EXTENSIONS)
    candidates.extend(f"{base}/index{ext}" for ext in _JS_EXTENSIONS)
    for c in candidates:
        if c in repo_paths:
            return c
    return None


def _js_edges(file_path: str, content: str, repo_paths: set[str]) -> list[str]:
    edges: list[str] = []
    for m in _JS_IMPORT_RE.finditer(content or ""):
        r = _resolve_js_specifier(m.group(1), file_path, repo_paths)
        if r and r != file_path:
            edges.append(r)
    return edges


def build_import_graph(repo_files: dict[str, str]) -> nx.DiGraph:
    """Build a directed import graph: A -> B means file A imports file B."""
    repo_files = repo_files or {}
    repo_paths: set[str] = {_normalize(p) for p in repo_files}
    graph: nx.DiGraph = nx.DiGraph()
    for path in repo_paths:
        graph.add_node(path)
    for raw_path, content in repo_files.items():
        path = _normalize(raw_path)
        if path.endswith(".py"):
            edges = _python_edges(path, content or "", repo_paths)
        elif path.endswith(_JS_EXTENSIONS):
            edges = _js_edges(path, content or "", repo_paths)
        else:
            continue
        for tgt in edges:
            if tgt in repo_paths:
                graph.add_edge(path, tgt)
    return graph


def find_circular_imports(graph: nx.DiGraph) -> list[list[str]]:
    """Return cycles found in the import graph."""
    if graph is None or graph.number_of_nodes() == 0:
        return []
    try:
        return [list(c) for c in nx.simple_cycles(graph)]
    except Exception:
        return []


def compute_fan_metrics(graph: nx.DiGraph) -> dict[str, dict[str, int]]:
    """Per-node fan_in (incoming) and fan_out (outgoing)."""
    if graph is None or graph.number_of_nodes() == 0:
        return {}
    return {n: {"fan_in": int(graph.in_degree(n)), "fan_out": int(graph.out_degree(n))} for n in graph.nodes()}


def find_god_modules(graph: nx.DiGraph, threshold: int = 20) -> list[str]:
    """Files with fan_in > threshold."""
    if graph is None or graph.number_of_nodes() == 0:
        return []
    return sorted(n for n in graph.nodes() if graph.in_degree(n) > threshold)


def _default_entry_points(graph: nx.DiGraph) -> set[str]:
    return {n for n in graph.nodes() if n.rsplit("/", 1)[-1] in (_PY_ENTRYPOINTS | _JS_ENTRYPOINTS)}


def find_orphan_modules(graph: nx.DiGraph, entry_points: set[str] | None = None) -> list[str]:
    """Files with fan_in == 0 that aren't entry points."""
    if graph is None or graph.number_of_nodes() == 0:
        return []
    entries = set(entry_points) if entry_points else _default_entry_points(graph)
    return sorted(n for n in graph.nodes() if graph.in_degree(n) == 0 and n not in entries)
