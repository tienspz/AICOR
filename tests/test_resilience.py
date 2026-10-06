"""
Unit tests for RateLimiter and Retry Backoff mechanism.
"""
import time
import requests
import pytest
from unittest.mock import MagicMock
from src.common.resilience import RateLimiter, retry_with_backoff


def test_rate_limiter_timing():
    limiter = RateLimiter(min_interval=0.1, max_interval=0.15)
    start = time.time()
    limiter.wait()
    limiter.wait()
    elapsed = time.time() - start
    assert elapsed >= 0.1, f"Expected elapsed >= 0.1s, got {elapsed:.4f}s"


def test_retry_with_backoff_success():
    mock_func = MagicMock(return_value="success")
    decorated = retry_with_backoff(max_retries=2, initial_delay=0.01)(mock_func)
    res = decorated()
    assert res == "success"
    assert mock_func.call_count == 1


def test_retry_with_backoff_retries_on_429():
    mock_func = MagicMock()
    # Create mock response for 429 Too Many Requests
    resp_429 = requests.Response()
    resp_429.status_code = 429
    err_429 = requests.exceptions.HTTPError(response=resp_429)

    # Fail twice with 429, then succeed
    mock_func.side_effect = [err_429, err_429, "finally_success"]

    decorated = retry_with_backoff(max_retries=3, initial_delay=0.01, backoff_factor=1.5, jitter=0.01)(mock_func)
    result = decorated()
    assert result == "finally_success"
    assert mock_func.call_count == 3


def test_retry_with_backoff_exhausts_retries():
    mock_func = MagicMock()
    resp_500 = requests.Response()
    resp_500.status_code = 500
    err_500 = requests.exceptions.HTTPError(response=resp_500)
    mock_func.side_effect = err_500

    decorated = retry_with_backoff(max_retries=2, initial_delay=0.01, jitter=0.01)(mock_func)
    with pytest.raises(requests.exceptions.RequestException):
        decorated()
    assert mock_func.call_count == 3  # initial + 2 retries
