import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import (
    get_rag_service,
    get_current_user_id,
    get_db,
    get_vector_store,
    get_orchestrator,
)
from app.models.session import ChatSession, ChatMessage, MessageRole
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatSessionListResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.services.rag import RAGService
from app.services.vector_store import VectorStoreService
from app.agents.orchestrator import OrchestratorAgent

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(
    request: ChatRequest,
    use_agents: bool = Query(default=False, description="Use multi-agent pipeline"),
    owner_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator),
):
    """Send a message and get a RAG-powered response.

    Set use_agents=true for the multi-agent pipeline (higher quality, slower).
    """
    # Get or create session
    session = None
    chat_history = []

    if request.session_id:
        session = await db.get(ChatSession, request.session_id)
        if session and session.user_id != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        if session:
            msg_stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.created_at)
            )
            result = await db.execute(msg_stmt)
            for msg in result.scalars():
                chat_history.append({"role": msg.role.value, "content": msg.content})

    if not session:
        session = ChatSession(
            user_id=owner_id,
            title=request.query[:100],
            document_ids=request.document_ids,
        )
        db.add(session)
        await db.flush()

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=request.query,
    )
    db.add(user_msg)

    # Handle streaming (simple RAG only)
    if request.stream and not use_agents:
        # Commit the session and user message before streaming starts,
        # because the get_db dependency commits when the endpoint returns,
        # which happens before the streaming generator finishes.
        await db.commit()
        return StreamingResponse(
            _stream_response(
                rag=rag,
                session=session,
                query=request.query,
                owner_id=owner_id,
                document_ids=request.document_ids,
                chat_history=chat_history,
            ),
            media_type="text/event-stream",
        )

    # Multi-agent or non-streaming response
    if use_agents:
        result = await orchestrator.run(
            query=request.query,
            owner_id=owner_id,
            document_ids=request.document_ids,
            chat_history=chat_history,
        )
    else:
        result = await rag.query(
            question=request.query,
            owner_id=owner_id,
            document_ids=request.document_ids,
            chat_history=chat_history,
        )

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=result["content"],
        sources=result["sources"],
        latency_ms=result["latency_ms"],
        metadata_={
            "agent_trace": result.get("agent_trace", []),
            "revisions": result.get("revisions", 0),
        },
    )
    db.add(assistant_msg)
    await db.flush()

    return ChatResponse(
        session_id=session.id,
        message_id=assistant_msg.id,
        content=result["content"],
        sources=result.get("sources", []),
        latency_ms=result["latency_ms"],
    )


async def _stream_response(
    rag: RAGService,
    session: ChatSession,
    query: str,
    owner_id: uuid.UUID,
    document_ids: list[uuid.UUID] | None,
    chat_history: list[dict],
):
    """Server-Sent Events stream for real-time responses."""
    from app.db.session import async_session_factory

    full_content = ""
    sources = []

    async for chunk in rag.query_stream(
        question=query,
        owner_id=owner_id,
        document_ids=document_ids,
        chat_history=chat_history,
    ):
        if chunk["type"] == "text":
            full_content += chunk["content"]
            yield f"data: {json.dumps({'type': 'text', 'content': chunk['content']})}\n\n"
        elif chunk["type"] == "sources":
            sources = chunk["sources"]
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        elif chunk["type"] == "done":
            # Use a fresh session to persist the assistant message
            async with async_session_factory() as db:
                assistant_msg = ChatMessage(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=full_content,
                    sources=sources,
                )
                db.add(assistant_msg)
                await db.commit()
                yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_msg.id)})}\n\n"


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions(
    owner_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List chat sessions for the current user."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == owner_id)
        .order_by(ChatSession.updated_at.desc())
        .options(selectinload(ChatSession.messages))
    )
    result = await db.execute(stmt)
    sessions = list(result.scalars().all())

    return ChatSessionListResponse(
        sessions=[ChatSessionResponse.model_validate(s) for s in sessions],
        total=len(sessions),
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a chat session with all messages."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == owner_id)
        .options(selectinload(ChatSession.messages))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return ChatSessionResponse.model_validate(session)


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    owner_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store),
):
    """Semantic search across uploaded documents."""
    from app.models.document import Document

    results = await vector_store.search(
        query=request.query,
        owner_id=owner_id,
        top_k=request.top_k,
        filter_document_ids=request.document_ids,
    )

    # Look up document names for the results
    doc_ids = list({r["document_id"] for r in results if r.get("document_id")})
    doc_name_map: dict[str, str] = {}
    if doc_ids:
        doc_uuids = [uuid.UUID(d) for d in doc_ids]
        stmt = select(Document).where(Document.id.in_(doc_uuids))
        doc_result = await db.execute(stmt)
        for doc in doc_result.scalars():
            doc_name_map[str(doc.id)] = doc.original_filename

    search_results = []
    for r in results:
        if request.threshold and r.get("score", 0) < request.threshold:
            continue
        search_results.append(
            SearchResult(
                document_id=r["document_id"],
                document_name=doc_name_map.get(r["document_id"], ""),
                chunk_id=r.get("vector_id", ""),
                content=r.get("content_preview", ""),
                page_number=r.get("page_number"),
                score=r.get("score", 0),
            )
        )

    return SearchResponse(
        results=search_results, query=request.query, total=len(search_results)
    )
