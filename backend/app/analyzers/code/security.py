"""Security: high-confidence secret patterns and dangerous code patterns. No execution."""

import re
from typing import Any

# High-confidence only to minimize false positives
SECRET_PATTERNS = [
    (re.compile(r"(?:^|\s)(?:AWS_SECRET_ACCESS_KEY|aws_secret_access_key)\s*=\s*['\"]?(AKIA[0-9A-Z]{16})['\"]?", re.M), "AWS secret key"),
    (re.compile(r"(?:^|\s)(?:api_key|apikey|api-key)\s*=\s*['\"]?(ghp_[a-zA-Z0-9]{36,})['\"]?", re.M), "GitHub token (ghp_)"),
    (re.compile(r"(?:^|\s)(?:api_key|apikey)\s*=\s*['\"]?(sk-[a-zA-Z0-9]{20,})['\"]?", re.M), "API key (sk-)"),
    (re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"), "Private key"),
    (re.compile(r"(?:^|\s)password\s*=\s*['\"][^'\"]{8,}['\"]", re.M | re.I), "Hardcoded password"),
]

DANGEROUS_PATTERNS = [
    (re.compile(r"\beval\s*\("), "eval() use"),
    (re.compile(r"\bexec\s*\("), "exec() use"),
    (re.compile(r"subprocess\.(run|call|Popen)\s*\([^)]*shell\s*=\s*True"), "subprocess with shell=True"),
    (re.compile(r"pickle\.loads\s*\([^)]*\)"), "pickle.loads (untrusted input risk)"),
]


def _snippet_from_lines(content: str, start_line: int, end_line: int, max_len: int = 300) -> str:
    lines = content.splitlines()
    if not lines:
        return ""
    start = max(0, start_line - 1)
    end = min(len(lines), end_line)
    chunk = "\n".join(lines[start:end])
    return chunk[:max_len] + ("..." if len(chunk) > max_len else "")


def run_security_analysis(files: dict[str, str]) -> dict[str, Any]:
    """Scan for secrets and dangerous patterns. Returns security_signals and findings."""
    findings: list[dict[str, Any]] = []

    for path, content in files.items():
        lines = content.splitlines()
        for pattern, label in SECRET_PATTERNS:
            for i, line in enumerate(lines):
                if pattern.search(line):
                    start_line = i + 1
                    end_line = i + 1
                    snippet = _snippet_from_lines(content, start_line, end_line, 200)
                    findings.append({
                        "title": f"Possible secret: {label}",
                        "severity": "high",
                        "description": f"High-confidence secret pattern detected: {label}.",
                        "evidence": {
                            "path": path,
                            "start_line": start_line,
                            "end_line": end_line,
                            "snippet": snippet,
                        },
                    })
                    break  # one finding per file per pattern

        for pattern, label in DANGEROUS_PATTERNS:
            for i, line in enumerate(lines):
                if pattern.search(line):
                    start_line = i + 1
                    end_line = i + 1
                    snippet = _snippet_from_lines(content, start_line, end_line, 200)
                    findings.append({
                        "title": f"Dangerous pattern: {label}",
                        "severity": "medium",
                        "description": f"Potentially dangerous pattern: {label}. Review for untrusted input.",
                        "evidence": {
                            "path": path,
                            "start_line": start_line,
                            "end_line": end_line,
                            "snippet": snippet,
                        },
                    })
                    break

    return {
        "security_signals": {"secret_findings": len([f for f in findings if f.get("severity") == "high"]),
                           "danger_findings": len([f for f in findings if f.get("severity") == "medium"])},
        "findings": findings,
    }
