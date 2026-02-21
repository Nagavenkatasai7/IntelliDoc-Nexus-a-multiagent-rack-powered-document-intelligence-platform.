import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_register(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"email": "dup@example.com", "password": "testpassword123"}
        await client.post("/api/v1/auth/register", json=payload)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    async def test_login_success(self, client: AsyncClient):
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "testpassword123"},
        )
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "wrong@example.com", "password": "correctpassword"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_get_profile(self, client: AsyncClient):
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "profile@example.com", "password": "testpassword123", "full_name": "Profile User"},
        )
        token = reg_resp.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["full_name"] == "Profile User"

    async def test_profile_no_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
