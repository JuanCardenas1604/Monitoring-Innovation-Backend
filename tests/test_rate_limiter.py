import time

from app.core.rate_limiter import check_rate_limit


class TestRateLimiter:
    def test_first_request_allowed(self):
        allowed, retry = check_rate_limit("test:1", max_requests=3, window=60)
        assert allowed
        assert retry == 0

    def test_under_limit_allowed(self):
        key = "test:under"
        for _ in range(3):
            allowed, _ = check_rate_limit(key, max_requests=5, window=60)
            assert allowed

    def test_exact_limit_allowed(self):
        key = "test:exact"
        for _ in range(5):
            allowed, _ = check_rate_limit(key, max_requests=5, window=60)
            assert allowed

    def test_over_limit_blocked(self):
        key = f"test:over:{time.time_ns()}"
        for _ in range(3):
            check_rate_limit(key, max_requests=3, window=60)
        allowed, retry = check_rate_limit(key, max_requests=3, window=60)
        assert not allowed
        assert retry > 0

    def test_window_expires(self):
        key = f"test:expire:{time.time_ns()}"
        for _ in range(3):
            check_rate_limit(key, max_requests=3, window=1)
        allowed, _ = check_rate_limit(key, max_requests=3, window=1)
        assert not allowed
        time.sleep(1.1)
        allowed, _ = check_rate_limit(key, max_requests=3, window=1)
        assert allowed

    def test_different_keys_independent(self):
        allowed_a = True
        allowed_b = True
        for i in range(5):
            allowed_a = check_rate_limit(f"test:indep:a:{i}", max_requests=3, window=60)[0]
            allowed_b = check_rate_limit(f"test:indep:b:{i}", max_requests=3, window=60)[0]
            assert allowed_a and allowed_b

    def test_returns_retry_seconds(self):
        key = f"test:retry:{time.time_ns()}"
        for _ in range(3):
            check_rate_limit(key, max_requests=3, window=10)
        _, retry = check_rate_limit(key, max_requests=3, window=10)
        assert 1 <= retry <= 10
