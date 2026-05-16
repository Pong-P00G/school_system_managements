"""Simple in-memory rate limiter for auth endpoints."""

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


# 5 login attempts per minute per IP
auth_limiter = RateLimiter(max_requests=5, window_seconds=60)


async def rate_limit_auth(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    auth_limiter.check(client_ip)
