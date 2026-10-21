"""Real Vault KV v2 client boundary (enabled only with approved Vault configuration)."""

from __future__ import annotations

import os
from urllib.parse import quote

import httpx

from src.infrastructure.di.inject import inject
from src.infrastructure.utils.config_reader import ConfigReader


class VaultUnavailable(RuntimeError):
    pass


@inject
class VaultService:
    __di_singleton__ = True

    def __init__(self, config_reader: ConfigReader):
        self._cfg = config_reader.settings.vaulthc

    async def read_secret_async(self, path: str) -> dict:
        if not self._cfg.enabled or not path or path.startswith("/") or ".." in path.split("/"):
            raise VaultUnavailable("Vault access unavailable")
        token = os.environ.get("SCB_VAULT_TOKEN")
        if not token:
            raise VaultUnavailable("Vault credential unavailable")
        url = f"{self._cfg.address.rstrip('/')}/v1/{quote(self._cfg.mount, safe='')}/data/{quote(path, safe='/')}"
        try:
            async with httpx.AsyncClient(timeout=5, follow_redirects=False, trust_env=False) as client:
                response = await client.get(url, headers={"X-Vault-Token": token})
                response.raise_for_status()
                secret = response.json()["data"]["data"]
                if not isinstance(secret, dict):
                    raise ValueError("Unexpected Vault response")
                return secret
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise VaultUnavailable("Vault access unavailable") from None

    async def check_async(self) -> None:
        if self._cfg.enabled:
            await self.read_secret_async(self._cfg.startup_check_path)
