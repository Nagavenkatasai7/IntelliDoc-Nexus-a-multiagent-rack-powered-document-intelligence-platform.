import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.compat import GUID, JSONType, ArrayType


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (Index("ix_sessions_user_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(500))
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    document_ids: Mapped[list | None] = mapped_column(ArrayType())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_messages_session_id", "session_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSONType())
    token_count: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONType(), default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session = relationship("ChatSession", back_populates="messages")
