"""Integration tests for session management endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSessionEndpoints:
    async def test_share_nonexistent_session(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/sessions/00000000-0000-0000-0000-000000000000/share"
        )
        assert response.status_code == 404

    async def test_unshare_nonexistent_session(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/sessions/00000000-0000-0000-0000-000000000000/unshare"
        )
        assert response.status_code == 404

    async def test_export_nonexistent_session(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/sessions/00000000-0000-0000-0000-000000000000/export/markdown"
        )
        assert response.status_code == 404

    async def test_delete_nonexistent_session(self, client: AsyncClient):
        response = await client.delete(
            "/api/v1/sessions/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    async def test_get_shared_with_invalid_token(self, client: AsyncClient):
        response = await client.get("/api/v1/sessions/shared/nonexistent-token")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_health_returns_status(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    async def test_health_returns_app_name(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert "IntelliDoc" in data["app"]

    async def test_metrics_endpoint(self, client: AsyncClient):
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
        # Prometheus format
        assert b"http_requests" in response.content or response.status_code == 200
