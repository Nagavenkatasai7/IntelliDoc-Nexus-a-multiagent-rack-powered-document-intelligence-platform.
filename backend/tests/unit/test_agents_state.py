import pytest
from app.agents.state import AgentState


class TestAgentState:
    def test_default_state(self):
        state = AgentState()
        assert state.query == ""
        assert state.retrieved_chunks == []
        assert state.revision_count == 0
        assert state.max_revisions == 2
        assert state.needs_revision is False

    def test_log_trace(self):
        state = AgentState()
        state.log("TestAgent", "test message")
        assert len(state.agent_trace) == 1
        assert "[TestAgent] test message" == state.agent_trace[0]

    def test_multiple_logs(self):
        state = AgentState(query="test query")
        state.log("A", "step 1")
        state.log("B", "step 2")
        state.log("C", "step 3")
        assert len(state.agent_trace) == 3
        assert state.query == "test query"

    def test_state_with_data(self):
        state = AgentState(
            query="What is machine learning?",
            owner_id="user-1",
            document_ids=["doc-1", "doc-2"],
        )
        assert state.query == "What is machine learning?"
        assert len(state.document_ids) == 2
