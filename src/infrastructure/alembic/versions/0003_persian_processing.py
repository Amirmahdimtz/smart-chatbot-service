"""Add source-mapped text to existing Phase03 knowledge_chunk.

Revision ID: 0003_persian_processing
Revises: 0002_ingestion
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_persian_processing"
down_revision = "0002_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_chunk", sa.Column("original_text", sa.Text()))
    op.add_column("knowledge_chunk", sa.Column("canonical_text", sa.Text()))
    op.add_column("knowledge_chunk", sa.Column("page_number", sa.Integer()))
    op.add_column("knowledge_chunk", sa.Column("source_start", sa.Integer()))
    op.add_column("knowledge_chunk", sa.Column("source_end", sa.Integer()))
    op.add_column("knowledge_chunk", sa.Column("section_title", sa.String(200)))
    op.add_column("knowledge_chunk", sa.Column("extractor_method", sa.String(32)))
    op.add_column("knowledge_chunk", sa.Column("processor_version", sa.String(64)))
    op.create_check_constraint(
        "ck_chunk_source_span",
        "knowledge_chunk",
        "(source_start IS NULL AND source_end IS NULL) OR (source_start >= 0 AND source_end > source_start)",
    )
    op.create_check_constraint("ck_chunk_page_number", "knowledge_chunk", "page_number IS NULL OR page_number > 0")


def downgrade() -> None:
    op.drop_constraint("ck_chunk_page_number", "knowledge_chunk", type_="check")
    op.drop_constraint("ck_chunk_source_span", "knowledge_chunk", type_="check")
    for name in (
        "processor_version",
        "extractor_method",
        "section_title",
        "source_end",
        "source_start",
        "page_number",
        "canonical_text",
        "original_text",
    ):
        op.drop_column("knowledge_chunk", name)
