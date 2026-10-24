"""ASGI regression coverage for HTTP framing ambiguity and body-size bypasses."""

from __future__ import annotations

import asyncio

from src.infrastructure.security.http_security import HttpSecurityMiddleware


def _scope(method="GET", headers=()):
    return {"type": "http", "method": method, "headers": list(headers), "client": ("test-peer", 12345)}


async def _exercise_async(frames, *, method="GET", headers=(), limit=8):
    messages = []
    received = []
    upstream_called = False
    incoming = iter(frames)

    async def upstream(scope, receive, send):
        nonlocal upstream_called
        upstream_called = True
        event = await receive()
        received.append(event)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def receive():
        return next(incoming)

    async def send(message):
        messages.append(message)

    middleware = HttpSecurityMiddleware(upstream, max_bytes=limit, rate_per_minute=30, timeout=1.0)
    await middleware(_scope(method, headers), receive, send)
    statuses = [message["status"] for message in messages if message["type"] == "http.response.start"]
    return statuses, upstream_called, received


def test_chunked_get_body_larger_than_limit_is_rejected_even_without_content_length():
    frames = [
        {"type": "http.request", "body": b"123456", "more_body": True},
        {"type": "http.request", "body": b"789", "more_body": False},
    ]
    statuses, called, received = asyncio.run(_exercise_async(frames))
    assert statuses == [413]
    assert not called
    assert received == []


def test_empty_chunk_flood_is_coalesced_to_one_bounded_asgi_event():
    frames = [{"type": "http.request", "body": b"", "more_body": True} for _ in range(2000)]
    frames.append({"type": "http.request", "body": b"abc", "more_body": False})
    statuses, called, received = asyncio.run(_exercise_async(frames, method="OPTIONS"))
    assert statuses == [200]
    assert called
    assert received == [{"type": "http.request", "body": b"abc", "more_body": False}]


def test_declared_length_mismatch_rejected_without_invoking_application():
    frames = [{"type": "http.request", "body": b"abc", "more_body": False}]
    statuses, called, _ = asyncio.run(
        _exercise_async(frames, method="POST", headers=[(b"content-length", b"4")])
    )
    assert statuses == [400]
    assert not called


def test_ambiguous_http_body_framing_rejected_before_body_read():
    cases = [
        [(b"content-length", b"1"), (b"content-length", b"1")],
        [(b"content-length", b"1"), (b"transfer-encoding", b"chunked")],
    ]
    for headers in cases:
        statuses, called, _ = asyncio.run(_exercise_async([], method="POST", headers=headers))
        assert statuses == [400]
        assert not called


def test_body_replay_preserves_payload_for_standard_post():
    frames = [
        {"type": "http.request", "body": b"ab", "more_body": True},
        {"type": "http.request", "body": b"cd", "more_body": False},
    ]
    statuses, called, received = asyncio.run(
        _exercise_async(frames, method="POST", headers=[(b"content-length", b"4")])
    )
    assert statuses == [200]
    assert called
    assert received == [{"type": "http.request", "body": b"abcd", "more_body": False}]
