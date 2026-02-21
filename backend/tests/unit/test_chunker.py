import pytest
from app.services.chunker import SemanticChunker


class TestSemanticChunker:
    def setup_method(self):
        self.chunker = SemanticChunker(chunk_size=50, chunk_overlap=10)

    def test_chunk_simple_text(self):
        pages = [{"page_number": 1, "content": "This is a simple test document. It has two sentences."}]
        chunks = self.chunker.chunk_document(pages)
        assert len(chunks) >= 1
        assert chunks[0]["page_number"] == 1
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["token_count"] > 0

    def test_empty_pages(self):
        pages = [{"page_number": 1, "content": ""}]
        chunks = self.chunker.chunk_document(pages)
        assert len(chunks) == 0

    def test_preserves_page_numbers(self):
        pages = [
            {"page_number": 1, "content": "Content on page one."},
            {"page_number": 2, "content": "Content on page two."},
        ]
        chunks = self.chunker.chunk_document(pages)
        page_numbers = {c["page_number"] for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_sections_detected(self):
        text = """# Introduction
This is the introduction section with some content.

# Methods
This describes the methods used in the study."""
        pages = [{"page_number": 1, "content": text}]
        chunks = self.chunker.chunk_document(pages)
        sections = [c.get("section_title") for c in chunks if c.get("section_title")]
        assert len(sections) >= 1

    def test_token_count_accuracy(self):
        pages = [{"page_number": 1, "content": "Hello world, this is a test."}]
        chunks = self.chunker.chunk_document(pages)
        assert chunks[0]["token_count"] == self.chunker.count_tokens(chunks[0]["content"])

    def test_large_text_gets_split(self):
        # Create text that exceeds chunk_size tokens
        long_text = " ".join(["This is sentence number {}.".format(i) for i in range(100)])
        pages = [{"page_number": 1, "content": long_text}]
        chunks = self.chunker.chunk_document(pages)
        assert len(chunks) > 1
        # Verify chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i
