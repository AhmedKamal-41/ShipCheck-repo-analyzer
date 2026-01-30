"""JS/TS route detection: Next.js and Express heuristics. No full parse, no execution."""

import re
from typing import Any

NEXT_API_PREFIXES = ("pages/api/", "app/api/")
EXPRESS_PATTERN = re.compile(
    r"(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*[\"']([^\"']*)[\"']",
    re.IGNORECASE,
)


def _next_routes_from_path(file_path: str) -> list[dict[str, Any]]:
    """Infer route from file path for Next.js API routes."""
    path = file_path.replace("\\", "/")
    route_path = ""
    if path.startswith("pages/api/"):
        # pages/api/foo/bar.ts -> /api/foo/bar
        route_path = "/" + path[9:]  # strip "pages"
        # remove file extension and [param]
        parts = route_path.rsplit(".", 1)
        if len(parts) == 2:
            route_path = parts[0]
        return [{"method": "GET", "path": route_path, "file": file_path, "framework": "Next.js"}]
    if path.startswith("app/api/"):
        # app/api/foo/route.ts -> /api/foo
        rest = path[8:]  # after "app/api/"
        if "/" in rest:
            route_path = "/api/" + rest.split("/")[0]
        else:
            route_path = "/api/" + rest
        parts = route_path.rsplit(".", 1)
        if len(parts) == 2:
            route_path = parts[0]
        return [{"method": "GET", "path": route_path, "file": file_path, "framework": "Next.js"}]
    return []


def _express_routes_from_content(file_path: str, content: str) -> list[dict[str, Any]]:
    """Heuristic scan for router.get("/path") or app.post("/path")."""
    results: list[dict[str, Any]] = []
    lines = content.splitlines()
    for i, line in enumerate(lines):
        for m in EXPRESS_PATTERN.finditer(line):
            method = (m.group(1) or "get").upper()
            path = m.group(2) or "/"
            results.append({
                "method": method,
                "path": path,
                "file": file_path,
                "start_line": i + 1,
                "end_line": i + 1,
                "snippet": line.strip()[:300],
                "framework": "Express",
            })
    return results


def run_js_routes_analysis(files: dict[str, str]) -> dict[str, Any]:
    """Run Next.js path convention + Express regex. Returns {endpoints: [...], frameworks_detected: [...]}."""
    endpoints: list[dict[str, Any]] = []
    frameworks: list[str] = []

    for path, content in files.items():
        path_n = path.replace("\\", "/")
        if path_n.startswith(NEXT_API_PREFIXES):
            for ep in _next_routes_from_path(path):
                endpoints.append(ep)
                if "Next.js" not in frameworks:
                    frameworks.append("Next.js")

        if path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
            express_eps = _express_routes_from_content(path, content)
            for ep in express_eps:
                endpoints.append(ep)
                if "Express" not in frameworks:
                    frameworks.append("Express")

    return {
        "endpoints": endpoints,
        "frameworks_detected": frameworks,
    }
