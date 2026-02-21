"""Initial schema - users, documents, chunks, sessions, messages.

Revision ID: 001_initial
Revises:
Create Date: 2026-02-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column(
            "file_type",
            sa.Enum("pdf", "docx", "txt", "image", name="documenttype"),
            nullable=False,
        ),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("s3_key", sa.String(1000)),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", name="documentstatus"),
            default="pending",
            nullable=False,
        ),
        sa.Column("page_count", sa.Integer()),
        sa.Column("metadata", postgresql.JSONB(), default={}),
        sa.Column("error_message", sa.Text()),
        sa.Column("processing_time_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_owner_status", "documents", ["owner_id", "status"])
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])

    # Document chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("section_title", sa.String(500)),
        sa.Column("vector_id", sa.String(255)),
        sa.Column("metadata", postgresql.JSONB(), default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_chunks_vector_id", "document_chunks", ["vector_id"])

    # Chat sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500)),
        sa.Column("is_shared", sa.Boolean(), default=False),
        sa.Column("share_token", sa.String(64), unique=True),
        sa.Column("document_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sessions_user_id", "chat_sessions", ["user_id"])

    # Chat messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("user", "assistant", "system", name="messagerole"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB()),
        sa.Column("token_count", sa.Integer()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("metadata", postgresql.JSONB(), default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_messages_session_id", "chat_messages", ["session_id"])


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("users")

    # Clean up enums
    op.execute("DROP TYPE IF EXISTS documenttype")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS messagerole")
