"""Durable Phase07 index manifests, fenced jobs and PG publication pointer.

Revision ID: 0004_index_lifecycle
Revises: 0003_persian_processing
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_index_lifecycle"
down_revision = "0003_persian_processing"
branch_labels = None
depends_on = None


def _uuid():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "index_job",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("document_id", _uuid(), nullable=False),
        sa.Column("version_id", _uuid(), nullable=False),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("owner_principal_id", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(64), nullable=False),
        sa.Column("manifest_id", _uuid(), nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("model_revision", sa.String(100), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("lease_token", _uuid()),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(48)),
        sa.Column("cleanup_pending", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("approved_by", sa.String(255)),
        sa.Column("approval_ref", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["document_id", "deployment_scope"],
            ["knowledge_document.id", "knowledge_document.deployment_scope"],
            name="fk_index_job_document_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["version_id", "deployment_scope"],
            ["document_version.id", "document_version.deployment_scope"],
            name="fk_index_job_version_scope",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("deployment_scope = 'internal'", name="ck_index_job_internal"),
        sa.CheckConstraint(
            "status IN ('queued','leased','staged','approved','published','revoked','dead')",
            name="ck_index_job_status",
        ),
        sa.CheckConstraint(
            "attempts >= 0 AND attempts <= max_attempts AND max_attempts > 0", name="ck_index_job_attempts"
        ),
        sa.CheckConstraint("chunk_count BETWEEN 1 AND 4096", name="ck_index_job_chunk_count"),
        sa.UniqueConstraint("version_id", "deployment_scope", name="uq_index_job_version_scope"),
    )
    op.create_index("ix_index_job_claim", "index_job", ["deployment_scope", "status", "lease_expires_at"])
    op.create_table(
        "index_manifest",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("job_id", _uuid(), nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("manifest_json", postgresql.JSONB(), nullable=False),
        sa.Column("point_ids", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["job_id"], ["index_job.id"], name="fk_index_manifest_job", ondelete="RESTRICT"),
        sa.UniqueConstraint("job_id", name="uq_index_manifest_job"),
    )
    op.create_table(
        "index_publication",
        sa.Column("document_id", _uuid(), primary_key=True),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("active_version_id", _uuid()),
        sa.Column("generation", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["document_id", "deployment_scope"],
            ["knowledge_document.id", "knowledge_document.deployment_scope"],
            name="fk_index_publication_document",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["active_version_id", "deployment_scope"],
            ["document_version.id", "document_version.deployment_scope"],
            name="fk_index_publication_version",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("deployment_scope = 'internal'", name="ck_index_publication_scope"),
    )


def downgrade() -> None:
    op.drop_table("index_publication")
    op.drop_table("index_manifest")
    op.drop_index("ix_index_job_claim", table_name="index_job")
    op.drop_table("index_job")
