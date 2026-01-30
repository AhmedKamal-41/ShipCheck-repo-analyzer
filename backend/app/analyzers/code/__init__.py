"""Code analyzers: language, frameworks, endpoints, quality, security. No code execution."""

from typing import Any

from app.analyzers.code import js_routes, language_detect, python_fastapi, quality, security


def run_code_analysis(files: dict[str, str], stats: dict | None = None) -> dict[str, Any]:
    """Run all code analyzers on ingested files. Returns unified code_analysis structure."""
    paths = list(files.keys())
    lang = language_detect.language_breakdown(paths)
    fastapi_out = python_fastapi.run_fastapi_analysis(files)
    js_out = js_routes.run_js_routes_analysis(files)
    quality_out = quality.run_quality_analysis(files)
    security_out = security.run_security_analysis(files)

    frameworks: list[str] = []
    seen_fw = set()
    for f in fastapi_out.get("frameworks_detected") or []:
        if f not in seen_fw:
            frameworks.append(f)
            seen_fw.add(f)
    for f in js_out.get("frameworks_detected") or []:
        if f not in seen_fw:
            frameworks.append(f)
            seen_fw.add(f)

    endpoints: list[dict[str, Any]] = []
    for ep in fastapi_out.get("endpoints") or []:
        ep["framework"] = "FastAPI"
        endpoints.append(ep)
    for ep in js_out.get("endpoints") or []:
        endpoints.append(ep)

    # Architecture summary: entrypoints, routers, services, db (simple heuristics from paths)
    entrypoints: list[str] = []
    routers: list[str] = []
    services: list[str] = []
    db_hints: list[str] = []
    for p in paths:
        pn = p.replace("\\", "/").lower()
        if "main.py" in pn or "app.py" in pn or "index.js" in pn or "index.ts" in pn:
            entrypoints.append(p)
        if "router" in pn or "routes" in pn:
            routers.append(p)
        if "service" in pn:
            services.append(p)
        if "model" in pn or "database" in pn or "db" in pn or "migrate" in pn:
            db_hints.append(p)
    architecture_summary = {
        "entrypoints": entrypoints[:10],
        "routers": routers[:15],
        "services": services[:15],
        "db_related": db_hints[:10],
    }

    # Summary bullets
    summary_bullets: list[str] = []
    if lang:
        lang_str = ", ".join(f"{k}: {v}" for k, v in sorted(lang.items(), key=lambda x: -x[1])[:8])
        summary_bullets.append(f"Languages: {lang_str}")
    if frameworks:
        summary_bullets.append(f"Frameworks: {', '.join(frameworks)}")
    summary_bullets.append(f"Endpoints: {len(endpoints)}")
    if stats and stats.get("truncated"):
        summary_bullets.append("Truncated due to limits.")

    # Collect all findings with evidence shape path, start_line, end_line, snippet
    findings: list[dict[str, Any]] = []
    for f in quality_out.get("findings") or []:
        ev = f.get("evidence") or {}
        findings.append({
            "title": f.get("title", ""),
            "severity": f.get("severity", "info"),
            "description": f.get("description", ""),
            "evidence": {
                "path": ev.get("path", ""),
                "start_line": ev.get("start_line"),
                "end_line": ev.get("end_line"),
                "snippet": ev.get("snippet", ""),
            },
        })
    for f in security_out.get("findings") or []:
        ev = f.get("evidence") or {}
        findings.append({
            "title": f.get("title", ""),
            "severity": f.get("severity", "medium"),
            "description": f.get("description", ""),
            "evidence": {
                "path": ev.get("path", ""),
                "start_line": ev.get("start_line"),
                "end_line": ev.get("end_line"),
                "snippet": ev.get("snippet", ""),
            },
        })

    return {
        "summary_bullets": summary_bullets,
        "language_breakdown": lang,
        "frameworks_detected": frameworks,
        "endpoints": endpoints,
        "architecture_summary": architecture_summary,
        "quality_signals": quality_out.get("quality_signals") or {},
        "security_signals": security_out.get("security_signals") or {},
        "findings": findings,
    }
