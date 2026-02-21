"""Shared state definition for the multi-agent graph."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Immutable state passed through the agent graph."""

    # Input
    query: str = ""
    owner_id: str = ""
    document_ids: list[str] = field(default_factory=list)
    chat_history: list[dict[str, str]] = field(default_factory=list)

    # Retrieval
    search_queries: list[str] = field(default_factory=list)
    retrieval_strategy: str = "hybrid"  # hybrid | dense | sparse
    retrieved_chunks: list[dict[str, Any]] = field(default_factory=list)
    reranked_chunks: list[dict[str, Any]] = field(default_factory=list)

    # Synthesis
    draft_response: str = ""
    sources_used: list[dict[str, Any]] = field(default_factory=list)

    # Citation
    cited_response: str = ""
    citation_verified: bool = False

    # Reflection
    reflection_notes: str = ""
    needs_revision: bool = False
    revision_count: int = 0
    max_revisions: int = 2

    # Final
    final_response: str = ""
    final_sources: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: int = 0
    agent_trace: list[str] = field(default_factory=list)

    def log(self, agent: str, message: str) -> None:
        self.agent_trace.append(f"[{agent}] {message}")
