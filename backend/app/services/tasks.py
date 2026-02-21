"""Celery background tasks for async document processing."""

import uuid
import asyncio
from datetime import datetime, timezone

try:
    from celery import shared_task
except ImportError:
    # Celery not available (e.g., serverless deployment)
    def shared_task(*args, **kwargs):
        def decorator(func):
            func.delay = lambda *a, **kw: None
            return func
        if args and callable(args[0]):
            return decorator(args[0])
        return decorator

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Lazy sync engine creation (avoid crash if database_url_sync is invalid)
_sync_engine = None
_SyncSession = None


def _get_sync_session():
    global _sync_engine, _SyncSession
    if _SyncSession is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session, sessionmaker
        _sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
        _SyncSession = sessionmaker(_sync_engine, class_=Session)
    return _SyncSession


@shared_task(
    bind=True,
    name="process_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_document_task(self, document_id: str, file_content_hex: str, filename: str):
    """Background task to process a document through the full pipeline.

    Args:
        document_id: UUID string of the document record
        file_content_hex: Hex-encoded file bytes
        filename: Original filename
    """
    from sqlalchemy import select
    from app.models.document import Document, DocumentChunk, DocumentStatus
    from app.services.document_processor import DocumentProcessor
    from app.services.chunker import SemanticChunker
    from app.services.embedding import EmbeddingService

    task_id = self.request.id
    logger.info("task_started", task_id=task_id, document_id=document_id, filename=filename)

    file_content = bytes.fromhex(file_content_hex)
    processor = DocumentProcessor()
    chunker = SemanticChunker()

    with _get_sync_session()() as db:
        doc = db.get(Document, uuid.UUID(document_id))
        if not doc:
            logger.error("document_not_found", document_id=document_id)
            return {"status": "error", "detail": "Document not found"}

        doc.status = DocumentStatus.PROCESSING
        db.commit()

        try:
            # Update progress: extracting
            self.update_state(state="EXTRACTING", meta={"step": "extracting", "progress": 20})

            extraction = asyncio.run(processor.extract_text(file_content, filename))
            doc.page_count = extraction.get("page_count", 0)
            doc.metadata_ = extraction.get("metadata", {})
            db.commit()

            # Update progress: chunking
            self.update_state(state="CHUNKING", meta={"step": "chunking", "progress": 40})

            chunks_data = chunker.chunk_document(extraction.get("pages", []))
            if not chunks_data:
                doc.status = DocumentStatus.FAILED
                doc.error_message = "No text content extracted"
                db.commit()
                return {"status": "failed", "detail": "No text content"}

            # Update progress: storing chunks
            self.update_state(state="STORING", meta={"step": "storing_chunks", "progress": 60})

            for chunk_data in chunks_data:
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    token_count=chunk_data["token_count"],
                    page_number=chunk_data.get("page_number"),
                    section_title=chunk_data.get("section_title"),
                )
                db.add(db_chunk)
            db.commit()

            # Update progress: embedding
            self.update_state(state="EMBEDDING", meta={"step": "embedding", "progress": 80})

            embedding_service = EmbeddingService()
            texts = [c["content"] for c in chunks_data]
            _embeddings = embedding_service.embed_texts(texts)

            # Note: Vector store upsert would happen here with Pinecone
            # Skipped in background task for now — handled by the sync ingestion path

            # Update progress: complete
            self.update_state(state="COMPLETE", meta={"step": "complete", "progress": 100})

            doc.status = DocumentStatus.COMPLETED
            db.commit()

            logger.info(
                "task_completed",
                task_id=task_id,
                document_id=document_id,
                chunks=len(chunks_data),
            )

            return {
                "status": "completed",
                "document_id": document_id,
                "chunks": len(chunks_data),
                "pages": doc.page_count,
            }

        except Exception as exc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)[:500]
            db.commit()
            logger.error("task_failed", task_id=task_id, error=str(exc))
            raise self.retry(exc=exc)


@shared_task(name="cleanup_failed_documents")
def cleanup_failed_documents():
    """Periodic task to clean up documents stuck in PROCESSING state."""
    from sqlalchemy import select
    from app.models.document import Document, DocumentStatus

    with _get_sync_session()() as db:
        stuck_docs = db.execute(
            select(Document).where(Document.status == DocumentStatus.PROCESSING)
        ).scalars().all()

        for doc in stuck_docs:
            age_hours = (datetime.now(timezone.utc) - doc.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if age_hours > 1:
                doc.status = DocumentStatus.FAILED
                doc.error_message = "Processing timed out"
                logger.warning("stuck_document_cleaned", document_id=str(doc.id))

        db.commit()
