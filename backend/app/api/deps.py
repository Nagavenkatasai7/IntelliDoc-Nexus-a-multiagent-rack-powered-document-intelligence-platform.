import uuid
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService
from app.services.ingestion import IngestionService
from app.services.rag import RAGService
from app.agents.orchestrator import OrchestratorAgent

# Singletons for shared services
_vector_store: VectorStoreService | None = None
_bm25_service: BM25SearchService | None = None
_orchestrator: OrchestratorAgent | None = None


def get_vector_store() -> VectorStoreService:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store


def get_bm25_service() -> BM25SearchService:
    global _bm25_service
    if _bm25_service is None:
        _bm25_service = BM25SearchService()
    return _bm25_service


def get_ingestion_service(
    db: AsyncSession = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store),
    bm25_service: BM25SearchService = Depends(get_bm25_service),
) -> IngestionService:
    return IngestionService(db=db, vector_store=vector_store, bm25_service=bm25_service)


def get_rag_service(
    db: AsyncSession = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store),
    bm25_service: BM25SearchService = Depends(get_bm25_service),
) -> RAGService:
    return RAGService(vector_store=vector_store, bm25_service=bm25_service, db=db)


def get_orchestrator(
    vector_store: VectorStoreService = Depends(get_vector_store),
    bm25_service: BM25SearchService = Depends(get_bm25_service),
) -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent(vector_store=vector_store, bm25_service=bm25_service)
    return _orchestrator


async def get_current_user_id() -> uuid.UUID:
    """Placeholder for auth - returns a default user ID for development.

    In production, replace with JWT-based auth from auth.get_authenticated_user.
    """
    return uuid.UUID("00000000-0000-0000-0000-000000000001")
