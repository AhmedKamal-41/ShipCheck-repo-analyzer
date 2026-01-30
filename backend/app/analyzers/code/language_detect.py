"""Language breakdown by file extension. No code execution."""

from collections import Counter

EXT_TO_LANG: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".rb": "Ruby",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".hpp": "C++",
    ".php": "PHP",
    ".swift": "Swift",
    ".md": "Markdown",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
}


def language_breakdown(paths: list[str]) -> dict[str, int]:
    """Return {language: count} by file extension."""
    counts: Counter[str] = Counter()
    for path in paths:
        ext = "." + path.split(".")[-1].lower() if "." in path else ""
        lang = EXT_TO_LANG.get(ext, "Other")
        counts[lang] += 1
    return dict(counts)
