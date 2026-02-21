import re
from rank_bm25 import BM25Okapi

from app.core.logging import get_logger

logger = get_logger(__name__)


class BM25SearchService:
    """Sparse retrieval using BM25 algorithm for hybrid search."""

    def __init__(self):
        self._indices: dict[str, dict] = {}  # namespace -> {bm25, chunks}

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        # Simple stop word removal
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "and", "or"}
        return [t for t in tokens if t not in stop_words and len(t) > 1]

    def build_index(self, namespace: str, chunks: list[dict]) -> None:
        """Build BM25 index for a set of chunks."""
        tokenized_corpus = [self._tokenize(c["content"]) for c in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        self._indices[namespace] = {"bm25": bm25, "chunks": chunks}
        logger.info("bm25_index_built", namespace=namespace, doc_count=len(chunks))

    def add_to_index(self, namespace: str, chunks: list[dict]) -> None:
        """Add chunks to an existing BM25 index (rebuilds)."""
        existing = self._indices.get(namespace, {}).get("chunks", [])
        all_chunks = existing + chunks
        self.build_index(namespace, all_chunks)

    def search(
        self,
        query: str,
        namespace: str,
        top_k: int = 10,
        filter_document_ids: list[str] | None = None,
    ) -> list[dict]:
        """Search using BM25 scoring."""
        index_data = self._indices.get(namespace)
        if not index_data:
            return []

        bm25 = index_data["bm25"]
        chunks = index_data["chunks"]

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []

        scores = bm25.get_scores(tokenized_query)

        # Pair scores with chunks and filter
        scored_chunks = []
        for i, (score, chunk) in enumerate(zip(scores, chunks)):
            if filter_document_ids and chunk.get("document_id") not in filter_document_ids:
                continue
            if score > 0:
                scored_chunks.append({**chunk, "bm25_score": float(score)})

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_chunks[:top_k]

    def remove_document(self, namespace: str, document_id: str) -> None:
        """Remove a document's chunks from the index and rebuild."""
        index_data = self._indices.get(namespace)
        if not index_data:
            return
        remaining = [c for c in index_data["chunks"] if c.get("document_id") != document_id]
        if remaining:
            self.build_index(namespace, remaining)
        else:
            self._indices.pop(namespace, None)
