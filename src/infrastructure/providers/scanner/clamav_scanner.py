"""ClamAV INSTREAM scanning; only an explicit clean verdict succeeds."""

from __future__ import annotations

import asyncio
import struct

from src.infrastructure.di.inject import inject
from src.infrastructure.utils.config_reader import ConfigReader


class ScanUnavailable(RuntimeError):
    pass


class MalwareDetected(RuntimeError):
    pass


@inject
class ClamAvScanner:
    __di_singleton__ = True

    def __init__(self, config_reader: ConfigReader):
        self._cfg = config_reader.settings.ingestion

    async def scan_async(self, contents: bytes) -> None:
        if not self._cfg.enabled or not contents or len(contents) > self._cfg.max_file_bytes:
            raise ScanUnavailable("Antivirus scan unavailable")

        async def scan():
            reader, writer = await asyncio.open_connection(self._cfg.clamd_host, self._cfg.clamd_port)
            try:
                writer.write(b"zINSTREAM" + bytes((0,)))
                for offset in range(0, len(contents), 65536):
                    chunk = contents[offset : offset + 65536]
                    writer.write(struct.pack("!I", len(chunk)) + chunk)
                    await writer.drain()
                writer.write(struct.pack("!I", 0))
                await writer.drain()
                verdict = await reader.readuntil(bytes((0,)))
                if verdict.startswith(b"stream: ") and verdict.endswith(b" FOUND" + bytes((0,))):
                    raise MalwareDetected("Malware detected")
                if verdict != b"stream: OK" + bytes((0,)):
                    raise ScanUnavailable("Antivirus scan unavailable")
            finally:
                writer.close()
                await writer.wait_closed()

        try:
            await asyncio.wait_for(scan(), timeout=self._cfg.timeout_seconds)
        except MalwareDetected:
            raise
        except (OSError, TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, ScanUnavailable):
            raise ScanUnavailable("Antivirus scan unavailable") from None
