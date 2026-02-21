"""CitationAgent: Verifies facts and ensures source citations are accurate."""

from __future__ import annotations

import re

from app.core.config import get_settings
from app.core.logging import get_logger
from app.agents.state import AgentState

logger = get_logger(__name__)
settings = get_settings()

CITATION_SYSTEM = """You are a citation verification specialist. Your job is to review a response
and ensure every factual claim is properly cited with [Source N] references.

Given:
1. The original sources with their [Source N] markers
2. A draft response

Your task:
- Check that all factual claims in the response have appropriate [Source N] citations
- Add missing citations where claims are made without references
- Remove or flag citations that don't match the source content
- Keep the response structure and content intact — only adjust citations
- If a claim cannot be verified from any source, mark it as [Unverified]

Return the corrected response. Do NOT add commentary — just the corrected text."""


class CitationAgent:
    """Verifies and corrects source citations in the synthesized response."""

    async def run(self, state: AgentState) -> AgentState:
        state.log("CitationAgent", "Verifying citations")

        if not state.draft_response or not state.sources_used:
            state.cited_response = state.draft_response
            state.citation_verified = True
            return state

        source_context = []
        for src in state.sources_used:
            source_context.append(
                f"[Source {src['source_index']}]: {src['content_preview']}"
            )

        messages = [{
            "role": "user",
            "content": (
                f"SOURCES:\n" + "\n".join(source_context) + "\n\n"
                f"DRAFT RESPONSE:\n{state.draft_response}\n\n"
                f"Verify and correct all citations in the response."
            ),
        }]

        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=CITATION_SYSTEM,
            messages=messages,
        )

        state.cited_response = response.content[0].text
        state.citation_verified = True

        citations_found = set(re.findall(r"\[Source (\d+)\]", state.cited_response))
        state.log(
            "CitationAgent",
            f"Verified: {len(citations_found)} unique source refs in response",
        )

        return state
