"""Unit tests for complexity analyzer (Python via radon, JS/TS via tree-sitter)."""

from app.analyzers.code.complexity import parse_js_complexity, parse_python_complexity


def test_parse_python_complexity_happy_path():
    src = (
        "def small(x):\n"
        "    return x\n"
        "\n"
        "def branchy(x, y):\n"
        "    if x > 0:\n"
        "        if y > 0:\n"
        "            return 1\n"
        "        return 2\n"
        "    elif x < 0:\n"
        "        return 3\n"
        "    return 0\n"
    )
    out = parse_python_complexity("a.py", src)
    names = {f["name"]: f for f in out["functions"]}
    assert "small" in names and "branchy" in names
    assert names["small"]["complexity"] == 1
    assert names["branchy"]["complexity"] >= 4
    fm = out["file_metrics"]
    assert fm["max_complexity"] == names["branchy"]["complexity"]
    assert fm["loc"] > 0
    assert fm["avg_complexity"] > 0


def test_parse_python_complexity_parse_failure_returns_empty():
    out = parse_python_complexity("a.py", "def (((( bad python")
    assert out["functions"] == []
    assert out["file_metrics"]["max_complexity"] == 0
    assert out["file_metrics"]["avg_complexity"] == 0.0


def test_parse_js_complexity_happy_path():
    src = (
        "function add(a, b) {\n"
        "  if (a > 0) {\n"
        "    for (let i = 0; i < 10; i++) { console.log(i); }\n"
        "  }\n"
        "  return a + b;\n"
        "}\n"
        "const arrow = (x) => x * 2;\n"
    )
    out = parse_js_complexity("a.ts", src, "typescript")
    assert out["function_count"] == 2
    names = {f["name"] for f in out["functions"]}
    assert "add" in names
    assert "arrow" in names
    add_fn = next(f for f in out["functions"] if f["name"] == "add")
    assert add_fn["max_nesting"] >= 2
    assert add_fn["lines"] >= 5


def test_complexity_edge_cases_return_empty_safely():
    assert parse_python_complexity("a.py", "")["functions"] == []
    assert parse_python_complexity("a.py", "   \n  \n")["functions"] == []
    assert parse_js_complexity("a.go", "x := 1", "go") == {"function_count": 0, "functions": [], "any_count": 0}
    assert parse_js_complexity("a.ts", "", "typescript")["function_count"] == 0
    # method inside class — name comes from method_definition parent
    cls = "class A {\n  greet(name: string) {\n    return name;\n  }\n}\n"
    out = parse_js_complexity("a.ts", cls, "typescript")
    assert any(f["name"] == "greet" for f in out["functions"])


def test_parse_js_complexity_typescript_any_count():
    src = (
        "function f(x: any): any {\n"
        "  const y: any = x;\n"
        "  return y as any;\n"
        "}\n"
        "const g = (z: number) => z;\n"
    )
    out_ts = parse_js_complexity("a.ts", src, "typescript")
    assert out_ts["any_count"] >= 3

    out_js = parse_js_complexity("a.js", "const x = 1; var y = 2;", "javascript")
    assert out_js["any_count"] == 0
