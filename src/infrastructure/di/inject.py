"""Architecture-guide constructor injection with per-composition-container scoping."""
from __future__ import annotations

from contextvars import ContextVar
from functools import wraps
from typing import TYPE_CHECKING, TypeVar, get_type_hints

if TYPE_CHECKING:
    from src.infrastructure.di.bootstrap import Container

_active: ContextVar[Container | None] = ContextVar("scb_di_container", default=None)
T = TypeVar("T", bound=type)


def inject(cls: T) -> T:
    original = cls.__init__

    @wraps(original)
    def initialize(self, *args, **kwargs):
        import inspect
        sig = inspect.signature(original)
        bound = sig.bind_partial(self, *args, **kwargs)
        container = _active.get()
        if container is not None:
            hints = get_type_hints(original)
            for name, parameter in sig.parameters.items():
                if name == "self" or name in bound.arguments or parameter.default is not inspect.Parameter.empty:
                    continue
                dependency = hints.get(name)
                if isinstance(dependency, type):
                    kwargs[name] = container.resolve(dependency)
        original(self, *args, **kwargs)

    cls.__init__ = initialize
    cls.__di_injectable__ = True
    return cls
