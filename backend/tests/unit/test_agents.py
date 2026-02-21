"""Tests for multi-agent pipeline components — state, strategies, fusion, orchestrator logic."""

import pytest
from app.agents.state import AgentState
from app.agents.retrieval_agent import RetrievalAgent


class TestAgentState:
    def test_default_state(self):
        state = AgentState()
        assert state.query == ""
        assert state.retrieved_chunks == []
        assert state.needs_revision is False
        assert state.revision_count == 0
        assert state.max_revisions == 2

    def test_log_traces(self):
        state = AgentState(query="test")
        state.log("TestAgent", "Step 1")
        state.log("TestAgent", "Step 2")
        assert len(state.agent_trace) == 2
        assert "[TestAgent] Step 1" in state.agent_trace[0]

    def test_state_mutation(self):
        state = AgentState(query="How does ML work?")
        state.retrieved_chunks = [{"content": "ML is..."}]
        state.draft_response = "Machine learning works by..."
        state.needs_revision = True
        state.revision_count = 1
        assert len(state.retrieved_chunks) == 1
        assert state.needs_revision is True

    def test_state_with_document_ids(self):
        state = AgentState(
            query="test",
            owner_id="owner-1",
            document_ids=["doc-1", "doc-2"],
        )
        assert len(state.document_ids) == 2

    def test_max_revisions_default(self):
        state = AgentState()
        assert state.max_revisions == 2

    def test_custom_max_revisions(self):
        state = AgentState(max_revisions=5)
        assert state.max_revisions == 5


class TestRetrievalStrategy:
    def test_hybrid_for_short_query(self):
        assert RetrievalAgent._select_strategy("what is AI") == "hybrid"

    def test_hybrid_for_quoted_query(self):
        assert RetrievalAgent._select_strategy('"exact phrase" in context') == "hybrid"

    def test_sparse_for_definition_query(self):
        assert RetrievalAgent._select_strategy("what is the definition of machine learning") == "sparse"

    def test_hybrid_for_long_query(self):
        result = RetrievalAgent._select_strategy("explain the process of training neural networks")
        assert result == "hybrid"

    def test_sparse_for_meaning_query(self):
        assert RetrievalAgent._select_strategy("meaning of backpropagation in deep learning") == "sparse"


class TestRankFusion:
    def test_combined_scoring(self):
        chunks = [
            {"content": "A", "dense_score": 0.9, "sparse_score": 10.0},
            {"content": "B", "dense_score": 0.5, "sparse_score": 0.0},
        ]
        ranked = RetrievalAgent._rank_fusion(chunks)
        assert ranked[0]["content"] == "A"
        assert ranked[0]["combined_score"] > ranked[1]["combined_score"]

    def test_dense_only_scoring(self):
        chunks = [{"content": "X", "dense_score": 0.8}]
        ranked = RetrievalAgent._rank_fusion(chunks)
        assert ranked[0]["combined_score"] == 0.8 * 0.6

    def test_sparse_only_scoring(self):
        chunks = [{"content": "Y", "sparse_score": 20.0}]
        ranked = RetrievalAgent._rank_fusion(chunks)
        # sparse contribution: min(20/20, 1.0) * 0.4 = 0.4
        assert ranked[0]["combined_score"] == pytest.approx(0.4)

    def test_empty_chunks(self):
        assert RetrievalAgent._rank_fusion([]) == []

    def test_sorting_order(self):
        chunks = [
            {"content": "Low", "dense_score": 0.1, "sparse_score": 1.0},
            {"content": "High", "dense_score": 0.95, "sparse_score": 15.0},
            {"content": "Mid", "dense_score": 0.5, "sparse_score": 8.0},
        ]
        ranked = RetrievalAgent._rank_fusion(chunks)
        scores = [c["combined_score"] for c in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_sparse_score_capped(self):
        # sparse_score / 20 capped at 1.0
        chunks = [{"content": "Z", "sparse_score": 100.0}]
        ranked = RetrievalAgent._rank_fusion(chunks)
        # max sparse contribution = 1.0 * 0.4 = 0.4
        assert ranked[0]["combined_score"] == pytest.approx(0.4)


class TestSynthesisAgentNoChunks:
    """Test SynthesisAgent behavior with empty chunks (no API call needed)."""

    @pytest.mark.asyncio
    async def test_no_chunks_returns_fallback(self):
        from app.agents.synthesis_agent import SynthesisAgent

        agent = SynthesisAgent()
        state = AgentState(query="What is something?")
        # No chunks retrieved
        result = await agent.run(state)
        assert "couldn't find" in result.draft_response.lower()
        assert result.sources_used == []


class TestCitationAgentNoSources:
    """Test CitationAgent behavior with no sources (no API call needed)."""

    @pytest.mark.asyncio
    async def test_no_sources_passes_through(self):
        from app.agents.citation_agent import CitationAgent

        agent = CitationAgent()
        state = AgentState(query="test", draft_response="Answer", sources_used=[])
        result = await agent.run(state)
        assert result.cited_response == "Answer"
        assert result.citation_verified is True

    @pytest.mark.asyncio
    async def test_no_draft_passes_through(self):
        from app.agents.citation_agent import CitationAgent

        agent = CitationAgent()
        state = AgentState(query="test")
        result = await agent.run(state)
        assert result.cited_response == ""
        assert result.citation_verified is True


class TestReflectionAgentNoResponse:
    """Test ReflectionAgent behavior with empty response (no API call needed)."""

    @pytest.mark.asyncio
    async def test_empty_response_no_revision(self):
        from app.agents.reflection_agent import ReflectionAgent

        agent = ReflectionAgent()
        state = AgentState(query="test")
        result = await agent.run(state)
        assert result.needs_revision is False
