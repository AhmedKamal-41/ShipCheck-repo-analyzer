"""Unit tests for code-smell detection."""

from app.analyzers.code.smells import detect_js_smells, detect_python_smells


def test_python_empty_except_is_high_severity():
    src = (
        "def safe():\n"
        "    try:\n"
        "        do_thing()\n"
        "    except Exception:\n"
        "        pass\n"
        "\n"
        "def also():\n"
        "    try:\n"
        "        do_thing()\n"
        "    except:\n"
        "        ...\n"
    )
    smells = detect_python_smells("app/foo.py", src)
    empties = [s for s in smells if s["type"] == "empty_except"]
    assert len(empties) == 2
    assert all(s["severity"] == "high" for s in empties)
    assert {s["line"] for s in empties} == {4, 10}


def test_python_magic_numbers_skip_constants_and_test_files():
    src = (
        "TIMEOUT = 3600\n"
        "MAX_RETRIES = 5\n"
        "def f(x):\n"
        "    if x > 100:\n"
        "        return 200\n"
        "    return 0\n"
    )
    smells = detect_python_smells("app/biz.py", src)
    magic = [s for s in smells if s["type"] == "magic_number"]
    magic_lines = {s["line"] for s in magic}
    assert 1 not in magic_lines
    assert 2 not in magic_lines
    assert 4 in magic_lines or 5 in magic_lines

    smells_test = detect_python_smells("tests/test_biz.py", src)
    assert not any(s["type"] == "magic_number" for s in smells_test)


def test_js_console_log_skipped_in_test_files():
    code = "console.log('debug');\nconsole.error('oops');\n"
    prod = detect_js_smells("src/app.ts", code)
    assert any(s["type"] == "console_log" for s in prod)

    test_file = detect_js_smells("src/app.test.ts", code)
    assert not any(s["type"] == "console_log" for s in test_file)

    spec = detect_js_smells("src/app.spec.ts", code)
    assert not any(s["type"] == "console_log" for s in spec)

    in_tests_dir = detect_js_smells("tests/app.ts", code)
    assert not any(s["type"] == "console_log" for s in in_tests_dir)


def test_js_eval_detected_high_severity():
    src = "function bad() {\n  return eval(userInput);\n}\n"
    smells = detect_js_smells("src/bad.js", src)
    evals = [s for s in smells if s["type"] == "eval_use"]
    assert len(evals) == 1
    assert evals[0]["severity"] == "high"
    assert evals[0]["line"] == 2
