"""Unit tests for repo_content: batch_fetch_text respects limits and cache."""

from unittest.mock import patch

from app.services.repo_content import batch_fetch_text


@patch("app.services.repo_content.get_blob_text")
def test_batch_fetch_text_returns_dict_by_path(mock_get_blob):
    """batch_fetch_text returns dict keyed by path."""
    mock_get_blob.return_value = "content"
    blobs = [{"path": "a.py", "sha": "s1"}, {"path": "b.py", "sha": "s2"}]
    out = batch_fetch_text("o", "r", blobs, max_files=10, max_total_bytes=1_000_000)
    assert out["a.py"] == "content"
    assert out["b.py"] == "content"
    assert mock_get_blob.call_count == 2


@patch("app.services.repo_content.get_blob_text")
def test_batch_fetch_text_respects_max_files(mock_get_blob):
    """batch_fetch_text stops after max_files."""
    mock_get_blob.return_value = "x"
    blobs = [{"path": f"f{i}.py", "sha": f"s{i}"} for i in range(10)]
    out = batch_fetch_text("o", "r", blobs, max_files=3, max_total_bytes=1_000_000)
    assert len(out) == 3
    assert mock_get_blob.call_count == 3


@patch("app.services.repo_content.get_blob_text")
def test_batch_fetch_text_respects_max_total_bytes(mock_get_blob):
    """batch_fetch_text stops when max_total_bytes is reached."""
    mock_get_blob.return_value = "x" * 50  # 50 bytes each
    blobs = [
        {"path": "a.py", "sha": "s1"},
        {"path": "b.py", "sha": "s2"},
        {"path": "c.py", "sha": "s3"},
    ]
    out = batch_fetch_text("o", "r", blobs, max_files=10, max_total_bytes=75)
    # 50 + 25 (truncated) = 75 then stop
    assert len(out) <= 2
    total = sum(len(v.encode("utf-8")) for v in out.values())
    assert total <= 75
    assert mock_get_blob.call_count <= 2


@patch("app.services.repo_content.get_blob_text")
def test_batch_fetch_text_uses_cache_same_sha(mock_get_blob):
    """Same sha not fetched twice (cache)."""
    mock_get_blob.return_value = "same"
    blobs = [
        {"path": "a.py", "sha": "s1"},
        {"path": "b.py", "sha": "s1"},
    ]
    out = batch_fetch_text("o", "r", blobs, max_files=10, max_total_bytes=1_000_000)
    assert out["a.py"] == "same"
    assert out["b.py"] == "same"
    assert mock_get_blob.call_count == 1
