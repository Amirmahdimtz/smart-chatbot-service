"""Phase07 durable indexing state; PostgreSQL authoritative, Qdrant advisory."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.context.sql_db.psql_dbcontext import Base


class IndexJob(Base):
    __tablename__ = "index_job"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "deployment_scope"],
            ["knowledge_document.id", "knowledge_document.deployment_scope"],
            name="fk_index_job_document_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["version_id", "deployment_scope"],
            ["document_version.id", "document_version.deployment_scope"],
            name="fk_index_job_version_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("deployment_scope = 'internal'", name="ck_index_job_internal"),
        CheckConstraint(
            "status IN ('queued','leased','staged','approved','published','revoked','dead')",
            name="ck_index_job_status",
        ),
        CheckConstraint(
            "attempts >= 0 AND attempts <= max_attempts AND max_attempts > 0", name="ck_index_job_attempts"
        ),
        CheckConstraint("chunk_count BETWEEN 1 AND 4096", name="ck_index_job_chunk_count"),
        UniqueConstraint("version_id", "deployment_scope", name="uq_index_job_version_scope"),
        Index("ix_index_job_claim", "deployment_scope", "status", "lease_expires_at"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    version_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    owner_principal_id: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    model_revision: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    lease_token: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(48))
    cleanup_pending: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    approved_by: Mapped[str | None] = mapped_column(String(255))
    approval_ref: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class IndexManifestRecord(Base):
    __tablename__ = "index_manifest"
    __table_args__ = (
        ForeignKeyConstraint(["job_id"], ["index_job.id"], name="fk_index_manifest_job", ondelete="RESTRICT"),
        UniqueConstraint("job_id", name="uq_index_manifest_job"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    point_ids: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class IndexPublication(Base):
    """Exactly one authoritative active version per document, switchable in one PG transaction."""

    __tablename__ = "index_publication"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "deployment_scope"],
            ["knowledge_document.id", "knowledge_document.deployment_scope"],
            name="fk_index_publication_document",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["active_version_id", "deployment_scope"],
            ["document_version.id", "document_version.deployment_scope"],
            name="fk_index_publication_version",
            ondelete="RESTRICT",
        ),
        CheckConstraint("deployment_scope = 'internal'", name="ck_index_publication_scope"),
    )
    document_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    active_version_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    generation: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
