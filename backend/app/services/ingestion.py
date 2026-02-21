import uuid
import time

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentType
from app.services.document_processor import DocumentProcessor
from app.services.chunker import SemanticChunker
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

logger = get_logger(__name__)

# Map file extensions to DocumentType
EXTENSION_MAP = {
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".doc": DocumentType.DOCX,
    ".txt": DocumentType.TXT,
    ".png": DocumentType.IMAGE,
    ".jpg": DocumentType.IMAGE,
    ".jpeg": DocumentType.IMAGE,
    ".tiff": DocumentType.IMAGE,
}


class IngestionService:
    """Orchestrates the full document ingestion pipeline."""

    def __init__(
        self,
        db: AsyncSession,
        vector_store: VectorStoreService,
        bm25_service: BM25SearchService,
    ):
        self.db = db
        self.processor = DocumentProcessor()
        self.chunker = SemanticChunker()
        self.vector_store = vector_store
        self.bm25_service = bm25_service

    async def ingest_document(
        self,
        file_content: bytes,
        filename: str,
        owner_id: uuid.UUID,
    ) -> Document:
        """Full pipeline: validate, extract, chunk, embed, store."""
        start = time.time()
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        # 1. Validate file type
        file_type = EXTENSION_MAP.get(ext)
        if file_type is None:
            raise ValueError(f"Unsupported file type: {ext}")

        # 2. Check for duplicate
        content_hash = DocumentProcessor.compute_content_hash(file_content)
        existing = await self._find_duplicate(content_hash, owner_id)
        if existing:
            logger.info("duplicate_detected", filename=filename, existing_id=str(existing.id))
            return existing

        # 3. Create document record
        doc = Document(
            owner_id=owner_id,
            filename=filename,
            original_filename=filename,
            file_type=file_type,
            file_size=len(file_content),
            content_hash=content_hash,
            status=DocumentStatus.PROCESSING,
        )
        self.db.add(doc)
        await self.db.flush()

        try:
            # 4. Extract text
            extraction = await self.processor.extract_text(file_content, filename)
            doc.page_count = extraction.get("page_count", 0)
            doc.metadata_ = extraction.get("metadata", {})

            # 5. Chunk document
            chunks_data = self.chunker.chunk_document(extraction.get("pages", []))

            if not chunks_data:
                doc.status = DocumentStatus.FAILED
                doc.error_message = "No text content could be extracted from the document"
                await self.db.flush()
                return doc

            # 6. Store chunks in database
            db_chunks = []
            for chunk_data in chunks_data:
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    token_count=chunk_data["token_count"],
                    page_number=chunk_data.get("page_number"),
                    section_title=chunk_data.get("section_title"),
                )
                db_chunks.append(db_chunk)
                self.db.add(db_chunk)

            await self.db.flush()

            # 7. Embed and upsert to vector store (gracefully skip if deps missing)
            try:
                vector_ids = await self.vector_store.upsert_chunks(
                    chunks=chunks_data,
                    document_id=doc.id,
                    owner_id=owner_id,
                )
                for db_chunk, vector_id in zip(db_chunks, vector_ids):
                    db_chunk.vector_id = vector_id
            except (RuntimeError, ImportError) as ve:
                logger.warning("vector_upsert_skipped", reason=str(ve))

            # 8. Add to BM25 index
            bm25_chunks = [
                {
                    "content": c["content"],
                    "document_id": str(doc.id),
                    "chunk_index": c["chunk_index"],
                    "page_number": c.get("page_number"),
                    "section_title": c.get("section_title"),
                }
                for c in chunks_data
            ]
            self.bm25_service.add_to_index(str(owner_id), bm25_chunks)

            # 9. Mark as completed
            elapsed_ms = int((time.time() - start) * 1000)
            doc.status = DocumentStatus.COMPLETED
            doc.processing_time_ms = elapsed_ms

            logger.info(
                "document_ingested",
                document_id=str(doc.id),
                filename=filename,
                chunks=len(chunks_data),
                elapsed_ms=elapsed_ms,
            )

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)[:500]
            logger.error("ingestion_failed", filename=filename, error=str(e))
            raise

        return doc

    async def delete_document(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        """Delete a document and all associated data."""
        doc = await self.db.get(Document, document_id)
        if not doc or doc.owner_id != owner_id:
            return False

        # Remove from vector store
        try:
            await self.vector_store.delete_document_vectors(document_id, owner_id)
        except Exception as e:
            logger.error("vector_delete_failed", error=str(e))

        # Remove from BM25 index
        self.bm25_service.remove_document(str(owner_id), str(document_id))

        # Delete from database (cascades to chunks)
        await self.db.delete(doc)
        return True

    async def get_document_with_chunks(
        self, document_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id, Document.owner_id == owner_id)
            .options(selectinload(Document.chunks))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self, owner_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[Document], int]:
        count_stmt = select(func.count()).select_from(Document).where(
            Document.owner_id == owner_id
        )
        total = (await self.db.execute(count_stmt)).scalar()

        stmt = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .options(selectinload(Document.chunks))
        )
        result = await self.db.execute(stmt)
        documents = list(result.scalars().all())

        return documents, total

    async def _find_duplicate(
        self, content_hash: str, owner_id: uuid.UUID
    ) -> Document | None:
        stmt = select(Document).where(
            Document.content_hash == content_hash,
            Document.owner_id == owner_id,
            Document.status != DocumentStatus.FAILED,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
