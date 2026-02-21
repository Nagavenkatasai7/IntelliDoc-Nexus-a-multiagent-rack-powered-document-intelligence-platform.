import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.compat import GUID, JSONType


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_owner_status", "owner_id", "status"),
        Index("ix_documents_content_hash", "content_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False
    )
    page_count: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONType(), default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="documents")
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_chunks_document_id", "document_id"),
        Index("ix_chunks_vector_id", "vector_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(500))
    vector_id: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONType(), default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document = relationship("Document", back_populates="chunks")
