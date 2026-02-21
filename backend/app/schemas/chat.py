import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.session import MessageRole


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: uuid.UUID | None = None
    document_ids: list[uuid.UUID] | None = None
    stream: bool = True


class SourceReference(BaseModel):
    source_index: int | None = None
    document_id: str | None = None
    document_name: str | None = ""
    chunk_index: int | None = None
    chunk_id: str | None = ""
    content_preview: str | None = ""
    page_number: int | None = None
    section_title: str | None = ""
    score: float = 0.0
    relevance_score: float = 0.0


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    message_id: uuid.UUID
    content: str
    sources: list[dict] = []
    latency_ms: int


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    sources: list[SourceReference] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str | None = None
    is_shared: bool = False
    document_ids: list[uuid.UUID] | None = None
    messages: list[ChatMessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionResponse]
    total: int


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    document_ids: list[uuid.UUID] | None = None
    top_k: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    document_id: str
    document_name: str = ""
    chunk_id: str = ""
    content: str = ""
    page_number: int | None = None
    score: float = 0.0


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    total: int
