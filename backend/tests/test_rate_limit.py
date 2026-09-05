from fastapi import HTTPException
import pytest

from app.core.rate_limit import RateLimiter


def test_allows_up_to_max_attempts():
    limiter = RateLimiter(max_attempts=3, window_seconds=60)
    for _ in range(3):
        limiter.check("1.2.3.4")


def test_blocks_after_max_attempts():
    limiter = RateLimiter(max_attempts=3, window_seconds=60)
    for _ in range(3):
        limiter.check("1.2.3.4")
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("1.2.3.4")
    assert exc_info.value.status_code == 429


def test_keys_are_independent():
    limiter = RateLimiter(max_attempts=1, window_seconds=60)
    limiter.check("1.2.3.4")
    limiter.check("5.6.7.8")  # andere sleutel, mag niet geblokkeerd worden
    with pytest.raises(HTTPException):
        limiter.check("1.2.3.4")


def test_old_attempts_expire_out_of_window():
    limiter = RateLimiter(max_attempts=1, window_seconds=0)
    limiter.check("1.2.3.4")
    # window_seconds=0: de vorige poging is meteen "verlopen"
    limiter.check("1.2.3.4")
