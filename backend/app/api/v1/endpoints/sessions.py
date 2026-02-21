"""Session management: sharing, export, delete."""

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user_id, get_db
from app.models.session import ChatSession, ChatMessage

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/{session_id}/share")
async def share_session(
    session_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a share link for a conversation."""
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == owner_id,
    )
    session = (await db.execute(stmt)).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if not session.share_token:
        session.share_token = secrets.token_urlsafe(32)
        session.is_shared = True
        await db.flush()

    return {
        "share_token": session.share_token,
        "is_shared": True,
    }


@router.get("/shared/{share_token}")
async def get_shared_session(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Access a shared conversation (no auth required)."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.share_token == share_token, ChatSession.is_shared.is_(True))
        .options(selectinload(ChatSession.messages))
    )
    session = (await db.execute(stmt)).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared session not found")

    return {
        "id": str(session.id),
        "title": session.title,
        "messages": [
            {
                "role": msg.role.value,
                "content": msg.content,
                "sources": msg.sources,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in session.messages
        ],
    }


@router.post("/{session_id}/unshare")
async def unshare_session(
    session_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Revoke sharing for a conversation."""
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == owner_id,
    )
    session = (await db.execute(stmt)).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    session.share_token = None
    session.is_shared = False
    await db.flush()

    return {"is_shared": False}


@router.get("/{session_id}/export/markdown", response_class=PlainTextResponse)
async def export_session_markdown(
    session_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export a conversation as Markdown."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == owner_id)
        .options(selectinload(ChatSession.messages))
    )
    session = (await db.execute(stmt)).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    lines = [
        f"# {session.title or 'Conversation'}",
        f"*Exported from IntelliDoc Nexus*\n",
    ]

    for msg in session.messages:
        role_label = "**You**" if msg.role.value == "user" else "**IntelliDoc**"
        lines.append(f"### {role_label}")
        lines.append(msg.content)

        if msg.sources:
            lines.append("\n**Sources:**")
            for src in msg.sources:
                page_info = f" (Page {src.get('page_number')})" if src.get("page_number") else ""
                lines.append(f"- Source {src.get('source_index', '?')}{page_info}: {src.get('content_preview', '')[:100]}...")

        lines.append("")

    return "\n".join(lines)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session."""
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == owner_id,
    )
    session = (await db.execute(stmt)).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(session)
