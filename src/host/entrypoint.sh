#!/bin/sh
set -eu
exec python -m uvicorn src.host.app:app --host "${SCB_LISTEN_HOST:-0.0.0.0}" --port "${SCB_LISTEN_PORT:-5000}" --no-access-log --no-proxy-headers
