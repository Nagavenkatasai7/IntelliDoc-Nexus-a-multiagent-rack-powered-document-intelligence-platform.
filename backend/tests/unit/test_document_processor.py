import pytest
from app.services.document_processor import DocumentProcessor


class TestDocumentProcessor:
    def setup_method(self):
        self.processor = DocumentProcessor()

    def test_compute_content_hash(self):
        content = b"test content"
        hash1 = DocumentProcessor.compute_content_hash(content)
        hash2 = DocumentProcessor.compute_content_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest

    def test_different_content_different_hash(self):
        hash1 = DocumentProcessor.compute_content_hash(b"content A")
        hash2 = DocumentProcessor.compute_content_hash(b"content B")
        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_extract_txt(self):
        content = b"Hello, this is a plain text document.\nWith multiple lines."
        result = await self.processor.extract_text(content, "test.txt")
        assert "Hello" in result["text"]
        assert result["page_count"] == 1
        assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_unsupported_format(self):
        with pytest.raises(ValueError, match="Unsupported"):
            await self.processor.extract_text(b"data", "file.xyz")

    @pytest.mark.asyncio
    async def test_extract_txt_unicode(self):
        content = "Unicode text: cafe\u0301 \u00e9l\u00e8ve \u00fc\u00f6\u00e4".encode("utf-8")
        result = await self.processor.extract_text(content, "unicode.txt")
        assert "Unicode" in result["text"]

    def test_supported_extensions(self):
        assert ".pdf" in DocumentProcessor.SUPPORTED_EXTENSIONS
        assert ".docx" in DocumentProcessor.SUPPORTED_EXTENSIONS
        assert ".txt" in DocumentProcessor.SUPPORTED_EXTENSIONS
        assert ".png" in DocumentProcessor.SUPPORTED_EXTENSIONS
