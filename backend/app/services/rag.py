import uuid
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

logger = get_logger(__name__)
settings = get_settings()


def _get_anthropic_client():
    import anthropic
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


class RAGService:
    """Retrieval-Augmented Generation service combining retrieval with Claude."""

    def __init__(
        self,
        vector_store: VectorStoreService,
        bm25_service: BM25SearchService,
        db: AsyncSession | None = None,
    ):
        self.vector_store = vector_store
        self.bm25_service = bm25_service
        self.db = db

    async def _enrich_contexts(self, contexts: list[dict]) -> None:
        """Enrich context dicts with document names and full chunk content from DB."""
        if not self.db:
            return
        from app.models.document import Document, DocumentChunk

        # Resolve document names
        doc_ids = list({c.get("document_id") for c in contexts if c.get("document_id")})
        if not doc_ids:
            return
        doc_uuids = [uuid.UUID(d) for d in doc_ids]
        stmt = select(Document.id, Document.original_filename).where(Document.id.in_(doc_uuids))
        result = await self.db.execute(stmt)
        name_map = {str(row[0]): row[1] for row in result}

        # Fetch full chunk content from DB (content_preview in Pinecone is truncated)
        chunk_keys = [
            (c.get("document_id"), c.get("chunk_index"))
            for c in contexts
            if c.get("document_id") and c.get("chunk_index") is not None
        ]
        content_map: dict[tuple, str] = {}
        if chunk_keys:
            from sqlalchemy import and_, tuple_
            # Fetch full content for matching chunks
            chunk_stmt = select(
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
            ).where(DocumentChunk.document_id.in_(doc_uuids))
            chunk_result = await self.db.execute(chunk_stmt)
            for row in chunk_result:
                content_map[(str(row[0]), row[1])] = row[2]

        for ctx in contexts:
            ctx["document_name"] = name_map.get(ctx.get("document_id", ""), "")
            # Replace truncated content_preview with full content from DB
            full_content = content_map.get(
                (ctx.get("document_id"), ctx.get("chunk_index"))
            )
            if full_content:
                ctx["full_content"] = full_content

    async def query(
        self,
        question: str,
        owner_id: uuid.UUID,
        document_ids: list[uuid.UUID] | None = None,
        chat_history: list[dict] | None = None,
        top_k: int = 8,
    ) -> dict:
        """Execute RAG pipeline: retrieve context, generate answer with citations."""
        start = time.time()

        # 1. Retrieve relevant chunks via hybrid search
        contexts = await self._hybrid_search(
            query=question,
            owner_id=owner_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        if not contexts:
            return {
                "content": "I couldn't find any relevant information in the uploaded documents to answer your question. Please make sure you've uploaded relevant documents.",
                "sources": [],
                "latency_ms": int((time.time() - start) * 1000),
            }

        # 2. Resolve document names for source references
        await self._enrich_contexts(contexts)

        # 3. Build context string with source markers
        context_str = self._build_context(contexts)

        # 3. Generate response with Claude
        messages = self._build_messages(question, context_str, chat_history)

        response = await _get_anthropic_client().messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=self._system_prompt(),
            messages=messages,
        )

        content = response.content[0].text

        # 4. Extract source references
        sources = self._extract_sources(contexts)

        latency_ms = int((time.time() - start) * 1000)
        logger.info(
            "rag_query_complete",
            question_len=len(question),
            context_chunks=len(contexts),
            response_len=len(content),
            latency_ms=latency_ms,
        )

        return {
            "content": content,
            "sources": sources,
            "latency_ms": latency_ms,
        }

    async def query_stream(
        self,
        question: str,
        owner_id: uuid.UUID,
        document_ids: list[uuid.UUID] | None = None,
        chat_history: list[dict] | None = None,
        top_k: int = 8,
    ):
        """Stream RAG response for real-time UI updates."""
        contexts = await self._hybrid_search(
            query=question,
            owner_id=owner_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        if not contexts:
            yield {
                "type": "text",
                "content": "I couldn't find any relevant information in the uploaded documents.",
            }
            yield {"type": "sources", "sources": []}
            yield {"type": "done"}
            return

        await self._enrich_contexts(contexts)
        context_str = self._build_context(contexts)
        messages = self._build_messages(question, context_str, chat_history)

        async with _get_anthropic_client().messages.stream(
            model=settings.claude_model,
            max_tokens=4096,
            system=self._system_prompt(),
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield {"type": "text", "content": text}

        sources = self._extract_sources(contexts)
        yield {"type": "sources", "sources": sources}
        yield {"type": "done"}

    async def _hybrid_search(
        self,
        query: str,
        owner_id: uuid.UUID,
        document_ids: list[uuid.UUID] | None = None,
        top_k: int = 10,
    ) -> list[dict]:
        """Combine dense (vector) and sparse (BM25) search results."""
        # Dense search via Pinecone
        dense_results = await self.vector_store.search(
            query=query,
            owner_id=owner_id,
            top_k=top_k,
            filter_document_ids=document_ids,
        )

        # Sparse search via BM25
        namespace = str(owner_id)
        filter_ids = [str(d) for d in document_ids] if document_ids else None
        sparse_results = self.bm25_service.search(
            query=query,
            namespace=namespace,
            top_k=top_k,
            filter_document_ids=filter_ids,
        )

        # Reciprocal Rank Fusion
        return self._reciprocal_rank_fusion(dense_results, sparse_results, top_k)

    @staticmethod
    def _reciprocal_rank_fusion(
        dense: list[dict],
        sparse: list[dict],
        top_k: int,
        k: int = 60,
    ) -> list[dict]:
        """Combine ranked lists using Reciprocal Rank Fusion (RRF)."""
        scores: dict[str, float] = {}
        result_map: dict[str, dict] = {}

        for rank, item in enumerate(dense):
            key = item.get("vector_id", f"dense_{rank}")
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            result_map[key] = item

        for rank, item in enumerate(sparse):
            key = f"{item.get('document_id')}_{item.get('chunk_index')}"
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            if key not in result_map:
                result_map[key] = item

        sorted_keys = sorted(scores, key=lambda x: scores[x], reverse=True)
        results = []
        for key in sorted_keys[:top_k]:
            item = result_map[key]
            item["rrf_score"] = scores[key]
            results.append(item)

        return results

    @staticmethod
    def _build_context(contexts: list[dict]) -> str:
        parts = []
        for i, ctx in enumerate(contexts):
            source_id = i + 1
            doc_name = ctx.get("document_name") or ctx.get("document_id", "unknown")
            page = ctx.get("page_number", "?")
            # Prefer full content from DB, fall back to content_preview from Pinecone
            content = (
                ctx.get("full_content")
                or ctx.get("content_preview")
                or ctx.get("content", "")
            )
            parts.append(
                f"[Source {source_id}] (Document: {doc_name}, Page: {page})\n{content}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _build_messages(
        question: str,
        context: str,
        chat_history: list[dict] | None = None,
    ) -> list[dict]:
        messages = []
        if chat_history:
            for msg in chat_history[-10:]:  # Keep last 10 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})

        user_msg = (
            f"Based on the following document excerpts, answer the question. "
            f"Always cite your sources using [Source N] notation.\n\n"
            f"DOCUMENT EXCERPTS:\n{context}\n\n"
            f"QUESTION: {question}"
        )
        messages.append({"role": "user", "content": user_msg})
        return messages

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are IntelliDoc Nexus, an intelligent document analysis assistant. "
            "Your role is to answer questions based ONLY on the provided document excerpts. "
            "Follow these rules:\n"
            "1. Always cite sources using [Source N] notation when referencing information.\n"
            "2. If the documents don't contain enough information to answer, say so clearly.\n"
            "3. Be precise and factual - never fabricate information.\n"
            "4. When synthesizing from multiple sources, reference each source.\n"
            "5. Format responses clearly with paragraphs and bullet points when appropriate."
        )

    @staticmethod
    def _extract_sources(contexts: list[dict]) -> list[dict]:
        sources = []
        for i, ctx in enumerate(contexts):
            score = ctx.get("rrf_score", ctx.get("score", 0))
            sources.append({
                "source_index": i + 1,
                "document_id": ctx.get("document_id"),
                "document_name": ctx.get("document_name", ""),
                "chunk_index": ctx.get("chunk_index"),
                "page_number": ctx.get("page_number"),
                "section_title": ctx.get("section_title", ""),
                "content_preview": (ctx.get("content_preview") or ctx.get("content", ""))[:200],
                "score": score,
                "relevance_score": score,
            })
        return sources
