import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.document import DocumentStatus, DocumentType


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: DocumentType
    file_size: int
    status: DocumentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    original_filename: str
    file_type: DocumentType
    file_size: int
    status: DocumentStatus
    page_count: int | None = None
    metadata_: dict | None = Field(None, alias="metadata_")
    chunk_count: int = 0
    processing_time_ms: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    chunk_index: int
    content: str
    page_number: int | None = None
    section_title: str | None = None
    token_count: int

    model_config = {"from_attributes": True}
