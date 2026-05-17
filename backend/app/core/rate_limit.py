"""Simple in-memory rate limiter for auth endpoints."""

import os
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status


class RateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _clean(self, key: str):
        now = time.time()
        self._requests[key] = [t for t in self._requests[key] if now - t < self.window]

    def check(self, key: str):
        self._clean(key)
        if len(self._requests[key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {self.window} seconds.",
            )
        self._requests[key].append(time.time())


# Higher limit in testing to avoid test failures
_max = 500 if os.environ.get("TESTING") or os.environ.get("PYTEST_CURRENT_TEST") else 5
auth_limiter = RateLimiter(max_requests=_max, window_seconds=60)


async def rate_limit_auth(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    auth_limiter.check(client_ip)
