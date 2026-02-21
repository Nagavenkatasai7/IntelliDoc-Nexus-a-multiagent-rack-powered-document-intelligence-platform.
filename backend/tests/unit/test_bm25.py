import pytest
from app.services.bm25_search import BM25SearchService


class TestBM25Search:
    def setup_method(self):
        self.bm25 = BM25SearchService()
        self.chunks = [
            {"content": "Machine learning is a subset of artificial intelligence.", "document_id": "doc1", "chunk_index": 0},
            {"content": "Deep learning uses neural networks with many layers.", "document_id": "doc1", "chunk_index": 1},
            {"content": "Python is a popular programming language for data science.", "document_id": "doc2", "chunk_index": 0},
            {"content": "Natural language processing helps computers understand text.", "document_id": "doc2", "chunk_index": 1},
        ]
        self.bm25.build_index("test-ns", self.chunks)

    def test_basic_search(self):
        results = self.bm25.search("machine learning", "test-ns", top_k=2)
        assert len(results) > 0
        assert results[0]["content"] == self.chunks[0]["content"]

    def test_search_returns_scores(self):
        results = self.bm25.search("neural networks", "test-ns")
        for r in results:
            assert "bm25_score" in r
            assert r["bm25_score"] > 0

    def test_search_empty_namespace(self):
        results = self.bm25.search("test", "nonexistent-ns")
        assert results == []

    def test_filter_by_document(self):
        results = self.bm25.search(
            "learning", "test-ns", filter_document_ids=["doc2"]
        )
        for r in results:
            assert r["document_id"] == "doc2"

    def test_top_k_limit(self):
        results = self.bm25.search("learning", "test-ns", top_k=1)
        assert len(results) <= 1

    def test_remove_document(self):
        self.bm25.remove_document("test-ns", "doc1")
        results = self.bm25.search("machine learning", "test-ns")
        for r in results:
            assert r["document_id"] != "doc1"

    def test_add_to_index(self):
        new_chunks = [
            {"content": "Reinforcement learning trains agents via rewards.", "document_id": "doc3", "chunk_index": 0}
        ]
        self.bm25.add_to_index("test-ns", new_chunks)
        results = self.bm25.search("reinforcement rewards", "test-ns")
        assert any(r["document_id"] == "doc3" for r in results)
