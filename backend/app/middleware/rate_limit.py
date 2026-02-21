import time
from collections import defaultdict

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter. Use Redis for production."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        # Clean old entries
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        if len(self._requests[client_ip]) >= self.requests_per_minute:
            logger.warning("rate_limit_exceeded", client_ip=client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )

        self._requests[client_ip].append(now)
        response = await call_next(request)
        return response
