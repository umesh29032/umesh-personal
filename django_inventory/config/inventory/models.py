"""Inventory app — RBAC models relocated to `accounts` (2026-06).

`Role` + `SidebarItemRule` now live in `accounts.models` so identity + access
control are ONE foundation the whole app depends on (and which depends on nothing
domain-specific). They're re-exported here so existing `from inventory.models
import Role` call-sites keep working unchanged.

inventory still owns the access-control ADMIN UI (Access Hub + Sidebar Access
editor), `SidebarAccessMiddleware`, the sidebar context processor, and the
cross-domain dashboards — all of which now consume RBAC from accounts (via the
`inventory.services` re-export shim).
"""
from accounts.models import Role, SidebarItemRule  # noqa: F401  (re-export shim)

__all__ = ['Role', 'SidebarItemRule']
