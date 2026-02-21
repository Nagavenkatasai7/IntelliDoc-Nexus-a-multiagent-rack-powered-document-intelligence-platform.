import re

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SemanticChunker:
    """Splits text into semantically meaningful chunks preserving context boundaries."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self._tokenizer = None

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            try:
                import tiktoken
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                self._tokenizer = None
        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # Fallback: ~4 chars per token approximation
        return len(text) // 4

    def chunk_document(self, pages: list[dict]) -> list[dict]:
        """Split document pages into semantic chunks.

        Each chunk dict contains: content, token_count, page_number, section_title, chunk_index
        """
        chunks = []
        chunk_index = 0

        for page in pages:
            page_number = page.get("page_number")
            content = page.get("content", "")
            if not content.strip():
                continue

            # Split into semantic sections
            sections = self._split_into_sections(content)

            for section_title, section_text in sections:
                if not section_text.strip():
                    continue

                # If section fits in one chunk, keep it whole
                token_count = self.count_tokens(section_text)
                if token_count <= self.chunk_size:
                    chunks.append({
                        "content": section_text.strip(),
                        "token_count": token_count,
                        "page_number": page_number,
                        "section_title": section_title,
                        "chunk_index": chunk_index,
                    })
                    chunk_index += 1
                else:
                    # Split large sections with overlap
                    sub_chunks = self._split_with_overlap(section_text)
                    for sub in sub_chunks:
                        token_count = self.count_tokens(sub)
                        chunks.append({
                            "content": sub.strip(),
                            "token_count": token_count,
                            "page_number": page_number,
                            "section_title": section_title,
                            "chunk_index": chunk_index,
                        })
                        chunk_index += 1

        logger.info("document_chunked", total_chunks=len(chunks))
        return chunks

    def _split_into_sections(self, text: str) -> list[tuple[str | None, str]]:
        """Split text into sections based on headings and structural markers."""
        # Match common heading patterns
        heading_pattern = re.compile(
            r"^(#{1,6}\s+.+|[A-Z][A-Z\s]{2,}$|\d+\.\s+[A-Z].+|Chapter\s+\d+.*)$",
            re.MULTILINE,
        )

        sections = []
        matches = list(heading_pattern.finditer(text))

        if not matches:
            return [(None, text)]

        # Text before first heading
        if matches[0].start() > 0:
            preamble = text[: matches[0].start()]
            if preamble.strip():
                sections.append((None, preamble))

        for i, match in enumerate(matches):
            title = match.group().strip().lstrip("#").strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end]
            if section_text.strip():
                sections.append((title, section_text))

        if not sections:
            return [(None, text)]

        return sections

    def _split_with_overlap(self, text: str) -> list[str]:
        """Split text into overlapping chunks at sentence boundaries."""
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))

                # Calculate overlap: keep last sentences up to overlap token count
                overlap_tokens = 0
                overlap_start = len(current_chunk)
                for j in range(len(current_chunk) - 1, -1, -1):
                    t = self.count_tokens(current_chunk[j])
                    if overlap_tokens + t > self.chunk_overlap:
                        break
                    overlap_tokens += t
                    overlap_start = j

                current_chunk = current_chunk[overlap_start:]
                current_tokens = sum(self.count_tokens(s) for s in current_chunk)

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences, preserving abbreviations and decimals."""
        # Split on sentence-ending punctuation followed by space and capital letter
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        return [s.strip() for s in sentences if s.strip()]
