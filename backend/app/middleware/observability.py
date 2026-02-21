"""OpenTelemetry tracing and Prometheus metrics middleware."""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge

from app.core.logging import get_logger

logger = get_logger(__name__)

# Prometheus Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "intellidoc_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "intellidoc_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ACTIVE_CONNECTIONS = Gauge(
    "intellidoc_active_connections",
    "Number of active HTTP connections",
)

DOCUMENTS_PROCESSED = Counter(
    "intellidoc_documents_processed_total",
    "Total documents processed",
    ["status"],
)

RAG_QUERIES_TOTAL = Counter(
    "intellidoc_rag_queries_total",
    "Total RAG queries executed",
    ["mode"],  # simple or multi_agent
)

RAG_QUERY_DURATION = Histogram(
    "intellidoc_rag_query_duration_seconds",
    "RAG query latency in seconds",
    ["mode"],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 30.0],
)

EMBEDDING_DURATION = Histogram(
    "intellidoc_embedding_duration_seconds",
    "Embedding generation latency",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collects Prometheus metrics for all HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        ACTIVE_CONNECTIONS.inc()
        start = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start

            endpoint = self._normalize_path(request.url.path)
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration)

            return response
        finally:
            ACTIVE_CONNECTIONS.dec()

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize URL paths to avoid high-cardinality labels."""
        parts = path.split("/")
        normalized = []
        for part in parts:
            # Replace UUIDs and numeric IDs with placeholders
            if len(part) == 36 and part.count("-") == 4:
                normalized.append("{id}")
            elif part.isdigit():
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)
