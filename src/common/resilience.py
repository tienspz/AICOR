"""
AICOR Anti-ban & Resilience Subsystem
Provides rate limiting, token-bucket throttling, exponential backoff with jitter,
and compliant HTTP sessions (SEC EDGAR & Google Trends).
"""
import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.common.config import (
    SEC_USER_AGENT,
    SEC_RATE_LIMIT_DELAY,
    TRENDS_MIN_DELAY,
    TRENDS_MAX_DELAY,
    MAX_RETRIES,
    BACKOFF_FACTOR,
)

logger = logging.getLogger("aicor.resilience")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class RateLimiter:
    """
    Enforces delay between successive calls to the same host/service.
    Uses last_request timestamp and optional jitter to avoid predictable robot patterns.
    """
    def __init__(self, min_interval: float = 1.0, max_interval: Optional[float] = None):
        self.min_interval = min_interval
        self.max_interval = max_interval if max_interval is not None else min_interval
        self.last_call_time = 0.0

    def wait(self) -> None:
        """Blocks execution until the required delay has elapsed."""
        now = time.time()
        elapsed = now - self.last_call_time
        
        target_delay = self.min_interval
        if self.max_interval > self.min_interval:
            target_delay += random.uniform(0, self.max_interval - self.min_interval)
            
        remaining = target_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self.last_call_time = time.time()


# Global rate limiter singletons for key services
sec_rate_limiter = RateLimiter(min_interval=SEC_RATE_LIMIT_DELAY, max_interval=SEC_RATE_LIMIT_DELAY + 0.05)
trends_rate_limiter = RateLimiter(min_interval=TRENDS_MIN_DELAY, max_interval=TRENDS_MAX_DELAY)


def retry_with_backoff(
    max_retries: int = MAX_RETRIES,
    initial_delay: float = 2.0,
    backoff_factor: float = BACKOFF_FACTOR,
    jitter: float = 1.0,
    retry_statuses: tuple = (429, 500, 502, 503, 504),
) -> Callable:
    """
    Decorator that retries an operation on network errors or rate limit codes (429).
    Uses exponential backoff with additive random jitter: delay = initial_delay * (backoff_factor ** attempt) + random(0, jitter).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            current_delay = initial_delay
            func_name = getattr(func, "__name__", str(func))
            while True:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    attempt += 1
                    status_code = getattr(getattr(e, "response", None), "status_code", None)
                    
                    # If it's a 4xx error that is NOT 429, don't retry (client error, e.g. 404, 400)
                    if status_code is not None and status_code < 500 and status_code not in retry_statuses:
                        logger.error(f"Client error {status_code} in {func_name}: {e}. Not retrying.")
                        raise e
                    
                    if attempt > max_retries:
                        logger.error(f"Exceeded max retries ({max_retries}) in {func_name}: {e}")
                        raise e
                    
                    sleep_time = current_delay + random.uniform(0, jitter)
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed for {func_name} (status={status_code}): {e}. "
                        f"Backing off for {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    current_delay *= backoff_factor

                except Exception as ex:
                    # Non-network error, re-raise immediately
                    raise ex
        return wrapper
    return decorator


def create_sec_session() -> requests.Session:
    """
    Creates an HTTP requests session configured to SEC EDGAR standards:
    - User-Agent header with contact info (mandatory by SEC guidelines)
    - Connection pooling & retries for transient connection drops
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    })
    
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
