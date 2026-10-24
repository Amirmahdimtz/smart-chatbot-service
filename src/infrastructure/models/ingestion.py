"""Durable ingestion identity and redacted audit records; no publication writes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.context.sql_db.psql_dbcontext import Base


class IngestionJob(Base):
    __tablename__ = "ingestion_job"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "deployment_scope"],
            ["knowledge_source.id", "knowledge_source.deployment_scope"],
            name="fk_ingestion_source_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["version_id", "deployment_scope"],
            ["document_version.id", "document_version.deployment_scope"],
            name="fk_ingestion_version_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_ingestion_scope"),
        CheckConstraint(
            "status IN ('staging','queued','leased','retry_wait','completed','dead','cancelled')",
            name="ck_ingestion_status",
        ),
        CheckConstraint("attempts >= 0 AND max_attempts > 0", name="ck_ingestion_attempts"),
        UniqueConstraint(
            "source_id", "deployment_scope", "owner_principal_id", "idempotency_key",
            name="uq_ingestion_idempotency",
        ),
        UniqueConstraint("source_id", "checksum_sha256", name="uq_ingestion_source_checksum"),
        Index("ix_ingestion_claim", "deployment_scope", "status", "next_retry_at", "lease_expires_at"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    version_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    owner_principal_id: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="staging")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    lease_owner: Mapped[str | None] = mapped_column(String(80))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(48))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class IngestionAuditEvent(Base):
    __tablename__ = "ingestion_audit_event"
    __table_args__ = (
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_ingestion_audit_scope"),
        Index("ix_ingestion_audit_job", "job_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    source_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    event: Mapped[str] = mapped_column(String(48), nullable=False)
    code: Mapped[str | None] = mapped_column(String(48))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
