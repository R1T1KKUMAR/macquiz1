from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time
from typing import Deque, Dict


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int | None = None


# In-memory sliding-window counters.
# Note: resets on process restart and isn't shared across workers.
_requests: Dict[str, Deque[float]] = {}


def check_rate_limit(key: str, limit: int, window_seconds: int) -> RateLimitResult:
    """Simple sliding-window rate limiter.

    Returns whether the request is allowed, and (if blocked) how long to wait.
    """
    now = time.monotonic()
    window_start = now - window_seconds

    bucket = _requests.get(key)
    if bucket is None:
        bucket = deque()
        _requests[key] = bucket

    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= limit:
        retry_after = int(max(1, bucket[0] + window_seconds - now))
        return RateLimitResult(allowed=False, retry_after_seconds=retry_after)

    bucket.append(now)
    return RateLimitResult(allowed=True)
