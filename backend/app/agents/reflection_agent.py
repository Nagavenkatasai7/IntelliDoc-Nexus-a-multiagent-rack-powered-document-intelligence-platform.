"""ReflectionAgent: Self-critiques responses for accuracy and completeness."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.agents.state import AgentState

logger = get_logger(__name__)
settings = get_settings()

REFLECTION_SYSTEM = """You are a quality assurance reviewer for AI-generated responses about documents.

Evaluate the response on these criteria:
1. **Accuracy**: Does the response match what the sources say?
2. **Completeness**: Does it address all parts of the question?
3. **Citation quality**: Are sources properly referenced?
4. **Clarity**: Is the response well-structured and easy to follow?
5. **Hallucination check**: Does it contain information NOT in the sources?

Respond in this exact format:
VERDICT: PASS or REVISE
ISSUES: (list issues if REVISE, "None" if PASS)
SUGGESTIONS: (specific improvement suggestions if REVISE, "None" if PASS)"""


class ReflectionAgent:
    """Self-critiques responses and decides if revision is needed."""

    async def run(self, state: AgentState) -> AgentState:
        state.log("ReflectionAgent", f"Reviewing (revision {state.revision_count})")

        response_to_check = state.cited_response or state.draft_response
        if not response_to_check:
            state.needs_revision = False
            return state

        source_summaries = []
        for src in state.sources_used[:5]:
            source_summaries.append(
                f"[Source {src['source_index']}]: {src['content_preview']}"
            )

        messages = [{
            "role": "user",
            "content": (
                f"QUESTION: {state.query}\n\n"
                f"AVAILABLE SOURCES:\n" + "\n".join(source_summaries) + "\n\n"
                f"RESPONSE TO REVIEW:\n{response_to_check}\n\n"
                f"Evaluate this response."
            ),
        }]

        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            system=REFLECTION_SYSTEM,
            messages=messages,
        )

        review_text = response.content[0].text
        state.reflection_notes = review_text

        if "VERDICT: REVISE" in review_text and state.revision_count < state.max_revisions:
            state.needs_revision = True
            state.revision_count += 1
            state.log("ReflectionAgent", f"REVISE needed: revision #{state.revision_count}")
        else:
            state.needs_revision = False
            state.log("ReflectionAgent", "PASS — response quality acceptable")

        return state
