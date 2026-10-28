"""Phase 05 durable ingestion work state; PostgreSQL remains authoritative."""

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
            ["document_version_id", "deployment_scope"],
            ["document_version.id", "document_version.deployment_scope"],
            name="fk_ingestion_version_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_ingestion_scope"),
        CheckConstraint(
            "status IN ('queued', 'processing', 'retry_wait', 'completed', 'dead_letter', 'cancelled')",
            name="ck_ingestion_status",
        ),
        CheckConstraint(
            "attempts >= 0 AND max_attempts BETWEEN 1 AND 20 AND attempts <= max_attempts", name="ck_ingestion_attempts"
        ),
        CheckConstraint(
            "(status = 'processing' AND lease_owner IS NOT NULL AND lease_token IS NOT NULL "
            "AND lease_expires_at IS NOT NULL) OR "
            "(status <> 'processing' AND lease_owner IS NULL AND lease_token IS NULL "
            "AND lease_expires_at IS NULL)",
            name="ck_ingestion_lease_state",
        ),
        UniqueConstraint("source_id", "idempotency_key", name="uq_ingestion_source_idempotency"),
        Index("ix_ingestion_claim", "deployment_scope", "status", "available_at", "lease_expires_at"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    document_version_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    deployment_scope: Mapped[str] = mapped_column(String(8), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    lease_owner: Mapped[str | None] = mapped_column(String(128))
    lease_token: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
