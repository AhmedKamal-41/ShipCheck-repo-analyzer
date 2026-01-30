"""Unit tests for security analyzer: secret scan false positives minimized."""

from app.analyzers.code.security import run_security_analysis


def test_no_false_positive_on_example_placeholder():
    """Placeholder or example key should not be flagged (high-confidence only)."""
    files = {
        "config.py": "API_KEY = 'your-api-key-here'  # replace with real key",
        "README.md": "Set API_KEY=example in .env",
    }
    result = run_security_analysis(files)
    findings = result.get("findings") or []
    secret_titles = [f["title"] for f in findings if "secret" in f.get("title", "").lower()]
    assert len(secret_titles) == 0


def test_ghp_token_flagged():
    """High-confidence ghp_ token pattern (with api_key=) should be flagged."""
    files = {
        "env.py": "api_key=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    }
    result = run_security_analysis(files)
    findings = result.get("findings") or []
    assert any("ghp_" in (f.get("evidence") or {}).get("snippet", "") for f in findings)


def test_private_key_header_flagged():
    """Private key header should be flagged."""
    files = {
        "key.pem": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...",
    }
    result = run_security_analysis(files)
    findings = result.get("findings") or []
    assert any("PRIVATE KEY" in (f.get("evidence") or {}).get("snippet", "") for f in findings)


def test_eval_flagged():
    """eval() use should be flagged as dangerous pattern."""
    files = {
        "script.py": "result = eval(user_input)",
    }
    result = run_security_analysis(files)
    findings = result.get("findings") or []
    assert any("eval" in (f.get("title") or "").lower() for f in findings)


def test_clean_file_no_findings():
    """Clean code should yield no security findings."""
    files = {
        "main.py": "def hello():\n    return 'world'",
    }
    result = run_security_analysis(files)
    findings = result.get("findings") or []
    assert len(findings) == 0
