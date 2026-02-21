import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_ingestion_service, get_current_user_id, get_db
from app.core.config import get_settings
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
)
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    owner_id: uuid.UUID = Depends(get_current_user_id),
    ingestion: IngestionService = Depends(get_ingestion_service),
):
    """Upload and process a document (PDF, DOCX, TXT, or image)."""
    # Validate file size
    content = await file.read()
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb}MB",
        )

    # Validate file extension
    filename = file.filename or "unnamed"
    ext = Path(filename).suffix.lower()
    if ext not in {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", ".tiff"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Supported: PDF, DOCX, TXT, PNG, JPG",
        )

    try:
        document = await ingestion.ingest_document(
            file_content=content,
            filename=filename,
            owner_id=owner_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}",
        )

    return DocumentUploadResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    owner_id: uuid.UUID = Depends(get_current_user_id),
    ingestion: IngestionService = Depends(get_ingestion_service),
):
    """List all documents for the current user."""
    documents, total = await ingestion.list_documents(
        owner_id=owner_id, page=page, page_size=page_size
    )

    doc_responses = []
    for doc in documents:
        resp = DocumentResponse.model_validate(doc)
        resp.chunk_count = len(doc.chunks) if doc.chunks else 0
        doc_responses.append(resp)

    return DocumentListResponse(
        documents=doc_responses, total=total, page=page, page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user_id),
    ingestion: IngestionService = Depends(get_ingestion_service),
):
    """Get document details."""
    doc = await ingestion.get_document_with_chunks(document_id, owner_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    resp = DocumentResponse.model_validate(doc)
    resp.chunk_count = len(doc.chunks) if doc.chunks else 0
    return resp


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user_id),
    ingestion: IngestionService = Depends(get_ingestion_service),
):
    """Delete a document and its associated data."""
    deleted = await ingestion.delete_document(document_id, owner_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
