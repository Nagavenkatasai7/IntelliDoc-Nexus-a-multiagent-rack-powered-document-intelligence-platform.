"""Tests for the RAG service — hybrid search, RRF, context building, message building."""

import pytest
from app.services.rag import RAGService


class TestReciprocalRankFusion:
    def test_rrf_combines_results(self):
        dense = [
            {"vector_id": "a", "content": "Dense result A", "score": 0.9},
            {"vector_id": "b", "content": "Dense result B", "score": 0.7},
        ]
        sparse = [
            {"document_id": "doc1", "chunk_index": 0, "content": "Sparse result C", "bm25_score": 5.0},
            {"document_id": "doc1", "chunk_index": 1, "content": "Same as B", "bm25_score": 3.0},
        ]
        results = RAGService._reciprocal_rank_fusion(dense, sparse, top_k=5)
        assert len(results) >= 2
        for r in results:
            assert "rrf_score" in r
            assert r["rrf_score"] > 0

    def test_rrf_respects_top_k(self):
        dense = [
            {"vector_id": f"d{i}", "content": f"Result {i}", "score": 0.5}
            for i in range(10)
        ]
        results = RAGService._reciprocal_rank_fusion(dense, [], top_k=3)
        assert len(results) == 3

    def test_rrf_empty_inputs(self):
        results = RAGService._reciprocal_rank_fusion([], [], top_k=5)
        assert results == []

    def test_rrf_dense_only(self):
        dense = [
            {"vector_id": "x", "content": "Only dense", "score": 0.95},
        ]
        results = RAGService._reciprocal_rank_fusion(dense, [], top_k=5)
        assert len(results) == 1
        assert results[0]["rrf_score"] > 0

    def test_rrf_sparse_only(self):
        sparse = [
            {"document_id": "doc1", "chunk_index": 0, "content": "Only sparse", "bm25_score": 4.0},
        ]
        results = RAGService._reciprocal_rank_fusion([], sparse, top_k=5)
        assert len(results) == 1

    def test_rrf_scores_decrease_with_rank(self):
        dense = [
            {"vector_id": "a", "content": "First", "score": 0.9},
            {"vector_id": "b", "content": "Second", "score": 0.8},
            {"vector_id": "c", "content": "Third", "score": 0.7},
        ]
        results = RAGService._reciprocal_rank_fusion(dense, [], top_k=3)
        scores = [r["rrf_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestBuildContext:
    def test_builds_formatted_context(self):
        contexts = [
            {"document_id": "doc1", "page_number": 1, "content": "Hello world"},
            {"document_id": "doc2", "page_number": 3, "content_preview": "Preview text"},
        ]
        result = RAGService._build_context(contexts)
        assert "[Source 1]" in result
        assert "[Source 2]" in result
        assert "doc1" in result
        assert "Preview text" in result
        assert "---" in result

    def test_empty_contexts(self):
        result = RAGService._build_context([])
        assert result == ""

    def test_missing_page_number(self):
        contexts = [{"document_id": "doc1", "content": "No page"}]
        result = RAGService._build_context(contexts)
        assert "Page: ?" in result


class TestBuildMessages:
    def test_basic_message(self):
        messages = RAGService._build_messages("What is AI?", "Some context")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "What is AI?" in messages[0]["content"]
        assert "Some context" in messages[0]["content"]

    def test_with_chat_history(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]
        messages = RAGService._build_messages("Follow up", "Context", history)
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hi"
        assert messages[-1]["role"] == "user"
        assert "Follow up" in messages[-1]["content"]

    def test_chat_history_truncated_to_10(self):
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Msg {i}"}
            for i in range(20)
        ]
        messages = RAGService._build_messages("Question", "Ctx", history)
        # 10 history + 1 question = 11
        assert len(messages) == 11


class TestExtractSources:
    def test_extracts_source_info(self):
        contexts = [
            {
                "document_id": "doc1",
                "chunk_index": 0,
                "page_number": 1,
                "section_title": "Intro",
                "content": "Full content that is long " * 20,
                "rrf_score": 0.5,
            }
        ]
        sources = RAGService._extract_sources(contexts)
        assert len(sources) == 1
        assert sources[0]["source_index"] == 1
        assert sources[0]["document_id"] == "doc1"
        assert sources[0]["score"] == 0.5
        assert len(sources[0]["content_preview"]) <= 200

    def test_multiple_sources(self):
        contexts = [
            {"document_id": f"doc{i}", "chunk_index": i, "content": f"Content {i}"}
            for i in range(5)
        ]
        sources = RAGService._extract_sources(contexts)
        assert len(sources) == 5
        assert sources[0]["source_index"] == 1
        assert sources[4]["source_index"] == 5

    def test_fallback_score(self):
        contexts = [{"document_id": "d", "content": "c", "score": 0.8}]
        sources = RAGService._extract_sources(contexts)
        assert sources[0]["score"] == 0.8


class TestSystemPrompt:
    def test_system_prompt_content(self):
        prompt = RAGService._system_prompt()
        assert "IntelliDoc Nexus" in prompt
        assert "[Source N]" in prompt
        assert "fabricate" in prompt
