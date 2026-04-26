"""Declared vs imported dependency analysis for Python and JS/TS. Read-only."""

from __future__ import annotations

import ast
import json
import re
import sys
from typing import Any

_PY_REQ_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*(\[[^\]]*\])?\s*([<>=!~]=?[^;\s#]+(?:\s*,\s*[<>=!~]=?[^;\s#]+)*)?")
_JS_IMPORT_RE = re.compile(r"""(?:import\s+(?:[^'"]*?\s+from\s+)?|require\s*\(\s*|import\s*\(\s*)['"]([^'"]+)['"]""")

_NODE_BUILTINS = frozenset({
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console",
    "constants", "crypto", "dgram", "dns", "domain", "events", "fs", "http",
    "http2", "https", "inspector", "module", "net", "os", "path", "perf_hooks",
    "process", "punycode", "querystring", "readline", "repl", "stream",
    "string_decoder", "sys", "timers", "tls", "tty", "url", "util", "v8",
    "vm", "wasi", "worker_threads", "zlib",
})

_PY_IMPORT_TO_PACKAGE = {
    "yaml": "pyyaml", "cv2": "opencv-python", "PIL": "pillow",
    "sklearn": "scikit-learn", "bs4": "beautifulsoup4", "dotenv": "python-dotenv",
    "jose": "python-jose", "dateutil": "python-dateutil", "magic": "python-magic",
    "psycopg2": "psycopg2-binary",
}


def _normalize_pkg(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def _parse_requirements(content: str) -> tuple[list[str], list[str]]:
    declared, unpinned = [], []
    for raw in (content or "").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("-r", "-e", "-c", "--", "git+", "http://", "https://")):
            continue
        m = _PY_REQ_LINE_RE.match(line)
        if not m:
            continue
        name = _normalize_pkg(m.group(1))
        spec = (m.group(3) or "").strip()
        declared.append(name)
        if "==" not in spec:
            unpinned.append(name)
    return declared, unpinned


def _python_imports(repo_files: dict[str, str]) -> set[str]:
    imported: set[str] = set()
    for path, content in repo_files.items():
        if not path.endswith(".py"):
            continue
        try:
            tree = ast.parse(content or "")
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = (alias.name or "").split(".", 1)[0]
                    if top:
                        imported.add(top)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue
                if node.module:
                    imported.add(node.module.split(".", 1)[0])
    return imported


def _local_python_packages(repo_files: dict[str, str]) -> set[str]:
    local: set[str] = set()
    for path in repo_files:
        pn = path.replace("\\", "/")
        if not pn.endswith(".py"):
            continue
        parts = pn.split("/")
        if len(parts) > 1:
            local.add(parts[0])
        local.add(parts[-1][:-3])
    return local


def _stdlib_names() -> set[str]:
    names = set(getattr(sys, "stdlib_module_names", set()))
    names.update({"__future__", "typing", "typing_extensions"})
    return names


def check_python_deps(repo_files: dict[str, str]) -> dict[str, Any]:
    """Compare requirements.txt declarations against imports across .py files."""
    repo_files = repo_files or {}
    declared, unpinned = _parse_requirements(repo_files.get("requirements.txt") or "")
    declared_set = set(declared)
    imported_top = _python_imports(repo_files)
    stdlib = _stdlib_names()
    local = _local_python_packages(repo_files)

    imported_pkgs: set[str] = set()
    for name in imported_top:
        if name in stdlib or name in local:
            continue
        imported_pkgs.add(_normalize_pkg(_PY_IMPORT_TO_PACKAGE.get(name, name)))

    return {
        "declared": sorted(declared_set),
        "imported": sorted(imported_pkgs),
        "unused": sorted(p for p in declared_set if p not in imported_pkgs),
        "missing": sorted(p for p in imported_pkgs if p not in declared_set),
        "unpinned": sorted(set(unpinned)),
        "pinning_ratio": round((len(declared) - len(unpinned)) / len(declared), 2) if declared else 0.0,
    }


def _parse_package_json(content: str) -> tuple[dict[str, str], dict[str, str]]:
    try:
        data = json.loads(content or "{}")
    except (json.JSONDecodeError, ValueError):
        return {}, {}
    declared: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        block = data.get(key)
        if isinstance(block, dict):
            for name, version in block.items():
                if isinstance(name, str) and isinstance(version, str):
                    declared[name] = version
    unpinned: dict[str, str] = {}
    for name, ver in declared.items():
        v = ver.strip()
        if v.startswith(("^", "~", ">", "<", "*")) or " " in v or "||" in v or "x" in v.lower():
            unpinned[name] = ver
    return declared, unpinned


def _js_imports(repo_files: dict[str, str]) -> set[str]:
    imported: set[str] = set()
    for path, content in repo_files.items():
        if not path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
            continue
        for m in _JS_IMPORT_RE.finditer(content or ""):
            spec = m.group(1)
            if not spec or spec.startswith((".", "/")):
                continue
            if spec.startswith("node:"):
                spec = spec[5:]
            if spec.startswith("@"):
                parts = spec.split("/", 2)
                if len(parts) >= 2:
                    imported.add(f"{parts[0]}/{parts[1]}")
            else:
                imported.add(spec.split("/", 1)[0])
    return imported


def check_js_deps(repo_files: dict[str, str]) -> dict[str, Any]:
    """Compare package.json against import/require statements."""
    repo_files = repo_files or {}
    declared, unpinned = _parse_package_json(repo_files.get("package.json") or "")
    declared_set = set(declared)
    imported = {n for n in _js_imports(repo_files) if n not in _NODE_BUILTINS}
    return {
        "declared": sorted(declared_set),
        "imported": sorted(imported),
        "unused": sorted(p for p in declared_set if p not in imported),
        "missing": sorted(p for p in imported if p not in declared_set),
        "unpinned": sorted(unpinned.keys()),
        "pinning_ratio": round((len(declared) - len(unpinned)) / len(declared), 2) if declared else 0.0,
    }
