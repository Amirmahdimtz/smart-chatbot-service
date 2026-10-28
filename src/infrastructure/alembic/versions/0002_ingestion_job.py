"""Durable ingestion job with transactional leases.

Revision ID: 0002_ingestion_job
Revises: 0001_foundation
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_ingestion_job"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("lease_owner", sa.String(128)),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["source_id", "deployment_scope"], ["knowledge_source.id", "knowledge_source.deployment_scope"],
            name="fk_ingestion_source_scope", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id", "deployment_scope"], ["document_version.id", "document_version.deployment_scope"],
            name="fk_ingestion_version_scope", ondelete="RESTRICT",
        ),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_ingestion_scope"),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'retry_wait', 'completed', 'dead_letter', 'cancelled')",
            name="ck_ingestion_status",
        ),
        sa.CheckConstraint("attempts >= 0 AND max_attempts BETWEEN 1 AND 20 AND attempts <= max_attempts",
                           name="ck_ingestion_attempts"),
        sa.CheckConstraint(
            "(status = 'processing' AND lease_owner IS NOT NULL AND lease_token IS NOT NULL "
            "AND lease_expires_at IS NOT NULL) OR "
            "(status <> 'processing' AND lease_owner IS NULL AND lease_token IS NULL "
            "AND lease_expires_at IS NULL)",
            name="ck_ingestion_lease_state",
        ),
        sa.UniqueConstraint("source_id", "idempotency_key", name="uq_ingestion_source_idempotency"),
    )
    op.create_index(
        "ix_ingestion_claim", "ingestion_job",
        ["deployment_scope", "status", "available_at", "lease_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_claim", table_name="ingestion_job")
    op.drop_table("ingestion_job")
