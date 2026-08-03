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


def _generic_fallback(code: str):
    """R10-B (frozen rule 11): any ACTIVE Stage row WITHOUT a bespoke package
    is served by ONE GenericStageHandler instance — new operations are
    configuration, not code. Instances are cached in the registry so every
    dispatch site keeps its by-code lookup semantics. Lazy DB read (registry
    loads at app-ready, before DB use elsewhere); returns None when the code
    isn't a real active stage (callers keep their fail-closed behavior)."""
    try:
        from production.models import Stage
        row = Stage.objects.filter(code=code, is_active=True).only(
            'code', 'name').first()
    except Exception:      # DB not ready (migrations/collectstatic) — no fallback
        return None
    if row is None:
        return None
    from production.stages.generic_stage.handler import GenericStageHandler
    instance = GenericStageHandler(code=row.code, name=row.name)
    _REGISTRY[code] = instance
    return instance


def get(code: str):
    """Return the handler for `code` — bespoke first, else the generic
    archetype for any active configured stage; KeyError otherwise."""
    try:
        return _REGISTRY[code]
    except KeyError:
        instance = _generic_fallback(code)
        if instance is not None:
            return instance
        raise KeyError(f"No stage handler registered for {code!r}")


def has(code: str) -> bool:
    if code in _REGISTRY:
        return True
    return _generic_fallback(code) is not None


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
