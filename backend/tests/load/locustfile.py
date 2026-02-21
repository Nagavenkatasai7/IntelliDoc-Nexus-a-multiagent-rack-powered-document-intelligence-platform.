"""Load tests for IntelliDoc Nexus API using Locust.

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    Or with Docker:
    docker compose -f infrastructure/docker-compose.yml --profile loadtest up
"""

import io
import uuid

from locust import HttpUser, task, between, tag


class IntelliDocUser(HttpUser):
    """Simulates a typical IntelliDoc Nexus user."""

    wait_time = between(1, 5)

    def on_start(self):
        """Register and login to get auth token."""
        email = f"loadtest-{uuid.uuid4().hex[:8]}@test.com"
        password = "loadtest123"

        # Register
        resp = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Load Test User"},
        )
        if resp.status_code == 201:
            self.token = resp.json().get("access_token", "")
        else:
            # Fallback: use dev user
            resp = self.client.post(
                "/api/v1/auth/login",
                json={"email": "dev@intellidoc.ai", "password": "devpassword123"},
            )
            self.token = resp.json().get("access_token", "")

        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.uploaded_doc_id = None

    @tag("health")
    @task(5)
    def health_check(self):
        """High-frequency health checks."""
        self.client.get("/api/v1/health")

    @tag("documents")
    @task(3)
    def list_documents(self):
        """List user's documents."""
        self.client.get("/api/v1/documents", headers=self.headers)

    @tag("documents")
    @task(1)
    def upload_document(self):
        """Upload a small test document."""
        content = f"Load test document {uuid.uuid4().hex}. " * 50
        files = {
            "file": ("loadtest.txt", io.BytesIO(content.encode()), "text/plain"),
        }
        resp = self.client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=self.headers,
        )
        if resp.status_code == 201:
            self.uploaded_doc_id = resp.json().get("id")

    @tag("documents")
    @task(2)
    def get_document(self):
        """Fetch a specific document if one was uploaded."""
        if self.uploaded_doc_id:
            self.client.get(
                f"/api/v1/documents/{self.uploaded_doc_id}",
                headers=self.headers,
            )

    @tag("chat")
    @task(2)
    def chat_query(self):
        """Send a chat query (will fail without Anthropic key, but tests throughput)."""
        self.client.post(
            "/api/v1/chat/",
            json={"question": "What is machine learning?"},
            headers=self.headers,
            name="/api/v1/chat/",
        )

    @tag("auth")
    @task(1)
    def get_profile(self):
        """Fetch user profile."""
        self.client.get("/api/v1/auth/me", headers=self.headers)


class HealthCheckUser(HttpUser):
    """Lightweight user that only hits health endpoints — for baseline load."""

    wait_time = between(0.5, 2)
    weight = 1  # Lower weight than main user

    @task
    def health(self):
        self.client.get("/api/v1/health")

    @task
    def root(self):
        self.client.get("/")
