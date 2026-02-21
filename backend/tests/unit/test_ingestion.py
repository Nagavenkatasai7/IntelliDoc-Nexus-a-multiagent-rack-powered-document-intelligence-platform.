"""Tests for the ingestion service — file type validation, dedup, extension mapping."""

import pytest
from app.services.ingestion import EXTENSION_MAP, IngestionService
from app.models.document import DocumentType


class TestExtensionMap:
    def test_pdf_extension(self):
        assert EXTENSION_MAP[".pdf"] == DocumentType.PDF

    def test_docx_extension(self):
        assert EXTENSION_MAP[".docx"] == DocumentType.DOCX

    def test_doc_extension(self):
        assert EXTENSION_MAP[".doc"] == DocumentType.DOCX

    def test_txt_extension(self):
        assert EXTENSION_MAP[".txt"] == DocumentType.TXT

    def test_image_extensions(self):
        assert EXTENSION_MAP[".png"] == DocumentType.IMAGE
        assert EXTENSION_MAP[".jpg"] == DocumentType.IMAGE
        assert EXTENSION_MAP[".jpeg"] == DocumentType.IMAGE
        assert EXTENSION_MAP[".tiff"] == DocumentType.IMAGE

    def test_unsupported_extension(self):
        assert EXTENSION_MAP.get(".xyz") is None
        assert EXTENSION_MAP.get(".csv") is None
        assert EXTENSION_MAP.get(".mp4") is None


class TestContentHash:
    def test_hash_deterministic(self):
        from app.services.document_processor import DocumentProcessor

        content = b"Hello, world!"
        hash1 = DocumentProcessor.compute_content_hash(content)
        hash2 = DocumentProcessor.compute_content_hash(content)
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        from app.services.document_processor import DocumentProcessor

        hash1 = DocumentProcessor.compute_content_hash(b"Content A")
        hash2 = DocumentProcessor.compute_content_hash(b"Content B")
        assert hash1 != hash2

    def test_hash_is_hex_string(self):
        from app.services.document_processor import DocumentProcessor

        h = DocumentProcessor.compute_content_hash(b"test")
        assert all(c in "0123456789abcdef" for c in h)


class TestFilenameExtraction:
    """Test the extension extraction logic used in ingest_document."""

    def test_pdf_filename(self):
        filename = "report.pdf"
        ext = "." + filename.rsplit(".", 1)[-1].lower()
        assert ext == ".pdf"
        assert EXTENSION_MAP.get(ext) == DocumentType.PDF

    def test_uppercase_extension(self):
        filename = "photo.JPG"
        ext = "." + filename.rsplit(".", 1)[-1].lower()
        assert ext == ".jpg"
        assert EXTENSION_MAP.get(ext) == DocumentType.IMAGE

    def test_no_extension(self):
        filename = "noext"
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        assert ext == ""
        assert EXTENSION_MAP.get(ext) is None

    def test_multiple_dots(self):
        filename = "my.report.final.docx"
        ext = "." + filename.rsplit(".", 1)[-1].lower()
        assert ext == ".docx"
        assert EXTENSION_MAP.get(ext) == DocumentType.DOCX
