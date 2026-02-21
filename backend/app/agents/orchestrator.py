"""OrchestratorAgent: Routes queries through the multi-agent pipeline."""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.agents.state import AgentState
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.agents.citation_agent import CitationAgent
from app.agents.reflection_agent import ReflectionAgent
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

logger = get_logger(__name__)
settings = get_settings()


class OrchestratorAgent:
    """Executes the multi-agent workflow: retrieve -> synthesize -> cite -> reflect (loop)."""

    def __init__(
        self,
        vector_store: VectorStoreService,
        bm25_service: BM25SearchService,
    ):
        self.retrieval_agent = RetrievalAgent(vector_store, bm25_service)
        self.synthesis_agent = SynthesisAgent()
        self.citation_agent = CitationAgent()
        self.reflection_agent = ReflectionAgent()

    async def run(
        self,
        query: str,
        owner_id: uuid.UUID,
        document_ids: list[uuid.UUID] | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Execute the full multi-agent pipeline.

        Flow:
          retrieve -> synthesize -> cite -> reflect
                                              |
                                      needs_revision?
                                        yes -> synthesize (loop back)
                                        no  -> finalize
        """
        start = time.time()

        state = AgentState(
            query=query,
            owner_id=str(owner_id),
            document_ids=[str(d) for d in document_ids] if document_ids else [],
            chat_history=chat_history or [],
        )

        # Step 1: Retrieve
        state = await self.retrieval_agent.run(state)

        # Step 2-4: Synthesize -> Cite -> Reflect loop
        while True:
            state = await self.synthesis_agent.run(state)
            state = await self.citation_agent.run(state)
            state = await self.reflection_agent.run(state)

            if not state.needs_revision:
                break

        # Finalize
        state.final_response = state.cited_response or state.draft_response
        state.final_sources = state.sources_used
        state.log("Orchestrator", "Pipeline complete")

        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            "orchestrator_complete",
            query_len=len(query),
            revisions=state.revision_count,
            sources=len(state.final_sources),
            latency_ms=latency_ms,
        )

        return {
            "content": state.final_response,
            "sources": state.final_sources,
            "latency_ms": latency_ms,
            "agent_trace": state.agent_trace,
            "revisions": state.revision_count,
        }
