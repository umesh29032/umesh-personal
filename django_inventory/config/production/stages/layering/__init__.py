"""Layering stage package (M2.2 — adapter-only for now).

Currently holds just the handler (a thin adapter over layering_service). The
service / models / views / templates stay in place until dispatch is migrated to
the registry and proven (M2.6); they move here only after that.
"""
