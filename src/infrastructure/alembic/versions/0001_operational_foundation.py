"""Initial conversation and knowledge identity schema.

Revision ID: 0001_foundation
Revises:
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _created() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"))


def upgrade() -> None:
    op.create_table(
        "conversation",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("owner_principal_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        _created(),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_conversation_scope"),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_conversation_status"),
        sa.UniqueConstraint("id", "deployment_scope", name="uq_conversation_id_scope"),
    )
    op.create_index("ix_conversation_owner_created", "conversation", [
        "deployment_scope", "owner_principal_id", "created_at"
    ])
    op.create_table(
        "message",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("conversation_id", _uuid(), nullable=False),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(128)),
        _created(),
        sa.ForeignKeyConstraint(
            ["conversation_id", "deployment_scope"], ["conversation.id", "conversation.deployment_scope"],
            name="fk_message_conversation_scope", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_message_scope"),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_message_role"),
        sa.CheckConstraint("sequence_number > 0", name="ck_message_sequence"),
        sa.UniqueConstraint("conversation_id", "sequence_number", name="uq_message_sequence"),
        sa.UniqueConstraint("conversation_id", "idempotency_key", name="uq_message_idempotency"),
    )
    op.create_table(
        "knowledge_source",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("owner_principal_id", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(64), nullable=False),
        _created(),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_source_scope"),
        sa.UniqueConstraint("id", "deployment_scope", name="uq_source_id_scope"),
    )
    op.create_table(
        "knowledge_document",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("source_id", _uuid(), nullable=False),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("classification", sa.String(64)),
        _created(),
        sa.ForeignKeyConstraint(
            ["source_id", "deployment_scope"], ["knowledge_source.id", "knowledge_source.deployment_scope"],
            name="fk_document_source_scope", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_document_scope"),
        sa.UniqueConstraint("id", "deployment_scope", name="uq_document_id_scope"),
    )
    op.create_table(
        "document_version",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("document_id", _uuid(), nullable=False),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="draft"),
        _created(),
        sa.ForeignKeyConstraint(
            ["document_id", "deployment_scope"], ["knowledge_document.id", "knowledge_document.deployment_scope"],
            name="fk_version_document_scope", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_version_scope"),
        sa.CheckConstraint("version_number > 0", name="ck_version_number"),
        sa.CheckConstraint("state IN ('draft', 'revoked')", name="ck_version_state"),
        sa.UniqueConstraint("document_id", "version_number", name="uq_document_version"),
        sa.UniqueConstraint("id", "deployment_scope", name="uq_version_id_scope"),
    )
    op.create_table(
        "knowledge_chunk",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("version_id", _uuid(), nullable=False),
        sa.Column("deployment_scope", sa.String(8), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("canonical_text_ref", sa.String(1024)),
        _created(),
        sa.ForeignKeyConstraint(
            ["version_id", "deployment_scope"], ["document_version.id", "document_version.deployment_scope"],
            name="fk_chunk_version_scope", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("deployment_scope IN ('public', 'internal')", name="ck_chunk_scope"),
        sa.CheckConstraint("ordinal >= 0", name="ck_chunk_ordinal"),
        sa.UniqueConstraint("version_id", "ordinal", name="uq_chunk_ordinal"),
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunk")
    op.drop_table("document_version")
    op.drop_table("knowledge_document")
    op.drop_table("knowledge_source")
    op.drop_table("message")
    op.drop_index("ix_conversation_owner_created", table_name="conversation")
    op.drop_table("conversation")
