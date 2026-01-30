"""Light per-IP rate limit for POST /api/analyze. In-memory only."""

import time

WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 10

_store: dict[str, list[float]] = {}


class RateLimitExceeded(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def _prune(ts_list: list[float], window: int) -> None:
    cutoff = time.monotonic() - window
    while ts_list and ts_list[0] < cutoff:
        ts_list.pop(0)


def check_analyze_rate_limit(ip: str) -> None:
    """Raise RateLimitExceeded if ip has exceeded the limit. Otherwise record request."""
    now = time.monotonic()
    if ip not in _store:
        _store[ip] = []
    ts_list = _store[ip]
    _prune(ts_list, WINDOW_SECONDS)
    if len(ts_list) >= MAX_REQUESTS_PER_WINDOW:
        raise RateLimitExceeded(
            "Too many analyze requests. Try again in a minute."
        )
    ts_list.append(now)
