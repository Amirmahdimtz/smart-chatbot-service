"""Deterministic provider discovery using architecture-guide package conventions."""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path

SKIP = frozenset({"di", "dtos", "models", "scripts", "alembic", "versions", "res", "sso"})
ROOTS = ("src.infrastructure", "src.core", "src.application")


def discover_providers() -> dict[type, type]:
    providers: dict[type, type] = {}
    for root_name in ROOTS:
        root = importlib.import_module(root_name)
        modules: list[str] = []
        for root_path in root.__path__:
            for path in Path(root_path).rglob("*.py"):
                parts = path.relative_to(root_path).with_suffix("").parts
                if path.name == "__init__.py" or any(part in SKIP for part in parts):
                    continue
                modules.append(root_name + "." + ".".join(parts))
        for module_name in sorted(set(modules)):
            # Import errors are fatal: a missing security provider must not be silently skipped.
            module = importlib.import_module(module_name)
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ != module.__name__ or not cls.__dict__.get("__di_injectable__", False):
                    continue
                if cls in providers:
                    raise RuntimeError("Duplicate injectable class")
                providers[cls] = cls
    return providers
