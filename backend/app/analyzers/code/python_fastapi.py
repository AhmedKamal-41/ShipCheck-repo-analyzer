"""FastAPI endpoint discovery via Python ast. No code execution."""

import ast
from dataclasses import dataclass
from typing import Any


@dataclass
class EndpointInfo:
    method: str
    path: str
    function_name: str
    file: str
    start_line: int
    end_line: int
    snippet: str


HTTP_METHODS = frozenset({"get", "post", "put", "delete", "patch", "head", "options"})


def _get_decorator_route(node: ast.FunctionDef, app_var_names: set[str]) -> tuple[str, str] | None:
    """If node is decorated with app.get(path) / router.post(path), return (method, path)."""
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        if isinstance(func, ast.Attribute):
            # app.get, router.post
            if isinstance(func.value, ast.Name):
                var_name = func.value.id
                if var_name in app_var_names and func.attr in HTTP_METHODS:
                    path = ""
                    if dec.args:
                        arg0 = dec.args[0]
                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            path = arg0.value
                    return (func.attr.upper(), path or "/")
    return None


def _find_fastapi_app_names(tree: ast.AST) -> set[str]:
    """Find variable names assigned from FastAPI() call."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    if isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Name):
                            if node.value.func.id == "FastAPI":
                                names.add(t.id)
                        if isinstance(node.value.func, ast.Attribute):
                            if node.value.func.attr == "FastAPI":
                                names.add(t.id)
        # router = APIRouter() then app.include_router(router) -> router is also a route holder
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    if isinstance(node.value, ast.Call):
                        func = node.value.func
                        if isinstance(func, ast.Name) and func.id == "APIRouter":
                            names.add(t.id)
                        if isinstance(func, ast.Attribute) and func.attr == "APIRouter":
                            names.add(t.id)
    return names


def extract_fastapi_endpoints(file_path: str, source: str) -> list[EndpointInfo]:
    """Parse Python source and return list of FastAPI/APIRouter endpoints."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    app_names = _find_fastapi_app_names(tree)
    if not app_names:
        return []

    lines = source.splitlines()
    results: list[EndpointInfo] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            route = _get_decorator_route(node, app_names)
            if not route:
                continue
            method, path = route
            start = node.lineno
            end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start
            snippet_lines = lines[start - 1 : end] if lines else []
            snippet = "\n".join(snippet_lines)[:500]

            results.append(
                EndpointInfo(
                    method=method,
                    path=path,
                    function_name=node.name,
                    file=file_path,
                    start_line=start,
                    end_line=end,
                    snippet=snippet,
                )
            )

    return results


def run_fastapi_analysis(files: dict[str, str]) -> dict[str, Any]:
    """Run on all .py files. Returns {endpoints: [...], frameworks_detected: [...]}."""
    all_endpoints: list[dict[str, Any]] = []
    for path, content in files.items():
        if not path.endswith(".py"):
            continue
        for ep in extract_fastapi_endpoints(path, content):
            all_endpoints.append({
                "method": ep.method,
                "path": ep.path,
                "function_name": ep.function_name,
                "file": ep.file,
                "start_line": ep.start_line,
                "end_line": ep.end_line,
                "snippet": ep.snippet,
            })

    frameworks = []
    if all_endpoints:
        frameworks.append("FastAPI")

    return {
        "endpoints": all_endpoints,
        "frameworks_detected": frameworks,
    }
