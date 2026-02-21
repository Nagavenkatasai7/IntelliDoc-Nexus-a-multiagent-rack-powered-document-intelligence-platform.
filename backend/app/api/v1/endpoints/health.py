from datetime import datetime, timezone

from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.core.config import get_settings

router = APIRouter(tags=["system"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
