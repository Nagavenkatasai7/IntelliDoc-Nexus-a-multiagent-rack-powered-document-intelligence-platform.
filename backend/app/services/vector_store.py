from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VectorStoreService:
    """Manages vector storage and retrieval via Pinecone."""

    def __init__(self):
        self._index = None
        self._embedding_service = None

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            from app.services.embedding import EmbeddingService

            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @property
    def index(self):
        if self._index is None:
            if not settings.pinecone_api_key:
                raise RuntimeError(
                    "PINECONE_API_KEY not configured. "
                    "Set it in .env to enable vector search."
                )
            from pinecone import Pinecone, ServerlessSpec

            pc = Pinecone(api_key=settings.pinecone_api_key)

            existing = [idx.name for idx in pc.list_indexes()]
            if settings.pinecone_index_name not in existing:
                logger.info("creating_pinecone_index", name=settings.pinecone_index_name)
                pc.create_index(
                    name=settings.pinecone_index_name,
                    dimension=settings.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=settings.pinecone_environment),
                )

            self._index = pc.Index(settings.pinecone_index_name)
            logger.info("pinecone_index_ready", name=settings.pinecone_index_name)
        return self._index

    async def upsert_chunks(
        self,
        chunks: list[dict],
        document_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> list[str]:
        texts = [c["content"] for c in chunks]
        embeddings = self.embedding_service.embed_texts(texts)
        namespace = str(owner_id)

        vectors = []
        vector_ids = []
        for chunk, embedding in zip(chunks, embeddings):
            vector_id = f"{document_id}_{chunk['chunk_index']}"
            vector_ids.append(vector_id)
            metadata = {
                "document_id": str(document_id),
                "chunk_index": chunk["chunk_index"],
                "content_preview": chunk["content"][:1000],
                "token_count": chunk["token_count"],
            }
            # Pinecone rejects null values — only include non-None fields
            if chunk.get("page_number") is not None:
                metadata["page_number"] = chunk["page_number"]
            if chunk.get("section_title"):
                metadata["section_title"] = chunk["section_title"]
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata,
            })

        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self.index.upsert(vectors=batch, namespace=namespace)

        logger.info(
            "vectors_upserted",
            document_id=str(document_id),
            count=len(vectors),
        )
        return vector_ids

    async def search(
        self,
        query: str,
        owner_id: uuid.UUID,
        top_k: int = 10,
        filter_document_ids: list[uuid.UUID] | None = None,
    ) -> list[dict]:
        query_embedding = self.embedding_service.embed_query(query)
        namespace = str(owner_id)

        filter_dict = {}
        if filter_document_ids:
            filter_dict["document_id"] = {
                "$in": [str(did) for did in filter_document_ids]
            }

        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
        )

        matches = []
        for match in results.matches:
            matches.append({
                "vector_id": match.id,
                "score": match.score,
                "document_id": match.metadata.get("document_id"),
                "chunk_index": match.metadata.get("chunk_index"),
                "page_number": match.metadata.get("page_number"),
                "section_title": match.metadata.get("section_title"),
                "content_preview": match.metadata.get("content_preview"),
            })

        return matches

    async def delete_document_vectors(
        self, document_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        namespace = str(owner_id)
        self.index.delete(
            filter={"document_id": {"$eq": str(document_id)}},
            namespace=namespace,
        )
        logger.info("vectors_deleted", document_id=str(document_id))
