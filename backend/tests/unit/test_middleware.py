"""Tests for middleware components — rate limiting, security headers, metrics."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from app.middleware.rate_limit import RateLimitMiddleware


class TestRateLimitMiddleware:
    def setup_method(self):
        self.app = MagicMock()
        self.middleware = RateLimitMiddleware(self.app, requests_per_minute=5)

    def _make_request(self, ip: str = "127.0.0.1"):
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = ip
        return request

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        request = self._make_request()
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        # Should allow 5 requests
        for _ in range(5):
            response = await self.middleware.dispatch(request, call_next)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self):
        from fastapi import HTTPException

        request = self._make_request()
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        # Fill up the limit
        for _ in range(5):
            await self.middleware.dispatch(request, call_next)

        # 6th request should be blocked
        with pytest.raises(HTTPException) as exc_info:
            await self.middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_different_ips_independent(self):
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        # Fill up limit for IP 1
        for _ in range(5):
            await self.middleware.dispatch(self._make_request("1.1.1.1"), call_next)

        # IP 2 should still be allowed
        response = await self.middleware.dispatch(self._make_request("2.2.2.2"), call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_window_cleanup(self):
        request = self._make_request()
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        # Inject old timestamps (> 60 seconds ago)
        old_time = time.time() - 120
        self.middleware._requests["127.0.0.1"] = [old_time] * 10

        # Should still allow because old entries get cleaned
        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_client_uses_unknown(self):
        request = MagicMock()
        request.client = None
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200
        assert "unknown" in self.middleware._requests
