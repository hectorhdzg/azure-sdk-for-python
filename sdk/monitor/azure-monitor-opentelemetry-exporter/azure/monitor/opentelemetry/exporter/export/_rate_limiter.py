# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import threading
import time


# Default: 10 transmissions per second, burst up to 30
_DEFAULT_RATE_LIMIT = 10.0  # tokens per second
_DEFAULT_BURST_CAPACITY = 30  # max tokens (burst allowance)


class _TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter for controlling transmission rate.

    Limits the number of _transmit calls per second to prevent overwhelming
    the ingestion endpoint during telemetry bursts.
    """

    def __init__(self, rate: float = _DEFAULT_RATE_LIMIT, capacity: int = _DEFAULT_BURST_CAPACITY) -> None:
        """Initialize the token bucket.

        :param rate: Tokens added per second (sustained send rate).
        :param capacity: Maximum number of tokens (burst allowance).
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens from the bucket.

        :param tokens: Number of tokens to consume.
        :return: True if tokens were available and consumed, False otherwise.
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time. Must be called under lock."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now
