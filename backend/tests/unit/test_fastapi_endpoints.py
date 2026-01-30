"""Unit tests for FastAPI endpoint extraction (AST, no execution)."""

from app.analyzers.code.python_fastapi import extract_fastapi_endpoints


def test_extract_single_get():
    source = """
app = FastAPI()

@app.get("/")
def root():
    return {"hello": "world"}
"""
    result = extract_fastapi_endpoints("main.py", source)
    assert len(result) == 1
    assert result[0].method == "GET"
    assert result[0].path == "/"
    assert result[0].function_name == "root"
    assert result[0].file == "main.py"
    assert result[0].start_line >= 4
    assert result[0].end_line >= result[0].start_line


def test_extract_post_and_get():
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
def list_items():
    pass

@app.post("/items")
def create_item():
    pass
"""
    result = extract_fastapi_endpoints("api/routes.py", source)
    assert len(result) == 2
    methods = {r.method for r in result}
    assert "GET" in methods
    assert "POST" in methods
    paths = {r.path for r in result}
    assert "/items" in paths
    assert all(r.file == "api/routes.py" for r in result)


def test_extract_router():
    source = """
from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}
"""
    result = extract_fastapi_endpoints("routes.py", source)
    assert len(result) == 1
    assert result[0].method == "GET"
    assert result[0].path == "/health"
    assert result[0].function_name == "health"


def test_no_fastapi_no_endpoints():
    source = """
def foo():
    pass
"""
    result = extract_fastapi_endpoints("other.py", source)
    assert len(result) == 0


def test_syntax_error_returns_empty():
    result = extract_fastapi_endpoints("bad.py", "def incomplete(")
    assert result == []
