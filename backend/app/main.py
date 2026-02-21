from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.session import engine, Base, async_session_factory
from app.db.seed import seed_dev_user
from app.middleware.observability import MetricsMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger("startup")
    logger.info("starting_app", app=settings.app_name, env=settings.app_env)

    # Create tables (use alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database_tables_ready")

    # Seed dev user
    if settings.app_env == "development":
        async with async_session_factory() as session:
            await seed_dev_user(session)
        logger.info("dev_user_seeded")

    # Rebuild BM25 index from existing documents so keyword search works
    # after container restart (BM25 index is in-memory only)
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.document import Document, DocumentStatus
        from app.api.deps import get_bm25_service

        bm25 = get_bm25_service()
        async with async_session_factory() as session:
            stmt = (
                select(Document)
                .where(Document.status == DocumentStatus.COMPLETED)
                .options(selectinload(Document.chunks))
            )
            result = await session.execute(stmt)
            documents = list(result.scalars().all())

            for doc in documents:
                if doc.chunks:
                    namespace = str(doc.owner_id)
                    bm25_chunks = [
                        {
                            "content": chunk.content,
                            "document_id": str(doc.id),
                            "chunk_index": chunk.chunk_index,
                            "page_number": chunk.page_number,
                            "section_title": chunk.section_title,
                        }
                        for chunk in doc.chunks
                    ]
                    bm25.add_to_index(namespace, bm25_chunks)

            logger.info("bm25_index_rebuilt", documents=len(documents))
    except Exception as e:
        logger.warning("bm25_rebuild_failed", error=str(e))

    yield

    await engine.dispose()
    logger.info("app_shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Multi-agent RAG-powered document intelligence platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware stack (order matters: outermost first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

# Allow Vercel deployment URLs
import os
vercel_url = os.environ.get("VERCEL_URL")
if vercel_url:
    allowed_origins.append(f"https://{vercel_url}")
vercel_project_url = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
if vercel_project_url:
    allowed_origins.append(f"https://{vercel_project_url}")

# Allow custom frontend URL via env var
custom_frontend = os.environ.get("FRONTEND_URL")
if custom_frontend:
    allowed_origins.append(custom_frontend)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
    }
