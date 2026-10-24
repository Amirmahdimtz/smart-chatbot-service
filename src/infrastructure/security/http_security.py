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
        raw_headers = scope.get("headers", [])
        content_lengths = [value for name, value in raw_headers if name.lower() == b"content-length"]
        has_transfer_encoding = any(name.lower() == b"transfer-encoding" for name, _ in raw_headers)
        headers_to_add = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"no-referrer"),
            (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
            (b"cache-control", b"no-store"),
        ]

        response_started = False

        async def secured_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + headers_to_add
                response_started = True
            await send(message)

        async def reject(status, code):
            await JSONResponse({"error": code}, status_code=status)(scope, receive, secured_send)

        # Conflicting framing is rejected before reading a body: proxy interpretation
        # must not differ from the application's interpretation.
        if len(content_lengths) > 1 or (content_lengths and has_transfer_encoding):
            await reject(400, "bad_request")
            return
        try:
            declared_length = int(content_lengths[0]) if content_lengths else None
        except ValueError:
            await reject(400, "bad_request")
            return
        if declared_length is not None and declared_length < 0:
            await reject(400, "bad_request")
            return
        if declared_length is not None and declared_length > self.max_bytes:
            await reject(413, "payload_too_large")
            return
        ip = scope.get("client")
        key = ip[0] if ip else "unknown"
        async with self._lock:
            now = time.monotonic()
            if key not in self._hits and len(self._hits) >= 10000:
                # Clear expired entries before enforcing the tracking capacity.
                for host, bucket in list(self._hits.items()):
                    while bucket and bucket[0] <= now - 60:
                        bucket.popleft()
                    if not bucket:
                        del self._hits[host]
                if len(self._hits) >= 10000:
                    await reject(429, "rate_limited")
                    return
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
            # Every HTTP method may carry a body, including GET/HEAD/OPTIONS.
            # Aggregate payload bytes into a single bounded frame: storing every
            # incoming ASGI frame separately has unbounded overhead for empty chunks.
            body = bytearray()
            while True:
                event = await receive()
                if event["type"] == "http.disconnect":
                    return
                chunk = event.get("body", b"")
                if len(body) + len(chunk) > self.max_bytes:
                    raise RequestTooLarge()
                body.extend(chunk)
                if not event.get("more_body", False):
                    break
            if declared_length is not None and len(body) != declared_length:
                raise InvalidRequestBody()

            delivered = False

            async def replay_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, replay_receive, secured_send)

        try:
            await asyncio.wait_for(handle_request(), timeout=self.timeout)
        except RequestTooLarge:
            await reject(413, "payload_too_large")
        except InvalidRequestBody:
            await reject(400, "bad_request")
        except TimeoutError:
            if response_started:
                # A second http.response.start is invalid after headers were sent.
                # Abort the incomplete response rather than misreporting a new status.
                raise
            await reject(504, "request_timeout")


class RequestTooLarge(Exception):
    pass


class InvalidRequestBody(Exception):
    pass
