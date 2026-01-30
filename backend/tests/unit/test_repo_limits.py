"""Unit tests for repo_limits: should_skip_path, is_text_candidate."""

import pytest

from app.core.repo_limits import is_text_candidate, should_skip_path


def test_should_skip_path_node_modules():
    assert should_skip_path("node_modules/foo/bar.js") is True
    assert should_skip_path("src/node_modules/x") is True


def test_should_skip_path_skip_dirs():
    assert should_skip_path(".git/config") is True
    assert should_skip_path("__pycache__/x.pyc") is True
    assert should_skip_path("dist/bundle.js") is True
    assert should_skip_path("build/out") is True
    assert should_skip_path(".next/cache") is True
    assert should_skip_path(".venv/bin/python") is True
    assert should_skip_path("venv/lib/x") is True


def test_should_skip_path_binary_ext():
    assert should_skip_path("image.png") is True
    assert should_skip_path("doc.pdf") is True
    assert should_skip_path("archive.zip") is True
    assert should_skip_path("file.exe") is True
    assert should_skip_path("lib.so") is True


def test_should_skip_path_minified():
    assert should_skip_path("vendor/jquery.min.js") is True
    assert should_skip_path("static/style.min.css") is True


def test_should_skip_path_egg_info():
    assert should_skip_path("pkg/foo.egg-info/bar") is True


def test_should_skip_path_allows_src_py():
    assert should_skip_path("src/main.py") is False
    assert should_skip_path("app/routes.py") is False


def test_is_text_candidate_python():
    assert is_text_candidate("src/main.py") is True
    assert is_text_candidate("app/__init__.py") is True


def test_is_text_candidate_js_ts():
    assert is_text_candidate("pages/index.tsx") is True
    assert is_text_candidate("lib/utils.js") is True


def test_is_text_candidate_rejects_skip_dirs():
    assert is_text_candidate("node_modules/foo.js") is False
    assert is_text_candidate(".git/HEAD") is False


def test_is_text_candidate_rejects_minified():
    assert is_text_candidate("bundle.min.js") is False
    assert is_text_candidate("style.min.css") is False
