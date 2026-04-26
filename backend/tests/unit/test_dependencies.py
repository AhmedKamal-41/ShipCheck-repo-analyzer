"""Unit tests for declared-vs-imported dependency analysis."""

from app.analyzers.code.dependencies import check_js_deps, check_python_deps


def test_python_unused_dependency_is_flagged():
    repo = {
        "requirements.txt": "fastapi==0.109.0\nrich==13.0.0\nrequests==2.31.0\n",
        "app/main.py": "import fastapi\nfrom fastapi import APIRouter\nimport os\n",
    }
    out = check_python_deps(repo)
    assert "fastapi" in out["declared"]
    assert "fastapi" in out["imported"]
    assert "rich" in out["unused"]
    assert "requests" in out["unused"]
    assert out["pinning_ratio"] == 1.0


def test_python_unpinned_and_pinning_ratio():
    repo = {
        "requirements.txt": "fastapi==0.109.0\nrequests>=2.31\nrich\n",
        "app/main.py": "import fastapi\nimport requests\nimport rich\n",
    }
    out = check_python_deps(repo)
    assert "requests" in out["unpinned"]
    assert "rich" in out["unpinned"]
    assert "fastapi" not in out["unpinned"]
    assert out["pinning_ratio"] == round(1 / 3, 2)


def test_js_missing_dependency_excludes_node_builtins():
    repo = {
        "package.json": '{"dependencies": {"react": "18.2.0"}, "devDependencies": {"jest": "^29.0.0"}}',
        "src/index.ts": (
            "import React from 'react';\n"
            "import _ from 'lodash';\n"
            "import fs from 'fs';\n"
            "import path from 'node:path';\n"
            "import {x} from './local';\n"
        ),
    }
    out = check_js_deps(repo)
    assert "lodash" in out["missing"]
    assert "fs" not in out["missing"]
    assert "path" not in out["missing"]
    assert "react" in out["declared"]
    assert "jest" in out["unpinned"]
    assert "react" not in out["unpinned"]
