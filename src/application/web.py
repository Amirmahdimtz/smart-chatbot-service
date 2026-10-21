"""Controller auto discovery: {prefix}/{feature}, deterministic and duplicate-safe."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

from fastapi import FastAPI

from src.infrastructure.di.bootstrap import Container
from src.infrastructure.utils.config_reader import ConfigReader


def mount_controllers(app: FastAPI, container: Container) -> None:
    prefix = container.resolve(ConfigReader).get_api_prefix()
    feature_root = Path(__file__).resolve().parent
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for folder in sorted(feature_root.iterdir()):
        if not folder.is_dir() or folder.name.startswith("_") or not re.fullmatch(r"[a-z][a-z0-9_]*", folder.name):
            continue
        module_path = folder / f"{folder.name}_controller.py"
        if not module_path.is_file():
            continue
        module = importlib.import_module(f"src.application.{folder.name}.{folder.name}_controller")
        class_name = "".join(s.capitalize() for s in folder.name.split("_")) + "Controller"
        cls = getattr(module, class_name)
        controller = container.compose(cls)
        router = controller.api()
        route_prefix = f"{prefix}/{folder.name}"
        for route in router.routes:
            key = (route_prefix + route.path, tuple(sorted(route.methods or ())))
            if key in seen:
                raise RuntimeError("Duplicate API route")
            seen.add(key)
        app.include_router(router, prefix=route_prefix)
