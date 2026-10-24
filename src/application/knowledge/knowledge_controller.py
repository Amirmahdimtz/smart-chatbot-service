"""Deny-by-default knowledge ingestion API for isolated synthetic integration."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Header, Request, UploadFile, status
from fastapi.responses import JSONResponse

from src.application.knowledge.dtos.knowledge_dto import (
    DocumentVersionResponseDto,
    JobResponseDto,
    SourceCreateDto,
    SourceResponseDto,
)
from src.core.services.ingestion.ingestion_service import IngestionService
from src.core.services.ingestion.upload_validation import UploadRejected
from src.infrastructure.di.inject import inject
from src.infrastructure.providers.storage.quarantine_storage import StorageUnavailable
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class KnowledgeController:
    def __init__(self, ingestion_service: IngestionService, config_reader: ConfigReader):
        self._service = ingestion_service
        self._enabled = config_reader.settings.ingestion.enabled

    def api(self) -> APIRouter:
        router = APIRouter(tags=["Knowledge ingestion (synthetic only)"])

        def principal(request: Request):
            return getattr(request.state, "principal", None)

        def disabled():
            if not self._enabled:
                return JSONResponse({"error": "not_found"}, status_code=404)
            return None

        @router.post("/sources", response_model=SourceResponseDto, status_code=status.HTTP_201_CREATED)
        async def create_source_async(payload: SourceCreateDto, request: Request):
            if (denied := disabled()) is not None:
                return denied
            try:
                source = await self._service.create_source_async(principal(request), payload.domain)
                return SourceResponseDto.model_validate(source)
            except PermissionError:
                return JSONResponse({"error": "forbidden"}, status_code=403)

        @router.get("/sources/{source_id}", response_model=SourceResponseDto)
        async def get_source_async(source_id: UUID, request: Request):
            if (denied := disabled()) is not None:
                return denied
            try:
                source = await self._service.get_source_async(principal(request), source_id)
            except PermissionError:
                return JSONResponse({"error": "forbidden"}, status_code=403)
            if source is None:
                return JSONResponse({"error": "not_found"}, status_code=404)
            return SourceResponseDto.model_validate(source)

        @router.post(
            "/sources/{source_id}/documents",
            response_model=JobResponseDto,
            status_code=status.HTTP_202_ACCEPTED,
        )
        async def upload_async(
            source_id: UUID,
            request: Request,
            file: UploadFile = File(...),
            idempotency_key: str = Header(..., alias="Idempotency-Key"),
        ):
            if (denied := disabled()) is not None:
                return denied
            try:
                job, _, _ = await self._service.upload_async(principal(request), source_id, file, idempotency_key)
                return JobResponseDto.model_validate(job)
            except UploadRejected as exc:
                code = exc.code
                response_status = 413 if code == "file_too_large" else 415 if code.startswith("unsupported_") else 422
                return JSONResponse({"error": code}, status_code=response_status)
            except ValueError:
                return JSONResponse({"error": "idempotency_conflict"}, status_code=409)
            except PermissionError:
                return JSONResponse({"error": "forbidden"}, status_code=403)
            except StorageUnavailable:
                return JSONResponse({"error": "storage_unavailable"}, status_code=503)

        @router.get("/jobs/{job_id}", response_model=JobResponseDto)
        async def job_status_async(job_id: UUID, request: Request):
            if (denied := disabled()) is not None:
                return denied
            try:
                result = await self._service.get_job_async(principal(request), job_id)
            except PermissionError:
                return JSONResponse({"error": "forbidden"}, status_code=403)
            if result is None:
                return JSONResponse({"error": "not_found"}, status_code=404)
            return JobResponseDto.model_validate(result[0])

        @router.get("/versions/{version_id}", response_model=DocumentVersionResponseDto)
        async def version_status_async(version_id: UUID, request: Request):
            if (denied := disabled()) is not None:
                return denied
            try:
                version = await self._service.get_version_async(principal(request), version_id)
            except PermissionError:
                return JSONResponse({"error": "forbidden"}, status_code=403)
            if version is None:
                return JSONResponse({"error": "not_found"}, status_code=404)
            return DocumentVersionResponseDto.model_validate(version)

        @router.post("/jobs/{job_id}/cancel", response_model=JobResponseDto)
        async def cancel_async(job_id: UUID, request: Request):
            if (denied := disabled()) is not None:
                return denied
            try:
                cancelled = await self._service.cancel_async(principal(request), job_id)
                current = await self._service.get_job_async(principal(request), job_id)
            except PermissionError:
                return JSONResponse({"error": "forbidden"}, status_code=403)
            if not cancelled or current is None:
                return JSONResponse({"error": "not_found"}, status_code=404)
            return JobResponseDto.model_validate(current[0])

        return router
