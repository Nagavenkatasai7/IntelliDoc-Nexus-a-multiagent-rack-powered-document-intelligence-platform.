"""RetrievalAgent: Optimizes search queries and selects retrieval strategy."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.agents.state import AgentState
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

logger = get_logger(__name__)
settings = get_settings()

QUERY_EXPANSION_PROMPT = """You are a search query optimizer. Given a user question, generate 2-3
alternative search queries that would help find relevant information in a document collection.

User question: {query}

Return ONLY the queries, one per line. No numbering, no explanations."""


class RetrievalAgent:
    """Optimizes search queries, selects retrieval strategy, and fetches relevant chunks."""

    def __init__(
        self,
        vector_store: VectorStoreService,
        bm25_service: BM25SearchService,
    ):
        self.vector_store = vector_store
        self.bm25_service = bm25_service

    async def run(self, state: AgentState) -> AgentState:
        state.log("RetrievalAgent", "Starting retrieval")

        # Step 1: Query expansion using Claude
        expanded_queries = await self._expand_query(state.query)
        state.search_queries = [state.query] + expanded_queries
        state.log("RetrievalAgent", f"Expanded to {len(state.search_queries)} queries")

        # Step 2: Select retrieval strategy
        state.retrieval_strategy = self._select_strategy(state.query)
        state.log("RetrievalAgent", f"Strategy: {state.retrieval_strategy}")

        # Step 3: Execute retrieval across all expanded queries
        all_chunks: dict[str, dict[str, Any]] = {}
        owner_id = uuid.UUID(state.owner_id)
        doc_ids = [uuid.UUID(d) for d in state.document_ids] if state.document_ids else None

        for query in state.search_queries:
            if state.retrieval_strategy in ("hybrid", "dense"):
                try:
                    dense_results = await self.vector_store.search(
                        query=query, owner_id=owner_id, top_k=5, filter_document_ids=doc_ids
                    )
                    for r in dense_results:
                        key = r.get("vector_id", "")
                        if key not in all_chunks:
                            all_chunks[key] = {**r, "dense_score": r.get("score", 0)}
                        else:
                            all_chunks[key]["dense_score"] = max(
                                all_chunks[key].get("dense_score", 0), r.get("score", 0)
                            )
                except RuntimeError:
                    state.log("RetrievalAgent", "Pinecone not configured, skipping dense search")

            if state.retrieval_strategy in ("hybrid", "sparse"):
                namespace = state.owner_id
                filter_ids = [str(d) for d in state.document_ids] if state.document_ids else None
                sparse_results = self.bm25_service.search(
                    query=query, namespace=namespace, top_k=5, filter_document_ids=filter_ids
                )
                for r in sparse_results:
                    key = f"{r.get('document_id')}_{r.get('chunk_index')}"
                    if key not in all_chunks:
                        all_chunks[key] = {**r, "sparse_score": r.get("bm25_score", 0)}
                    else:
                        all_chunks[key]["sparse_score"] = max(
                            all_chunks[key].get("sparse_score", 0), r.get("bm25_score", 0)
                        )

        scored = self._rank_fusion(list(all_chunks.values()))
        state.retrieved_chunks = scored[:10]
        state.log("RetrievalAgent", f"Retrieved {len(state.retrieved_chunks)} unique chunks")

        return state

    async def _expand_query(self, query: str) -> list[str]:
        """Use Claude to generate alternative search queries."""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": QUERY_EXPANSION_PROMPT.format(query=query),
                }],
            )
            text = response.content[0].text.strip()
            queries = [q.strip() for q in text.split("\n") if q.strip()]
            return queries[:3]
        except Exception as e:
            logger.warning("query_expansion_failed", error=str(e))
            return []

    @staticmethod
    def _select_strategy(query: str) -> str:
        words = query.split()
        has_quotes = '"' in query
        if has_quotes or len(words) <= 3:
            return "hybrid"
        if any(w in query.lower() for w in ["definition", "what is", "meaning of"]):
            return "sparse"
        return "hybrid"

    @staticmethod
    def _rank_fusion(chunks: list[dict], k: int = 60) -> list[dict]:
        for chunk in chunks:
            dense = chunk.get("dense_score", 0)
            sparse = chunk.get("sparse_score", 0)
            chunk["combined_score"] = dense * 0.6 + min(sparse / 20.0, 1.0) * 0.4

        chunks.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        return chunks
