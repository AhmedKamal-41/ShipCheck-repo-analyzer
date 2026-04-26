"""Unit tests for the import-graph architecture analyzer."""

from app.analyzers.code.architecture import (
    build_import_graph,
    compute_fan_metrics,
    find_circular_imports,
    find_god_modules,
    find_orphan_modules,
)


def test_build_import_graph_resolves_python_and_js_edges():
    repo = {
        "app/main.py": "from app.services import worker\nimport app.utils\n",
        "app/services.py": "from app import utils\n",
        "app/utils.py": "VAL = 1\n",
        "src/index.ts": "import {a} from './lib/foo';\nimport {b} from './lib/bar';\n",
        "src/lib/foo.ts": "export const a = 1;\n",
        "src/lib/bar.ts": "export const b = 2;\n",
    }
    g = build_import_graph(repo)
    edges = set(g.edges())
    assert ("app/main.py", "app/services.py") in edges
    assert ("app/main.py", "app/utils.py") in edges
    assert ("app/services.py", "app/utils.py") in edges
    assert ("src/index.ts", "src/lib/foo.ts") in edges
    assert ("src/index.ts", "src/lib/bar.ts") in edges
    # third-party imports must NOT appear as edges
    repo2 = {"a.py": "import requests\nimport networkx\n"}
    g2 = build_import_graph(repo2)
    assert g2.number_of_edges() == 0


def test_find_circular_imports_detects_cycle():
    repo = {
        "pkg/a.py": "from pkg import b\n",
        "pkg/b.py": "from pkg import c\n",
        "pkg/c.py": "from pkg import a\n",
    }
    g = build_import_graph(repo)
    cycles = find_circular_imports(g)
    assert len(cycles) == 1
    assert set(cycles[0]) == {"pkg/a.py", "pkg/b.py", "pkg/c.py"}

    no_cycle = build_import_graph({"a.py": "x = 1", "b.py": "import a"})
    assert find_circular_imports(no_cycle) == []


def test_compute_fan_metrics():
    repo = {
        "app/main.py": "from app.services import s\n",
        "app/services.py": "from app import utils\n",
        "app/utils.py": "x = 1\n",
    }
    g = build_import_graph(repo)
    fan = compute_fan_metrics(g)
    assert fan["app/main.py"]["fan_out"] == 1
    assert fan["app/main.py"]["fan_in"] == 0
    assert fan["app/services.py"]["fan_out"] == 1
    assert fan["app/services.py"]["fan_in"] == 1
    assert fan["app/utils.py"]["fan_in"] == 1
    assert fan["app/utils.py"]["fan_out"] == 0


def test_relative_imports_and_empty_graph_edge_cases():
    repo = {
        "pkg/__init__.py": "",
        "pkg/sub/__init__.py": "",
        "pkg/sub/a.py": "from . import b\nfrom ..top import shared\n",
        "pkg/sub/b.py": "x = 1\n",
        "pkg/top.py": "shared = 1\n",
        "pkg/bad.py": "def (((( malformed\n",
    }
    g = build_import_graph(repo)
    edges = set(g.edges())
    assert ("pkg/sub/a.py", "pkg/sub/b.py") in edges
    assert ("pkg/sub/a.py", "pkg/top.py") in edges

    empty = build_import_graph({})
    assert find_circular_imports(empty) == []
    assert compute_fan_metrics(empty) == {}
    assert find_god_modules(empty) == []
    assert find_orphan_modules(empty) == []


def test_js_specifier_resolution_variants():
    repo = {
        "src/index.ts": "import a from '/lib/foo';\nimport b from './bar.js';\n",
        "src/bar.js": "export const b = 1;\n",
        "lib/foo.ts": "export const a = 1;\n",
    }
    g = build_import_graph(repo)
    edges = set(g.edges())
    assert ("src/index.ts", "lib/foo.ts") in edges
    assert ("src/index.ts", "src/bar.js") in edges


def test_find_god_modules_and_orphans():
    importers = {f"app/m{i}.py": "from app import shared\n" for i in range(5)}
    repo = {**importers, "app/shared.py": "VALUE = 1\n", "app/lonely.py": "x = 1\n", "app/main.py": "from app import shared\n"}
    g = build_import_graph(repo)
    gods = find_god_modules(g, threshold=3)
    assert "app/shared.py" in gods
    orphans = find_orphan_modules(g)
    assert "app/lonely.py" in orphans
    assert "app/main.py" not in orphans  # entry point
    for i in range(5):
        assert f"app/m{i}.py" in orphans  # not entry points; nothing imports them
