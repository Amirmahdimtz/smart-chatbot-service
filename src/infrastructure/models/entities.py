"""Phase 03 structural data contract; policy-dependent publication is not enabled."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.context.sql_db.psql_dbcontext import Base


class Conversation(Base):
    __tablename__ = "conversation"
    __table_args__ = (
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_conversation_scope"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_conversation_status"),
        UniqueConstraint("id", "deployment_scope", name="uq_conversation_id_scope"),
        Index("ix_conversation_owner_created", "deployment_scope", "owner_principal_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    owner_principal_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="active")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    __mapper_args__ = {"version_id_col": revision}


class Message(Base):
    __tablename__ = "message"
    __table_args__ = (
        ForeignKeyConstraint(
            ["conversation_id", "deployment_scope"],
            ["conversation.id", "conversation.deployment_scope"],
            name="fk_message_conversation_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_message_scope"),
        CheckConstraint("role IN ('user', 'assistant')", name="ck_message_role"),
        CheckConstraint("sequence_number > 0", name="ck_message_sequence"),
        UniqueConstraint("conversation_id", "sequence_number", name="uq_message_sequence"),
        UniqueConstraint("conversation_id", "idempotency_key", name="uq_message_idempotency"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class KnowledgeSource(Base):
    __tablename__ = "knowledge_source"
    __table_args__ = (
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_source_scope"),
        UniqueConstraint("id", "deployment_scope", name="uq_source_id_scope"),
        CheckConstraint("source_type IN ('file')", name="ck_source_type"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_source_status"),
        CheckConstraint("classification = 'synthetic_unclassified'", name="ck_source_synthetic_class"),
        CheckConstraint("policy_ref = 'synthetic-only'", name="ck_source_synthetic_policy"),
        CheckConstraint("max_file_bytes IS NULL OR max_file_bytes >= 1024", name="ck_source_file_limit"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    owner_principal_id: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False, server_default="file")
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="active")
    classification: Mapped[str] = mapped_column(String(64), nullable=False, server_default="synthetic_unclassified")
    policy_ref: Mapped[str] = mapped_column(String(64), nullable=False, server_default="synthetic-only")
    max_file_bytes: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "deployment_scope"],
            ["knowledge_source.id", "knowledge_source.deployment_scope"],
            name="fk_document_source_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_document_scope"),
        UniqueConstraint("id", "deployment_scope", name="uq_document_id_scope"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    classification: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DocumentVersion(Base):
    __tablename__ = "document_version"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "deployment_scope"],
            ["knowledge_document.id", "knowledge_document.deployment_scope"],
            name="fk_version_document_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_version_scope"),
        CheckConstraint("version_number > 0", name="ck_version_number"),
        CheckConstraint(
            "state IN ('draft', 'processing', 'failed', 'awaiting_approval', 'published', 'revoked', 'superseded')",
            name="ck_version_state",
        ),
        UniqueConstraint("document_id", "version_number", name="uq_document_version"),
        UniqueConstraint("id", "deployment_scope", name="uq_version_id_scope"),
        UniqueConstraint("object_key", name="uq_document_version_object_key"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    safe_filename: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(80))
    object_key: Mapped[str | None] = mapped_column(String(256))
    byte_size: Mapped[int | None] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(32), nullable=False, server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"
    __table_args__ = (
        ForeignKeyConstraint(
            ["version_id", "deployment_scope"],
            ["document_version.id", "document_version.deployment_scope"],
            name="fk_chunk_version_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_chunk_scope"),
        CheckConstraint("ordinal >= 0", name="ck_chunk_ordinal"),
        CheckConstraint(
            "(source_start IS NULL AND source_end IS NULL) OR (source_start >= 0 AND source_end > source_start)",
            name="ck_chunk_source_span",
        ),
        CheckConstraint("page_number IS NULL OR page_number > 0", name="ck_chunk_page_number"),
        UniqueConstraint("version_id", "ordinal", name="uq_chunk_ordinal"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    version_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_text_ref: Mapped[str | None] = mapped_column(String(1024))
    original_text: Mapped[str | None] = mapped_column(Text)
    canonical_text: Mapped[str | None] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer)
    source_start: Mapped[int | None] = mapped_column(Integer)
    source_end: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(200))
    extractor_method: Mapped[str | None] = mapped_column(String(32))
    processor_version: Mapped[str | None] = mapped_column(String(64))
    normalizer_version: Mapped[str | None] = mapped_column(String(64))
    engine_version: Mapped[str | None] = mapped_column(String(180))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
