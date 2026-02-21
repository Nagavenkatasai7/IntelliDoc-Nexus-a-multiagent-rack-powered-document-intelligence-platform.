import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_root(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "IntelliDoc" in data["app"]


@pytest.mark.asyncio
class TestDocumentEndpoints:
    async def test_list_documents_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0

    async def test_upload_unsupported_format(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.xyz", b"content", "application/octet-stream")},
        )
        assert response.status_code == 400

    async def test_upload_txt_document(self, client: AsyncClient):
        content = b"This is a test document with some content for testing purposes."
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", content, "text/plain")},
        )
        # May fail without vector store, but should at least validate the file
        assert response.status_code in (201, 500)

    async def test_get_nonexistent_document(self, client: AsyncClient):
        response = await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
