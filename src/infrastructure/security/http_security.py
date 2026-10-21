"""ASGI enforcement of body limits, basic client limits, deadlines and headers."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

from starlette.responses import JSONResponse


class HttpSecurityMiddleware:
    def __init__(self, app, *, max_bytes: int, rate_per_minute: int, timeout: float):
        self.app = app
        self.max_bytes = max_bytes
        self.limit = rate_per_minute
        self.timeout = timeout
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        headers_to_add = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"no-referrer"),
            (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
            (b"cache-control", b"no-store"),
        ]

        async def secured_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + headers_to_add
            await send(message)

        async def reject(status, code):
            await JSONResponse({"error": code}, status_code=status)(scope, receive, secured_send)

        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            await reject(400, "bad_request")
            return
        if length < 0 or length > self.max_bytes:
            await reject(413, "payload_too_large")
            return
        ip = scope.get("client")
        key = ip[0] if ip else "unknown"
        async with self._lock:
            if key not in self._hits and len(self._hits) >= 10000:
                await reject(429, "rate_limited")
                return
            now = time.monotonic()
            hits = self._hits[key]
            while hits and hits[0] < now - 60:
                hits.popleft()
            if len(hits) >= self.limit:
                blocked = True
            else:
                hits.append(now)
                blocked = False
            # Prevent unbounded growth of idle client tracking.
            if len(self._hits) > 10000:
                for host in list(self._hits):
                    if not self._hits[host] or self._hits[host][-1] < now - 60:
                        del self._hits[host]
        if blocked:
            await reject(429, "rate_limited")
            return

        async def handle_request():
            # Buffer a bounded request body before entering handlers, including transfer-encoded bodies.
            # This closes the gap where a handler never consumes the request stream.
            events = []
            size = 0
            if scope["method"] in ("POST", "PUT", "PATCH", "DELETE"):
                while True:
                    event = await receive()
                    if event["type"] == "http.disconnect":
                        return
                    events.append(event)
                    size += len(event.get("body", b""))
                    if size > self.max_bytes:
                        raise RequestTooLarge()
                    if not event.get("more_body", False):
                        break

            async def replay_receive():
                if events:
                    return events.pop(0)
                return await receive()

            await self.app(scope, replay_receive, secured_send)

        try:
            await asyncio.wait_for(handle_request(), timeout=self.timeout)
        except RequestTooLarge:
            await reject(413, "payload_too_large")
        except TimeoutError:
            await reject(504, "request_timeout")


class RequestTooLarge(Exception):
    pass
