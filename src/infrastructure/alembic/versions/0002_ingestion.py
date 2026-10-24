"""Phase 05 additive document metadata and durable ingestion tables.

Revision ID: 0002_ingestion
Revises: 0001_foundation
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_ingestion"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def _uuid():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column("knowledge_source", sa.Column("source_type", sa.String(16), nullable=False, server_default="file"))
    op.add_column("knowledge_source", sa.Column("status", sa.String(16), nullable=False, server_default="active"))
    op.create_check_constraint("ck_source_type", "knowledge_source", "source_type IN ('file')")
    op.create_check_constraint("ck_source_status", "knowledge_source", "status IN ('active', 'disabled')")
    op.add_column("document_version", sa.Column("safe_filename", sa.String(255)))
    op.add_column("document_version", sa.Column("content_type", sa.String(80)))
    op.add_column("document_version", sa.Column("object_key", sa.String(256)))
    op.add_column("document_version", sa.Column("byte_size", sa.Integer()))
    op.create_unique_constraint("uq_document_version_object_key", "document_version", ["object_key"])
    op.drop_constraint("ck_version_state", "document_version", type_="check")
    op.create_check_constraint(
        "ck_version_state", "document_version",
        "state IN ('draft', 'processing', 'failed', 'awaiting_approval', 'published', 'revoked', 'superseded')",
    )
    op.create_table(
        "ingestion_job",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("source_id", _uuid(), nullable=False),
        sa.Column("version_id", _uuid(), nullable=False),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("owner_principal_id", sa.String(255), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="staging"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("lease_owner", sa.String(80)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(48)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["source_id", "deployment_scope"], ["knowledge_source.id", "knowledge_source.deployment_scope"],
            name="fk_ingestion_source_scope", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["version_id", "deployment_scope"], ["document_version.id", "document_version.deployment_scope"],
            name="fk_ingestion_version_scope", ondelete="RESTRICT",
        ),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_ingestion_scope"),
        sa.CheckConstraint(
            "status IN ('staging','queued','leased','retry_wait','completed','dead','cancelled')",
            name="ck_ingestion_status",
        ),
        sa.CheckConstraint("attempts >= 0 AND max_attempts > 0", name="ck_ingestion_attempts"),
        sa.UniqueConstraint(
            "source_id", "deployment_scope", "owner_principal_id", "idempotency_key",
            name="uq_ingestion_idempotency",
        ),
        sa.UniqueConstraint("source_id", "checksum_sha256", name="uq_ingestion_source_checksum"),
    )
    op.create_index(
        "ix_ingestion_claim", "ingestion_job", ["deployment_scope", "status", "next_retry_at", "lease_expires_at"]
    )
    op.create_table(
        "ingestion_audit_event",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("job_id", _uuid()),
        sa.Column("source_id", _uuid(), nullable=False),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("actor_ref", sa.String(255), nullable=False),
        sa.Column("event", sa.String(48), nullable=False),
        sa.Column("code", sa.String(48)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_ingestion_audit_scope"),
    )
    op.create_index("ix_ingestion_audit_job", "ingestion_audit_event", ["job_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_audit_job", table_name="ingestion_audit_event")
    op.drop_table("ingestion_audit_event")
    op.drop_index("ix_ingestion_claim", table_name="ingestion_job")
    op.drop_table("ingestion_job")
    op.drop_constraint("ck_version_state", "document_version", type_="check")
    op.create_check_constraint("ck_version_state", "document_version", "state IN ('draft', 'revoked')")
    op.drop_constraint("uq_document_version_object_key", "document_version", type_="unique")
    for col in ("byte_size", "object_key", "content_type", "safe_filename"):
        op.drop_column("document_version", col)
    op.drop_constraint("ck_source_status", "knowledge_source", type_="check")
    op.drop_constraint("ck_source_type", "knowledge_source", type_="check")
    op.drop_column("knowledge_source", "status")
    op.drop_column("knowledge_source", "source_type")
