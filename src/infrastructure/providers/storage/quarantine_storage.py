"""S3-compatible quarantine adapter; never issues public ACLs or download links."""

from __future__ import annotations

import asyncio
from io import BytesIO

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from src.infrastructure.di.inject import inject
from src.infrastructure.utils.config_reader import ConfigReader


class StorageUnavailable(RuntimeError):
    pass


class StorageMissing(StorageUnavailable):
    pass


@inject
class QuarantineStorage:
    __di_singleton__ = True

    def __init__(self, config_reader: ConfigReader):
        self._cfg = config_reader.settings.ingestion
        self._client = None

    async def start_async(self) -> None:
        if not self._cfg.enabled:
            raise StorageUnavailable("Quarantine storage disabled")
        if self._client is not None:
            return
        client = boto3.client(
            "s3",
            endpoint_url=self._cfg.s3_url,
            aws_access_key_id=self._cfg.s3_access_key,
            aws_secret_access_key=self._cfg.s3_secret_key,
            region_name="us-east-1",
            config=BotoConfig(
                signature_version="s3v4",
                retries={"max_attempts": 0},
                connect_timeout=self._cfg.timeout_seconds,
                read_timeout=self._cfg.timeout_seconds,
                s3={"addressing_style": "path"},
            ),
        )
        try:
            await asyncio.to_thread(client.head_bucket, Bucket=self._cfg.s3_bucket)
        except (ClientError, BotoCoreError, OSError):
            raise StorageUnavailable("Quarantine storage unavailable") from None
        self._client = client

    async def close_async(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            await asyncio.to_thread(client.close)

    async def put_async(self, key: str, contents: bytes, checksum: str) -> None:
        if self._client is None or not key.startswith("quarantine/internal/"):
            raise StorageUnavailable("Quarantine storage unavailable")
        try:
            await asyncio.to_thread(
                self._client.put_object,
                Bucket=self._cfg.s3_bucket,
                Key=key,
                Body=BytesIO(contents),
                ContentLength=len(contents),
                Metadata={"sha256": checksum},
            )
            info = await asyncio.to_thread(self._client.head_object, Bucket=self._cfg.s3_bucket, Key=key)
            if info["ContentLength"] != len(contents) or info.get("Metadata", {}).get("sha256") != checksum:
                raise StorageUnavailable("Storage integrity failed")
        except (ClientError, BotoCoreError, OSError):
            raise StorageUnavailable("Quarantine storage unavailable") from None

    async def get_async(self, key: str) -> bytes:
        if self._client is None or not key.startswith("quarantine/internal/"):
            raise StorageUnavailable("Quarantine storage unavailable")

        def read_bounded():
            response = self._client.get_object(Bucket=self._cfg.s3_bucket, Key=key)
            body = response["Body"]
            try:
                data = body.read(self._cfg.max_file_bytes + 1)
                if len(data) > self._cfg.max_file_bytes:
                    raise StorageUnavailable("Quarantine object too large")
                return data
            finally:
                body.close()

        try:
            return await asyncio.to_thread(read_bounded)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                raise StorageMissing("Quarantine object missing") from None
            raise StorageUnavailable("Quarantine storage unavailable") from None
        except (BotoCoreError, OSError):
            raise StorageUnavailable("Quarantine storage unavailable") from None
