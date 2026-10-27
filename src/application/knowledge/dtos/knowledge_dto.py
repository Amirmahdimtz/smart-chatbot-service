"""Phase 05 synthetic ingestion API contracts; no object download or publish route."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourceCreateDto(BaseModel):
    domain: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    classification: Literal["synthetic_unclassified"] = "synthetic_unclassified"
    policy_ref: Literal["synthetic-only"] = "synthetic-only"
    max_file_bytes: int | None = Field(default=None, ge=1024, le=5242880)


class SourceResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    domain: str
    deployment_scope: str
    source_type: str
    status: str
    classification: str
    policy_ref: str
    max_file_bytes: int | None


class JobResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_id: UUID
    status: str
    attempts: int
    error_code: str | None
    created_at: datetime


class DocumentVersionResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    state: str
    safe_filename: str | None
    content_type: str | None
    byte_size: int | None
    checksum_sha256: str
