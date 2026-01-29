"""Unit tests for rate limiting logic."""

import time
import pytest

from app.core.rate_limit import (
    RateLimitExceeded,
    check_analyze_rate_limit,
    WINDOW_SECONDS,
    MAX_REQUESTS_PER_WINDOW,
)


def test_rate_limit_allows_requests():
    """Test that requests within limit are allowed."""
    ip = "127.0.0.1"
    # Clear any existing state
    from app.core.rate_limit import _store
    _store.clear()
    
    # Make requests up to limit
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        check_analyze_rate_limit(ip)
    
    # Should not raise


def test_rate_limit_blocks_excess():
    """Test that exceeding limit raises error."""
    ip = "127.0.0.2"
    from app.core.rate_limit import _store
    _store.clear()
    
    # Make requests up to limit
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        check_analyze_rate_limit(ip)
    
    # Next request should fail
    with pytest.raises(RateLimitExceeded, match="Too many analyze requests"):
        check_analyze_rate_limit(ip)


def test_rate_limit_different_ips():
    """Test that different IPs have separate limits."""
    ip1 = "127.0.0.3"
    ip2 = "127.0.0.4"
    from app.core.rate_limit import _store
    _store.clear()
    
    # Exhaust limit for ip1
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        check_analyze_rate_limit(ip1)
    
    # ip2 should still be able to make requests
    check_analyze_rate_limit(ip2)
    check_analyze_rate_limit(ip2)


def test_rate_limit_window_expiry():
    """Test that old requests expire after window."""
    ip = "127.0.0.5"
    from app.core.rate_limit import _store, _prune
    _store.clear()
    
    # Make requests up to limit
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        check_analyze_rate_limit(ip)
    
    # Manually expire old timestamps (simulate time passing)
    _store[ip] = [time.monotonic() - WINDOW_SECONDS - 1]
    
    # Prune expired entries (this happens in check_analyze_rate_limit)
    _prune(_store[ip], WINDOW_SECONDS)
    
    # Should be able to make new request
    check_analyze_rate_limit(ip)
    # After pruning and adding new request, should have 1 item (old was pruned)
    assert len(_store[ip]) == 1
