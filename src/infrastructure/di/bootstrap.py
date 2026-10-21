"""App-scoped DI container. No mutable global provider instances."""
from __future__ import annotations

import inspect
from typing import get_type_hints

from src.infrastructure.di.reflection import discover_providers
from src.infrastructure.di.inject import _active


class DependencyResolutionError(RuntimeError):
    pass


class Container:
    def __init__(self, providers: dict[type, type]):
        self._providers = providers
        self._singletons: dict[type, object] = {}
        self._resolving: set[type] = set()

    def resolve(self, cls: type):
        if cls not in self._providers:
            raise DependencyResolutionError(f"Unregistered dependency: {cls.__name__}")
        if cls in self._singletons:
            return self._singletons[cls]
        if cls in self._resolving:
            raise DependencyResolutionError(f"Circular dependency: {cls.__name__}")
        self._resolving.add(cls)
        try:
            sig = inspect.signature(cls.__init__)
            annotations = get_type_hints(cls.__init__)
            kwargs = {}
            for name, parameter in sig.parameters.items():
                if name == "self" or parameter.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
                    continue
                if parameter.default is not inspect.Parameter.empty:
                    continue
                target = annotations.get(name)
                if target is None or not isinstance(target, type):
                    raise DependencyResolutionError(f"Missing type hint: {cls.__name__}.{name}")
                kwargs[name] = self.resolve(target)
            token = _active.set(self)
            try:
                instance = cls(**kwargs)
            finally:
                _active.reset(token)
            if getattr(cls, "__di_singleton__", False):
                self._singletons[cls] = instance
            return instance
        finally:
            self._resolving.remove(cls)

    def compose(self, cls: type):
        if cls not in self._providers:
            raise DependencyResolutionError(f"Unregistered controller: {cls.__name__}")
        token = _active.set(self)
        try:
            return cls()
        finally:
            _active.reset(token)


def bootstrap_di() -> Container:
    return Container(discover_providers())
