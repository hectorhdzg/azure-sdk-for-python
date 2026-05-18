# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import time
import threading
import unittest

from azure.monitor.opentelemetry.exporter.export._rate_limiter import (
    _TokenBucketRateLimiter,
    _DEFAULT_RATE_LIMIT,
    _DEFAULT_BURST_CAPACITY,
)


class TestTokenBucketRateLimiter(unittest.TestCase):
    def test_defaults(self):
        limiter = _TokenBucketRateLimiter()
        self.assertEqual(limiter._rate, _DEFAULT_RATE_LIMIT)
        self.assertEqual(limiter._capacity, _DEFAULT_BURST_CAPACITY)

    def test_consume_within_capacity(self):
        limiter = _TokenBucketRateLimiter(rate=10.0, capacity=5)
        # Should succeed up to capacity
        for _ in range(5):
            self.assertTrue(limiter.consume())
        # Next should fail (no refill yet)
        self.assertFalse(limiter.consume())

    def test_refill_over_time(self):
        limiter = _TokenBucketRateLimiter(rate=100.0, capacity=10)
        # Exhaust all tokens
        for _ in range(10):
            limiter.consume()
        self.assertFalse(limiter.consume())
        # Simulate time passing (enough for 1 token at rate=100/s -> 0.01s)
        limiter._last_refill = time.monotonic() - 0.05  # 5 tokens worth
        self.assertTrue(limiter.consume())

    def test_capacity_is_ceiling(self):
        limiter = _TokenBucketRateLimiter(rate=1000.0, capacity=5)
        # Even after a lot of time, tokens capped at capacity
        limiter._last_refill = time.monotonic() - 100.0  # way more than needed
        limiter._refill()
        self.assertEqual(limiter._tokens, 5.0)

    def test_thread_safety(self):
        limiter = _TokenBucketRateLimiter(rate=10.0, capacity=20)
        results = []

        def worker():
            result = limiter.consume()
            results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 20 should succeed (capacity), rest should fail
        self.assertEqual(sum(1 for r in results if r), 20)
        self.assertEqual(sum(1 for r in results if not r), 10)

    def test_custom_rate_and_capacity(self):
        limiter = _TokenBucketRateLimiter(rate=50.0, capacity=100)
        self.assertEqual(limiter._rate, 50.0)
        self.assertEqual(limiter._capacity, 100)

    def test_consume_multiple_tokens(self):
        limiter = _TokenBucketRateLimiter(rate=10.0, capacity=10)
        self.assertTrue(limiter.consume(5))
        self.assertTrue(limiter.consume(5))
        self.assertFalse(limiter.consume(1))


if __name__ == "__main__":
    unittest.main()
