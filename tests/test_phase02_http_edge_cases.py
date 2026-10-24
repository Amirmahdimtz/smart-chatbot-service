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
    statuses, called, _ = asyncio.run(_exercise_async(frames, method="POST", headers=[(b"content-length", b"4")]))
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


def test_malformed_content_length_values_are_rejected():
    invalid_values = (b"+3", b"-3", b" 3", b"3 ", b"3, 3", b"")
    for value in invalid_values:
        statuses, called, received = asyncio.run(
            _exercise_async([], method="POST", headers=[(b"content-length", value)])
        )
        assert statuses == [400]
        assert not called
        assert not received


def test_full_rate_limit_cache_does_not_hold_lock_during_slow_rejection():
    import time
    from collections import defaultdict, deque

    async def exercise():
        started = asyncio.Event()
        release = asyncio.Event()

        async def upstream(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        guard = HttpSecurityMiddleware(upstream, max_bytes=8, rate_per_minute=2, timeout=1)
        guard._hits = defaultdict(deque, {f"client-{i}": deque([time.monotonic()]) for i in range(10000)})

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def slow_send(message):
            if message["type"] == "http.response.start":
                started.set()
                await release.wait()

        async def normal_send(message):
            pass

        async def rejected():
            await guard(
                _scope() | {"client": ("unknown", 1234)},
                receive,
                slow_send,
            )

        first = asyncio.create_task(rejected())
        try:
            await asyncio.wait_for(started.wait(), timeout=1)
            # A slow client's 429 response must not block another client's
            # normal request from entering the rate limiter.
            await asyncio.wait_for(
                guard(
                    _scope() | {"client": ("client-0", 1234)},
                    receive,
                    normal_send,
                ),
                timeout=0.5,
            )
        finally:
            release.set()
            await first

    asyncio.run(exercise())
