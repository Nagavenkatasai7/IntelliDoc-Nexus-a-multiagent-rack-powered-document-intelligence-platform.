from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("loading_embedding_model", model=settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
    return _model


class EmbeddingService:
    """Generate embeddings for text using sentence-transformers."""

    def __init__(self):
        self._model = None
        self.dimension = settings.embedding_dimension

    @property
    def model(self):
        if self._model is None:
            self._model = get_embedding_model()
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Batch in groups of 32 to avoid memory issues on large documents
        all_embeddings = []
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
            all_embeddings.extend(embeddings.tolist())
        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        embedding = self.model.encode(query, normalize_embeddings=True, show_progress_bar=False)
        return embedding.tolist()

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        import numpy as np

        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))
