"""SynthesisAgent: Combines information from multiple sources into a coherent response."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.agents.state import AgentState

logger = get_logger(__name__)
settings = get_settings()

SYNTHESIS_SYSTEM = """You are an expert research synthesizer. Your task is to combine information
from multiple document sources into a clear, comprehensive answer.

Rules:
1. Reference sources using [Source N] notation based on the source numbers provided.
2. If sources contain contradictory information, acknowledge and explain the differences.
3. Synthesize across sources — don't just summarize each source sequentially.
4. Be precise and factual. Never add information not present in the sources.
5. If the sources don't fully answer the question, say what's missing.
6. Use clear structure: paragraphs, bullet points, or numbered lists where appropriate."""


class SynthesisAgent:
    """Combines retrieved chunks into a coherent, well-structured response."""

    async def run(self, state: AgentState) -> AgentState:
        state.log("SynthesisAgent", "Synthesizing response from retrieved chunks")

        chunks = state.reranked_chunks or state.retrieved_chunks
        if not chunks:
            state.draft_response = (
                "I couldn't find relevant information in the uploaded documents "
                "to answer your question. Please try rephrasing or upload relevant documents."
            )
            state.sources_used = []
            return state

        context_parts = []
        for i, chunk in enumerate(chunks):
            src_num = i + 1
            doc_id = chunk.get("document_id", "unknown")
            page = chunk.get("page_number", "?")
            content = chunk.get("content_preview") or chunk.get("content", "")
            context_parts.append(
                f"[Source {src_num}] (Document: {doc_id}, Page: {page})\n{content}"
            )

        context = "\n\n---\n\n".join(context_parts)

        messages = []
        for msg in state.chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({
            "role": "user",
            "content": (
                f"Based on the following document excerpts, answer the question thoroughly.\n\n"
                f"DOCUMENT EXCERPTS:\n{context}\n\n"
                f"QUESTION: {state.query}"
            ),
        })

        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=SYNTHESIS_SYSTEM,
            messages=messages,
        )

        state.draft_response = response.content[0].text
        state.sources_used = [
            {
                "source_index": i + 1,
                "document_id": c.get("document_id"),
                "chunk_index": c.get("chunk_index"),
                "page_number": c.get("page_number"),
                "section_title": c.get("section_title", ""),
                "content_preview": (c.get("content_preview") or c.get("content", ""))[:200],
                "score": c.get("combined_score", c.get("score", 0)),
            }
            for i, c in enumerate(chunks)
        ]

        state.log(
            "SynthesisAgent",
            f"Draft: {len(state.draft_response)} chars, {len(state.sources_used)} sources",
        )
        return state
