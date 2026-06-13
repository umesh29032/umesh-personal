"""Stage handler registry (M2 stage engine).

Each stage registers a StageHandler under its `code`. Dispatch (views, services,
costing) looks the handler up by code instead of branching on `if stage_type ==`.
autodiscover() imports every production/stages/<stage>/handler.py so a new stage
is registered just by existing — no central list to edit (open-closed).
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .handler import StageHandler

_REGISTRY: dict[str, "StageHandler"] = {}


def register(handler):
    """Register a StageHandler. Accepts a class (instantiated once) or an instance,
    so it works as a class decorator: `@register` above `class FooHandler(...)`.
    Returns the original argument unchanged (decorator-friendly)."""
    instance = handler() if isinstance(handler, type) else handler
    code = getattr(instance, 'code', '')
    if not code:
        raise ValueError("StageHandler.code must be set before registering")
    existing = _REGISTRY.get(code)
    if existing is not None and existing is not instance:
        raise ValueError(f"Duplicate stage handler registered for code {code!r}")
    _REGISTRY[code] = instance
    return handler


def get(code: str):
    """Return the handler for `code`, or raise KeyError if none is registered."""
    try:
        return _REGISTRY[code]
    except KeyError:
        raise KeyError(f"No stage handler registered for {code!r}")


def has(code: str) -> bool:
    return code in _REGISTRY


def all_handlers() -> dict:
    """Snapshot copy of the registry (safe to mutate)."""
    return dict(_REGISTRY)


def clear() -> None:
    """Reset the registry — test helper only."""
    _REGISTRY.clear()


def autodiscover() -> None:
    """Import every production/stages/<stage>/handler.py so handlers self-register.
    Idempotent; stage packages without a handler module are skipped. Called from
    production.apps.ready() once the first stage migrates (M2.2)."""
    import production.stages as stages_pkg

    for mod in pkgutil.iter_modules(stages_pkg.__path__):
        if mod.name == 'base' or not mod.ispkg:
            continue
        try:
            importlib.import_module(f"production.stages.{mod.name}.handler")
        except ModuleNotFoundError:
            continue
