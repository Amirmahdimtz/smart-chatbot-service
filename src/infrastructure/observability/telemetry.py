"""Bounded, non-identifying HTTP telemetry; never record headers, bodies or subjects."""
from __future__ import annotations

import json
import logging
import re
import time
from uuid import UUID, uuid4

from opentelemetry import trace
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware


class HttpMetrics:
    def __init__(self):
        self.registry = CollectorRegistry(auto_describe=True)
        self.requests = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"], registry=self.registry)
        self.duration = Histogram("http_request_duration_seconds", "HTTP response seconds", ["method", "route"], registry=self.registry)

    def output(self) -> bytes:
        return generate_latest(self.registry)


class SafeJsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"event": "http_request", "level": record.levelname,
                           "method": getattr(record, "http_method", ""),
                           "route": getattr(record, "route_template", ""),
                           "status": getattr(record, "status_code", 0),
                           "request_id": getattr(record, "request_id", ""),
                           "duration_ms": getattr(record, "duration_ms", 0)}, separators=(",", ":"))


def safe_id(value: str | None) -> str:
    try:
        return str(UUID(value)) if value else str(uuid4())
    except (ValueError, TypeError, AttributeError):
        return str(uuid4())


class TelemetryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, metrics: HttpMetrics):
        super().__init__(app)
        self.metrics = metrics
        self.logger = logging.getLogger("scb.http")
        self.tracer = trace.get_tracer("smart-chatbot-service")

    async def dispatch(self, request, call_next):
        request_id = safe_id(request.headers.get("x-request-id"))
        correlation_id = safe_id(request.headers.get("x-correlation-id"))
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        start = time.monotonic()
        with self.tracer.start_as_current_span("http.server") as span:
            try:
                response = await call_next(request)
            except Exception:
                # Never include exception message or raw path in HTTP telemetry.
                self.logger.exception("Unhandled HTTP error")
                raise
            finally:
                elapsed = time.monotonic() - start
        route = request.scope.get("route")
        path = route.path if route is not None else "unmatched"
        # Only static registered templates are allowed as metric labels.
        if not re.fullmatch(r"/[A-Za-z0-9_/{}/-]+", path):
            path = "unmatched"
        method = request.method if request.method in {"GET", "POST", "HEAD", "OPTIONS", "PUT", "PATCH", "DELETE"} else "OTHER"
        self.metrics.requests.labels(method, path, str(response.status_code)).inc()
        self.metrics.duration.labels(method, path).observe(elapsed)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        self.logger.info("request", extra={"http_method": method, "route_template": path,
                                            "status_code": response.status_code,
                                            "duration_ms": round(elapsed * 1000), "request_id": request_id})
        return response
