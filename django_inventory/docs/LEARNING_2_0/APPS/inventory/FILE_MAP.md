# inventory — FILE_MAP

## TL;DR (1 min)
FILE_MAP: every important file in this app and how they connect.

## models.py — NO tables; re-exports Role/SidebarItemRule from accounts (back-compat shim).
## middleware.py ★ — SidebarAccessMiddleware (menu+URL gated together).
## context_processors.py — sidebar data to every template.
## signals.py — TOMBSTONE explaining why signals are BANNED (ADR-0001) — read it.
## views/ — dashboard.py (role-aware home), access_hub_views/role_views/
sidebar_access_views (Access hub), tracking_*.py (4: barcode dashboard/export/
history — inventory owns /tracking/), mixins.py (RBAC gates).
## forms/ — role_forms. urls.py + tracking_urls.py — route maps in headers.
## Junior note: this app SAVES nothing of its own — it composes reads and routes
role/sidebar writes to accounts services. A new view without a SidebarItemRule =
an unprotected URL (the whitelist-bug class — always register the rule).

---
*Depth: [config/inventory/README.md](../../../../config/inventory/README.md) (business) ·
[docs/apps/inventory/GUIDE.md](../../../apps/inventory/GUIDE.md) (file-by-file). This = navigation/flow only.*
